"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config.py
@DateTime: 2025-06-17
@Docs: 配置模板相关校验模型
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.data_enum import DeviceTypeEnum, TemplateTypeEnum

from .base import BaseQueryParams
from .device import BrandResponse


class ConfigTemplateBase(BaseModel):
    """配置模板基础模型"""

    name: str = Field(min_length=1, max_length=100, description="模板名称")
    brand_id: int | None = Field(default=None, gt=0, description="适用品牌ID")
    device_type: DeviceTypeEnum | None = Field(default=None, description="适用设备类型")
    template_type: TemplateTypeEnum = Field(description="模板类型")
    content: str = Field(min_length=1, description="模板内容")
    variables: dict[str, Any] | None = Field(default=None, description="模板变量定义")
    description: str | None = Field(default=None, description="模板描述")
    is_active: bool = Field(default=True, description="是否启用")


class ConfigTemplateCreate(ConfigTemplateBase):
    """创建配置模板模型"""

    pass


class ConfigTemplateUpdate(BaseModel):
    """更新配置模板模型"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="模板名称")
    brand_id: int | None = Field(default=None, gt=0, description="适用品牌ID")
    device_type: DeviceTypeEnum | None = Field(default=None, description="适用设备类型")
    template_type: TemplateTypeEnum | None = Field(default=None, description="模板类型")
    content: str | None = Field(default=None, min_length=1, description="模板内容")
    variables: dict[str, Any] | None = Field(default=None, description="模板变量定义")
    description: str | None = Field(default=None, description="模板描述")
    is_active: bool | None = Field(default=None, description="是否启用")


class ConfigTemplateResponse(ConfigTemplateBase):
    """配置模板响应模型"""

    id: int = Field(description="模板ID")
    brand: BrandResponse | None = Field(description="适用品牌")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class ConfigTemplateQueryParams(BaseQueryParams):
    """配置模板查询参数"""

    brand_id: int | None = Field(default=None, gt=0, description="品牌ID筛选")
    device_type: DeviceTypeEnum | None = Field(default=None, description="设备类型筛选")
    template_type: TemplateTypeEnum | None = Field(default=None, description="模板类型筛选")


class TemplateVariableSchema(BaseModel):
    """模板变量定义"""

    name: str = Field(description="变量名")
    type: str = Field(description="变量类型")
    description: str | None = Field(default=None, description="变量描述")
    default_value: str | None = Field(default=None, description="默认值")
    required: bool = Field(default=True, description="是否必填")


class TemplateRenderRequest(BaseModel):
    """模板渲染请求"""

    template_id: int = Field(gt=0, description="模板ID")
    variables: dict[str, str] = Field(description="变量值映射")


class TemplateRenderResponse(BaseModel):
    """模板渲染响应"""

    rendered_content: str = Field(description="渲染后的内容")
    variables_used: list[str] = Field(description="使用的变量列表")
