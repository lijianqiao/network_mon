"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli.py
@DateTime: 2025-06-17
@Docs: CLI相关API端点
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CLIManagerDep
from app.network.schemas import CreateSessionRequest, ExecuteCommandRequest, SendConfigurationRequest

# 创建路由器
router = APIRouter(prefix="/cli", tags=["CLI管理"])


@router.post("/sessions", summary="创建CLI会话")
async def create_session(request: CreateSessionRequest, cli_manager: CLIManagerDep) -> dict[str, Any]:
    """创建CLI会话

    Args:
        request: 创建会话请求

    Returns:
        dict: 创建结果

    Raises:
        HTTPException: 当创建失败时
    """
    try:
        result = await cli_manager.create_session(request.device_id, request.user_id)

        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "创建会话失败"))

        return {"message": "CLI会话创建成功", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建CLI会话失败: {str(e)}"
        ) from e


@router.delete("/sessions/{session_id}", summary="关闭CLI会话")
async def close_session(session_id: str, cli_manager: CLIManagerDep) -> dict[str, Any]:
    """关闭CLI会话

    Args:
        session_id: 会话ID

    Returns:
        dict: 关闭结果

    Raises:
        HTTPException: 当关闭失败时
    """
    try:
        result = await cli_manager.close_session(session_id)

        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关闭会话失败")

        return {"message": "CLI会话关闭成功", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"关闭CLI会话失败: {str(e)}"
        ) from e


@router.post("/sessions/execute", summary="执行CLI命令")
async def execute_command(request: ExecuteCommandRequest, cli_manager: CLIManagerDep) -> dict[str, Any]:
    """执行CLI命令

    Args:
        request: 执行命令请求

    Returns:
        dict: 执行结果

    Raises:
        HTTPException: 当执行失败时
    """
    try:
        result = await cli_manager.execute_command(request.session_id, request.command)

        return {"message": "命令执行完成", "data": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"执行CLI命令失败: {str(e)}"
        ) from e


@router.post("/sessions/configure", summary="发送配置")
async def send_configuration(request: SendConfigurationRequest, cli_manager: CLIManagerDep) -> dict[str, Any]:
    """发送配置到设备

    Args:
        request: 发送配置请求

    Returns:
        dict: 配置结果

    Raises:
        HTTPException: 当配置失败时
    """
    try:
        result = await cli_manager.send_configuration(request.session_id, request.config_lines)

        return {"message": "配置发送完成", "data": result}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"发送配置失败: {str(e)}") from e


@router.get("/sessions", summary="列出CLI会话")
async def list_sessions(
    cli_manager: CLIManagerDep, user_id: str | None = None, device_id: int | None = None
) -> dict[str, Any]:
    """列出CLI会话

    Args:
        user_id: 用户ID（可选）
        device_id: 设备ID（可选）

    Returns:
        dict: 会话列表

    Raises:
        HTTPException: 当获取失败时
    """
    try:
        result = cli_manager.list_sessions(user_id, device_id)

        return {"message": "获取会话列表成功", "data": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取会话列表失败: {str(e)}"
        ) from e


@router.get("/sessions/{session_id}", summary="获取会话信息")
async def get_session_info(session_id: str, cli_manager: CLIManagerDep) -> dict[str, Any]:
    """获取会话信息

    Args:
        session_id: 会话ID

    Returns:
        dict: 会话信息

    Raises:
        HTTPException: 当获取失败时
    """
    try:
        result = cli_manager.get_session_info(session_id)

        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "会话不存在"))

        return {"message": "获取会话信息成功", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取会话信息失败: {str(e)}"
        ) from e


@router.get("/statistics", summary="获取CLI统计信息")
async def get_statistics(cli_manager: CLIManagerDep) -> dict[str, Any]:
    """获取CLI统计信息

    Returns:
        dict: 统计信息

    Raises:
        HTTPException: 当获取失败时
    """
    try:
        result = cli_manager.get_statistics()

        return {"message": "获取统计信息成功", "data": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计信息失败: {str(e)}"
        ) from e


@router.post("/sessions/{session_id}/validate", summary="验证会话")
async def validate_session(session_id: str, cli_manager: CLIManagerDep) -> dict[str, Any]:
    """验证会话是否有效

    Args:
        session_id: 会话ID

    Returns:
        dict: 验证结果

    Raises:
        HTTPException: 当验证失败时
    """
    try:
        is_valid = await cli_manager.validate_session(session_id)

        return {"message": "会话验证完成", "data": {"session_id": session_id, "is_valid": is_valid}}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"验证会话失败: {str(e)}") from e
