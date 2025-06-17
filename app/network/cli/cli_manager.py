"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli_manager.py
@DateTime: 2025-06-17
@Docs: CLI统一管理接口
"""

from collections.abc import AsyncGenerator
from typing import Any

from app.services.device_service import DeviceService
from app.utils.logger import logger

from .cli_session import cli_session_manager


class CLIManager:
    """CLI统一管理接口

    提供CLI会话管理、命令执行、配置下发等功能的统一接口
    """

    def __init__(self):
        """初始化CLI管理器"""
        self.device_service = DeviceService()
        self.session_manager = cli_session_manager

    async def start(self) -> None:
        """启动CLI管理器"""
        await self.session_manager.start()
        logger.info("CLI管理器已启动")

    async def stop(self) -> None:
        """停止CLI管理器"""
        await self.session_manager.stop()
        logger.info("CLI管理器已停止")

    async def create_session(self, device_id: int, user_id: str | None = None) -> dict[str, Any]:
        """创建CLI会话

        Args:
            device_id: 设备ID
            user_id: 用户ID

        Returns:
            dict: 创建结果
        """
        try:
            # 获取设备信息
            device = await self.device_service.get_by_id(device_id)
            if not device:
                return {"success": False, "error": f"设备 {device_id} 不存在", "session_id": None}

            # 创建会话
            session_id = await self.session_manager.create_session(device, user_id)
            if not session_id:
                return {"success": False, "error": "创建会话失败", "session_id": None}

            return {
                "success": True,
                "session_id": session_id,
                "device_id": device_id,
                "device_name": device.name,
                "device_ip": device.management_ip,
            }

        except Exception as e:
            logger.error(f"创建CLI会话失败: {e}")
            return {"success": False, "error": f"创建会话失败: {str(e)}", "session_id": None}

    async def close_session(self, session_id: str) -> dict[str, Any]:
        """关闭CLI会话

        Args:
            session_id: 会话ID

        Returns:
            dict: 关闭结果
        """
        try:
            success = await self.session_manager.close_session(session_id)
            return {"success": success, "session_id": session_id}
        except Exception as e:
            logger.error(f"关闭CLI会话失败: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    async def execute_command(self, session_id: str, command: str) -> dict[str, Any]:
        """执行命令

        Args:
            session_id: 会话ID
            command: 命令

        Returns:
            dict: 命令执行结果
        """
        try:
            result = await self.session_manager.execute_command(session_id, command)
            return result
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return {"success": False, "error": f"执行命令失败: {str(e)}", "command": command, "output": ""}

    async def execute_interactive_command(self, session_id: str, command: str) -> AsyncGenerator[dict[str, Any]]:
        """执行交互式命令（流式输出）

        Args:
            session_id: 会话ID
            command: 命令

        Yields:
            dict: 命令输出片段
        """
        try:
            session = await self.session_manager.get_session(session_id)
            if not session:
                yield {
                    "success": False,
                    "error": "会话不存在或已过期",
                    "command": command,
                    "output": "",
                    "chunk_type": "error",
                }
                return

            async for chunk in session.connection.execute_interactive_command(command):
                yield chunk

        except Exception as e:
            logger.error(f"执行交互式命令失败: {e}")
            yield {
                "success": False,
                "error": f"执行交互式命令失败: {str(e)}",
                "command": command,
                "output": "",
                "chunk_type": "error",
            }

    async def send_configuration(self, session_id: str, config_lines: list[str]) -> dict[str, Any]:
        """发送配置

        Args:
            session_id: 会话ID
            config_lines: 配置命令列表

        Returns:
            dict: 配置结果
        """
        try:
            result = await self.session_manager.send_configuration(session_id, config_lines)
            return result
        except Exception as e:
            logger.error(f"发送配置失败: {e}")
            return {"success": False, "error": f"发送配置失败: {str(e)}", "config_lines": config_lines}

    def list_sessions(self, user_id: str | None = None, device_id: int | None = None) -> dict[str, Any]:
        """列出会话

        Args:
            user_id: 用户ID（可选）
            device_id: 设备ID（可选）

        Returns:
            dict: 会话列表
        """
        try:
            sessions = self.session_manager.list_sessions(user_id, device_id)
            return {"success": True, "sessions": sessions, "total": len(sessions)}
        except Exception as e:
            logger.error(f"列出会话失败: {e}")
            return {"success": False, "error": str(e), "sessions": [], "total": 0}

    def get_session_info(self, session_id: str) -> dict[str, Any]:
        """获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            dict: 会话信息
        """
        try:
            session = self.session_manager.sessions.get(session_id)
            if not session or not session.is_active:
                return {"success": False, "error": "会话不存在或已过期"}

            return {
                "success": True,
                "session_id": session.session_id,
                "user_id": session.user_id,
                "device_id": session.device_id,
                "device_name": session.device_name,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_connected": session.connection.is_connected,
            }
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return {"success": False, "error": str(e)}

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        try:
            stats = self.session_manager.get_statistics()
            return {"success": True, **stats}
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"success": False, "error": str(e)}

    async def validate_session(self, session_id: str) -> bool:
        """验证会话是否有效

        Args:
            session_id: 会话ID

        Returns:
            bool: 会话是否有效
        """
        try:
            session = await self.session_manager.get_session(session_id)
            return session is not None and session.is_active
        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return False


# 全局CLI管理器实例
cli_manager = CLIManager()
