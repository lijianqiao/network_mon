"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli_session.py
@DateTime: 2025-06-17
@Docs: CLI会话管理
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.models.data_models import Device
from app.utils.logger import logger

from .cli_connection import CLIConnection


@dataclass
class CLISession:
    """CLI会话信息"""

    session_id: str
    user_id: str | None
    device_id: int
    device_name: str
    connection: CLIConnection
    created_at: datetime
    last_activity: datetime
    is_active: bool = True


class CLISessionManager:
    """CLI会话管理器

    管理所有活跃的CLI会话，包括连接池、会话超时、资源清理等
    """

    def __init__(self, max_sessions_per_user: int = 5, session_timeout_minutes: int = 30):
        """初始化会话管理器

        Args:
            max_sessions_per_user: 每个用户最大会话数
            session_timeout_minutes: 会话超时时间（分钟）
        """
        self.max_sessions_per_user = max_sessions_per_user
        self.session_timeout_minutes = session_timeout_minutes

        # 会话存储
        self.sessions: dict[str, CLISession] = {}
        self.user_sessions: dict[str, set[str]] = {}  # user_id -> session_ids
        self.device_sessions: dict[int, set[str]] = {}  # device_id -> session_ids

        # 后台任务
        self._cleanup_task: asyncio.Task | None = None
        self._is_running = False

    async def start(self) -> None:
        """启动会话管理器"""
        if self._is_running:
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("CLI会话管理器已启动")

    async def stop(self) -> None:
        """停止会话管理器"""
        if not self._is_running:
            return

        self._is_running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 清理所有会话
        for session in list(self.sessions.values()):
            await self._close_session(session.session_id)

        logger.info("CLI会话管理器已停止")

    async def create_session(self, device: Device, user_id: str | None = None) -> str | None:
        """创建新的CLI会话

        Args:
            device: 设备信息
            user_id: 用户ID（可选）

        Returns:
            str | None: 会话ID，创建失败时返回None
        """
        try:
            # 检查用户会话数限制
            if user_id and user_id in self.user_sessions:
                user_session_count = len(self.user_sessions[user_id])
                if user_session_count >= self.max_sessions_per_user:
                    logger.warning(f"用户 {user_id} 已达到最大会话数限制: {self.max_sessions_per_user}")
                    return None

            # 创建连接
            connection = CLIConnection(device)
            if not await connection.connect():
                logger.error(f"无法连接到设备 {device.name} ({device.management_ip})")
                return None

            # 创建会话
            session_id = str(uuid.uuid4())
            session = CLISession(
                session_id=session_id,
                user_id=user_id,
                device_id=device.id,
                device_name=device.name,
                connection=connection,
                created_at=datetime.now(),
                last_activity=datetime.now(),
            )

            # 存储会话
            self.sessions[session_id] = session

            # 更新索引
            if user_id:
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(session_id)

            if device.id not in self.device_sessions:
                self.device_sessions[device.id] = set()
            self.device_sessions[device.id].add(session_id)

            logger.info(f"创建CLI会话 {session_id}，设备: {device.name}，用户: {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"创建CLI会话失败: {e}")
            return None

    async def get_session(self, session_id: str) -> CLISession | None:
        """获取CLI会话

        Args:
            session_id: 会话ID

        Returns:
            CLISession | None: 会话对象，不存在时返回None
        """
        session = self.sessions.get(session_id)
        if session and session.is_active:
            # 更新活动时间
            session.last_activity = datetime.now()
            return session
        return None

    async def close_session(self, session_id: str) -> bool:
        """关闭CLI会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功关闭
        """
        return await self._close_session(session_id)

    async def _close_session(self, session_id: str) -> bool:
        """内部方法：关闭CLI会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        try:
            # 断开连接
            await session.connection.disconnect()

            # 更新会话状态
            session.is_active = False

            # 从索引中移除
            if session.user_id and session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)
                if not self.user_sessions[session.user_id]:
                    del self.user_sessions[session.user_id]

            if session.device_id in self.device_sessions:
                self.device_sessions[session.device_id].discard(session_id)
                if not self.device_sessions[session.device_id]:
                    del self.device_sessions[session.device_id]

            # 从会话存储中移除
            del self.sessions[session_id]

            logger.info(f"关闭CLI会话 {session_id}")
            return True

        except Exception as e:
            logger.error(f"关闭CLI会话 {session_id} 失败: {e}")
            return False

    async def execute_command(self, session_id: str, command: str) -> dict[str, Any]:
        """在指定会话中执行命令

        Args:
            session_id: 会话ID
            command: 要执行的命令

        Returns:
            dict: 命令执行结果
        """
        session = await self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "会话不存在或已过期",
                "command": command,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            result = await session.connection.execute_command(command)
            return result
        except Exception as e:
            logger.error(f"会话 {session_id} 执行命令失败: {e}")
            return {
                "success": False,
                "error": f"执行命令失败: {str(e)}",
                "command": command,
                "timestamp": datetime.now().isoformat(),
            }

    async def send_configuration(self, session_id: str, config_lines: list[str]) -> dict[str, Any]:
        """在指定会话中发送配置

        Args:
            session_id: 会话ID
            config_lines: 配置命令列表

        Returns:
            dict: 配置结果
        """
        session = await self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "会话不存在或已过期",
                "config_lines": config_lines,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            result = await session.connection.send_configuration(config_lines)
            return result
        except Exception as e:
            logger.error(f"会话 {session_id} 发送配置失败: {e}")
            return {
                "success": False,
                "error": f"发送配置失败: {str(e)}",
                "config_lines": config_lines,
                "timestamp": datetime.now().isoformat(),
            }

    def list_sessions(self, user_id: str | None = None, device_id: int | None = None) -> list[dict[str, Any]]:
        """列出会话

        Args:
            user_id: 用户ID（可选）
            device_id: 设备ID（可选）

        Returns:
            list: 会话列表
        """
        sessions = []

        for session in self.sessions.values():
            if not session.is_active:
                continue

            if user_id and session.user_id != user_id:
                continue

            if device_id and session.device_id != device_id:
                continue

            sessions.append(
                {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "device_id": session.device_id,
                    "device_name": session.device_name,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "is_connected": session.connection.is_connected,
                }
            )

        return sessions

    def get_statistics(self) -> dict[str, Any]:
        """获取会话统计信息

        Returns:
            dict: 统计信息
        """
        active_sessions = [s for s in self.sessions.values() if s.is_active]

        return {
            "total_sessions": len(active_sessions),
            "users_count": len(self.user_sessions),
            "devices_count": len(self.device_sessions),
            "sessions_by_user": {user_id: len(session_ids) for user_id, session_ids in self.user_sessions.items()},
            "sessions_by_device": {
                device_id: len(session_ids) for device_id, session_ids in self.device_sessions.items()
            },
        }

    async def _cleanup_loop(self) -> None:
        """后台清理任务"""
        while self._is_running:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(60)  # 每分钟检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"会话清理任务异常: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        timeout_threshold = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if session.last_activity < timeout_threshold:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            logger.info(f"清理过期会话: {session_id}")
            await self._close_session(session_id)


# 全局会话管理器实例
cli_session_manager = CLISessionManager()
