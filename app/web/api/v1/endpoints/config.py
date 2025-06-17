"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config.py
@DateTime: 2025-06-17
@Docs: 配置管理API端点
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import ConfigManagerDep
from app.network.schemas import ConfigBackupRequest, ConfigDeployRequest, ConfigDiffRequest, ConfigRollbackRequest

router = APIRouter(prefix="/config", tags=["配置管理"])


@router.post("/backup", summary="备份设备配置")
async def backup_config(request: ConfigBackupRequest, config_manager: ConfigManagerDep) -> dict[str, Any]:
    """备份设备配置

    Args:
        request: 备份请求参数

    Returns:
        dict: 备份结果
    """
    try:
        if len(request.device_ids) == 1:
            # 单设备备份
            result = await config_manager.backup_device_config(request.device_ids[0])
            return {"success": True, "data": result}
        else:
            # 多设备批量备份
            result = await config_manager.backup_multiple_devices(request.device_ids)
            return {"success": True, "data": result}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"配置备份失败: {str(e)}") from e


@router.post("/deploy", summary="部署配置")
async def deploy_config(request: ConfigDeployRequest, config_manager: ConfigManagerDep) -> dict[str, Any]:
    """部署配置到设备

    Args:
        request: 部署请求参数

    Returns:
        dict: 部署结果
    """
    try:
        result = await config_manager.deploy_config(
            device_id=request.device_id, config_content=request.config_content, dry_run=request.dry_run
        )
        return {"success": True, "data": result}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"配置部署失败: {str(e)}") from e


@router.post("/diff", summary="配置差异比较")
async def compare_config(request: ConfigDiffRequest, config_manager: ConfigManagerDep) -> dict[str, Any]:
    """比较设备当前配置与目标配置的差异

    Args:
        request: 差异比较请求参数

    Returns:
        dict: 差异比较结果
    """
    try:
        result = await config_manager.compare_config(device_id=request.device_id, target_config=request.target_config)
        return {"success": True, "data": result}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"配置差异比较失败: {str(e)}"
        ) from e


@router.post("/rollback", summary="回滚配置")
async def rollback_config(request: ConfigRollbackRequest, config_manager: ConfigManagerDep) -> dict[str, Any]:
    """回滚设备配置到指定备份

    Args:
        request: 回滚请求参数

    Returns:
        dict: 回滚结果
    """
    try:
        result = await config_manager.rollback_config(device_id=request.device_id, backup_path=request.backup_path)
        return {"success": True, "data": result}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"配置回滚失败: {str(e)}") from e


@router.get("/operations", summary="查询操作记录")
async def list_operations(config_manager: ConfigManagerDep, device_id: int | None = None) -> dict[str, Any]:
    """查询配置操作记录

    Args:
        device_id: 可选，过滤指定设备的操作记录

    Returns:
        dict: 操作记录列表
    """
    try:
        operations = config_manager.list_operations(device_id=device_id)
        return {"success": True, "data": {"operations": operations, "total": len(operations)}}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"查询操作记录失败: {str(e)}"
        ) from e


@router.get("/operations/{operation_id}", summary="查询操作状态")
async def get_operation_status(operation_id: str, config_manager: ConfigManagerDep) -> dict[str, Any]:
    """查询指定操作的状态

    Args:
        operation_id: 操作ID

    Returns:
        dict: 操作状态信息
    """
    try:
        operation = config_manager.get_operation_status(operation_id)
        if not operation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"操作 {operation_id} 不存在")

        return {"success": True, "data": operation}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"查询操作状态失败: {str(e)}"
        ) from e


@router.get("/backups", summary="查询备份文件")
async def list_backups(config_manager: ConfigManagerDep, device_id: int | None = None) -> dict[str, Any]:
    """查询备份文件列表

    Args:
        device_id: 可选，过滤指定设备的备份文件

    Returns:
        dict: 备份文件列表
    """
    try:
        backups = config_manager.list_backups(device_id=device_id)
        return {"success": True, "data": {"backups": backups, "total": len(backups)}}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"查询备份文件失败: {str(e)}"
        ) from e


@router.get("/backups/{backup_filename}/content", summary="获取备份文件内容")
async def get_backup_content(backup_filename: str, config_manager: ConfigManagerDep) -> dict[str, Any]:
    """获取备份文件内容

    Args:
        backup_filename: 备份文件名

    Returns:
        dict: 备份文件内容
    """
    try:
        backup_path = config_manager.backup_dir / backup_filename

        if not backup_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"备份文件 {backup_filename} 不存在")

        if not backup_path.suffix.lower() == ".cfg":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只支持读取.cfg格式的备份文件")

        with open(backup_path, encoding="utf-8") as f:
            content = f.read()

        file_stat = backup_path.stat()

        return {
            "success": True,
            "data": {
                "filename": backup_filename,
                "content": content,
                "size": file_stat.st_size,
                "created_time": file_stat.st_ctime,
                "modified_time": file_stat.st_mtime,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"读取备份文件失败: {str(e)}"
        ) from e
