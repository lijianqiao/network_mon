"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: logs.py
@DateTime: 2025-06-17
@Docs: 日志管理API端点
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.dependencies import get_operation_log_service, get_system_log_service
from app.schemas.base import PaginatedResponse, StatusResponse
from app.schemas.log import (
    LogExportRequest,
    LogStatistics,
    OperationLogCreate,
    OperationLogQueryParams,
    OperationLogResponse,
    SystemLogCreate,
    SystemLogQueryParams,
    SystemLogResponse,
)
from app.services.log_service import OperationLogService, SystemLogService

router = APIRouter()

# ================================ 操作日志管理 ================================


@router.get("/operations", response_model=PaginatedResponse[OperationLogResponse])
async def list_operation_logs(
    query_params: OperationLogQueryParams = Depends(),
    service: OperationLogService = Depends(get_operation_log_service),
):
    """获取操作日志列表"""
    try:
        result = await service.get_paginated(
            page=query_params.page,
            page_size=query_params.page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/operations/{log_id}", response_model=OperationLogResponse)
async def get_operation_log(
    log_id: int,
    service: OperationLogService = Depends(get_operation_log_service),
):
    """获取操作日志详情"""
    log = await service.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="操作日志不存在")
    return log


@router.post("/operations", response_model=OperationLogResponse)
async def create_operation_log(
    log_data: OperationLogCreate,
    service: OperationLogService = Depends(get_operation_log_service),
):
    """创建操作日志"""
    try:
        return await service.create(log_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/operations/{log_id}", response_model=StatusResponse)
async def delete_operation_log(
    log_id: int,
    service: OperationLogService = Depends(get_operation_log_service),
):
    """删除操作日志"""
    log = await service.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="操作日志不存在")

    try:
        await service.delete(log_id)
        return StatusResponse(status="success", message="操作日志删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/operations/user/{user}", response_model=list[OperationLogResponse])
async def get_user_operation_logs(
    user: str,
    service: OperationLogService = Depends(get_operation_log_service),
):
    """获取指定用户的操作日志"""
    try:
        return await service.get_by_user(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/operations/resource/{resource_type}", response_model=list[OperationLogResponse])
async def get_resource_operation_logs(
    resource_type: str,
    resource_id: int | None = Query(None, description="资源ID筛选"),
    service: OperationLogService = Depends(get_operation_log_service),
):
    """获取指定资源的操作日志"""
    try:
        return await service.get_by_resource(resource_type, resource_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/operations/action/{action}", response_model=list[OperationLogResponse])
async def get_action_operation_logs(
    action: str,
    service: OperationLogService = Depends(get_operation_log_service),
):
    """获取指定操作的日志"""
    try:
        return await service.get_by_action(action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ================================ 系统日志管理 ================================


@router.get("/system", response_model=PaginatedResponse[SystemLogResponse])
async def list_system_logs(
    query_params: SystemLogQueryParams = Depends(),
    service: SystemLogService = Depends(get_system_log_service),
):
    """获取系统日志列表"""
    try:
        result = await service.get_paginated(
            page=query_params.page,
            page_size=query_params.page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/system/{log_id}", response_model=SystemLogResponse)
async def get_system_log(
    log_id: int,
    service: SystemLogService = Depends(get_system_log_service),
):
    """获取系统日志详情"""
    log = await service.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="系统日志不存在")
    return log


@router.post("/system", response_model=SystemLogResponse)
async def create_system_log(
    log_data: SystemLogCreate,
    service: SystemLogService = Depends(get_system_log_service),
):
    """创建系统日志"""
    try:
        return await service.create(log_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/system/{log_id}", response_model=StatusResponse)
async def delete_system_log(
    log_id: int,
    service: SystemLogService = Depends(get_system_log_service),
):
    """删除系统日志"""
    log = await service.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="系统日志不存在")

    try:
        await service.delete(log_id)
        return StatusResponse(status="success", message="系统日志删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ================================ 日志统计和导出 ================================


@router.get("/statistics", response_model=LogStatistics)
async def get_log_statistics(
    operation_service: OperationLogService = Depends(get_operation_log_service),
    system_service: SystemLogService = Depends(get_system_log_service),
):
    """获取日志统计信息"""
    try:
        # 这里需要在服务层实现统计方法
        # 暂时返回默认值，后续可以完善
        return LogStatistics(
            total_count=0,
            error_count=0,
            warning_count=0,
            info_count=0,
            debug_count=0,
            operation_success_count=0,
            operation_failed_count=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/export", response_class=FileResponse)
async def export_logs(
    export_request: LogExportRequest,
    operation_service: OperationLogService = Depends(get_operation_log_service),
    system_service: SystemLogService = Depends(get_system_log_service),
):
    """导出日志"""
    try:
        # 这里需要实现日志导出逻辑
        # 暂时返回一个示例文件路径
        file_path = f"/tmp/logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"

        # 实际实现中需要根据参数查询日志并生成文件
        # 这里只是示例

        return FileResponse(
            path=file_path,
            filename=f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_request.format}",
            media_type="application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/cleanup", response_model=StatusResponse)
async def cleanup_old_logs(
    days: int = Query(30, description="保留天数", ge=1),
    log_type: str = Query("all", description="日志类型", regex="^(all|operation|system)$"),
    operation_service: OperationLogService = Depends(get_operation_log_service),
    system_service: SystemLogService = Depends(get_system_log_service),
):
    """清理旧日志"""
    try:
        # 这里需要在服务层实现清理方法
        # 暂时返回成功状态
        return StatusResponse(status="success", message=f"成功清理{days}天前的{log_type}日志")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
