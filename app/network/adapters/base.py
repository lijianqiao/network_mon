"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025-06-17
@Docs: 设备适配器基类
"""

from abc import ABC, abstractmethod
from typing import Any

try:
    from ntc_templates.parse import parse_output  # type: ignore
    from textfsm import TextFSM  # type: ignore  # noqa: F401

    TEXTFSM_AVAILABLE = True
except ImportError:
    TEXTFSM_AVAILABLE = False
    parse_output = None


class BaseAdapter(ABC):
    """设备适配器基类

    定义所有厂商设备适配器的统一接口，支持 ntc-templates TextFSM 解析
    """

    @abstractmethod
    def get_command(self, action: str, **params) -> str:
        """根据动作和参数生成设备命令

        Args:
            action: 动作类型 (如: get_version, find_mac, get_interfaces)
            **params: 命令参数

        Returns:
            设备命令字符串

        Raises:
            ValueError: 当不支持的动作时
        """
        pass

    @abstractmethod
    def parse_output(self, action: str, output: str) -> dict[str, Any]:
        """解析设备命令输出

        优先使用 ntc-templates TextFSM 解析，失败时回退到自定义解析

        Args:
            action: 动作类型
            output: 设备原始输出

        Returns:
            解析后的结构化数据
        """
        pass

    @abstractmethod
    def get_platform(self) -> str:
        """获取设备平台标识

        Returns:
            Scrapli平台标识，也用于 ntc-templates 平台匹配
        """
        pass

    @abstractmethod
    def get_supported_actions(self) -> list[str]:
        """获取支持的动作列表

        Returns:
            支持的动作列表
        """
        pass

    def get_template_name(self, action: str, command: str) -> str | None:
        """获取 ntc-templates 模板名称

        Args:
            action: 动作类型
            command: 执行的命令

        Returns:
            模板名称，如果没有对应模板则返回 None
        """  # 基于平台的精确命令到模板映射
        platform = self.get_platform()

        if platform == "hp_comware":
            # H3C Comware 精确模板映射（基于实际可用模板）
            comware_template_map = {
                "display version": None,  # 无可用模板，使用fallback
                "display interface brief": "hp_comware_display_interface_brief.textfsm",
                "display interface": "hp_comware_display_interface.textfsm",
                "display mac-address": "hp_comware_display_mac-address.textfsm",
                "display arp": "hp_comware_display_arp.textfsm",
                "display vlan": "hp_comware_display_vlan_brief.textfsm",
                "display vlan all": "hp_comware_display_vlan_all.textfsm",
                "display ip interface": "hp_comware_display_ip_interface.textfsm",
                "display clock": "hp_comware_display_clock.textfsm",
                "display device manuinfo": "hp_comware_display_device_manuinfo.textfsm",
            }

            # 简化命令（移除参数和过滤器）
            base_command = command.split(" | ")[0].strip()
            return comware_template_map.get(base_command)

        # 其他平台的通用映射（可扩展）
        generic_template_map = {
            "show version": f"{platform}_show_version.textfsm",
            "show interfaces": f"{platform}_show_interfaces.textfsm",
            "show mac address-table": f"{platform}_show_mac_address_table.textfsm",
            "show arp": f"{platform}_show_arp.textfsm",
            "show vlan": f"{platform}_show_vlan.textfsm",
        }

        base_command = command.split(" | ")[0].strip()
        return generic_template_map.get(base_command)

    def parse_with_textfsm(self, action: str, command: str, output: str) -> list[dict[str, Any]] | None:
        """使用 ntc-templates TextFSM 解析输出

        Args:
            action: 动作类型
            command: 执行的命令
            output: 设备原始输出

        Returns:
            解析后的结构化数据列表，失败时返回 None
        """
        if not TEXTFSM_AVAILABLE or parse_output is None:
            return None

        try:
            platform = self.get_platform()

            # 使用 ntc-templates 解析
            parsed_output = parse_output(platform=platform, command=command, data=output)

            # 如果解析成功且有结果
            if parsed_output and isinstance(parsed_output, list):
                return parsed_output

        except Exception:
            # 解析失败，静默回退到自定义解析
            pass

        return None

    def parse_with_fallback(self, action: str, output: str) -> dict[str, Any]:
        """回退到自定义解析（子类实现）

        Args:
            action: 动作类型
            output: 设备原始输出

        Returns:
            解析后的结构化数据
        """
        # 默认实现：返回原始输出
        return {"raw": output, "parsed": None}

    def is_action_supported(self, action: str) -> bool:
        """检查是否支持指定动作

        Args:
            action: 动作类型

        Returns:
            是否支持
        """
        return action in self.get_supported_actions()

    def validate_params(self, action: str, **params) -> bool:
        """验证动作参数

        Args:
            action: 动作类型
            **params: 参数

        Returns:
            参数是否有效
        """
        # 基础实现，子类可以重写
        return True

    def get_connection_extras(self) -> dict[str, Any]:
        """获取连接特殊配置

        Returns:
            连接配置字典
        """
        # 默认无特殊配置，子类可以重写
        return {}


class AdapterError(Exception):
    """适配器异常基类"""

    pass


class UnsupportedActionError(AdapterError):
    """不支持的动作异常"""

    pass


class ParseError(AdapterError):
    """解析异常"""

    pass


class CommandError(AdapterError):
    """命令生成异常"""

    pass
