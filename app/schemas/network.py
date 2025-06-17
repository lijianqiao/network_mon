"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network.py
@DateTime: 2025-06-17
@Docs: 网络自动化相关校验模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, IPvAnyAddress

# ================================ 网络设备模型 ================================


class NetworkDeviceBase(BaseModel):
    """网络设备基础模型"""

    ip: IPvAnyAddress = Field(description="设备IP地址")
    hostname: str | None = Field(default=None, max_length=100, description="设备主机名")
    device_type: str = Field(max_length=50, description="设备类型")
    location: str | None = Field(default=None, max_length=200, description="设备位置")
    status: str = Field(default="unknown", description="设备状态")


class NetworkDeviceCreate(NetworkDeviceBase):
    """创建网络设备模型"""

    pass


class NetworkDeviceUpdate(BaseModel):
    """更新网络设备模型"""

    hostname: str | None = Field(default=None, max_length=100, description="设备主机名")
    device_type: str | None = Field(default=None, max_length=50, description="设备类型")
    location: str | None = Field(default=None, max_length=200, description="设备位置")
    status: str | None = Field(default=None, description="设备状态")


class NetworkDeviceResponse(NetworkDeviceBase):
    """网络设备响应模型"""

    id: str = Field(description="设备ID")
    last_seen: datetime | None = Field(default=None, description="最后在线时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


# ================================ 网络任务模型 ================================


class NetworkTaskRequest(BaseModel):
    """网络任务请求模型"""

    device_id: str = Field(description="设备ID")
    task_name: str = Field(description="任务名称")
    username: str = Field(default="admin", description="设备登录用户名")
    password: str = Field(default="admin", description="设备登录密码")
    task_params: dict[str, Any] = Field(default_factory=dict, description="任务参数")


class BatchNetworkTaskRequest(BaseModel):
    """批量网络任务请求模型"""

    device_ids: list[str] = Field(description="设备ID列表")
    task_name: str = Field(description="任务名称")
    username: str = Field(default="admin", description="设备登录用户名")
    password: str = Field(default="admin", description="设备登录密码")
    task_params: dict[str, Any] = Field(default_factory=dict, description="任务参数")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="最大并发数")


class NetworkTaskResponse(BaseModel):
    """网络任务响应模型"""

    success: bool = Field(description="执行是否成功")
    task_id: str = Field(description="任务ID")
    device_id: str = Field(description="设备ID")
    task_name: str = Field(description="任务名称")
    timestamp: datetime = Field(description="执行时间")
    duration: float | None = Field(default=None, description="执行耗时（秒）")
    result: dict[str, Any] | None = Field(default=None, description="执行结果")
    error: str | None = Field(default=None, description="错误信息")


class BatchNetworkTaskResponse(BaseModel):
    """批量网络任务响应模型"""

    batch_id: str = Field(description="批次ID")
    total_count: int = Field(description="总任务数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    pending_count: int = Field(description="待执行数")
    tasks: list[NetworkTaskResponse] = Field(description="任务列表")


# ================================ 设备连通性模型 ================================


class DeviceConnectivityRequest(BaseModel):
    """设备连通性测试请求模型"""

    device_id: str = Field(description="设备ID")
    username: str = Field(default="admin", description="设备登录用户名")
    password: str = Field(default="admin", description="设备登录密码")
    timeout: int = Field(default=30, ge=5, le=120, description="超时时间（秒）")


class DeviceConnectivityResponse(BaseModel):
    """设备连通性测试响应模型"""

    device_id: str = Field(description="设备ID")
    device_ip: str = Field(description="设备IP")
    success: bool = Field(description="连通性测试结果")
    response_time: float | None = Field(default=None, description="响应时间（毫秒）")
    error: str | None = Field(default=None, description="错误信息")
    timestamp: datetime = Field(description="测试时间")


# ================================ 网络发现模型 ================================


class NetworkDiscoveryRequest(BaseModel):
    """网络发现请求模型"""

    network_range: str = Field(description="网络范围 (CIDR格式，如 192.168.1.0/24)")
    device_types: list[str] = Field(default=["h3c"], description="要发现的设备类型")
    username: str = Field(default="admin", description="设备登录用户名")
    password: str = Field(default="admin", description="设备登录密码")
    timeout: int = Field(default=10, ge=5, le=60, description="超时时间（秒）")
    max_concurrent: int = Field(default=10, ge=1, le=50, description="最大并发数")


class DiscoveredDevice(BaseModel):
    """发现的设备信息"""

    ip: str = Field(description="设备IP")
    hostname: str | None = Field(default=None, description="设备主机名")
    device_type: str | None = Field(default=None, description="设备类型")
    vendor: str | None = Field(default=None, description="设备厂商")
    model: str | None = Field(default=None, description="设备型号")
    version: str | None = Field(default=None, description="软件版本")
    response_time: float = Field(description="响应时间（毫秒）")


class NetworkDiscoveryResponse(BaseModel):
    """网络发现响应模型"""

    discovery_id: str = Field(description="发现任务ID")
    network_range: str = Field(description="网络范围")
    total_hosts: int = Field(description="总主机数")
    scanned_hosts: int = Field(description="已扫描主机数")
    discovered_devices: list[DiscoveredDevice] = Field(description="发现的设备列表")
    start_time: datetime = Field(description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")
    duration: float | None = Field(default=None, description="耗时（秒）")


# ================================ 设备状态汇总模型 ================================


class DeviceStatusSummary(BaseModel):
    """设备状态汇总模型"""

    total_devices: int = Field(description="总设备数")
    online_devices: int = Field(description="在线设备数")
    offline_devices: int = Field(description="离线设备数")
    unknown_devices: int = Field(description="状态未知设备数")
    by_type: dict[str, int] = Field(description="按设备类型统计")
    by_location: dict[str, int] = Field(description="按位置统计")
    last_updated: datetime = Field(description="最后更新时间")


# ================================ 支持的任务模型 ================================


class SupportedTaskInfo(BaseModel):
    """支持的任务信息"""

    name: str = Field(description="任务名称")
    description: str = Field(description="任务描述")
    category: str = Field(description="任务分类")
    supported_devices: list[str] = Field(description="支持的设备类型")
    required_params: list[str] = Field(description="必需参数")
    optional_params: list[str] = Field(description="可选参数")


class SupportedTasksResponse(BaseModel):
    """支持的任务列表响应模型"""

    tasks: list[SupportedTaskInfo] = Field(description="任务列表")
    total_count: int = Field(description="任务总数")
    categories: list[str] = Field(description="任务分类列表")
