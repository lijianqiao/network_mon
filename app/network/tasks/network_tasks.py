"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_tasks.py
@DateTime: 2025-06-17
@Docs: 具体的网络任务实现
"""

import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from inspect import signature
from typing import Any

from scrapli import AsyncScrapli
from scrapli.exceptions import ScrapliException

from ..adapters.base import BaseAdapter
from ..adapters.cisco import CiscoAdapter
from ..adapters.h3c import H3CAdapter
from ..adapters.huawei import HuaweiAdapter
from ..core.runner import TaskResult


def get_adapter(device_type: str) -> BaseAdapter:
    """
    根据设备类型获取适配器实例
    """
    device_type_lower = device_type.lower()
    if device_type_lower == "h3c":
        return H3CAdapter()
    if device_type_lower == "huawei":
        return HuaweiAdapter()
    if device_type_lower == "cisco":
        return CiscoAdapter()

    raise NotImplementedError(f"不支持的设备类型: {device_type}")


@dataclass
class NetworkTaskContext:
    """网络任务上下文"""

    device_id: str
    device_ip: str
    device_type: str
    username: str
    password: str
    task_id: str
    timestamp: datetime
    extra_params: dict[str, Any] | None = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


@asynccontextmanager
async def device_connection(context: NetworkTaskContext) -> AsyncGenerator[AsyncScrapli]:
    """
    一个用于设备连接的异步上下文管理器
    """
    adapter = get_adapter(context.device_type)
    platform = adapter.get_platform()
    extras = adapter.get_connection_extras()

    conn_args: dict[str, Any] = {
        "host": context.device_ip,
        "auth_username": context.username,
        "auth_password": context.password,
        "platform": platform,
        "auth_strict_key": False,
        "timeout_socket": 15,
        "timeout_transport": 20,
        "timeout_ops": 30,
    }

    conn = AsyncScrapli(**conn_args)
    try:
        await conn.open()
        # 执行 on_open 命令
        on_open_commands = extras.get("on_open", [])
        for open_cmd in on_open_commands:
            await conn.send_command(open_cmd)
        yield conn
    finally:
        if conn.isalive():
            await conn.close()


class DeviceInfoTask:
    """设备信息查询任务"""

    @staticmethod
    async def get_device_version(context: NetworkTaskContext) -> TaskResult:
        """获取设备版本信息"""
        start_time = time.time()
        adapter = get_adapter(context.device_type)
        action = "get_version"
        command = adapter.get_command(action)

        try:
            async with device_connection(context) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    raise ScrapliException(f"命令执行失败: {response.result}")

                output = response.result
                parsed_result = adapter.parse_output(action, output)

                return TaskResult(
                    success=True,
                    task_id=context.task_id,
                    device_id=context.device_id,
                    command=command,
                    raw_output=output,
                    parsed_data=parsed_result,
                    execution_time=time.time() - start_time,
                )
        except (ScrapliException, NotImplementedError, ValueError) as e:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                device_id=context.device_id,
                command=command,
                error=str(e),
                execution_time=time.time() - start_time,
            )


class InterfaceManagementTask:
    """接口管理任务"""

    @staticmethod
    async def get_interface_status(context: NetworkTaskContext) -> TaskResult:
        """获取接口状态信息"""
        start_time = time.time()
        adapter = get_adapter(context.device_type)
        action = "get_interfaces"
        command = adapter.get_command(action)
        try:
            async with device_connection(context) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    raise ScrapliException(f"命令执行失败: {response.result}")
                output = response.result
                parsed_result = adapter.parse_output(action, output)
                return TaskResult(
                    success=True,
                    task_id=context.task_id,
                    device_id=context.device_id,
                    command=command,
                    raw_output=output,
                    parsed_data=parsed_result,
                    execution_time=time.time() - start_time,
                )
        except (ScrapliException, NotImplementedError, ValueError) as e:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                device_id=context.device_id,
                command=command,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    @staticmethod
    async def get_interface_detail(context: NetworkTaskContext, interface: str) -> TaskResult:
        """获取指定接口详细信息"""
        start_time = time.time()
        adapter = get_adapter(context.device_type)
        action = "get_interface_detail"
        command = adapter.get_command(action, interface=interface)
        try:
            async with device_connection(context) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    raise ScrapliException(f"命令执行失败: {response.result}")
                output = response.result
                parsed_result = adapter.parse_output(action, output)
                return TaskResult(
                    success=True,
                    task_id=context.task_id,
                    device_id=context.device_id,
                    command=command,
                    raw_output=output,
                    parsed_data=parsed_result,
                    execution_time=time.time() - start_time,
                )
        except (ScrapliException, NotImplementedError, ValueError) as e:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                device_id=context.device_id,
                command=command,
                error=str(e),
                execution_time=time.time() - start_time,
            )


class NetworkDiscoveryTask:
    """网络发现任务"""

    @staticmethod
    async def find_mac_address(context: NetworkTaskContext, mac_address: str) -> TaskResult:
        """查找MAC地址位置"""
        start_time = time.time()
        adapter = get_adapter(context.device_type)
        action = "find_mac"
        command = adapter.get_command(action, mac_address=mac_address)
        try:
            async with device_connection(context) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    raise ScrapliException(f"命令执行失败: {response.result}")
                output = response.result
                parsed_result = adapter.parse_output(action, output)
                return TaskResult(
                    success=True,
                    task_id=context.task_id,
                    device_id=context.device_id,
                    command=command,
                    raw_output=output,
                    parsed_data=parsed_result,
                    execution_time=time.time() - start_time,
                )
        except (ScrapliException, NotImplementedError, ValueError) as e:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                device_id=context.device_id,
                command=command,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    @staticmethod
    async def get_arp_table(context: NetworkTaskContext) -> TaskResult:
        """获取ARP表"""
        start_time = time.time()
        adapter = get_adapter(context.device_type)
        action = "get_arp_table"
        command = adapter.get_command(action)
        try:
            async with device_connection(context) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    raise ScrapliException(f"命令执行失败: {response.result}")
                output = response.result
                parsed_result = adapter.parse_output(action, output)
                return TaskResult(
                    success=True,
                    task_id=context.task_id,
                    device_id=context.device_id,
                    command=command,
                    raw_output=output,
                    parsed_data=parsed_result,
                    execution_time=time.time() - start_time,
                )
        except (ScrapliException, NotImplementedError, ValueError) as e:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                device_id=context.device_id,
                command=command,
                error=str(e),
                execution_time=time.time() - start_time,
            )


class ConnectivityTask:
    """连通性测试任务"""

    @staticmethod
    async def ping_host(context: NetworkTaskContext, target: str, count: int = 4) -> TaskResult:
        """Ping测试"""
        start_time = time.time()
        adapter = get_adapter(context.device_type)
        action = "ping"
        # 注意: count 参数在 scrapli 中通常通过多次执行或特定命令格式处理
        # 这里我们简化为执行一次ping
        command = adapter.get_command(action, target=target)
        try:
            async with device_connection(context) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    raise ScrapliException(f"命令执行失败: {response.result}")
                output = response.result
                parsed_result = adapter.parse_output(action, output)
                return TaskResult(
                    success=True,
                    task_id=context.task_id,
                    device_id=context.device_id,
                    command=command,
                    raw_output=output,
                    parsed_data=parsed_result,
                    execution_time=time.time() - start_time,
                )
        except (ScrapliException, NotImplementedError, ValueError) as e:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                device_id=context.device_id,
                command=command,
                error=str(e),
                execution_time=time.time() - start_time,
            )


# 定义任务可调用对象的类型别名
NetworkTaskCallable = Callable[..., Awaitable[TaskResult]]

# 任务注册表
NETWORK_TASKS: dict[str, NetworkTaskCallable] = {
    # 设备信息类
    "get_version": DeviceInfoTask.get_device_version,
    # 接口管理类
    "get_interfaces": InterfaceManagementTask.get_interface_status,
    "get_interface_detail": InterfaceManagementTask.get_interface_detail,
    # 网络发现类
    "find_mac": NetworkDiscoveryTask.find_mac_address,
    "get_arp_table": NetworkDiscoveryTask.get_arp_table,
    # 连通性测试类
    "ping": ConnectivityTask.ping_host,
}


def get_available_tasks() -> list[str]:
    """获取所有可用的网络任务"""
    return list(NETWORK_TASKS.keys())


async def execute_network_task(task_name: str, context: NetworkTaskContext, **kwargs) -> TaskResult:
    """
    执行指定的网络任务

    Args:
        task_name (str): 任务名称
        context (NetworkTaskContext): 任务上下文
        **kwargs: 任务需要的额外参数

    Returns:
        TaskResult: 任务结果
    """
    task_func = NETWORK_TASKS.get(task_name)
    if not task_func:
        return TaskResult(
            success=False,
            task_id=context.task_id,
            device_id=context.device_id,
            error=f"不支持的任务: {task_name}",
        )

    try:
        # 动态传递参数，不再使用硬编码的默认值
        return await task_func(context, **kwargs)
    except TypeError as e:
        # 捕获参数不匹配的错误
        required_params = list(signature(task_func).parameters.keys())[1:]  # 排除 context
        return TaskResult(
            success=False,
            task_id=context.task_id,
            device_id=context.device_id,
            error=f"任务 '{task_name}' 参数错误: {e}. 需要的参数: {required_params}, 提供的参数: {list(kwargs.keys())}",
        )
    except Exception as e:
        # 捕获其他未知异常
        return TaskResult(
            success=False,
            task_id=context.task_id,
            device_id=context.device_id,
            error=f"执行任务 '{task_name}' 时发生未知错误: {e}",
        )
