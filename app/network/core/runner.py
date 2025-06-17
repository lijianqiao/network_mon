"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: runner.py
@DateTime: 2025-06-17
@Docs: Nornir任务执行器
"""

import asyncio
from collections.abc import Callable
from typing import Any

from app.network.core.inventory import DynamicInventory


class TaskRunner:
    """Nornir任务执行器

    负责创建Nornir实例并执行网络自动化任务
    """

    def __init__(self, max_workers: int = 50):
        """初始化任务执行器

        Args:
            max_workers: 最大并发工作线程数
        """
        self.inventory_manager = DynamicInventory()
        self.max_workers = max_workers

    async def run_on_devices(
        self, task_function: Callable, device_ids: list[int], password: str | None = None, **task_kwargs
    ) -> dict[str, Any]:
        """在指定设备上执行任务

        Args:
            task_function: 要执行的任务函数
            device_ids: 目标设备ID列表
            password: 设备登录密码
            **task_kwargs: 传递给任务函数的参数

        Returns:
            执行结果字典，包含成功和失败的设备信息

        Raises:
            ValueError: 当设备ID列表为空时
            RuntimeError: 当任务执行失败时
        """
        if not device_ids:
            raise ValueError("设备ID列表不能为空")

        try:
            # 构建设备清单
            inventory_config = await self.inventory_manager.build_from_device_ids(
                device_ids=device_ids, password=password
            )

            # 创建任务列表
            tasks = []
            for host_name, host_config in inventory_config["hosts"].items():
                task = self._execute_single_task(
                    host_name=host_name, host_config=host_config, task_function=task_function, task_kwargs=task_kwargs
                )
                tasks.append(task)

            # 并发执行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            processed_results = {"success": {}, "failed": {}}
            for i, result in enumerate(results):
                host_name = list(inventory_config["hosts"].keys())[i]

                if isinstance(result, Exception):
                    processed_results["failed"][host_name] = str(result)
                else:
                    processed_results["success"][host_name] = result

            return processed_results

        except Exception as e:
            raise RuntimeError(f"任务执行失败: {str(e)}") from e

    async def run_on_filters(
        self,
        task_function: Callable,
        brand_ids: list[int] | None = None,
        area_ids: list[int] | None = None,
        group_ids: list[int] | None = None,
        password: str | None = None,
        **task_kwargs,
    ) -> dict[str, Any]:
        """根据过滤条件在设备上执行任务

        Args:
            task_function: 要执行的任务函数
            brand_ids: 品牌ID列表
            area_ids: 区域ID列表
            group_ids: 分组ID列表
            password: 设备登录密码
            **task_kwargs: 传递给任务函数的参数

        Returns:
            执行结果字典
        """
        try:
            # 构建设备清单
            inventory_config = await self.inventory_manager.build_from_filters(
                brand_ids=brand_ids, area_ids=area_ids, group_ids=group_ids, password=password
            )

            if not inventory_config["hosts"]:
                return {"success": {}, "failed": {}}

            # 创建任务列表
            tasks = []
            for host_name, host_config in inventory_config["hosts"].items():
                task = self._execute_single_task(
                    host_name=host_name, host_config=host_config, task_function=task_function, task_kwargs=task_kwargs
                )
                tasks.append(task)

            # 并发执行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            processed_results = {"success": {}, "failed": {}}
            for i, result in enumerate(results):
                host_name = list(inventory_config["hosts"].keys())[i]

                if isinstance(result, Exception):
                    processed_results["failed"][host_name] = str(result)
                else:
                    processed_results["success"][host_name] = result

            return processed_results

        except Exception as e:
            raise RuntimeError(f"根据过滤条件执行任务失败: {str(e)}") from e

    async def _execute_single_task(
        self, host_name: str, host_config: dict[str, Any], task_function: Callable, task_kwargs: dict[str, Any]
    ) -> Any:
        """在单个设备上执行任务

        Args:
            host_name: 设备名称
            host_config: 设备配置
            task_function: 任务函数
            task_kwargs: 任务参数

        Returns:
            任务执行结果

        Raises:
            Exception: 任务执行异常
        """
        try:
            # 这里暂时返回模拟结果，后续会集成真正的Nornir/Scrapli
            # 模拟任务执行
            await asyncio.sleep(0.1)  # 模拟网络延迟

            # 调用任务函数（这里是简化版本）
            result = await task_function(host_config, **task_kwargs)

            return {"host": host_name, "task": task_function.__name__, "result": result, "status": "success"}

        except Exception as e:
            raise RuntimeError(f"设备 {host_name} 任务执行异常: {e}") from e

    async def get_device_summary(self, device_ids: list[int]) -> dict[str, Any]:
        """获取设备摘要信息（用于调试和验证）

        Args:
            device_ids: 设备ID列表

        Returns:
            设备摘要信息
        """
        try:
            inventory_config = await self.inventory_manager.build_from_device_ids(device_ids)

            summary = {"total_devices": len(inventory_config["hosts"]), "devices": {}}

            for host_name, host_config in inventory_config["hosts"].items():
                summary["devices"][host_name] = {
                    "hostname": host_config["hostname"],
                    "platform": host_config["platform"],
                    "brand": host_config["data"]["brand"],
                    "model": host_config["data"]["model"],
                }

            return summary

        except Exception as e:
            raise RuntimeError(f"获取设备摘要失败: {str(e)}") from e

    def set_max_workers(self, max_workers: int) -> None:
        """设置最大工作线程数

        Args:
            max_workers: 最大工作线程数
        """
        if max_workers <= 0:
            raise ValueError("最大工作线程数必须大于0")

        self.max_workers = max_workers

    def get_max_workers(self) -> int:
        """获取当前最大工作线程数

        Returns:
            最大工作线程数
        """
        return self.max_workers
