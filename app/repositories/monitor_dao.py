"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: monitor_dao.py
@DateTime: 2025-06-17
@Docs: 监控和告警相关的数据访问层
"""

from datetime import datetime
from typing import Any

from app.models.data_models import Alert, MonitorMetric

from .base_dao import BaseDAO


class MonitorMetricDAO(BaseDAO[MonitorMetric]):
    """监控指标DAO"""

    def __init__(self):
        super().__init__(MonitorMetric)

    async def list_by_device(self, device_id: int, limit: int = 100) -> list[MonitorMetric]:
        """获取设备的监控指标（按时间倒序）"""
        results = await self.list_by_filters(
            filters={"device_id": device_id, "is_deleted": False},
            prefetch_related=["device"],
            order_by=["-collected_at"],
        )
        return results[:limit]

    async def list_by_device_and_metric_type(
        self, device_id: int, metric_type: str, limit: int = 100
    ) -> list[MonitorMetric]:
        """获取设备指定类型的监控指标"""
        results = await self.list_by_filters(
            filters={"device_id": device_id, "metric_type": metric_type, "is_deleted": False},
            prefetch_related=["device"],
            order_by=["-collected_at"],
        )
        return results[:limit]

    async def get_latest_metrics_by_device(self, device_id: int) -> list[MonitorMetric]:
        """获取设备的最新监控指标（每种类型的最新一条）"""
        # 获取所有指标类型
        metric_types = await (
            MonitorMetric.filter(device_id=device_id, is_deleted=False).distinct().values_list("metric_type", flat=True)
        )

        latest_metrics = []
        for metric_type in metric_types:
            metric = await (
                MonitorMetric.filter(device_id=device_id, metric_type=metric_type, is_deleted=False)
                .prefetch_related("device")
                .order_by("-collected_at")
                .first()
            )
            if metric:
                latest_metrics.append(metric)

        return latest_metrics

    async def get_metrics_in_time_range(
        self, device_id: int, metric_type: str, start_time: datetime, end_time: datetime
    ) -> list[MonitorMetric]:
        """获取指定时间范围内的监控指标"""
        return await self.list_by_filters(
            filters={
                "device_id": device_id,
                "metric_type": metric_type,
                "collected_at__gte": start_time,
                "collected_at__lte": end_time,
                "is_deleted": False,
            },
            prefetch_related=["device"],
            order_by=["collected_at"],
        )

    async def get_abnormal_metrics(self, limit: int = 100) -> list[MonitorMetric]:
        """获取异常的监控指标"""
        results = await self.list_by_filters(
            filters={"status__in": ["WARNING", "CRITICAL"], "is_deleted": False},
            prefetch_related=["device"],
            order_by=["-collected_at"],
        )
        return results[:limit]

    async def get_metric_statistics(
        self, device_id: int, metric_type: str, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """获取指标统计信息（最大值、最小值、平均值等）"""
        from tortoise.functions import Avg, Count, Max, Min

        result = await (
            MonitorMetric.filter(
                device_id=device_id,
                metric_type=metric_type,
                collected_at__gte=start_time,
                collected_at__lte=end_time,
                is_deleted=False,
            )
            .annotate(max_value=Max("value"), min_value=Min("value"), avg_value=Avg("value"), count=Count("id"))
            .values("max_value", "min_value", "avg_value", "count")
        )

        # 获取第一个结果
        if result:
            return result[0] if isinstance(result, list) else result
        return {"max_value": None, "min_value": None, "avg_value": None, "count": 0}

    async def clean_old_metrics(self, days: int = 30) -> int:
        """清理旧的监控数据"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        return await self.delete_by_filters(collected_at__lt=cutoff_date)

    async def get_device_metric_summary(self, device_id: int) -> dict[str, Any]:
        """获取设备监控指标汇总"""

        # 统计各状态的指标数量
        status_stats = await self.get_count_by_status("status")

        # 获取最新指标时间
        latest_metric = await (
            MonitorMetric.filter(device_id=device_id, is_deleted=False).order_by("-collected_at").first()
        )

        # 统计指标类型数量
        metric_type_count = await MonitorMetric.filter(device_id=device_id, is_deleted=False).distinct().count()

        return {
            "status_stats": status_stats,
            "latest_collected_at": latest_metric.collected_at if latest_metric else None,
            "metric_type_count": metric_type_count,
            "total_metrics": sum(status_stats.values()) if status_stats else 0,
        }


class AlertDAO(BaseDAO[Alert]):
    """告警DAO"""

    def __init__(self):
        super().__init__(Alert)

    async def list_active_alerts(self, limit: int = 100) -> list[Alert]:
        """获取活跃的告警"""
        results = await self.list_by_filters(
            filters={"status": "ACTIVE", "is_deleted": False},
            prefetch_related=["device"],
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_by_device(self, device_id: int, limit: int = 100) -> list[Alert]:
        """获取设备的告警记录"""
        results = await self.list_by_filters(
            filters={"device_id": device_id, "is_deleted": False},
            prefetch_related=["device"],
            order_by=["-created_at"],
        )
        return results[:limit]

    async def list_by_severity(self, severity: str, limit: int = 100) -> list[Alert]:
        """获取指定严重程度的告警"""
        results = await self.list_by_filters(
            filters={"severity": severity, "is_deleted": False},
            prefetch_related=["device"],
            order_by=["-created_at"],
        )
        return results[:limit]

    async def search_alerts(
        self,
        keyword: str | None = None,
        device_id: int | None = None,
        severity: str | None = None,
        status: str | None = None,
        alert_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """搜索告警"""
        filters: dict[str, Any] = {"is_deleted": False}

        if device_id:
            filters["device_id"] = device_id
        if severity:
            filters["severity"] = severity
        if status:
            filters["status"] = status
        if alert_type:
            filters["alert_type"] = alert_type
        if start_time:
            filters["created_at__gte"] = start_time
        if end_time:
            filters["created_at__lte"] = end_time

        # 如果有关键词，使用复杂查询
        if keyword:
            from tortoise.expressions import Q

            query = self.model.filter(**filters).filter(
                Q(title__icontains=keyword) | Q(message__icontains=keyword) | Q(metric_name__icontains=keyword)
            )

            # 计算总数
            total = await query.count()

            # 分页查询
            offset = (page - 1) * page_size
            items = await query.prefetch_related("device").offset(offset).limit(page_size).order_by("-created_at")

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
            return await self.paginate(
                page=page, page_size=page_size, filters=filters, prefetch_related=["device"], order_by=["-created_at"]
            )

    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> Alert | None:
        """确认告警"""
        return await self.update_by_id(
            alert_id, status="ACKNOWLEDGED", acknowledged_by=acknowledged_by, acknowledged_at=datetime.now()
        )

    async def resolve_alert(self, alert_id: int, resolved_by: str | None = None) -> Alert | None:
        """解决告警"""
        update_data = {"status": "RESOLVED", "resolved_at": datetime.now()}
        if resolved_by:
            update_data["acknowledged_by"] = resolved_by
            update_data["acknowledged_at"] = datetime.now()

        return await self.update_by_id(alert_id, **update_data)

    async def batch_acknowledge_alerts(self, alert_ids: list[int], acknowledged_by: str) -> int:
        """批量确认告警"""
        return await self.update_by_filters(
            filters={"id__in": alert_ids, "status": "ACTIVE"},
            status="ACKNOWLEDGED",
            acknowledged_by=acknowledged_by,
            acknowledged_at=datetime.now(),
        )

    async def batch_resolve_alerts(self, alert_ids: list[int]) -> int:
        """批量解决告警"""
        return await self.update_by_filters(
            filters={"id__in": alert_ids, "status__in": ["ACTIVE", "ACKNOWLEDGED"]},
            status="RESOLVED",
            resolved_at=datetime.now(),
        )

    async def get_alert_statistics(self, days: int = 30) -> dict[str, Any]:
        """获取告警统计信息"""
        from datetime import timedelta

        from tortoise.functions import Count

        start_date = datetime.now() - timedelta(days=days)

        # 按严重程度统计
        severity_stats = await (
            Alert.filter(created_at__gte=start_date, is_deleted=False)
            .group_by("severity")
            .annotate(count=Count("id"))
            .values("severity", "count")
        )

        # 按状态统计
        status_stats = await (
            Alert.filter(created_at__gte=start_date, is_deleted=False)
            .group_by("status")
            .annotate(count=Count("id"))
            .values("status", "count")
        )

        # 按类型统计
        type_stats = await (
            Alert.filter(created_at__gte=start_date, is_deleted=False)
            .group_by("alert_type")
            .annotate(count=Count("id"))
            .values("alert_type", "count")
        )

        # 总数统计
        total_alerts = await Alert.filter(created_at__gte=start_date, is_deleted=False).count()
        active_alerts = await Alert.filter(created_at__gte=start_date, status="ACTIVE", is_deleted=False).count()

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "severity_stats": {item["severity"]: item["count"] for item in severity_stats},
            "status_stats": {item["status"]: item["count"] for item in status_stats},
            "type_stats": {item["alert_type"]: item["count"] for item in type_stats},
            "period_days": days,
        }

    async def get_top_alert_devices(self, limit: int = 10, days: int = 30) -> list[dict[str, Any]]:
        """获取告警最多的设备"""
        from datetime import timedelta

        from tortoise.functions import Count

        start_date = datetime.now() - timedelta(days=days)

        results = await (
            Alert.filter(created_at__gte=start_date, is_deleted=False)
            .prefetch_related("device")
            .group_by("device_id")
            .annotate(alert_count=Count("id"))
            .values("device_id", "device__name", "device__management_ip", "device__hostname", "alert_count")
        )

        # 手动排序和限制
        sorted_results = sorted(results, key=lambda x: x["alert_count"], reverse=True)
        return sorted_results[:limit]

    async def clean_old_alerts(self, days: int = 90) -> int:
        """清理旧的告警记录"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        # 只删除已解决的告警
        return await self.delete_by_filters(status="RESOLVED", resolved_at__lt=cutoff_date)
