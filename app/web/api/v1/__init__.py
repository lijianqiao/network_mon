"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025-06-17
@Docs: API v1 路由注册
"""

from fastapi import APIRouter

from .endpoints import automation, configs, dashboard, devices, logs, monitors

api_router = APIRouter()

# 注册所有API路由
api_router.include_router(devices.router)
api_router.include_router(configs.router)
api_router.include_router(monitors.router)
api_router.include_router(logs.router)
api_router.include_router(dashboard.router)
api_router.include_router(automation.router)  # 网络自动化API
