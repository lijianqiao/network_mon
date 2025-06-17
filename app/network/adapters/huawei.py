"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: huawei.py
@DateTime: 2025-06-18
@Docs: Huawei设备适配器
"""

import re
from typing import Any

from .base import BaseAdapter, CommandError, ParseError, UnsupportedActionError


class HuaweiAdapter(BaseAdapter):
    """Huawei VRP设备适配器

    支持华为设备的命令生成和输出解析
    优先使用 ntc-templates TextFSM 解析，回退到手写正则解析
    """

    def __init__(self):
        """初始化Huawei适配器"""
        self._command_map = {
            "get_version": "display version",
            "get_interfaces": "display interface brief",
            "get_interface_detail": "display interface {interface}",
            "get_mac_address_table": "display mac-address",
            "get_arp_table": "display arp all",
            "get_vlan": "display vlan",
            # Raw commands
            "show_running_config": "display current-configuration",
            "show_startup_config": "display saved-configuration",
            # Commands with params
            "find_mac": "display mac-address | include {mac_address}",
            "find_arp": "display arp | include {ip_address}",
            "get_vlan_detail": "display vlan {vlan_id}",
            "ping": "ping {target}",
            "traceroute": "tracert {target}",
            "save_config": "save",
        }

        # 必需参数映射
        self._required_params = {
            "get_interface_detail": ["interface"],
            "find_mac": ["mac_address"],
            "find_arp": ["ip_address"],
            "get_vlan_detail": ["vlan_id"],
            "ping": ["target"],
            "traceroute": ["target"],
        }

    def get_platform(self) -> str:
        """获取华为设备的Scrapli平台标识

        Returns:
            平台标识
        """
        return "huawei_vrp"

    def get_supported_actions(self) -> list[str]:
        """获取支持的动作列表

        Returns:
            支持的动作列表
        """
        return list(self._command_map.keys())

    def get_command(self, action: str, **params) -> str:
        """根据动作和参数生成Huawei设备命令

        Args:
            action: 动作类型
            **params: 命令参数

        Returns:
            Huawei设备命令字符串

        Raises:
            UnsupportedActionError: 当不支持的动作时
            CommandError: 当参数错误时
        """
        if not self.is_action_supported(action):
            raise UnsupportedActionError(f"Huawei适配器不支持的动作: {action}")

        # 检查必需参数
        required_params = self._required_params.get(action, [])
        for param in required_params:
            if param not in params:
                raise CommandError(f"动作 {action} 缺少必需参数: {param}")

        # 获取命令模板
        command_template = self._command_map[action]

        try:
            # 格式化命令
            if action == "find_mac":
                # MAC地址格式化为华为格式 (xxxx-xxxx-xxxx)
                mac = self._format_mac_address(params["mac_address"])
                return command_template.format(mac_address=mac)
            else:
                return command_template.format(**params)

        except KeyError as e:
            raise CommandError(f"命令参数错误: {e}") from e

    def parse_output(self, action: str, output: str) -> dict[str, Any]:
        """解析Huawei设备命令输出

        优先使用 ntc-templates TextFSM 解析，失败时回退到自定义解析

        Args:
            action: 动作类型
            output: 设备原始输出

        Returns:
            解析后的结构化数据

        Raises:
            ParseError: 当解析失败时
        """
        if not output or not output.strip():
            return {"raw": "", "parsed": None}

        try:
            # 获取对应的命令
            command = self._command_map.get(action, "")

            # 尝试使用 TextFSM 解析
            textfsm_result = self.parse_with_textfsm(action, command, output)
            if textfsm_result is not None:
                return {"raw": output, "parsed": textfsm_result, "method": "textfsm", "action": action}

            # TextFSM 解析失败，使用自定义解析
            fallback_result = self.parse_with_fallback(action, output)
            fallback_result["method"] = "fallback"
            fallback_result["action"] = action
            return fallback_result

        except Exception as e:
            raise ParseError(f"解析 {action} 输出失败: {e}") from e

    def parse_with_fallback(self, action: str, output: str) -> dict[str, Any]:
        """回退到自定义解析

        Args:
            action: 动作类型
            output: 设备原始输出

        Returns:
            解析后的结构化数据
        """
        parser_method = getattr(self, f"_parse_fallback_{action}", None)
        if parser_method:
            parsed_data = parser_method(output)
            return {"raw": output, "parsed": parsed_data}
        return {"raw": output, "parsed": None}

    def _parse_fallback_get_version(self, output: str) -> dict[str, Any] | None:
        """Fallback parser for 'display version'."""
        version_info = {}
        # Huawei Versatile Routing Platform Software
        # VRP (R) software, Version 8.191 (CE6850 V200R019C10SPC800)
        match = re.search(r"VRP \(R\) software, Version ([\d\.]+) \((.+?)\)", output)
        if match:
            version_info["vrp_version"] = match.group(1)
            version_info["full_version"] = match.group(2)

        # Huawei CE6850-48S6Q-HI Switch uptime is 2 weeks, 4 days, 21 hours, 3 minutes
        match = re.search(r"uptime is (.*)", output, re.IGNORECASE)
        if match:
            version_info["uptime"] = match.group(1).strip()

        return version_info if version_info else None

    def _parse_fallback_get_interfaces(self, output: str) -> list[dict[str, str]] | None:
        """Fallback parser for 'display interface brief'."""
        interfaces = []
        lines = output.strip().split("\n")
        # PHY: Physical state, Protocol: Link-layer state
        # Interface                   PHY   Protocol  InUti/OutUti   inErrors/outErrors
        # Eth-Trunk1                  up    up        0.01%/0.01%          0/0
        # GigabitEthernet0/0/0        down  down         0%/0%             0/0
        # GigabitEthernet0/0/1        up    up        0.01%/0.01%          0/0
        for line in lines:
            # A simple regex to capture the main interface line, avoiding headers
            match = re.search(r"^(?P<interface>\S+)\s+(?P<phy>\*?down|up)\s+(?P<protocol>\*?down|up)\s+.*", line)
            if match:
                interfaces.append(match.groupdict())
        return interfaces if interfaces else None

    def get_connection_extras(self) -> dict[str, Any]:
        """获取Huawei设备连接特殊配置

        Returns:
            连接配置字典
        """
        return {
            "on_open": [
                "screen-length 0 temporary",  # 禁用分页
                "undo terminal monitor",  # 禁用终端监控
            ]
        }

    def _format_mac_address(self, mac: str) -> str:
        """格式化MAC地址为华为格式

        Args:
            mac: 原始MAC地址

        Returns:
            华为格式的MAC地址 (xxxx-xxxx-xxxx)
        """
        # 移除所有非字母数字字符
        clean_mac = re.sub(r"[^a-fA-F0-9]", "", mac.lower())

        if len(clean_mac) != 12:
            raise CommandError(f"无效的MAC地址格式: {mac}")

        # 转换为华为格式: xxxx-xxxx-xxxx
        return f"{clean_mac[0:4]}-{clean_mac[4:8]}-{clean_mac[8:12]}"
