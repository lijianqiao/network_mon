"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: 模型包初始化文件，导出所有模型类
"""

# 导入所有模型类
from .data_models import (
    Alert,
    Area,
    BaseModel,
    Brand,
    ConfigFile,
    ConfigTemplate,
    Device,
    DeviceConfig,
    DeviceGroup,
    DeviceInterface,
    DeviceType,
    MonitorMetric,
    OperationLog,
    Role,
    SystemLog,
    Task,
    TaskResult,
    User,
    UserRole,
)

__all__ = [
    # 基础模型
    "BaseModel",
    # 设备相关模型
    "Brand",
    "DeviceType",
    "Area",
    "DeviceGroup",
    "Device",
    # 任务相关模型
    "Task",
    "TaskResult",
    # 配置相关模型
    "DeviceConfig",
    "ConfigTemplate",
    # 监控相关模型
    "MonitorMetric",
    "Alert",
    # 用户管理模型
    "User",
    "Role",
    "UserRole",
    # 日志相关模型
    "OperationLog",
    "SystemLog",
    # 接口和文件模型
    "DeviceInterface",
    "ConfigFile",
]
