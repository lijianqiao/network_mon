"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: API v1 路由注册
"""

from fastapi import APIRouter

from .endpoints import automation, cli, config, configs, dashboard, devices, logs, monitoring, monitors

api_router = APIRouter()

# 注册所有API路由
api_router.include_router(devices.router)
api_router.include_router(configs.router)
api_router.include_router(monitors.router)
api_router.include_router(logs.router)
api_router.include_router(dashboard.router)
api_router.include_router(automation.router)  # 网络自动化API
api_router.include_router(config.router)  # 配置管理API
api_router.include_router(cli.router)  # CLI相关API
api_router.include_router(monitoring.router)  # SNMP监控API
