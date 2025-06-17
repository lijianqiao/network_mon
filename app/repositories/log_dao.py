"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: log_dao.py
@DateTime: 2025-06-17
@Docs: 日志相关的数据访问层
"""

from datetime import datetime
from typing import Any

from app.models.data_models import OperationLog, SystemLog

from .base_dao import BaseDAO


class OperationLogDAO(BaseDAO[OperationLog]):
    """操作日志DAO"""

    def __init__(self):
        super().__init__(OperationLog)

    async def list_by_user(self, user: str, limit: int = 100) -> list[OperationLog]:
        """获取指定用户的操作日志"""
        results = await self.list_by_filters(
            filters={"user": user, "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_by_action(self, action: str, limit: int = 100) -> list[OperationLog]:
        """获取指定操作的日志"""
        results = await self.list_by_filters(
            filters={"action": action, "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_by_resource_type(self, resource_type: str, limit: int = 100) -> list[OperationLog]:
        """获取指定资源类型的操作日志"""
        results = await self.list_by_filters(
            filters={"resource_type": resource_type, "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_failed_operations(self, limit: int = 100) -> list[OperationLog]:
        """获取失败的操作日志"""
        results = await self.list_by_filters(
            filters={"result": "FAILED", "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def search_operation_logs(
        self,
        keyword: str | None = None,
        user: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        result: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """搜索操作日志"""
        filters: dict[str, Any] = {"is_deleted": False}

        if user:
            filters["user"] = user
        if action:
            filters["action"] = action
        if resource_type:
            filters["resource_type"] = resource_type
        if result:
            filters["result"] = result
        if start_time:
            filters["created_at__gte"] = start_time
        if end_time:
            filters["created_at__lte"] = end_time

        # 如果有关键词，使用复杂查询
        if keyword:
            from tortoise.expressions import Q

            query = self.model.filter(**filters).filter(
                Q(resource_name__icontains=keyword)
                | Q(error_message__icontains=keyword)
                | Q(ip_address__icontains=keyword)
            )

            # 计算总数
            total = await query.count()

            # 分页查询
            offset = (page - 1) * page_size
            items = await query.offset(offset).limit(page_size).order_by("-created_at")

            # 计算分页信息
            total_pages = (total + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        else:
            return await self.paginate(page=page, page_size=page_size, filters=filters, order_by=["-created_at"])

    async def get_operation_statistics(self, days: int = 30) -> dict[str, Any]:
        """获取操作统计信息"""
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        # 按操作类型统计
        action_stats = await self.get_count_by_status("action")

        # 按结果统计
        result_stats = await self.get_count_by_status("result")

        # 按资源类型统计
        resource_stats = await self.get_count_by_status("resource_type")

        # 总数统计
        total_operations = await self.count(created_at__gte=start_date)
        failed_operations = await self.count(created_at__gte=start_date, result="FAILED")

        return {
            "total_operations": total_operations,
            "failed_operations": failed_operations,
            "success_rate": ((total_operations - failed_operations) / total_operations * 100)
            if total_operations > 0
            else 0,
            "action_stats": action_stats,
            "result_stats": result_stats,
            "resource_stats": resource_stats,
            "period_days": days,
        }

    async def get_user_activity_stats(self, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
        """获取用户活动统计"""
        from datetime import timedelta

        from tortoise.functions import Count

        start_date = datetime.now() - timedelta(days=days)

        results = await (
            OperationLog.filter(created_at__gte=start_date, is_deleted=False)
            .group_by("user")
            .annotate(operation_count=Count("id"))
            .values("user", "operation_count")
        )

        # 手动排序和限制
        sorted_results = sorted(results, key=lambda x: x["operation_count"], reverse=True)
        return sorted_results[:limit]

    async def get_slow_operations(self, threshold: float = 5.0, limit: int = 100) -> list[OperationLog]:
        """获取执行时间较长的操作"""
        results = await self.list_by_filters(
            filters={"execution_time__gte": threshold, "is_deleted": False},
            order_by=["-execution_time"],
        )
        return results[:limit]

    async def clean_old_operation_logs(self, days: int = 365) -> int:
        """清理旧的操作日志"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        return await self.delete_by_filters(created_at__lt=cutoff_date)


class SystemLogDAO(BaseDAO[SystemLog]):
    """系统日志DAO"""

    def __init__(self):
        super().__init__(SystemLog)

    async def list_by_level(self, level: str, limit: int = 100) -> list[SystemLog]:
        """获取指定级别的系统日志"""
        results = await self.list_by_filters(
            filters={"level": level, "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_by_module(self, module: str, limit: int = 100) -> list[SystemLog]:
        """获取指定模块的系统日志"""
        results = await self.list_by_filters(
            filters={"module": module, "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_error_logs(self, limit: int = 100) -> list[SystemLog]:
        """获取错误日志"""
        results = await self.list_by_filters(
            filters={"level__in": ["ERROR", "CRITICAL"], "is_deleted": False},
            order_by=["-created_at"],
        )
        return results[:limit]

    async def search_system_logs(
        self,
        keyword: str | None = None,
        level: str | None = None,
        module: str | None = None,
        logger_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """搜索系统日志"""
        filters: dict[str, Any] = {"is_deleted": False}

        if level:
            filters["level"] = level
        if module:
            filters["module"] = module
        if logger_name:
            filters["logger_name"] = logger_name
        if start_time:
            filters["created_at__gte"] = start_time
        if end_time:
            filters["created_at__lte"] = end_time

        # 如果有关键词，使用复杂查询
        if keyword:
            from tortoise.expressions import Q

            query = self.model.filter(**filters).filter(
                Q(message__icontains=keyword) | Q(exception_info__icontains=keyword) | Q(logger_name__icontains=keyword)
            )

            # 计算总数
            total = await query.count()

            # 分页查询
            offset = (page - 1) * page_size
            items = await query.offset(offset).limit(page_size).order_by("-created_at")

            # 计算分页信息
            total_pages = (total + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        else:
            return await self.paginate(page=page, page_size=page_size, filters=filters, order_by=["-created_at"])

    async def get_log_statistics(self, days: int = 30) -> dict[str, Any]:
        """获取日志统计信息"""
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        # 按日志级别统计
        level_stats = await self.get_count_by_status("level")

        # 按模块统计
        module_stats = await self.get_count_by_status("module")

        # 总数统计
        total_logs = await self.count(created_at__gte=start_date)
        error_logs = await self.count(created_at__gte=start_date, level__in=["ERROR", "CRITICAL"])

        return {
            "total_logs": total_logs,
            "error_logs": error_logs,
            "error_rate": (error_logs / total_logs * 100) if total_logs > 0 else 0,
            "level_stats": level_stats,
            "module_stats": module_stats,
            "period_days": days,
        }

    async def get_frequent_errors(self, days: int = 7, limit: int = 10) -> list[dict[str, Any]]:
        """获取频繁出现的错误"""
        from datetime import timedelta

        from tortoise.functions import Count

        start_date = datetime.now() - timedelta(days=days)

        results = await (
            SystemLog.filter(created_at__gte=start_date, level__in=["ERROR", "CRITICAL"], is_deleted=False)
            .group_by("message")
            .annotate(error_count=Count("id"))
            .values("message", "error_count", "level", "module")
        )

        # 手动排序和限制
        sorted_results = sorted(results, key=lambda x: x["error_count"], reverse=True)
        return sorted_results[:limit]

    async def clean_old_system_logs(self, days: int = 90) -> int:
        """清理旧的系统日志"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        return await self.delete_by_filters(created_at__lt=cutoff_date)
