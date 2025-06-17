"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025-06-17
@Docs: 设备相关校验模型
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, IPvAnyAddress

from app.models.data_enum import ConnectionTypeEnum, DeviceStatusEnum, DeviceTypeEnum

from .base import BaseQueryParams

# ================================ 品牌相关 ================================


class BrandBase(BaseModel):
    """品牌基础模型"""

    name: str = Field(min_length=1, max_length=50, description="品牌名称")
    code: str = Field(min_length=1, max_length=20, description="品牌代码")
    description: str | None = Field(default=None, description="品牌描述")
    is_active: bool = Field(default=True, description="是否启用")


class BrandCreate(BrandBase):
    """创建品牌模型"""

    pass


class BrandUpdate(BaseModel):
    """更新品牌模型"""

    name: str | None = Field(default=None, min_length=1, max_length=50, description="品牌名称")
    code: str | None = Field(default=None, min_length=1, max_length=20, description="品牌代码")
    description: str | None = Field(default=None, description="品牌描述")
    is_active: bool | None = Field(default=None, description="是否启用")


class BrandResponse(BrandBase):
    """品牌响应模型"""

    id: int = Field(description="品牌ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class BrandQueryParams(BaseQueryParams):
    """品牌查询参数"""

    code: str | None = Field(default=None, description="品牌代码筛选")


# ================================ 设备型号相关 ================================


class DeviceModelBase(BaseModel):
    """设备型号基础模型"""

    name: str = Field(min_length=1, max_length=100, description="型号名称")
    brand_id: int = Field(gt=0, description="所属品牌ID")
    device_type: DeviceTypeEnum = Field(description="设备类型")
    description: str | None = Field(default=None, description="型号描述")
    is_active: bool = Field(default=True, description="是否启用")


class DeviceModelCreate(DeviceModelBase):
    """创建设备型号模型"""

    pass


class DeviceModelUpdate(BaseModel):
    """更新设备型号模型"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="型号名称")
    brand_id: int | None = Field(default=None, gt=0, description="所属品牌ID")
    device_type: DeviceTypeEnum | None = Field(default=None, description="设备类型")
    description: str | None = Field(default=None, description="型号描述")
    is_active: bool | None = Field(default=None, description="是否启用")


class DeviceModelResponse(DeviceModelBase):
    """设备型号响应模型"""

    id: int = Field(description="型号ID")
    brand: BrandResponse = Field(description="品牌信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class DeviceModelQueryParams(BaseQueryParams):
    """设备型号查询参数"""

    brand_id: int | None = Field(default=None, gt=0, description="品牌ID筛选")
    device_type: DeviceTypeEnum | None = Field(default=None, description="设备类型筛选")


# ================================ 区域相关 ================================


class AreaBase(BaseModel):
    """区域基础模型"""

    name: str = Field(min_length=1, max_length=100, description="区域名称")
    code: str = Field(min_length=1, max_length=20, description="区域代码")
    parent_id: int | None = Field(default=None, gt=0, description="父级区域ID")
    description: str | None = Field(default=None, description="区域描述")
    is_active: bool = Field(default=True, description="是否启用")


class AreaCreate(AreaBase):
    """创建区域模型"""

    pass


class AreaUpdate(BaseModel):
    """更新区域模型"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="区域名称")
    code: str | None = Field(default=None, min_length=1, max_length=20, description="区域代码")
    parent_id: int | None = Field(default=None, gt=0, description="父级区域ID")
    description: str | None = Field(default=None, description="区域描述")
    is_active: bool | None = Field(default=None, description="是否启用")


class AreaResponse(AreaBase):
    """区域响应模型"""

    id: int = Field(description="区域ID")
    parent: AreaResponse | None = Field(default=None, description="父级区域")
    children: list[AreaResponse] = Field(default_factory=list, description="子区域列表")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class AreaQueryParams(BaseQueryParams):
    """区域查询参数"""

    parent_id: int | None = Field(default=None, gt=0, description="父级区域ID筛选")
    code: str | None = Field(default=None, description="区域代码筛选")


# ================================ 设备分组相关 ================================


class DeviceGroupBase(BaseModel):
    """设备分组基础模型"""

    name: str = Field(min_length=1, max_length=100, description="分组名称")
    area_id: int = Field(gt=0, description="所属区域ID")
    description: str | None = Field(default=None, description="分组描述")
    is_active: bool = Field(default=True, description="是否启用")


class DeviceGroupCreate(DeviceGroupBase):
    """创建设备分组模型"""

    pass


class DeviceGroupUpdate(BaseModel):
    """更新设备分组模型"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="分组名称")
    area_id: int | None = Field(default=None, gt=0, description="所属区域ID")
    description: str | None = Field(default=None, description="分组描述")
    is_active: bool | None = Field(default=None, description="是否启用")


class DeviceGroupResponse(DeviceGroupBase):
    """设备分组响应模型"""

    id: int = Field(description="分组ID")
    area: AreaResponse = Field(description="区域信息")
    device_count: int = Field(default=0, description="设备数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class DeviceGroupQueryParams(BaseQueryParams):
    """设备分组查询参数"""

    area_id: int | None = Field(default=None, gt=0, description="区域ID筛选")


# ================================ 设备相关 ================================


class DeviceBase(BaseModel):
    """设备基础模型"""

    name: str = Field(min_length=1, max_length=100, description="设备名称")
    hostname: str | None = Field(default=None, max_length=100, description="主机名")
    management_ip: IPvAnyAddress = Field(description="管理IP地址")
    port: int = Field(default=22, ge=1, le=65535, description="连接端口")
    account: str = Field(min_length=1, max_length=50, description="登录账号")
    password: str = Field(min_length=1, max_length=255, description="登录密码")
    enable_password: str | None = Field(default=None, max_length=255, description="特权模式密码")
    connection_type: ConnectionTypeEnum = Field(default=ConnectionTypeEnum.SSH, description="连接类型")
    brand_id: int = Field(gt=0, description="设备品牌ID")
    device_model_id: int | None = Field(default=None, gt=0, description="设备型号ID")
    area_id: int = Field(gt=0, description="所属区域ID")
    device_group_id: int | None = Field(default=None, gt=0, description="所属分组ID")
    description: str | None = Field(default=None, description="设备描述")
    is_active: bool = Field(default=True, description="是否启用")


class DeviceCreate(DeviceBase):
    """创建设备模型"""

    pass


class DeviceUpdate(BaseModel):
    """更新设备模型"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="设备名称")
    hostname: str | None = Field(default=None, max_length=100, description="主机名")
    management_ip: IPvAnyAddress | None = Field(default=None, description="管理IP地址")
    port: int | None = Field(default=None, ge=1, le=65535, description="连接端口")
    account: str | None = Field(default=None, min_length=1, max_length=50, description="登录账号")
    password: str | None = Field(default=None, min_length=1, max_length=255, description="登录密码")
    enable_password: str | None = Field(default=None, max_length=255, description="特权模式密码")
    connection_type: ConnectionTypeEnum | None = Field(default=None, description="连接类型")
    brand_id: int | None = Field(default=None, gt=0, description="设备品牌ID")
    device_model_id: int | None = Field(default=None, gt=0, description="设备型号ID")
    area_id: int | None = Field(default=None, gt=0, description="所属区域ID")
    device_group_id: int | None = Field(default=None, gt=0, description="所属分组ID")
    description: str | None = Field(default=None, description="设备描述")
    is_active: bool | None = Field(default=None, description="是否启用")


class DeviceResponse(BaseModel):
    """设备响应模型"""

    id: int = Field(description="设备ID")
    name: str = Field(description="设备名称")
    hostname: str | None = Field(description="主机名")
    management_ip: str = Field(description="管理IP地址")
    port: int = Field(description="连接端口")
    account: str = Field(description="登录账号")
    connection_type: ConnectionTypeEnum = Field(description="连接类型")
    brand: BrandResponse = Field(description="设备品牌")
    device_model: DeviceModelResponse | None = Field(description="设备型号")
    area: AreaResponse = Field(description="所属区域")
    device_group: DeviceGroupResponse | None = Field(description="所属分组")
    status: DeviceStatusEnum = Field(description="设备状态")
    last_check_time: datetime | None = Field(description="最后检查时间")
    version: str | None = Field(description="系统版本")
    serial_number: str | None = Field(description="序列号")
    description: str | None = Field(description="设备描述")
    is_active: bool = Field(description="是否启用")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class DeviceQueryParams(BaseQueryParams):
    """设备查询参数"""

    brand_id: int | None = Field(default=None, gt=0, description="品牌ID筛选")
    device_model_id: int | None = Field(default=None, gt=0, description="型号ID筛选")
    area_id: int | None = Field(default=None, gt=0, description="区域ID筛选")
    device_group_id: int | None = Field(default=None, gt=0, description="分组ID筛选")
    status: DeviceStatusEnum | None = Field(default=None, description="设备状态筛选")
    connection_type: ConnectionTypeEnum | None = Field(default=None, description="连接类型筛选")


class DeviceStatusUpdate(BaseModel):
    """设备状态更新模型"""

    status: DeviceStatusEnum = Field(description="设备状态")
    version: str | None = Field(default=None, description="系统版本")
    serial_number: str | None = Field(default=None, description="序列号")


# 解决循环引用
AreaResponse.model_rebuild()
