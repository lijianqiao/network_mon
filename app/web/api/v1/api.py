"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: api.py
@DateTime: 2025-06-17
@Docs: API路由注册
"""

from fastapi import APIRouter

from .endpoints import automation, configs, dashboard, devices, logs, monitors

api_router = APIRouter()

# 注册各模块的路由
api_router.include_router(devices.router, prefix="/devices", tags=["设备管理"])

api_router.include_router(configs.router, prefix="/configs", tags=["配置管理"])

api_router.include_router(monitors.router, prefix="/monitors", tags=["监控管理"])

api_router.include_router(logs.router, prefix="/logs", tags=["日志管理"])

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表板"])

api_router.include_router(
    automation.router, prefix="/network", tags=["网络自动化"]
)  # 假设network模块已存在并包含相关路由
