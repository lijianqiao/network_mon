"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dependencies.py
@DateTime: 2025-06-17
@Docs: FastAPI依赖注入容器
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from tortoise.transactions import in_transaction

from app.core.config import Settings, get_settings
from app.network.cli.cli_manager import CLIManager, cli_manager
from app.network.config.config_manager import ConfigManager
from app.network.monitoring.snmp_service import SNMPService
from app.network.services.network_service import NetworkAutomationService
from app.services import (
    AlertService,
    AreaService,
    BrandService,
    ConfigTemplateService,
    DeviceGroupService,
    DeviceModelService,
    DeviceService,
    MonitorMetricService,
    OperationLogService,
    SystemLogService,
)

# ========================= 数据库事务依赖 =========================


async def get_db_transaction() -> AsyncGenerator:
    """获取数据库事务上下文"""
    async with in_transaction() as conn:
        yield conn


# ========================= 网络模块服务依赖 =========================


def get_network_automation_service() -> NetworkAutomationService:
    """获取网络自动化服务实例"""
    return NetworkAutomationService()


def get_cli_manager() -> CLIManager:
    """获取CLI管理器实例"""
    return cli_manager


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    return ConfigManager()


def get_snmp_service() -> SNMPService:
    """获取SNMP服务实例"""
    return SNMPService()


# ========================= 传统服务层依赖 =========================


def get_brand_service() -> BrandService:
    """获取品牌服务"""
    return BrandService()


def get_device_model_service() -> DeviceModelService:
    """获取设备型号服务"""
    return DeviceModelService()


def get_area_service() -> AreaService:
    """获取区域服务"""
    return AreaService()


def get_device_group_service() -> DeviceGroupService:
    """获取设备分组服务"""
    return DeviceGroupService()


def get_device_service() -> DeviceService:
    """获取设备服务"""
    return DeviceService()


def get_config_template_service() -> ConfigTemplateService:
    """获取配置模板服务"""
    return ConfigTemplateService()


def get_monitor_metric_service() -> MonitorMetricService:
    """获取监控指标服务"""
    return MonitorMetricService()


def get_alert_service() -> AlertService:
    """获取告警服务"""
    return AlertService()


def get_operation_log_service() -> OperationLogService:
    """获取操作日志服务"""
    return OperationLogService()


def get_system_log_service() -> SystemLogService:
    """获取系统日志服务"""
    return SystemLogService()


# ========================= 常用依赖注解 =========================

# 配置依赖
SettingsDep = Annotated[Settings, Depends(get_settings)]

# 网络模块依赖
CLIManagerDep = Annotated[CLIManager, Depends(get_cli_manager)]
ConfigManagerDep = Annotated[ConfigManager, Depends(get_config_manager)]
SNMPServiceDep = Annotated[SNMPService, Depends(get_snmp_service)]
# 网络自动化服务依赖
NetworkAutomationServiceDep = Annotated[NetworkAutomationService, Depends(get_network_automation_service)]

# 服务依赖
BrandServiceDep = Annotated[BrandService, Depends(get_brand_service)]
DeviceModelServiceDep = Annotated[DeviceModelService, Depends(get_device_model_service)]
AreaServiceDep = Annotated[AreaService, Depends(get_area_service)]
DeviceGroupServiceDep = Annotated[DeviceGroupService, Depends(get_device_group_service)]
DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]
ConfigTemplateServiceDep = Annotated[ConfigTemplateService, Depends(get_config_template_service)]
MonitorMetricServiceDep = Annotated[MonitorMetricService, Depends(get_monitor_metric_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
OperationLogServiceDep = Annotated[OperationLogService, Depends(get_operation_log_service)]
SystemLogServiceDep = Annotated[SystemLogService, Depends(get_system_log_service)]

# 数据库事务依赖
TransactionDep = Annotated[None, Depends(get_db_transaction)]
