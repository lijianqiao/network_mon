"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: 数据访问层模块，导出所有DAO类
"""

from .base_dao import BaseDAO
from .config_dao import ConfigTemplateDAO
from .device_dao import (
    AreaDAO,
    BrandDAO,
    DeviceDAO,
    DeviceGroupDAO,
    DeviceModelDAO,
)
from .log_dao import OperationLogDAO, SystemLogDAO
from .monitor_dao import AlertDAO, MonitorMetricDAO

__all__ = [
    # 基础DAO
    "BaseDAO",
    # 设备相关DAO
    "BrandDAO",
    "DeviceModelDAO",
    "AreaDAO",
    "DeviceGroupDAO",
    "DeviceDAO",
    # 配置模板DAO
    "ConfigTemplateDAO",
    # 监控相关DAO
    "MonitorMetricDAO",
    "AlertDAO",
    # 日志相关DAO
    "OperationLogDAO",
    "SystemLogDAO",
]


# 创建DAO实例的便捷函数
def get_brand_dao() -> BrandDAO:
    """获取品牌DAO实例"""
    return BrandDAO()


def get_device_model_dao() -> DeviceModelDAO:
    """获取设备型号DAO实例"""
    return DeviceModelDAO()


def get_area_dao() -> AreaDAO:
    """获取区域DAO实例"""
    return AreaDAO()


def get_device_group_dao() -> DeviceGroupDAO:
    """获取设备分组DAO实例"""
    return DeviceGroupDAO()


def get_device_dao() -> DeviceDAO:
    """获取设备DAO实例"""
    return DeviceDAO()


def get_config_template_dao() -> ConfigTemplateDAO:
    """获取配置模板DAO实例"""
    return ConfigTemplateDAO()


def get_monitor_metric_dao() -> MonitorMetricDAO:
    """获取监控指标DAO实例"""
    return MonitorMetricDAO()


def get_alert_dao() -> AlertDAO:
    """获取告警DAO实例"""
    return AlertDAO()


def get_operation_log_dao() -> OperationLogDAO:
    """获取操作日志DAO实例"""
    return OperationLogDAO()


def get_system_log_dao() -> SystemLogDAO:
    """获取系统日志DAO实例"""
    return SystemLogDAO()
