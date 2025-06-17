"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: monitor_service.py
@DateTime: 2025-06-17
@Docs: 监控相关业务服务层
"""

from datetime import datetime
from typing import Any

from app.models.data_models import Alert, MonitorMetric
from app.repositories import AlertDAO, MonitorMetricDAO
from app.utils import LogConfig, system_log

from .base_service import BaseService


class MonitorMetricService(BaseService[MonitorMetric, MonitorMetricDAO]):
    """监控指标服务类"""

    def __init__(self):
        super().__init__(MonitorMetricDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """监控指标创建数据校验"""
        if not data.get("device_id"):
            raise ValueError("设备ID不能为空")
        if not data.get("metric_type"):
            raise ValueError("指标类型不能为空")
        if data.get("value") is None:
            raise ValueError("指标值不能为空")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_device(
        self, device_id: int, metric_type: str | None = None, user: str = "system"
    ) -> list[MonitorMetric]:
        """获取设备的监控指标"""
        filters: dict[str, Any] = {"device_id": device_id}
        if metric_type:
            filters["metric_type"] = metric_type
        return await self.dao.list_by_filters(filters=filters)


class AlertService(BaseService[Alert, AlertDAO]):
    """告警服务类"""

    def __init__(self):
        super().__init__(AlertDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """告警创建数据校验"""
        if not data.get("device_id"):
            raise ValueError("设备ID不能为空")
        if not data.get("alert_type"):
            raise ValueError("告警类型不能为空")
        if not data.get("message"):
            raise ValueError("告警消息不能为空")
        if not data.get("level"):
            raise ValueError("告警级别不能为空")

    @system_log(LogConfig(log_args=True))
    async def acknowledge_alert(self, alert_id: int, user: str = "system") -> Alert | None:
        """确认告警"""
        return await self.dao.update_by_id(
            alert_id, status="acknowledged", acknowledged_at=datetime.now(), acknowledged_by=user
        )
