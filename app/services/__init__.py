"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: 服务层模块，导出所有业务服务类
"""

from .base_service import BaseService
from .config_service import ConfigTemplateService
from .device_service import AreaService, BrandService, DeviceGroupService, DeviceModelService, DeviceService
from .log_service import OperationLogService, SystemLogService
from .monitor_service import AlertService, MonitorMetricService

__all__ = [
    # 基础服务
    "BaseService",
    # 设备相关服务
    "BrandService",
    "DeviceModelService",
    "AreaService",
    "DeviceGroupService",
    "DeviceService",
    # 配置模板服务
    "ConfigTemplateService",
    # 监控相关服务
    "MonitorMetricService",
    "AlertService",
    # 日志相关服务
    "OperationLogService",
    "SystemLogService",
]


# 创建服务实例的便捷函数
def get_brand_service() -> BrandService:
    """获取品牌服务实例"""
    return BrandService()


def get_device_model_service() -> DeviceModelService:
    """获取设备型号服务实例"""
    return DeviceModelService()


def get_area_service() -> AreaService:
    """获取区域服务实例"""
    return AreaService()


def get_device_group_service() -> DeviceGroupService:
    """获取设备分组服务实例"""
    return DeviceGroupService()


def get_device_service() -> DeviceService:
    """获取设备服务实例"""
    return DeviceService()


def get_config_template_service() -> ConfigTemplateService:
    """获取配置模板服务实例"""
    return ConfigTemplateService()


def get_monitor_metric_service() -> MonitorMetricService:
    """获取监控指标服务实例"""
    return MonitorMetricService()


def get_alert_service() -> AlertService:
    """获取告警服务实例"""
    return AlertService()


def get_operation_log_service() -> OperationLogService:
    """获取操作日志服务实例"""
    return OperationLogService()


def get_system_log_service() -> SystemLogService:
    """获取系统日志服务实例"""
    return SystemLogService()
