"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_service.py
@DateTime: 2025-06-17
@Docs: 网络自动化服务层
"""

import uuid
from datetime import datetime
from typing import Any

from app.services.device_service import DeviceService

from ..core.runner import TaskRunner
from ..tasks import NetworkTaskContext, execute_network_task, get_available_tasks


class NetworkAutomationService:
    """网络自动化服务层

    专注于网络自动化任务执行，不包含设备CRUD操作
    设备管理由DeviceService负责
    """

    def __init__(self, device_service: DeviceService | None = None):
        """初始化网络自动化服务

        Args:
            device_service: 设备服务实例，用于获取设备信息
        """
        self.device_service = device_service or DeviceService()
        self.task_runner = TaskRunner()

    def get_supported_tasks(self) -> list[str]:
        """获取支持的网络任务列表"""
        return get_available_tasks()

    def get_task_categories(self) -> dict[str, list[str]]:
        """获取任务分类信息"""
        task_info_map = {
            "device_version": "device_info",
            "interface_status": "interface",
            "interface_detail": "interface",
            "find_mac": "network",
            "arp_table": "network",
            "ping": "connectivity",
        }

        categories = {}
        for task_name in self.get_supported_tasks():
            category = task_info_map.get(task_name, "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(task_name)

        return categories

    async def execute_device_task(
        self, device_id: int, task_name: str, username: str = "admin", password: str = "admin", **task_params
    ) -> dict[str, Any]:
        """执行单个设备的自动化任务

        Args:
            device_id: 设备ID（数据库ID）
            task_name: 任务名称
            username: 设备登录用户名
            password: 设备登录密码
            **task_params: 任务特定参数

        Returns:
            任务执行结果
        """
        # 通过设备服务获取设备信息
        device = await self.device_service.get_by_id(device_id)
        if not device:
            return {
                "success": False,
                "error": f"设备不存在: {device_id}",
                "task_id": str(uuid.uuid4()),
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
            }

        # 检查任务是否支持
        if task_name not in get_available_tasks():
            return {
                "success": False,
                "error": f"不支持的任务: {task_name}",
                "task_id": str(uuid.uuid4()),
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
            }

        # 创建任务上下文
        task_id = str(uuid.uuid4())
        context = NetworkTaskContext(
            device_id=str(device.id),
            device_ip=str(device.management_ip),
            device_type=device.brand.code.lower() if device.brand else "unknown",
            username=username,
            password=password,
            task_id=task_id,
            timestamp=datetime.now(),
            extra_params=task_params,
        )

        try:
            # 执行任务
            result = await execute_network_task(task_name, context, **task_params)

            # 格式化返回结果
            return {
                "success": result.success,
                "task_id": result.task_id,
                "device_id": result.device_id,
                "command": result.command,
                "duration": result.execution_time,
                "timestamp": datetime.now().isoformat(),
                "result": result.parsed_data if result.success else None,
                "raw_output": result.raw_output if result.success else None,
                "error": result.error if not result.success else None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"任务执行异常: {str(e)}",
                "task_id": task_id,
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
            }

    async def execute_batch_task(
        self, device_ids: list[int], task_name: str, username: str = "admin", password: str = "admin", **task_params
    ) -> dict[str, Any]:
        """批量执行设备自动化任务

        Args:
            device_ids: 设备ID列表（数据库ID）
            task_name: 任务名称
            username: 设备登录用户名
            password: 设备登录密码
            **task_params: 任务特定参数

        Returns:
            批量任务执行结果
        """
        batch_id = str(uuid.uuid4())
        results = []

        for device_id in device_ids:
            result = await self.execute_device_task(device_id, task_name, username, password, **task_params)
            results.append(result)

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count

        return {
            "batch_id": batch_id,
            "total_count": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    async def test_device_connectivity(
        self, device_id: int, username: str = "admin", password: str = "admin", timeout: int = 30
    ) -> dict[str, Any]:
        """测试设备连通性

        Args:
            device_id: 设备ID（数据库ID）
            username: 设备登录用户名
            password: 设备登录密码
            timeout: 超时时间（秒）

        Returns:
            连通性测试结果
        """
        device = await self.device_service.get_by_id(device_id)
        if not device:
            return {
                "success": False,
                "error": f"设备不存在: {device_id}",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
            }

        # 执行ping测试
        result = await self.execute_device_task(
            device_id=device_id,
            task_name="ping",
            username=username,
            password=password,
            target_ip=str(device.management_ip),
            timeout=timeout,
        )

        return {
            "device_id": device_id,
            "device_ip": str(device.management_ip),
            "success": result["success"],
            "response_time": result.get("duration", 0) * 1000 if result["success"] else None,  # 转换为毫秒
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat(),
        }

    async def discover_network_devices(
        self,
        network_range: str,
        device_types: list[str] | None = None,
        username: str = "admin",
        password: str = "admin",
        timeout: int = 10,
    ) -> dict[str, Any]:
        """网络设备发现

        Args:
            network_range: 网络范围 (CIDR格式)
            device_types: 要发现的设备类型列表
            username: 设备登录用户名
            password: 设备登录密码
            timeout: 超时时间（秒）

        Returns:
            网络发现结果
        """
        discovery_id = str(uuid.uuid4())
        start_time = datetime.now()

        # 这里应该实现实际的网络扫描逻辑
        # 目前返回模拟数据
        discovered_devices = []

        # 模拟发现过程
        import ipaddress

        try:
            network = ipaddress.ip_network(network_range, strict=False)
            total_hosts = network.num_addresses

            # 模拟发现几个设备
            for i, ip in enumerate(network.hosts()):
                if i >= 5:  # 限制模拟数量
                    break

                discovered_devices.append(
                    {
                        "ip": str(ip),
                        "hostname": f"Device-{i + 1}",
                        "device_type": "h3c",
                        "vendor": "H3C",
                        "model": "Unknown",
                        "version": "Unknown",
                        "response_time": 5.0 + i,
                    }
                )
        except Exception as e:
            return {
                "success": False,
                "error": f"网络范围解析失败: {str(e)}",
                "discovery_id": discovery_id,
                "timestamp": start_time.isoformat(),
            }

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "discovery_id": discovery_id,
            "network_range": network_range,
            "total_hosts": total_hosts,
            "scanned_hosts": min(total_hosts, 5),  # 模拟扫描数量
            "discovered_devices": discovered_devices,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
        }

    async def get_automation_statistics(self) -> dict[str, Any]:
        """获取自动化任务统计信息

        Returns:
            自动化统计信息
        """
        # 这里应该从任务执行历史中获取统计信息
        # 目前返回模拟数据
        supported_tasks = self.get_supported_tasks()
        task_categories = self.get_task_categories()

        return {
            "total_supported_tasks": len(supported_tasks),
            "task_categories": list(task_categories.keys()),
            "tasks_by_category": {category: len(tasks) for category, tasks in task_categories.items()},
            "supported_device_types": ["h3c", "huawei", "cisco", "juniper"],
            "last_updated": datetime.now().isoformat(),
        }


# 向后兼容的别名
NetworkService = NetworkAutomationService
