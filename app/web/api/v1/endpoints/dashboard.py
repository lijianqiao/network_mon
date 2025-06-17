"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dashboard.py
@DateTime: 2025-06-17
@Docs: 仪表板API端点
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import (
    get_alert_service,
    get_device_service,
    get_monitor_metric_service,
    get_operation_log_service,
    get_system_log_service,
)
from app.services.device_service import DeviceService
from app.services.log_service import OperationLogService, SystemLogService
from app.services.monitor_service import AlertService, MonitorMetricService

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    device_service: DeviceService = Depends(get_device_service),
    alert_service: AlertService = Depends(get_alert_service),
    metric_service: MonitorMetricService = Depends(get_monitor_metric_service),
    operation_log_service: OperationLogService = Depends(get_operation_log_service),
    system_log_service: SystemLogService = Depends(get_system_log_service),
):
    """获取仪表板概览数据"""
    try:
        # 设备统计
        total_devices = await device_service.count()
        online_devices = await device_service.count()  # 需要实现在线设备统计

        # 告警统计
        total_alerts = await alert_service.count()
        active_alerts = await alert_service.count()  # 需要按状态筛选

        # 日志统计
        total_operation_logs = await operation_log_service.count()
        total_system_logs = await system_log_service.count()

        # 最近24小时的错误日志
        recent_errors = await system_log_service.get_recent_errors(hours=24)

        return {
            "devices": {
                "total": total_devices,
                "online": online_devices,
                "offline": total_devices - online_devices,
                "online_rate": round((online_devices / total_devices * 100) if total_devices > 0 else 0, 2),
            },
            "alerts": {"total": total_alerts, "active": active_alerts, "resolved": total_alerts - active_alerts},
            "logs": {
                "operation_total": total_operation_logs,
                "system_total": total_system_logs,
                "recent_errors": len(recent_errors),
            },
            "system_health": {
                "status": "healthy" if len(recent_errors) < 10 else "warning",
                "last_updated": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics/trend")
async def get_metrics_trend(
    device_id: int | None = Query(None, description="设备ID筛选"),
    metric_type: str | None = Query(None, description="指标类型筛选"),
    hours: int = Query(24, description="时间范围(小时)", ge=1, le=168),
    metric_service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """获取监控指标趋势数据"""
    try:
        # 这里需要在服务层实现趋势数据查询
        # 暂时返回示例数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # 模拟趋势数据
        trend_data = {
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "metrics": [
                {
                    "timestamp": (start_time + timedelta(hours=i)).isoformat(),
                    "cpu_usage": 50.5 + (i * 2.1),
                    "memory_usage": 60.2 + (i * 1.8),
                    "disk_usage": 40.1 + (i * 0.5),
                    "network_io": 1024.5 + (i * 10.2),
                }
                for i in range(min(hours, 24))
            ],
        }

        return trend_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/alerts/recent")
async def get_recent_alerts(
    hours: int = Query(24, description="时间范围(小时)", ge=1, le=168),
    severity: str | None = Query(None, description="严重级别筛选"),
    limit: int = Query(10, description="返回数量限制", ge=1, le=100),
    alert_service: AlertService = Depends(get_alert_service),
):
    """获取最近告警数据"""
    try:
        # 这里需要在服务层实现最近告警查询
        # 暂时返回示例数据
        return {"alerts": [], "summary": {"total": 0, "critical": 0, "warning": 0, "info": 0}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/devices/status")
async def get_devices_status(
    device_service: DeviceService = Depends(get_device_service),
):
    """获取设备状态分布"""
    try:
        # 这里需要在服务层实现设备状态统计
        # 暂时返回示例数据
        return {
            "status_distribution": {"online": 0, "offline": 0, "maintenance": 0, "error": 0},
            "type_distribution": {"router": 0, "switch": 0, "server": 0, "firewall": 0},
            "location_distribution": {},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/logs/activity")
async def get_log_activity(
    hours: int = Query(24, description="时间范围(小时)", ge=1, le=168),
    operation_log_service: OperationLogService = Depends(get_operation_log_service),
    system_log_service: SystemLogService = Depends(get_system_log_service),
):
    """获取日志活动统计"""
    try:
        # 获取操作日志统计
        operation_stats = await operation_log_service.get_operation_statistics()

        # 获取系统日志统计
        system_stats = await system_log_service.get_system_statistics()

        return {
            "operation_logs": operation_stats,
            "system_logs": system_stats,
            "activity_timeline": [],  # 需要实现时间线数据
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/performance")
async def get_performance_metrics(
    metric_service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """获取系统性能指标"""
    try:
        # 这里需要实现性能指标统计
        # 暂时返回示例数据
        return {
            "system_performance": {
                "avg_response_time": 120.5,
                "throughput": 1250.8,
                "error_rate": 0.02,
                "availability": 99.95,
            },
            "resource_utilization": {"cpu_avg": 45.2, "memory_avg": 67.8, "disk_avg": 35.1, "network_avg": 23.4},
            "top_devices": [],  # 资源使用率最高的设备
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def get_system_health(
    system_log_service: SystemLogService = Depends(get_system_log_service),
    alert_service: AlertService = Depends(get_alert_service),
):
    """获取系统健康状态"""
    try:
        # 获取最近错误日志
        recent_errors = await system_log_service.get_recent_errors(hours=1)

        # 获取活跃告警数量
        active_alerts_count = await alert_service.count()  # 需要按状态筛选

        # 计算健康分数
        health_score = 100
        if len(recent_errors) > 10:
            health_score -= 20
        if active_alerts_count > 5:
            health_score -= 15

        status = "healthy"
        if health_score < 70:
            status = "critical"
        elif health_score < 85:
            status = "warning"

        return {
            "status": status,
            "score": health_score,
            "issues": {"recent_errors": len(recent_errors), "active_alerts": active_alerts_count},
            "recommendations": [
                "检查最近的错误日志" if len(recent_errors) > 5 else None,
                "处理活跃告警" if active_alerts_count > 0 else None,
            ],
            "last_check": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
