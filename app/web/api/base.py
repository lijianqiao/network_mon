"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025-06-17
@Docs: API路由基类和通用响应模型
"""

from typing import Any, Generic, TypeVar

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """API统一响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: T | None = None
    code: int = 200


class APIErrorResponse(BaseModel):
    """API错误响应格式"""
    success: bool = False
    message: str
    code: int
    error_type: str | None = None


def success_response(data: Any = None, message: str = "操作成功") -> APIResponse[Any]:
    """创建成功响应"""
    return APIResponse(success=True, message=message, data=data, code=200)


def error_response(
    message: str,
    code: int = 400,
    error_type: str | None = None
) -> APIErrorResponse:
    """创建错误响应"""
    return APIErrorResponse(
        success=False,
        message=message,
        code=code,
        error_type=error_type
    )


def handle_service_error(e: Exception) -> HTTPException:
    """处理服务层异常"""
    if isinstance(e, ValueError):
        # 业务逻辑错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    elif isinstance(e, PermissionError):
        # 权限错误
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    elif isinstance(e, FileNotFoundError):
        # 资源不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    else:
        # 其他未知错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="内部服务器错误"
        )


class BaseRouter:
    """API路由基类"""
    
    def __init__(self, prefix: str, tags: list[str] | None = None):
        self.router = APIRouter(prefix=prefix, tags=tags or [])  # type: ignore[arg-type]
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由 - 子类需要重写此方法"""
        pass
    
    def get_router(self) -> APIRouter:
        """获取路由器"""
        return self.router
