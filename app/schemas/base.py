"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025-06-17
@Docs: 基础校验模型，包含通用响应和分页结构
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """统一响应模型"""

    success: bool = Field(description="操作是否成功")
    message: str = Field(default="", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")
    code: int = Field(default=200, description="状态码")


class SuccessResponse(BaseResponse[T]):
    """成功响应模型"""

    success: bool = Field(default=True, description="操作成功")
    code: int = Field(default=200, description="状态码")


class ErrorResponse(BaseResponse[None]):
    """错误响应模型"""

    success: bool = Field(default=False, description="操作失败")
    data: None = Field(default=None, description="错误时无数据")
    error_code: str | None = Field(default=None, description="错误代码")
    details: dict[str, Any] | None = Field(default=None, description="错误详情")


class PaginationInfo(BaseModel):
    """分页信息模型"""

    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, le=100, description="每页数量")
    total: int = Field(ge=0, description="总记录数")
    total_pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""

    items: list[T] = Field(description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


class BaseQueryParams(BaseModel):
    """基础查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    search: str | None = Field(default=None, min_length=1, description="搜索关键词")
    is_active: bool | None = Field(default=None, description="是否启用")


class BaseTimeRange(BaseModel):
    """时间范围查询"""

    start_time: str | None = Field(default=None, description="开始时间")
    end_time: str | None = Field(default=None, description="结束时间")


class IDResponse(BaseModel):
    """ID响应模型"""

    id: int = Field(description="资源ID")


class StatusResponse(BaseModel):
    """状态响应模型"""

    status: str = Field(description="操作状态")
    message: str = Field(description="状态消息")
