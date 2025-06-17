"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: 校验模型包初始化文件，导出所有校验模型
"""

# 基础响应模型
from .base import (
    BaseQueryParams,
    BaseResponse,
    BaseTimeRange,
    ErrorResponse,
    IDResponse,
    PaginatedResponse,
    PaginationInfo,
    StatusResponse,
    SuccessResponse,
)

# 配置模板模型
from .config import (
    ConfigTemplateCreate,
    ConfigTemplateQueryParams,
    ConfigTemplateResponse,
    ConfigTemplateUpdate,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateVariableSchema,
)

# 设备相关模型
from .device import (
    AreaCreate,
    AreaQueryParams,
    AreaResponse,
    AreaUpdate,
    BrandCreate,
    BrandQueryParams,
    BrandResponse,
    BrandUpdate,
    DeviceCreate,
    DeviceGroupCreate,
    DeviceGroupQueryParams,
    DeviceGroupResponse,
    DeviceGroupUpdate,
    DeviceModelCreate,
    DeviceModelQueryParams,
    DeviceModelResponse,
    DeviceModelUpdate,
    DeviceQueryParams,
    DeviceResponse,
    DeviceStatusUpdate,
    DeviceUpdate,
)

# 日志相关模型
from .log import (
    LogExportRequest,
    LogStatistics,
    OperationLogCreate,
    OperationLogQueryParams,
    OperationLogResponse,
    SystemLogCreate,
    SystemLogQueryParams,
    SystemLogResponse,
)

# 监控相关模型
from .monitor import (
    AlertAcknowledge,
    AlertCreate,
    AlertQueryParams,
    AlertResolve,
    AlertResponse,
    AlertStatistics,
    AlertUpdate,
    MetricStatistics,
    MonitorMetricCreate,
    MonitorMetricQueryParams,
    MonitorMetricResponse,
    MonitorMetricUpdate,
)

# 网络自动化模型
from .network import (
    BatchNetworkTaskRequest,
    BatchNetworkTaskResponse,
    DeviceConnectivityRequest,
    DeviceConnectivityResponse,
    DeviceStatusSummary,
    DiscoveredDevice,
    NetworkDeviceCreate,
    NetworkDeviceResponse,
    NetworkDeviceUpdate,
    NetworkDiscoveryRequest,
    NetworkDiscoveryResponse,
    NetworkTaskRequest,
    NetworkTaskResponse,
    SupportedTaskInfo,
    SupportedTasksResponse,
)

__all__ = [
    # 基础模型
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginationInfo",
    "PaginatedResponse",
    "BaseQueryParams",
    "BaseTimeRange",
    "IDResponse",
    "StatusResponse",
    # 设备相关
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "BrandQueryParams",
    "DeviceModelCreate",
    "DeviceModelUpdate",
    "DeviceModelResponse",
    "DeviceModelQueryParams",
    "AreaCreate",
    "AreaUpdate",
    "AreaResponse",
    "AreaQueryParams",
    "DeviceGroupCreate",
    "DeviceGroupUpdate",
    "DeviceGroupResponse",
    "DeviceGroupQueryParams",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceQueryParams",
    "DeviceStatusUpdate",
    # 配置模板
    "ConfigTemplateCreate",
    "ConfigTemplateUpdate",
    "ConfigTemplateResponse",
    "ConfigTemplateQueryParams",
    "TemplateVariableSchema",
    "TemplateRenderRequest",
    "TemplateRenderResponse",
    # 监控相关
    "MonitorMetricCreate",
    "MonitorMetricUpdate",
    "MonitorMetricResponse",
    "MonitorMetricQueryParams",
    "MetricStatistics",
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    "AlertQueryParams",
    "AlertAcknowledge",
    "AlertResolve",
    "AlertStatistics",
    # 日志相关
    "OperationLogCreate",
    "OperationLogResponse",
    "OperationLogQueryParams",
    "SystemLogCreate",
    "SystemLogResponse",
    "SystemLogQueryParams",
    "LogStatistics",
    "LogExportRequest",
    # 网络自动化
    "NetworkDeviceCreate",
    "NetworkDeviceUpdate",
    "NetworkDeviceResponse",
    "NetworkTaskRequest",
    "NetworkTaskResponse",
    "BatchNetworkTaskRequest",
    "BatchNetworkTaskResponse",
    "DeviceConnectivityRequest",
    "DeviceConnectivityResponse",
    "NetworkDiscoveryRequest",
    "NetworkDiscoveryResponse",
    "DiscoveredDevice",
    "DeviceStatusSummary",
    "SupportedTaskInfo",
    "SupportedTasksResponse",
]
