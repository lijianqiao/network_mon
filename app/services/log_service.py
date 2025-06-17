"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: log_service.py
@DateTime: 2025-06-17
@Docs: 日志相关业务服务层
"""

from datetime import datetime, timedelta
from typing import Any

from app.models.data_models import OperationLog, SystemLog
from app.repositories import OperationLogDAO, SystemLogDAO
from app.utils import LogConfig, system_log

from .base_service import BaseService


class OperationLogService(BaseService[OperationLog, OperationLogDAO]):
    """操作日志服务类"""

    def __init__(self):
        super().__init__(OperationLogDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """操作日志创建数据校验"""
        if not data.get("action"):
            raise ValueError("操作动作不能为空")
        if not data.get("resource_type"):
            raise ValueError("资源类型不能为空")
        if not data.get("user"):
            raise ValueError("操作用户不能为空")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_user(self, user: str, user_request: str = "system") -> list[OperationLog]:
        """获取指定用户的操作日志"""
        return await self.dao.list_by_filters(filters={"user": user})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_resource(
        self, resource_type: str, resource_id: int | None = None, user: str = "system"
    ) -> list[OperationLog]:
        """获取指定资源的操作日志"""
        filters: dict[str, Any] = {"resource_type": resource_type}
        if resource_id is not None:
            filters["resource_id"] = resource_id
        return await self.dao.list_by_filters(filters=filters)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_action(self, action: str, user: str = "system") -> list[OperationLog]:
        """获取指定动作的操作日志"""
        return await self.dao.list_by_filters(filters={"action": action})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime, user: str = "system"
    ) -> list[OperationLog]:
        """获取指定日期范围的操作日志"""
        return await self.dao.list_by_filters(filters={"created_at__gte": start_date, "created_at__lte": end_date})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_logs(
        self,
        keyword: str | None = None,
        user_filter: str | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        page: int = 1,
        page_size: int = 20,
        user: str = "system",
    ) -> dict[str, Any]:
        """搜索操作日志"""
        filters: dict[str, Any] = {}

        if user_filter:
            filters["user"] = user_filter
        if resource_type:
            filters["resource_type"] = resource_type
        if action:
            filters["action"] = action
        if keyword:
            filters["OR"] = [
                {"action__icontains": keyword},
                {"resource_type__icontains": keyword},
                {"details__icontains": keyword},
            ]

        return await self.dao.paginate(page=page, page_size=page_size, filters=filters, order_by=["-created_at"])

    @system_log(LogConfig(log_args=True))
    async def get_operation_statistics(self, user: str = "system") -> dict[str, Any]:
        """获取操作统计信息"""
        # 获取总数
        total_count = await self.dao.count()

        # 按用户统计
        user_stats = await self.dao.get_count_by_status("user")

        # 按资源类型统计
        resource_stats = await self.dao.get_count_by_status("resource_type")

        # 按动作统计
        action_stats = await self.dao.get_count_by_status("action")

        return {
            "total": total_count,
            "by_user": user_stats,
            "by_resource_type": resource_stats,
            "by_action": action_stats,
        }


class SystemLogService(BaseService[SystemLog, SystemLogDAO]):
    """系统日志服务类"""

    def __init__(self):
        super().__init__(SystemLogDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """系统日志创建数据校验"""
        if not data.get("level"):
            raise ValueError("日志级别不能为空")
        if not data.get("message"):
            raise ValueError("日志消息不能为空")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_level(self, level: str, user: str = "system") -> list[SystemLog]:
        """获取指定级别的系统日志"""
        return await self.dao.list_by_filters(filters={"level": level})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_module(self, module: str, user: str = "system") -> list[SystemLog]:
        """获取指定模块的系统日志"""
        return await self.dao.list_by_filters(filters={"module": module})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_function(self, function: str, user: str = "system") -> list[SystemLog]:
        """获取指定函数的系统日志"""
        return await self.dao.list_by_filters(filters={"function": function})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime, user: str = "system"
    ) -> list[SystemLog]:
        """获取指定日期范围的系统日志"""
        return await self.dao.list_by_filters(filters={"created_at__gte": start_date, "created_at__lte": end_date})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_logs(
        self,
        keyword: str | None = None,
        level: str | None = None,
        module: str | None = None,
        page: int = 1,
        page_size: int = 20,
        user: str = "system",
    ) -> dict[str, Any]:
        """搜索系统日志"""
        filters: dict[str, Any] = {}

        if level:
            filters["level"] = level
        if module:
            filters["module"] = module
        if keyword:
            filters["OR"] = [
                {"message__icontains": keyword},
                {"module__icontains": keyword},
                {"function__icontains": keyword},
                {"details__icontains": keyword},
            ]

        return await self.dao.paginate(page=page, page_size=page_size, filters=filters, order_by=["-created_at"])

    @system_log(LogConfig(log_args=True))
    async def get_system_statistics(self, user: str = "system") -> dict[str, Any]:
        """获取系统日志统计信息"""
        # 获取总数
        total_count = await self.dao.count()

        # 按级别统计
        level_stats = await self.dao.get_count_by_status("level")

        # 按模块统计
        module_stats = await self.dao.get_count_by_status("module")

        return {
            "total": total_count,
            "by_level": level_stats,
            "by_module": module_stats,
        }

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_recent_errors(self, hours: int = 24, user: str = "system") -> list[SystemLog]:
        """获取最近的错误日志"""
        since = datetime.now() - timedelta(hours=hours)
        return await self.dao.list_by_filters(
            filters={"level": "ERROR", "created_at__gte": since}, order_by=["-created_at"]
        )
