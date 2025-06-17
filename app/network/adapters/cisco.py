"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cisco.py
@DateTime: 2025-06-18
@Docs: Cisco IOS-XE设备适配器
"""

import re
from typing import Any

from .base import BaseAdapter, CommandError, UnsupportedActionError


class CiscoAdapter(BaseAdapter):
    """Cisco IOS-XE设备适配器

    支持Cisco设备的命令生成和输出解析
    """

    def __init__(self):
        """初始化Cisco适配器"""
        self._command_map = {
            "get_version": "show version",
            "get_interfaces": "show ip interface brief",
            "get_interface_detail": "show interfaces {interface}",
            "get_mac_address_table": "show mac address-table",
            "get_arp_table": "show ip arp",
            "get_vlan_brief": "show vlan brief",
            "show_running_config": "show running-config",
            "show_startup_config": "show startup-config",
            "find_mac": "show mac address-table | include {mac_address}",
            "find_arp": "show ip arp | include {ip_address}",
            "get_vlan_detail": "show vlan id {vlan_id}",
            "ping": "ping {target}",
            "traceroute": "traceroute {target}",
            "save_config": "write memory",
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
        """获取Cisco设备的Scrapli平台标识"""
        return "cisco_iosxe"

    def get_supported_actions(self) -> list[str]:
        """获取支持的动作列表"""
        return list(self._command_map.keys())

    def get_command(self, action: str, **params) -> str:
        """根据动作和参数生成Cisco设备命令"""
        if not self.is_action_supported(action):
            raise UnsupportedActionError(f"Cisco适配器不支持的动作: {action}")

        required_params = self._required_params.get(action, [])
        for param in required_params:
            if param not in params:
                raise CommandError(f"动作 {action} 缺少必需参数: {param}")

        command_template = self._command_map[action]

        try:
            if action == "find_mac":
                mac = self._format_mac_address(params["mac_address"])
                return command_template.format(mac_address=mac)
            else:
                return command_template.format(**params)
        except KeyError as e:
            raise CommandError(f"命令参数错误: {e}") from e

    def parse_output(self, action: str, output: str) -> dict[str, Any]:
        """解析Cisco设备命令输出"""
        if not output or not output.strip():
            return {"raw": "", "parsed": None}

        command = self._command_map.get(action, "")
        textfsm_result = self.parse_with_textfsm(action, command, output)
        if textfsm_result is not None:
            return {"raw": output, "parsed": textfsm_result, "method": "textfsm", "action": action}

        fallback_result = self.parse_with_fallback(action, output)
        fallback_result["method"] = "fallback"
        fallback_result["action"] = action
        return fallback_result

    def parse_with_fallback(self, action: str, output: str) -> dict[str, Any]:
        """回退到自定义解析（如果ntc-templates失败）"""
        parser_method = getattr(self, f"_parse_fallback_{action}", None)
        if parser_method:
            parsed_data = parser_method(output)
            return {"raw": output, "parsed": parsed_data}
        return {"raw": output, "parsed": None}

    def _parse_fallback_get_version(self, output: str) -> dict[str, Any] | None:
        """Fallback parser for 'show version'."""
        version_info = {}
        # Cisco IOS XE Software, Version 16.09.03
        match = re.search(r"Cisco IOS XE Software, Version (\S+)", output)
        if match:
            version_info["version"] = match.group(1)

        # Cisco IOS Software, [a-zA-Z\s]+, Version (\S+),
        match = re.search(r"Cisco IOS Software, .* Version (\S+),", output)
        if match and "version" not in version_info:
            version_info["version"] = match.group(1).replace(",", "")

        # System image file is "flash:cat9k_iosxe.16.09.03.SPA.bin"
        match = re.search(r'System image file is "([^"]+)"', output)
        if match:
            version_info["system_image"] = match.group(1)

        # Uptime is 2 weeks, 4 days, 21 hours, 3 minutes
        match = re.search(r"uptime is (.*)", output, re.IGNORECASE)
        if match:
            version_info["uptime"] = match.group(1).strip()

        # Last reload reason: Power-on
        match = re.search(r"Last reload reason: (.*)", output, re.IGNORECASE)
        if match:
            version_info["reload_reason"] = match.group(1).strip()

        # Serial number
        match = re.search(r"(?:System|Processor board ID) (\S+)", output)
        if match:
            version_info["serial_number"] = match.group(1)

        return version_info if version_info else None

    def _parse_fallback_get_interfaces(self, output: str) -> list[dict[str, str]] | None:
        """Fallback parser for 'show ip interface brief'."""
        interfaces = []
        lines = output.strip().split("\n")
        # Interface              IP-Address      OK? Method Status                Protocol
        # GigabitEthernet0/0     192.168.1.1     YES manual up                    up
        # Vlan1                  unassigned      YES unset  administratively down down
        for line in lines:
            parts = line.split()
            if len(parts) >= 6 and (parts[4] in ["up", "down", "administratively"] or parts[2] in ["YES", "NO"]):
                if "administratively down" in line:
                    status = "administratively down"
                    protocol = "down"
                else:
                    status = parts[-2]
                    protocol = parts[-1]

                interfaces.append(
                    {
                        "interface": parts[0],
                        "ip_address": parts[1],
                        "ok": parts[2],
                        "method": parts[3],
                        "status": status,
                        "protocol": protocol,
                    }
                )
        return interfaces if interfaces else None

    def get_connection_extras(self) -> dict[str, Any]:
        """获取Cisco设备连接特殊配置"""
        return {
            "on_open": [
                "terminal length 0",  # 禁用分页
                "terminal no monitor",  # 禁用终端监控
            ]
        }

    def _format_mac_address(self, mac: str) -> str:
        """格式化MAC地址为Cisco格式 (aabb.ccdd.eeff)"""
        clean_mac = re.sub(r"[^a-fA-F0-9]", "", mac.lower())
        if len(clean_mac) != 12:
            raise CommandError(f"无效的MAC地址格式: {mac}")
        return f"{clean_mac[0:4]}.{clean_mac[4:8]}.{clean_mac[8:12]}"
