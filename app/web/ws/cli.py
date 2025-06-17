"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli.py
@DateTime: 2025-06-17
@Docs: CLI WebSocket端点
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.network.cli.cli_manager import cli_manager


class CLIWebSocket:
    """CLI WebSocket连接管理"""

    def __init__(self):
        """初始化WebSocket管理器"""
        self.active_connections: dict[str, WebSocket] = {}
        self.session_connections: dict[str, str] = {}  # session_id -> websocket_id

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """接受WebSocket连接

        Args:
            websocket: WebSocket连接
            client_id: 客户端ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket客户端 {client_id} 已连接")

    def disconnect(self, client_id: str) -> None:
        """断开WebSocket连接

        Args:
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # 清理会话连接映射
        sessions_to_remove = []
        for session_id, ws_client_id in self.session_connections.items():
            if ws_client_id == client_id:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.session_connections[session_id]

        logger.info(f"WebSocket客户端 {client_id} 已断开")

    async def send_message(self, client_id: str, message: dict[str, Any]) -> bool:
        """发送消息给指定客户端

        Args:
            client_id: 客户端ID
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"发送消息给客户端 {client_id} 失败: {e}")
            return False

    async def handle_message(self, client_id: str, message: dict[str, Any]) -> None:
        """处理客户端消息

        Args:
            client_id: 客户端ID
            message: 消息内容
        """
        try:
            action = message.get("action")
            if not action:
                await self.send_error(client_id, "缺少action字段")
                return

            if action == "create_session":
                await self._handle_create_session(client_id, message)
            elif action == "close_session":
                await self._handle_close_session(client_id, message)
            elif action == "execute_command":
                await self._handle_execute_command(client_id, message)
            elif action == "execute_interactive_command":
                await self._handle_execute_interactive_command(client_id, message)
            elif action == "send_configuration":
                await self._handle_send_configuration(client_id, message)
            elif action == "list_sessions":
                await self._handle_list_sessions(client_id, message)
            elif action == "get_session_info":
                await self._handle_get_session_info(client_id, message)
            else:
                await self.send_error(client_id, f"未知的action: {action}")

        except Exception as e:
            logger.error(f"处理客户端 {client_id} 消息失败: {e}")
            await self.send_error(client_id, f"处理消息失败: {str(e)}")

    async def send_error(self, client_id: str, error_message: str) -> None:
        """发送错误消息

        Args:
            client_id: 客户端ID
            error_message: 错误消息
        """
        await self.send_message(
            client_id, {"type": "error", "message": error_message, "timestamp": asyncio.get_event_loop().time()}
        )

    async def _handle_create_session(self, client_id: str, message: dict[str, Any]) -> None:
        """处理创建会话请求"""
        device_id = message.get("device_id")
        user_id = message.get("user_id")

        if not device_id:
            await self.send_error(client_id, "缺少device_id参数")
            return

        result = await cli_manager.create_session(device_id, user_id)

        if result["success"]:
            session_id = result["session_id"]
            self.session_connections[session_id] = client_id

        await self.send_message(
            client_id,
            {
                "type": "session_created",
                "action": "create_session",
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

    async def _handle_close_session(self, client_id: str, message: dict[str, Any]) -> None:
        """处理关闭会话请求"""
        session_id = message.get("session_id")

        if not session_id:
            await self.send_error(client_id, "缺少session_id参数")
            return

        result = await cli_manager.close_session(session_id)

        if result["success"] and session_id in self.session_connections:
            del self.session_connections[session_id]

        await self.send_message(
            client_id,
            {
                "type": "session_closed",
                "action": "close_session",
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

    async def _handle_execute_command(self, client_id: str, message: dict[str, Any]) -> None:
        """处理执行命令请求"""
        session_id = message.get("session_id")
        command = message.get("command")

        if not session_id:
            await self.send_error(client_id, "缺少session_id参数")
            return
        if not command:
            await self.send_error(client_id, "缺少command参数")
            return

        result = await cli_manager.execute_command(session_id, command)

        await self.send_message(
            client_id,
            {
                "type": "command_result",
                "action": "execute_command",
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

    async def _handle_execute_interactive_command(self, client_id: str, message: dict[str, Any]) -> None:
        """处理执行交互式命令请求"""
        session_id = message.get("session_id")
        command = message.get("command")

        if not session_id:
            await self.send_error(client_id, "缺少session_id参数")
            return
        if not command:
            await self.send_error(client_id, "缺少command参数")
            return

        # 发送开始信号
        await self.send_message(
            client_id,
            {
                "type": "interactive_command_start",
                "action": "execute_interactive_command",
                "session_id": session_id,
                "command": command,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # 流式发送输出
        async for chunk in cli_manager.execute_interactive_command(session_id, command):
            await self.send_message(
                client_id,
                {
                    "type": "interactive_command_chunk",
                    "action": "execute_interactive_command",
                    "chunk": chunk,
                    "timestamp": asyncio.get_event_loop().time(),
                },
            )

        # 发送结束信号
        await self.send_message(
            client_id,
            {
                "type": "interactive_command_end",
                "action": "execute_interactive_command",
                "session_id": session_id,
                "command": command,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

    async def _handle_send_configuration(self, client_id: str, message: dict[str, Any]) -> None:
        """处理发送配置请求"""
        session_id = message.get("session_id")
        config_lines = message.get("config_lines")

        if not session_id:
            await self.send_error(client_id, "缺少session_id参数")
            return
        if not config_lines or not isinstance(config_lines, list):
            await self.send_error(client_id, "缺少config_lines参数或格式错误")
            return

        result = await cli_manager.send_configuration(session_id, config_lines)

        await self.send_message(
            client_id,
            {
                "type": "configuration_result",
                "action": "send_configuration",
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

    async def _handle_list_sessions(self, client_id: str, message: dict[str, Any]) -> None:
        """处理列出会话请求"""
        user_id = message.get("user_id")
        device_id = message.get("device_id")

        result = cli_manager.list_sessions(user_id, device_id)

        await self.send_message(
            client_id,
            {
                "type": "sessions_list",
                "action": "list_sessions",
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

    async def _handle_get_session_info(self, client_id: str, message: dict[str, Any]) -> None:
        """处理获取会话信息请求"""
        session_id = message.get("session_id")

        if not session_id:
            await self.send_error(client_id, "缺少session_id参数")
            return

        result = cli_manager.get_session_info(session_id)

        await self.send_message(
            client_id,
            {
                "type": "session_info",
                "action": "get_session_info",
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )


# 全局WebSocket管理器
cli_websocket = CLIWebSocket()


async def cli_websocket_endpoint(websocket: WebSocket, client_id: str = "default") -> None:
    """CLI WebSocket端点

    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
    """
    await cli_websocket.connect(websocket, client_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await cli_websocket.handle_message(client_id, message)
            except json.JSONDecodeError as e:
                await cli_websocket.send_error(client_id, f"JSON解析错误: {str(e)}")
            except Exception as e:
                logger.error(f"处理WebSocket消息异常: {e}")
                await cli_websocket.send_error(client_id, f"处理消息异常: {str(e)}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket客户端 {client_id} 主动断开连接")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
    finally:
        cli_websocket.disconnect(client_id)
