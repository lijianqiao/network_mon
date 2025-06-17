"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: h3c.py
@DateTime: 2025-06-17
@Docs: H3C设备适配器，集成 ntc-templates TextFSM 解析
"""

import re
from typing import Any

from .base import BaseAdapter, CommandError, ParseError, UnsupportedActionError


class H3CAdapter(BaseAdapter):
    """H3C设备适配器

    支持华三设备的命令生成和输出解析
    优先使用 ntc-templates TextFSM 解析，回退到手写正则解析
    """

    def __init__(self):
        """初始化H3C适配器"""
        self._command_map = {
            "get_version": "display version",
            "get_interfaces": "display interface brief",
            "get_interface_detail": "display interface {interface}",
            "find_mac": "display mac-address | include {mac_address}",
            "get_mac_table": "display mac-address",
            "get_arp_table": "display arp",
            "find_arp": "display arp | include {ip_address}",
            "get_vlan": "display vlan",
            "get_vlan_detail": "display vlan {vlan_id}",
            "show_running": "display current-configuration",
            "show_startup": "display saved-configuration",
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
        """获取H3C设备的Scrapli平台标识

        Returns:
            平台标识
        """
        return "hp_comware"

    def get_supported_actions(self) -> list[str]:
        """获取支持的动作列表

        Returns:
            支持的动作列表
        """
        return list(self._command_map.keys())

    def get_command(self, action: str, **params) -> str:
        """根据动作和参数生成H3C设备命令

        Args:
            action: 动作类型
            **params: 命令参数

        Returns:
            H3C设备命令字符串

        Raises:
            UnsupportedActionError: 当不支持的动作时
            CommandError: 当参数错误时
        """
        if not self.is_action_supported(action):
            raise UnsupportedActionError(f"H3C适配器不支持的动作: {action}")

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
                # MAC地址格式化为H3C格式 (xxxx-xxxx-xxxx)
                mac = self._format_mac_address(params["mac_address"])
                return command_template.format(mac_address=mac)
            else:
                return command_template.format(**params)

        except KeyError as e:
            raise CommandError(f"命令参数错误: {e}") from e

    def parse_output(self, action: str, output: str) -> dict[str, Any]:
        """解析H3C设备命令输出

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

        # Default case for actions without a specific parser
        return {"raw": output, "parsed": None}

    def get_connection_extras(self) -> dict[str, Any]:
        """获取H3C设备连接特殊配置

        Returns:
            连接配置字典
        """
        return {
            "on_open": [
                "screen-length disable",  # 禁用分页
                "undo terminal monitor",  # 禁用终端监控
            ]
        }

    def _format_mac_address(self, mac: str) -> str:
        """格式化MAC地址为H3C格式

        Args:
            mac: 原始MAC地址

        Returns:
            H3C格式的MAC地址 (xxxx-xxxx-xxxx)
        """
        # 移除所有非字母数字字符
        clean_mac = re.sub(r"[^a-fA-F0-9]", "", mac.lower())

        if len(clean_mac) != 12:
            raise CommandError(f"无效的MAC地址格式: {mac}")

        # 转换为H3C格式: xxxx-xxxx-xxxx
        return f"{clean_mac[0:4]}-{clean_mac[4:8]}-{clean_mac[8:12]}"

    def _parse_fallback_get_version(self, output: str) -> dict[str, Any] | None:
        """解析版本信息

        Args:
            output: display version 命令输出

        Returns:
            解析后的版本信息
        """
        result: dict[str, str] = {}

        # 提取系统版本
        version_match = re.search(r"H3C Comware Software, Version (.+)", output)
        if version_match:
            result["version"] = version_match.group(1).strip()

        # 提取设备型号
        device_match = re.search(r"H3C (.+?) uptime", output)
        if device_match:
            result["device_model"] = device_match.group(1).strip()

        # 提取序列号
        serial_match = re.search(r"Device serial number : (.+)", output)
        if serial_match:
            result["serial_number"] = serial_match.group(1).strip()

        # 提取运行时间
        uptime_match = re.search(r"uptime is (.+)", output)
        if uptime_match:
            result["uptime"] = uptime_match.group(1).strip()

        return result if result else None

    def _parse_fallback_find_mac(self, output: str) -> list[dict[str, str]] | None:
        """解析MAC地址搜索结果

        Args:
            output: find_mac 命令输出

        Returns:
            解析后的MAC搜索结果
        """
        found_items: list[dict[str, str]] = []

        # H3C MAC表格式: MAC地址 VLAN ID 状态 端口
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line or "MAC" in line or "---" in line:
                continue

            parts = line.split()
            if len(parts) >= 4:
                found_items.append({"mac": parts[0], "vlan": parts[1], "status": parts[2], "interface": parts[3]})

        return found_items if found_items else None

    def _parse_fallback_get_interfaces(self, output: str) -> list[dict[str, Any]] | None:
        """解析接口简要信息

        Args:
            output: display interface brief 命令输出

        Returns:
            解析后的接口信息
        """
        interfaces: list[dict[str, Any]] = []

        # 解析接口列表
        for line in output.strip().split("\n"):
            if "Interface" in line or "---" in line:
                continue

            parts = line.split()
            if len(parts) >= 3:
                interfaces.append(
                    {
                        "interface": parts[0],
                        "link": parts[1],
                        "protocol": parts[2],
                        "ip_address": parts[3] if len(parts) > 3 else None,
                    }
                )

        return interfaces if interfaces else None

    def _parse_fallback_get_interface_detail(self, output: str) -> dict[str, Any] | None:
        """解析接口详细信息

        Args:
            output: display interface 命令输出

        Returns:
            解析后的接口详细信息
        """
        result: dict[str, str] = {}

        # 提取接口状态
        if "line protocol is up" in output:
            result["status"] = "up"
        elif "line protocol is down" in output:
            result["status"] = "down"
        else:
            result["status"] = "unknown"

        # 提取MAC地址
        mac_match = re.search(r"Hardware address is (.+)", output)
        if mac_match:
            result["mac_address"] = mac_match.group(1).strip()

        # 提取IP地址
        ip_match = re.search(r"Internet protocol processing : (.+)", output)
        if ip_match:
            result["ip_info"] = ip_match.group(1).strip()

        return result if result else None

    def _parse_fallback_get_mac_table(self, output: str) -> list[dict[str, str]] | None:
        """解析MAC地址表

        Args:
            output: display mac-address 命令输出

        Returns:
            解析后的MAC地址表
        """
        return self._parse_fallback_find_mac(output)  # 使用相同的解析逻辑

    def _parse_fallback_find_arp(self, output: str) -> list[dict[str, str]] | None:
        """解析ARP搜索结果

        Args:
            output: find_arp 命令输出

        Returns:
            解析后的ARP搜索结果
        """
        found: list[dict[str, str]] = []

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line or "Internet" in line or "---" in line:
                continue

            parts = line.split()
            if len(parts) >= 4:
                found.append({"ip": parts[0], "mac": parts[1], "type": parts[2], "interface": parts[3]})

        return found if found else None

    def _parse_fallback_get_vlan(self, output: str) -> list[dict[str, str]] | None:
        """解析VLAN简要信息

        Args:
            output: display vlan 命令输出

        Returns:
            解析后的VLAN信息
        """
        vlans: list[dict[str, str]] = []

        for line in output.strip().split("\n"):
            if "VLAN" in line or "---" in line:
                continue

            parts = line.split()
            if len(parts) >= 2:
                vlans.append(
                    {
                        "vlan_id": parts[0],
                        "name": parts[1] if len(parts) > 1 else "",
                        "status": parts[2] if len(parts) > 2 else "unknown",
                    }
                )

        return vlans if vlans else None

    def _parse_fallback_ping(self, output: str) -> dict[str, str] | None:
        """解析ping结果

        Args:
            output: ping 命令输出

        Returns:
            解析后的ping结果
        """
        result: dict[str, str] = {}

        # 提取成功率
        success_match = re.search(r"(\d+)% packet loss", output)
        if success_match:
            loss_rate = int(success_match.group(1))
            result["success_rate"] = str(100 - loss_rate)
            result["packet_loss"] = str(loss_rate)

        # 提取统计信息
        stats_match = re.search(r"(\d+) packets transmitted, (\d+) received", output)
        if stats_match:
            result["packets_sent"] = str(stats_match.group(1))
            result["packets_received"] = str(stats_match.group(2))

        return result if result else None
