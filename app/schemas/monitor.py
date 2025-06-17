"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: monitor.py
@DateTime: 2025-06-17
@Docs: 监控相关校验模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.data_enum import (
    AlertStatusEnum,
    AlertTypeEnum,
    MetricStatusEnum,
    MetricTypeEnum,
    SeverityEnum,
)

from .base import BaseQueryParams, BaseTimeRange
from .device import DeviceResponse


class MonitorMetricBase(BaseModel):
    """监控指标基础模型"""

    device_id: int = Field(gt=0, description="关联设备ID")
    metric_type: MetricTypeEnum = Field(description="指标类型")
    metric_name: str = Field(min_length=1, max_length=100, description="指标名称")
    value: float = Field(description="指标值")
    unit: str | None = Field(default=None, max_length=20, description="指标单位")
    threshold_warning: float | None = Field(default=None, description="告警阈值")
    threshold_critical: float | None = Field(default=None, description="严重告警阈值")


class MonitorMetricCreate(MonitorMetricBase):
    """创建监控指标模型"""

    collected_at: datetime | None = Field(default=None, description="采集时间")


class MonitorMetricUpdate(BaseModel):
    """更新监控指标模型"""

    value: float | None = Field(default=None, description="指标值")
    unit: str | None = Field(default=None, max_length=20, description="指标单位")
    threshold_warning: float | None = Field(default=None, description="告警阈值")
    threshold_critical: float | None = Field(default=None, description="严重告警阈值")
    status: MetricStatusEnum | None = Field(default=None, description="指标状态")


class MonitorMetricResponse(MonitorMetricBase):
    """监控指标响应模型"""

    id: int = Field(description="指标ID")
    device: DeviceResponse = Field(description="关联设备")
    status: MetricStatusEnum = Field(description="指标状态")
    collected_at: datetime = Field(description="采集时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class MonitorMetricQueryParams(BaseQueryParams, BaseTimeRange):
    """监控指标查询参数"""

    device_id: int | None = Field(default=None, gt=0, description="设备ID筛选")
    metric_type: MetricTypeEnum | None = Field(default=None, description="指标类型筛选")
    status: MetricStatusEnum | None = Field(default=None, description="指标状态筛选")


class MetricStatistics(BaseModel):
    """指标统计信息"""

    metric_type: MetricTypeEnum = Field(description="指标类型")
    device_count: int = Field(ge=0, description="设备数量")
    avg_value: float | None = Field(description="平均值")
    max_value: float | None = Field(description="最大值")
    min_value: float | None = Field(description="最小值")
    normal_count: int = Field(ge=0, description="正常数量")
    warning_count: int = Field(ge=0, description="告警数量")
    critical_count: int = Field(ge=0, description="严重告警数量")


# ================================ 告警相关 ================================


class AlertBase(BaseModel):
    """告警基础模型"""

    device_id: int = Field(gt=0, description="关联设备ID")
    alert_type: AlertTypeEnum = Field(description="告警类型")
    severity: SeverityEnum = Field(description="告警级别")
    title: str = Field(min_length=1, max_length=200, description="告警标题")
    message: str = Field(min_length=1, description="告警消息")
    metric_name: str | None = Field(default=None, max_length=100, description="相关指标名称")
    current_value: float | None = Field(default=None, description="当前值")
    threshold_value: float | None = Field(default=None, description="阈值")


class AlertCreate(AlertBase):
    """创建告警模型"""

    pass


class AlertUpdate(BaseModel):
    """更新告警模型"""

    status: AlertStatusEnum | None = Field(default=None, description="告警状态")
    acknowledged_by: str | None = Field(default=None, max_length=50, description="确认人")


class AlertResponse(AlertBase):
    """告警响应模型"""

    id: int = Field(description="告警ID")
    device: DeviceResponse = Field(description="关联设备")
    status: AlertStatusEnum = Field(description="告警状态")
    acknowledged_by: str | None = Field(description="确认人")
    acknowledged_at: datetime | None = Field(description="确认时间")
    resolved_at: datetime | None = Field(description="解决时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class AlertQueryParams(BaseQueryParams, BaseTimeRange):
    """告警查询参数"""

    device_id: int | None = Field(default=None, gt=0, description="设备ID筛选")
    alert_type: AlertTypeEnum | None = Field(default=None, description="告警类型筛选")
    severity: SeverityEnum | None = Field(default=None, description="告警级别筛选")
    status: AlertStatusEnum | None = Field(default=None, description="告警状态筛选")


class AlertAcknowledge(BaseModel):
    """告警确认模型"""

    acknowledged_by: str = Field(min_length=1, max_length=50, description="确认人")


class AlertResolve(BaseModel):
    """告警解决模型"""

    resolved_by: str = Field(min_length=1, max_length=50, description="解决人")
    resolution_note: str | None = Field(default=None, description="解决备注")


class AlertStatistics(BaseModel):
    """告警统计信息"""

    total_count: int = Field(ge=0, description="总告警数")
    active_count: int = Field(ge=0, description="活跃告警数")
    acknowledged_count: int = Field(ge=0, description="已确认告警数")
    resolved_count: int = Field(ge=0, description="已解决告警数")
    critical_count: int = Field(ge=0, description="严重告警数")
    warning_count: int = Field(ge=0, description="警告告警数")
    info_count: int = Field(ge=0, description="信息告警数")
