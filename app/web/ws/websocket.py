"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: websocket.py
@DateTime: 2025-06-17
@Docs: WebSocket实时数据推送端点
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.dependencies import (
    get_alert_service,
    get_device_service,
    get_monitor_metric_service,
    get_system_log_service,
)
from app.services.device_service import DeviceService
from app.services.log_service import SystemLogService
from app.services.monitor_service import AlertService, MonitorMetricService

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[str]] = {}  # 客户端订阅的数据类型

    async def connect(self, websocket: WebSocket, client_id: str):
        """接受新连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

    def disconnect(self, client_id: str):
        """断开连接"""
        self.active_connections.pop(client_id, None)
        self.subscriptions.pop(client_id, None)

    async def send_personal_message(self, message: str, client_id: str):
        """发送个人消息"""
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception:
                self.disconnect(client_id)

    async def broadcast(self, message: str, data_type: str | None = None):
        """广播消息"""
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            # 如果指定了数据类型，只发送给订阅了该类型的客户端
            if data_type and data_type not in self.subscriptions.get(client_id, set()):
                continue

            try:
                await websocket.send_text(message)
            except Exception:
                disconnected_clients.append(client_id)

        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    def subscribe(self, client_id: str, data_types: list[str]):
        """订阅数据类型"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].update(data_types)

    def unsubscribe(self, client_id: str, data_types: list[str]):
        """取消订阅数据类型"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].difference_update(data_types)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    device_service: DeviceService = Depends(get_device_service),
    alert_service: AlertService = Depends(get_alert_service),
    metric_service: MonitorMetricService = Depends(get_monitor_metric_service),
    log_service: SystemLogService = Depends(get_system_log_service),
):
    """WebSocket主端点"""
    await manager.connect(websocket, client_id)

    # 发送连接成功消息
    await manager.send_personal_message(
        json.dumps(
            {
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
            }
        ),
        client_id,
    )

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_client_message(message, client_id)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps(
                        {"type": "error", "message": "Invalid JSON format", "timestamp": datetime.now().isoformat()}
                    ),
                    client_id,
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)


async def handle_client_message(message: dict[str, Any], client_id: str):
    """处理客户端消息"""
    message_type = message.get("type")

    if message_type == "subscribe":
        # 订阅数据类型
        data_types = message.get("data_types", [])
        manager.subscribe(client_id, data_types)

        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "subscription",
                    "status": "subscribed",
                    "data_types": data_types,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            client_id,
        )

    elif message_type == "unsubscribe":
        # 取消订阅数据类型
        data_types = message.get("data_types", [])
        manager.unsubscribe(client_id, data_types)

        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "subscription",
                    "status": "unsubscribed",
                    "data_types": data_types,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            client_id,
        )

    elif message_type == "ping":
        # 心跳检测
        await manager.send_personal_message(
            json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}), client_id
        )


# 实时数据推送任务
async def push_real_time_data():
    """推送实时数据的后台任务"""
    while True:
        try:
            # 推送设备状态更新
            await push_device_status()

            # 推送新告警
            await push_new_alerts()

            # 推送监控指标更新
            await push_metric_updates()

            # 推送系统日志
            await push_system_logs()

            # 等待5秒后下次推送
            await asyncio.sleep(5)

        except Exception as e:
            print(f"推送实时数据时发生错误: {e}")
            await asyncio.sleep(10)  # 发生错误时等待更长时间


async def push_device_status():
    """推送设备状态更新"""
    # 这里应该查询最近更新的设备状态
    # 暂时发送示例数据
    device_update = {
        "type": "device_status",
        "data": {"device_id": 1, "status": "online", "last_seen": datetime.now().isoformat()},
        "timestamp": datetime.now().isoformat(),
    }

    await manager.broadcast(json.dumps(device_update), "device_status")


async def push_new_alerts():
    """推送新告警"""
    # 这里应该查询最近的新告警
    # 暂时发送示例数据
    alert_data = {
        "type": "new_alert",
        "data": {
            "alert_id": 1,
            "device_id": 1,
            "severity": "warning",
            "message": "CPU使用率过高",
            "created_at": datetime.now().isoformat(),
        },
        "timestamp": datetime.now().isoformat(),
    }

    await manager.broadcast(json.dumps(alert_data), "alerts")


async def push_metric_updates():
    """推送监控指标更新"""
    # 这里应该查询最新的监控指标数据
    # 暂时发送示例数据
    metric_data = {
        "type": "metric_update",
        "data": {
            "device_id": 1,
            "metrics": {"cpu_usage": 75.5, "memory_usage": 68.2, "disk_usage": 45.1, "network_io": 1250.8},
        },
        "timestamp": datetime.now().isoformat(),
    }

    await manager.broadcast(json.dumps(metric_data), "metrics")


async def push_system_logs():
    """推送系统日志"""
    # 这里应该查询最新的系统日志
    # 暂时发送示例数据
    log_data = {
        "type": "system_log",
        "data": {
            "level": "info",
            "message": "系统运行正常",
            "module": "monitor_service",
            "created_at": datetime.now().isoformat(),
        },
        "timestamp": datetime.now().isoformat(),
    }

    await manager.broadcast(json.dumps(log_data), "system_logs")


# 启动实时数据推送任务的函数
def start_real_time_push():
    """启动实时数据推送任务"""
    asyncio.create_task(push_real_time_data())
