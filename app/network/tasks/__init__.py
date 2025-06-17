"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: 网络任务模块
"""

from .network_tasks import (
    NETWORK_TASKS,
    ConnectivityTask,
    DeviceInfoTask,
    InterfaceManagementTask,
    NetworkDiscoveryTask,
    NetworkTaskContext,
    execute_network_task,
    get_available_tasks,
)

__all__ = [
    "NETWORK_TASKS",
    "NetworkTaskContext",
    "get_available_tasks",
    "execute_network_task",
    "DeviceInfoTask",
    "InterfaceManagementTask",
    "NetworkDiscoveryTask",
    "ConnectivityTask",
]
