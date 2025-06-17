"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_tasks.py
@DateTime: 2025-06-17
@Docs: 具体的网络任务实现
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..adapters.h3c import H3CAdapter
from ..core.runner import TaskResult


def get_adapter(device_type: str):
    """获取设备适配器"""
    if device_type.lower() in ["h3c", "hp_comware", "comware"]:
        return H3CAdapter()
    else:
        raise ValueError(f"不支持的设备类型: {device_type}")


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


class DeviceInfoTask:
    """设备信息查询任务"""

    @staticmethod
    async def get_device_version(context: NetworkTaskContext) -> TaskResult:
        """获取设备版本信息"""
        try:
            adapter = get_adapter(context.device_type)
            command = adapter.get_command("get_version")

            # 这里模拟设备连接和命令执行
            # 实际实现中会使用scrapli等库连接设备
            mock_output = """
H3C Comware Software, Version 7.1.070, Release 6604P01
Copyright (c) 2004-2018 New H3C Technologies Co., Ltd. All rights reserved.
H3C S5560S-EI uptime is 2 weeks, 1 day, 5 hours, 30 minutes
Device serial number : 210235A1JCH000000001
CPU utilization for five seconds: 8%
Memory utilization: 45%
            """

            parsed_result = adapter.parse_output("get_version", mock_output)

            return TaskResult(
                success=True,
                command=command,
                raw_output=mock_output,
                parsed_data=parsed_result,
                execution_time=0.5,
                task_id=context.task_id,
                device_id=context.device_id,
            )

        except Exception as e:
            return TaskResult(
                success=False,
                command="get_version",
                error=str(e),
                execution_time=0.0,
                task_id=context.task_id,
                device_id=context.device_id,
            )


class InterfaceManagementTask:
    """接口管理任务"""

    @staticmethod
    async def get_interface_status(context: NetworkTaskContext) -> TaskResult:
        """获取接口状态信息"""
        try:
            adapter = get_adapter(context.device_type)
            command = adapter.get_command("get_interfaces")

            mock_output = """
Interface                        Link Protocol   Primary IP      Description
GE1/0/1                          UP   UP         --              To_Core_Switch
GE1/0/2                          UP   UP         192.168.10.1    Management_Port
GE1/0/3                          DOWN DOWN       --              Unused_Port
GE1/0/4                          UP   UP         --              To_Server_Farm
Ten-GE1/0/49                     UP   UP         --              Uplink_Port
Vlan1                            UP   UP         10.0.0.1        Default_VLAN
            """

            parsed_result = adapter.parse_output("get_interfaces", mock_output)

            return TaskResult(
                success=True,
                command=command,
                raw_output=mock_output,
                parsed_data=parsed_result,
                execution_time=0.3,
                task_id=context.task_id,
                device_id=context.device_id,
            )

        except Exception as e:
            return TaskResult(
                success=False,
                command="get_interfaces",
                error=str(e),
                execution_time=0.0,
                task_id=context.task_id,
                device_id=context.device_id,
            )

    @staticmethod
    async def get_interface_detail(context: NetworkTaskContext, interface: str) -> TaskResult:
        """获取指定接口详细信息"""
        try:
            adapter = get_adapter(context.device_type)
            command = adapter.get_command("get_interface_detail", interface=interface)

            mock_output = f"""
{interface} current state : UP
Line protocol current state : UP
Description: Test Interface
The Maximum Transmit Unit is 1500
Internet protocol processing : disabled
IP Sending Frames' Format is PKTFMT_ETHNT_2, Hardware address is 0050-5688-70c0
Port link-type: access
VLAN Permitted: 1
Last 300 seconds input rate 0 bytes/sec, 0 packets/sec
Last 300 seconds output rate 0 bytes/sec, 0 packets/sec
            """

            parsed_result = adapter.parse_output("get_interface_detail", mock_output)

            return TaskResult(
                success=True,
                command=command,
                raw_output=mock_output,
                parsed_data=parsed_result,
                execution_time=0.2,
                task_id=context.task_id,
                device_id=context.device_id,
            )

        except Exception as e:
            return TaskResult(
                success=False,
                command=f"get_interface_detail {interface}",
                error=str(e),
                execution_time=0.0,
                task_id=context.task_id,
                device_id=context.device_id,
            )


class NetworkDiscoveryTask:
    """网络发现任务"""

    @staticmethod
    async def find_mac_address(context: NetworkTaskContext, mac_address: str) -> TaskResult:
        """查找MAC地址位置"""
        try:
            adapter = get_adapter(context.device_type)
            command = adapter.get_command("find_mac", mac_address=mac_address)

            # 格式化MAC地址为H3C格式
            formatted_mac = mac_address.replace(":", "").replace("-", "").replace(".", "")
            formatted_mac = f"{formatted_mac[0:4]}-{formatted_mac[4:8]}-{formatted_mac[8:12]}"

            mock_output = f"""
MAC              VLAN    State    Port                            AGING
{formatted_mac}   1       Learned  GE1/0/1                         Y
{formatted_mac}   10      Learned  GE1/0/2                         Y
            """

            parsed_result = adapter.parse_output("find_mac", mock_output)

            return TaskResult(
                success=True,
                command=command,
                raw_output=mock_output,
                parsed_data=parsed_result,
                execution_time=0.4,
                task_id=context.task_id,
                device_id=context.device_id,
            )

        except Exception as e:
            return TaskResult(
                success=False,
                command=f"find_mac {mac_address}",
                error=str(e),
                execution_time=0.0,
                task_id=context.task_id,
                device_id=context.device_id,
            )

    @staticmethod
    async def get_arp_table(context: NetworkTaskContext) -> TaskResult:
        """获取ARP表"""
        try:
            adapter = get_adapter(context.device_type)
            command = adapter.get_command("get_arp_table")

            mock_output = """
  Type: S-Static   D-Dynamic   O-Openflow   R-Rule   M-Multiport  I-Invalid
IP Address      MAC Address     VLAN     Interface                Aging   Type
192.168.1.1     0050-5688-70c0  1        GE1/0/1                  20      D
192.168.1.2     0050-5688-70c1  1        GE1/0/2                  15      D
192.168.1.100   0050-5688-70c2  10       GE1/0/3                  25      D
10.0.0.100      0050-5688-70c3  1        GE1/0/4                  30      D
            """

            parsed_result = adapter.parse_output("get_arp_table", mock_output)

            return TaskResult(
                success=True,
                command=command,
                raw_output=mock_output,
                parsed_data=parsed_result,
                execution_time=0.6,
                task_id=context.task_id,
                device_id=context.device_id,
            )

        except Exception as e:
            return TaskResult(
                success=False,
                command="get_arp_table",
                error=str(e),
                execution_time=0.0,
                task_id=context.task_id,
                device_id=context.device_id,
            )


class ConnectivityTask:
    """连通性测试任务"""

    @staticmethod
    async def ping_host(context: NetworkTaskContext, target: str, count: int = 4) -> TaskResult:
        """Ping测试"""
        try:
            adapter = get_adapter(context.device_type)
            command = adapter.get_command("ping", target=target)

            mock_output = f"""
PING {target}: 56  data bytes, press CTRL_C to break
56 bytes from {target}: icmp_seq=0 ttl=64 time=1.000 ms
56 bytes from {target}: icmp_seq=1 ttl=64 time=2.000 ms
56 bytes from {target}: icmp_seq=2 ttl=64 time=1.500 ms
56 bytes from {target}: icmp_seq=3 ttl=64 time=1.200 ms

--- {target} ping statistics ---
{count} packets transmitted, {count} received, 0% packet loss
round-trip min/avg/max = 1.000/1.425/2.000 ms
            """

            parsed_result = adapter.parse_output("ping", mock_output)

            return TaskResult(
                success=True,
                command=command,
                raw_output=mock_output,
                parsed_data=parsed_result,
                execution_time=4.2,
                task_id=context.task_id,
                device_id=context.device_id,
            )

        except Exception as e:
            return TaskResult(
                success=False,
                command=f"ping {target}",
                error=str(e),
                execution_time=0.0,
                task_id=context.task_id,
                device_id=context.device_id,
            )


# 任务注册表
NETWORK_TASKS = {
    # 设备信息类
    "device_version": DeviceInfoTask.get_device_version,
    # 接口管理类
    "interface_status": InterfaceManagementTask.get_interface_status,
    "interface_detail": InterfaceManagementTask.get_interface_detail,
    # 网络发现类
    "find_mac": NetworkDiscoveryTask.find_mac_address,
    "arp_table": NetworkDiscoveryTask.get_arp_table,
    # 连通性测试类
    "ping": ConnectivityTask.ping_host,
}


def get_available_tasks() -> list[str]:
    """获取所有可用的网络任务"""
    return list(NETWORK_TASKS.keys())


async def execute_network_task(task_name: str, context: NetworkTaskContext, **kwargs) -> TaskResult:
    """执行指定的网络任务"""
    if task_name not in NETWORK_TASKS:
        return TaskResult(
            success=False,
            command=f"unknown_task:{task_name}",
            error=f"未知的任务类型: {task_name}",
            execution_time=0.0,
            task_id=context.task_id,
            device_id=context.device_id,
        )

    task_func = NETWORK_TASKS[task_name]

    # 根据任务类型传递不同的参数
    if task_name == "interface_detail":
        return await task_func(context, kwargs.get("interface", "GE1/0/1"))
    elif task_name == "find_mac":
        return await task_func(context, kwargs.get("mac_address", ""))
    elif task_name == "ping":
        return await task_func(context, kwargs.get("target", ""), kwargs.get("count", 4))
    else:
        return await task_func(context)
