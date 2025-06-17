"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: monitors.py
@DateTime: 2025-06-17
@Docs: 监控指标和告警管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_alert_service, get_monitor_metric_service
from app.schemas.base import PaginatedResponse, StatusResponse
from app.schemas.monitor import (
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
from app.services.monitor_service import AlertService, MonitorMetricService

router = APIRouter()

# ================================ 监控指标管理 ================================


@router.get("/metrics", response_model=PaginatedResponse[MonitorMetricResponse])
async def list_monitor_metrics(
    query_params: MonitorMetricQueryParams = Depends(),
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """获取监控指标列表"""
    try:
        result = await service.get_paginated(
            page=query_params.page,
            page_size=query_params.page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics/{metric_id}", response_model=MonitorMetricResponse)
async def get_monitor_metric(
    metric_id: int,
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """获取监控指标详情"""
    metric = await service.get_by_id(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="监控指标不存在")
    return metric


@router.post("/metrics", response_model=MonitorMetricResponse)
async def create_monitor_metric(
    metric_data: MonitorMetricCreate,
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """创建监控指标"""
    try:
        return await service.create(metric_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/metrics/{metric_id}", response_model=MonitorMetricResponse)
async def update_monitor_metric(
    metric_id: int,
    metric_data: MonitorMetricUpdate,
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """更新监控指标"""
    metric = await service.get_by_id(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="监控指标不存在")

    try:
        update_data = {k: v for k, v in metric_data.model_dump().items() if v is not None}
        return await service.update(metric_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/metrics/{metric_id}", response_model=StatusResponse)
async def delete_monitor_metric(
    metric_id: int,
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """删除监控指标"""
    metric = await service.get_by_id(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="监控指标不存在")
    try:
        await service.delete(metric_id)
        return StatusResponse(status="success", message="监控指标删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics/device/{device_id}", response_model=list[MonitorMetricResponse])
async def get_device_metrics(
    device_id: int,
    metric_type: str | None = Query(None, description="指标类型筛选"),
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """获取设备的监控指标"""
    try:
        return await service.get_by_device(device_id, metric_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics/statistics", response_model=list[MetricStatistics])
async def get_metric_statistics(
    service: MonitorMetricService = Depends(get_monitor_metric_service),
):
    """获取监控指标统计信息"""
    try:
        # 这里需要在服务层实现统计方法
        # 暂时返回空列表，后续可以完善
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ================================ 告警管理 ================================


@router.get("/alerts", response_model=PaginatedResponse[AlertResponse])
async def list_alerts(
    query_params: AlertQueryParams = Depends(),
    service: AlertService = Depends(get_alert_service),
):
    """获取告警列表"""
    try:
        result = await service.get_paginated(
            page=query_params.page,
            page_size=query_params.page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    service: AlertService = Depends(get_alert_service),
):
    """获取告警详情"""
    alert = await service.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    return alert


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    service: AlertService = Depends(get_alert_service),
):
    """创建告警"""
    try:
        return await service.create(alert_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    service: AlertService = Depends(get_alert_service),
):
    """更新告警"""
    alert = await service.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    try:
        update_data = {k: v for k, v in alert_data.model_dump().items() if v is not None}
        return await service.update(alert_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/alerts/{alert_id}", response_model=StatusResponse)
async def delete_alert(
    alert_id: int,
    service: AlertService = Depends(get_alert_service),
):
    """删除告警"""
    alert = await service.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    try:
        await service.delete(alert_id)
        return StatusResponse(status="success", message="告警删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    acknowledge_data: AlertAcknowledge,
    service: AlertService = Depends(get_alert_service),
):
    """确认告警"""
    alert = await service.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    try:
        return await service.acknowledge_alert(alert_id, acknowledge_data.acknowledged_by)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    resolve_data: AlertResolve,
    service: AlertService = Depends(get_alert_service),
):
    """解决告警"""
    alert = await service.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    try:
        # 需要在服务层实现resolve_alert方法
        update_data = {
            "status": "resolved",
            "resolved_at": "now()",
            "resolution_note": resolve_data.resolution_note,
        }
        return await service.update(alert_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/alerts/statistics", response_model=AlertStatistics)
async def get_alert_statistics(
    service: AlertService = Depends(get_alert_service),
):
    """获取告警统计信息"""
    try:
        # 这里需要在服务层实现统计方法
        # 暂时返回默认值，后续可以完善
        return AlertStatistics(
            total_count=0,
            active_count=0,
            acknowledged_count=0,
            resolved_count=0,
            critical_count=0,
            warning_count=0,
            info_count=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
