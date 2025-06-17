"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli_connection.py
@DateTime: 2025-06-17
@Docs: CLI设备连接管理
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any

from scrapli import AsyncScrapli
from scrapli.exceptions import ScrapliException

from app.models.data_models import Device
from app.utils.logger import logger


class CLIConnection:
    """CLI设备连接类

    负责与网络设备建立CLI连接并执行命令
    """

    def __init__(self, device: Device):
        """初始化CLI连接

        Args:
            device: 设备信息
        """
        self.device = device
        self.connection: AsyncScrapli | None = None
        self.is_connected = False
        self.last_activity = datetime.now()
        self.connection_id = f"{device.id}_{datetime.now().timestamp()}"

    async def connect(self) -> bool:
        """建立设备连接

        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建scrapli连接配置
            device_config = {
                "host": self.device.management_ip,
                "auth_username": self.device.account,
                "auth_password": self.device.password,
                "auth_strict_key": False,
                "timeout_socket": 30,
                "timeout_transport": 30,
                "timeout_ops": 30,
            }

            # 根据设备品牌选择驱动
            device_brand = getattr(self.device.brand, "code", "").lower() if self.device.brand else ""
            if device_brand in ["cisco", "cisco_ios"]:
                device_config["platform"] = "cisco_iosxe"
            elif device_brand in ["huawei", "huawei_vrp"]:
                device_config["platform"] = "huawei_vrp"
            elif device_brand in ["juniper", "junos"]:
                device_config["platform"] = "juniper_junos"
            else:
                # 默认使用generic驱动
                device_config["platform"] = "generic"

            # 使用设备端口
            if self.device.port and self.device.port != 22:
                device_config["port"] = self.device.port

            self.connection = AsyncScrapli(**device_config)
            await self.connection.open()

            self.is_connected = True
            self.last_activity = datetime.now()
            logger.info(f"成功连接到设备 {self.device.hostname or self.device.name} ({self.device.management_ip})")
            return True

        except ScrapliException as e:
            logger.error(f"连接设备 {self.device.hostname or self.device.name} 失败: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"连接设备 {self.device.hostname or self.device.name} 时发生未知错误: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """断开设备连接"""
        if self.connection and self.is_connected:
            try:
                await self.connection.close()
                logger.info(f"已断开与设备 {self.device.hostname or self.device.name} 的连接")
            except Exception as e:
                logger.error(f"断开设备 {self.device.hostname or self.device.name} 连接时发生错误: {e}")
            finally:
                self.is_connected = False
                self.connection = None

    async def execute_command(self, command: str) -> dict[str, Any]:
        """执行单个命令

        Args:
            command: 要执行的命令

        Returns:
            dict: 包含命令结果的字典
        """
        if not self.is_connected or not self.connection:
            return {
                "success": False,
                "error": "设备未连接",
                "command": command,
                "output": "",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            self.last_activity = datetime.now()
            result = await self.connection.send_command(command)

            return {
                "success": True,
                "command": command,
                "output": result.result,
                "elapsed_time": result.elapsed_time,
                "timestamp": datetime.now().isoformat(),
            }

        except ScrapliException as e:
            logger.error(f"执行命令 '{command}' 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "output": "",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"执行命令 '{command}' 时发生未知错误: {e}")
            return {
                "success": False,
                "error": f"未知错误: {str(e)}",
                "command": command,
                "output": "",
                "timestamp": datetime.now().isoformat(),
            }

    async def execute_interactive_command(self, command: str) -> AsyncGenerator[dict[str, Any]]:
        """执行交互式命令（流式输出）

        Args:
            command: 要执行的命令

        Yields:
            dict: 包含输出片段的字典
        """
        if not self.is_connected or not self.connection:
            yield {
                "success": False,
                "error": "设备未连接",
                "command": command,
                "output": "",
                "timestamp": datetime.now().isoformat(),
                "chunk_type": "error",
            }
            return

        try:
            self.last_activity = datetime.now()

            # 发送命令并获取响应
            result = await self.connection.send_command(command)

            # 将输出按行分割，模拟流式输出
            output_lines = result.result.split("\n")
            for i, line in enumerate(output_lines):
                yield {
                    "success": True,
                    "command": command,
                    "output": line,
                    "timestamp": datetime.now().isoformat(),
                    "chunk_type": "stdout",
                    "line_number": i + 1,
                    "is_final": i == len(output_lines) - 1,
                }

                # 模拟实时输出的延迟
                await asyncio.sleep(0.1)

        except ScrapliException as e:
            logger.error(f"执行交互式命令 '{command}' 失败: {e}")
            yield {
                "success": False,
                "error": str(e),
                "command": command,
                "output": "",
                "timestamp": datetime.now().isoformat(),
                "chunk_type": "error",
            }
        except Exception as e:
            logger.error(f"执行交互式命令 '{command}' 时发生未知错误: {e}")
            yield {
                "success": False,
                "error": f"未知错误: {str(e)}",
                "command": command,
                "output": "",
                "timestamp": datetime.now().isoformat(),
                "chunk_type": "error",
            }

    async def send_configuration(self, config_lines: list[str]) -> dict[str, Any]:
        """发送配置命令

        Args:
            config_lines: 配置命令列表

        Returns:
            dict: 配置结果
        """
        if not self.is_connected or not self.connection:
            return {
                "success": False,
                "error": "设备未连接",
                "config_lines": config_lines,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            self.last_activity = datetime.now()
            result = await self.connection.send_configs(config_lines)

            return {
                "success": True,
                "config_lines": config_lines,
                "output": result.result,
                "timestamp": datetime.now().isoformat(),
            }

        except ScrapliException as e:
            logger.error(f"发送配置失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "config_lines": config_lines,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"发送配置时发生未知错误: {e}")
            return {
                "success": False,
                "error": f"未知错误: {str(e)}",
                "config_lines": config_lines,
                "timestamp": datetime.now().isoformat(),
            }

    def is_connection_active(self, timeout_minutes: int = 30) -> bool:
        """检查连接是否活跃

        Args:
            timeout_minutes: 超时时间（分钟）

        Returns:
            bool: 连接是否活跃
        """
        if not self.is_connected:
            return False

        timeout_threshold = datetime.now() - timedelta(minutes=timeout_minutes)
        return self.last_activity > timeout_threshold

    async def keep_alive(self) -> bool:
        """保持连接活跃

        Returns:
            bool: 保活是否成功
        """
        try:
            # 发送一个简单的命令来保持连接
            result = await self.execute_command("show clock")
            return result["success"]
        except Exception as e:
            logger.error(f"保活失败: {e}")
            return False
