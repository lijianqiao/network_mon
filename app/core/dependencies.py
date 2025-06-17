"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dependencies.py
@DateTime: 2025-06-17
@Docs: FastAPI依赖注入容器
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from tortoise.transactions import in_transaction

from app.core.config import Settings, get_settings
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

# ========================= 配置依赖 =========================
# 直接使用 config.py 中的 get_settings 函数，避免重复定义


# ========================= 认证依赖 =========================

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> str:
    """获取当前用户（简化版本，暂时返回默认用户）

    在没有用户管理系统的情况下，我们使用以下策略：
    - 如果有token，从token解析用户信息
    - 如果没有token，返回默认用户 'system'
    - 后续可以扩展为完整的JWT认证
    """
    if credentials and credentials.credentials:
        # TODO: 这里后续可以添加JWT token解析逻辑
        # 暂时从token中提取用户名（简化处理）
        try:
            # 假设token格式为 "user:username" 或直接是username
            token = credentials.credentials
            if ":" in token:
                user = token.split(":", 1)[1]
            else:
                user = token
            return user
        except Exception:
            # token解析失败，返回默认用户
            return "system"

    # 没有提供认证信息，返回默认用户
    return "system"


async def get_admin_user(current_user: Annotated[str, Depends(get_current_user)]) -> str:
    """获取管理员用户（需要管理员权限的操作）

    暂时简化处理：
    - 'admin' 用户拥有管理员权限
    - 'system' 用户拥有管理员权限（系统内部调用）
    - 其他用户抛出权限不足异常
    """
    if current_user in ["admin", "system"]:
        return current_user

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")


# ========================= 数据库事务依赖 =========================


async def get_db_transaction() -> AsyncGenerator:
    """获取数据库事务上下文"""
    async with in_transaction() as conn:
        yield conn


# ========================= 服务层依赖 =========================


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

# 用户依赖
CurrentUser = Annotated[str, Depends(get_current_user)]
AdminUser = Annotated[str, Depends(get_admin_user)]

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
