"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: log.py
@DateTime: 2025-06-17
@Docs: 日志相关校验模型
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.data_enum import ActionEnum, LogLevelEnum, OperationResultEnum, ResourceTypeEnum

from .base import BaseQueryParams, BaseTimeRange


class OperationLogBase(BaseModel):
    """操作日志基础模型"""

    user: str | None = Field(default=None, max_length=50, description="操作用户")
    action: ActionEnum = Field(description="操作动作")
    resource_type: ResourceTypeEnum = Field(description="资源类型")
    resource_id: str | None = Field(default=None, max_length=50, description="资源ID")
    resource_name: str | None = Field(default=None, max_length=200, description="资源名称")
    details: dict[str, Any] | None = Field(default=None, description="操作详情")
    ip_address: str | None = Field(default=None, max_length=45, description="操作IP地址")
    result: OperationResultEnum = Field(default=OperationResultEnum.SUCCESS, description="操作结果")
    error_message: str | None = Field(default=None, description="错误信息")
    execution_time: float | None = Field(default=None, ge=0, description="执行耗时(秒)")


class OperationLogCreate(OperationLogBase):
    """创建操作日志模型"""

    pass


class OperationLogResponse(OperationLogBase):
    """操作日志响应模型"""

    id: int = Field(description="日志ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class OperationLogQueryParams(BaseQueryParams, BaseTimeRange):
    """操作日志查询参数"""

    user: str | None = Field(default=None, description="操作用户筛选")
    action: ActionEnum | None = Field(default=None, description="操作动作筛选")
    resource_type: ResourceTypeEnum | None = Field(default=None, description="资源类型筛选")
    result: OperationResultEnum | None = Field(default=None, description="操作结果筛选")
    ip_address: str | None = Field(default=None, description="IP地址筛选")


class SystemLogBase(BaseModel):
    """系统日志基础模型"""

    level: LogLevelEnum = Field(description="日志级别")
    logger_name: str = Field(min_length=1, max_length=100, description="日志记录器名称")
    module: str | None = Field(default=None, max_length=100, description="模块名称")
    message: str = Field(min_length=1, description="日志消息内容")
    exception_info: str | None = Field(default=None, description="异常信息")
    extra_data: dict[str, Any] | None = Field(default=None, description="额外数据")


class SystemLogCreate(SystemLogBase):
    """创建系统日志模型"""

    pass


class SystemLogResponse(SystemLogBase):
    """系统日志响应模型"""

    id: int = Field(description="日志ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class SystemLogQueryParams(BaseQueryParams, BaseTimeRange):
    """系统日志查询参数"""

    level: LogLevelEnum | None = Field(default=None, description="日志级别筛选")
    logger_name: str | None = Field(default=None, description="记录器名称筛选")
    module: str | None = Field(default=None, description="模块名称筛选")


class LogStatistics(BaseModel):
    """日志统计信息"""

    total_count: int = Field(ge=0, description="总日志数")
    error_count: int = Field(ge=0, description="错误日志数")
    warning_count: int = Field(ge=0, description="警告日志数")
    info_count: int = Field(ge=0, description="信息日志数")
    debug_count: int = Field(ge=0, description="调试日志数")
    operation_success_count: int = Field(ge=0, description="操作成功数")
    operation_failed_count: int = Field(ge=0, description="操作失败数")


class LogExportRequest(BaseModel):
    """日志导出请求"""

    log_type: str = Field(description="日志类型", pattern="^(operation|system)$")
    start_time: datetime = Field(description="开始时间")
    end_time: datetime = Field(description="结束时间")
    level: LogLevelEnum | None = Field(default=None, description="日志级别筛选")
    format: str = Field(default="csv", description="导出格式", pattern="^(csv|json|xlsx)$")
