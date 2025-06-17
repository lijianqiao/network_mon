"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: monitoring.py
@DateTime: 2025-06-17
@Docs: SNMP监控API端点
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import SNMPServiceDep
from app.network.schemas import MonitoringStartRequest, ThresholdUpdateRequest

router = APIRouter(prefix="/monitoring", tags=["SNMP监控"])


@router.post("/start", summary="启动SNMP监控")
async def start_monitoring(request: MonitoringStartRequest, snmp_service: SNMPServiceDep) -> dict[str, Any]:
    """启动SNMP监控服务"""
    try:
        result = await snmp_service.start_monitoring(poll_interval=request.poll_interval)

        if result["success"]:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"启动监控失败: {str(e)}"
        ) from None


@router.post("/stop", summary="停止SNMP监控")
async def stop_monitoring(snmp_service: SNMPServiceDep) -> dict[str, Any]:
    """停止SNMP监控服务"""
    try:
        result = await snmp_service.stop_monitoring()

        if result["success"]:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"停止监控失败: {str(e)}"
        ) from None


@router.get("/status", summary="获取监控状态")
async def get_monitoring_status(snmp_service: SNMPServiceDep) -> dict[str, Any]:
    """获取SNMP监控服务状态"""
    try:
        status_info = snmp_service.get_monitoring_status()
        return {"success": True, "data": status_info}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取监控状态失败: {str(e)}"
        ) from None


@router.get("/devices", summary="获取所有设备监控数据")
async def get_all_device_metrics(snmp_service: SNMPServiceDep) -> dict[str, Any]:
    """获取所有设备的监控指标"""
    try:
        result = snmp_service.get_all_device_metrics()
        return {"success": True, "data": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备监控数据失败: {str(e)}"
        ) from None


@router.get("/devices/{device_id}", summary="获取指定设备监控数据")
async def get_device_metrics(device_id: int, snmp_service: SNMPServiceDep) -> dict[str, Any]:
    """获取指定设备的监控指标"""
    try:
        result = snmp_service.get_device_metrics(device_id)

        if result["success"]:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备监控数据失败: {str(e)}"
        ) from None


@router.get("/alerts", summary="获取告警信息")
async def get_alerts(snmp_service: SNMPServiceDep, hours: int = 24, device_id: int | None = None) -> dict[str, Any]:
    """获取告警信息

    Args:
        hours: 时间范围（小时）
        device_id: 可选，过滤指定设备的告警
    """
    try:
        result = snmp_service.get_alerts(hours=hours, device_id=device_id)
        return {"success": True, "data": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取告警信息失败: {str(e)}"
        ) from None


@router.put("/thresholds", summary="更新告警阈值")
async def update_thresholds(request: ThresholdUpdateRequest, snmp_service: SNMPServiceDep) -> dict[str, Any]:
    """更新告警阈值配置"""
    try:
        # 构建更新的阈值字典
        thresholds = {}
        if request.cpu_usage is not None:
            thresholds["cpu_usage"] = request.cpu_usage
        if request.memory_usage is not None:
            thresholds["memory_usage"] = request.memory_usage
        if request.interface_down_count is not None:
            thresholds["interface_down_count"] = request.interface_down_count

        if not thresholds:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少需要提供一个阈值参数")

        result = snmp_service.update_thresholds(thresholds)

        if result["success"]:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新告警阈值失败: {str(e)}"
        ) from None


@router.delete("/cleanup", summary="清理旧数据")
async def cleanup_old_data(snmp_service: SNMPServiceDep, hours: int = 24) -> dict[str, Any]:
    """清理旧的监控数据和告警

    Args:
        hours: 保留时间（小时）
    """
    try:
        if hours < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="保留时间必须大于等于1小时")

        result = snmp_service.cleanup_old_data(hours=hours)

        if result["success"]:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"清理旧数据失败: {str(e)}"
        ) from None
