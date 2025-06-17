"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: 模型包初始化文件，导出所有模型类和枚举
"""

from .data_enum import (
    ActionEnum,
    AlertStatusEnum,
    AlertTypeEnum,
    ConnectionTypeEnum,
    DeviceStatusEnum,
    DeviceTypeEnum,
    LogLevelEnum,
    MetricStatusEnum,
    MetricTypeEnum,
    OperationResultEnum,
    ResourceTypeEnum,
    SeverityEnum,
    TemplateTypeEnum,
)
from .data_models import (
    Alert,
    Area,
    BaseModel,
    Brand,
    ConfigTemplate,
    Device,
    DeviceGroup,
    DeviceModel,
    MonitorMetric,
    OperationLog,
    SystemLog,
)

__all__ = [
    # 基础模型
    "BaseModel",
    # 设备相关模型
    "Brand",
    "DeviceModel",
    "Area",
    "DeviceGroup",
    "Device",
    # 配置模板
    "ConfigTemplate",
    # 监控相关模型
    "MonitorMetric",
    "Alert",
    # 日志相关模型
    "OperationLog",
    "SystemLog",
    # 枚举类
    "ActionEnum",
    "AlertStatusEnum",
    "AlertTypeEnum",
    "ConnectionTypeEnum",
    "DeviceStatusEnum",
    "DeviceTypeEnum",
    "LogLevelEnum",
    "MetricStatusEnum",
    "MetricTypeEnum",
    "OperationResultEnum",
    "ResourceTypeEnum",
    "SeverityEnum",
    "TemplateTypeEnum",
]
