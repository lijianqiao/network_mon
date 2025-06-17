"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_service.py
@DateTime: 2025-06-17
@Docs: 设备相关业务服务层
"""

from typing import Any

from app.models.data_models import Area, Brand, Device, DeviceGroup, DeviceModel
from app.repositories import AreaDAO, BrandDAO, DeviceDAO, DeviceGroupDAO, DeviceModelDAO
from app.utils import LogConfig, system_log

from .base_service import BaseService


class BrandService(BaseService[Brand, BrandDAO]):
    """品牌服务类"""

    def __init__(self):
        super().__init__(BrandDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """品牌创建数据校验"""
        if not data.get("name"):
            raise ValueError("品牌名称不能为空")

        # 检查名称是否已存在
        existing = await self.dao.get_by_field("name", data["name"])
        if existing:
            raise ValueError(f"品牌名称 '{data['name']}' 已存在")

    async def _validate_update_data(self, data: dict, existing: Brand) -> None:
        """品牌更新数据校验"""
        if "name" in data and data["name"] != existing.name:
            # 检查新名称是否已存在
            existing_brand = await self.dao.get_by_field("name", data["name"])
            if existing_brand:
                raise ValueError(f"品牌名称 '{data['name']}' 已存在")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_name(self, name: str, user: str = "system") -> Brand | None:
        """根据名称获取品牌"""
        return await self.dao.get_by_field("name", name)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_brands(self, keyword: str, user: str = "system") -> list[Brand]:
        """搜索品牌"""
        return await self.dao.list_by_filters(filters={"name__icontains": keyword})


class DeviceModelService(BaseService[DeviceModel, DeviceModelDAO]):
    """设备型号服务类"""

    def __init__(self):
        super().__init__(DeviceModelDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """设备型号创建数据校验"""
        if not data.get("name"):
            raise ValueError("型号名称不能为空")
        if not data.get("brand_id"):
            raise ValueError("品牌ID不能为空")

        # 检查同一品牌下是否已存在相同型号
        existing = await self.dao.list_by_filters(filters={"name": data["name"], "brand_id": data["brand_id"]})
        if existing:
            raise ValueError(f"品牌下已存在型号 '{data['name']}'")

    async def _validate_update_data(self, data: dict, existing: DeviceModel) -> None:
        """设备型号更新数据校验"""
        if "name" in data and data["name"] != existing.name:
            # 检查同一品牌下是否已存在相同型号
            brand_id = data.get("brand_id", existing.brand.id)
            existing_model = await self.dao.list_by_filters(filters={"name": data["name"], "brand_id": brand_id})
            if existing_model:
                raise ValueError(f"品牌下已存在型号 '{data['name']}'")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_brand(self, brand_id: int, user: str = "system") -> list[DeviceModel]:
        """获取指定品牌的所有型号"""
        return await self.dao.list_by_filters(filters={"brand_id": brand_id})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_models(self, keyword: str, user: str = "system") -> list[DeviceModel]:
        """搜索设备型号"""
        return await self.dao.list_by_filters(filters={"name__icontains": keyword})


class AreaService(BaseService[Area, AreaDAO]):
    """区域服务类"""

    def __init__(self):
        super().__init__(AreaDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """区域创建数据校验"""
        if not data.get("name"):
            raise ValueError("区域名称不能为空")

        # 检查名称是否已存在
        existing = await self.dao.get_by_field("name", data["name"])
        if existing:
            raise ValueError(f"区域名称 '{data['name']}' 已存在")

    async def _validate_update_data(self, data: dict, existing: Area) -> None:
        """区域更新数据校验"""
        if "name" in data and data["name"] != existing.name:
            # 检查新名称是否已存在
            existing_area = await self.dao.get_by_field("name", data["name"])
            if existing_area:
                raise ValueError(f"区域名称 '{data['name']}' 已存在")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_name(self, name: str, user: str = "system") -> Area | None:
        """根据名称获取区域"""
        return await self.dao.get_by_field("name", name)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_areas(self, keyword: str, user: str = "system") -> list[Area]:
        """搜索区域"""
        return await self.dao.list_by_filters(filters={"name__icontains": keyword})


class DeviceGroupService(BaseService[DeviceGroup, DeviceGroupDAO]):
    """设备分组服务类"""

    def __init__(self):
        super().__init__(DeviceGroupDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """设备分组创建数据校验"""
        if not data.get("name"):
            raise ValueError("分组名称不能为空")

        # 检查名称是否已存在
        existing = await self.dao.get_by_field("name", data["name"])
        if existing:
            raise ValueError(f"分组名称 '{data['name']}' 已存在")

    async def _validate_update_data(self, data: dict, existing: DeviceGroup) -> None:
        """设备分组更新数据校验"""
        if "name" in data and data["name"] != existing.name:
            # 检查新名称是否已存在
            existing_group = await self.dao.get_by_field("name", data["name"])
            if existing_group:
                raise ValueError(f"分组名称 '{data['name']}' 已存在")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_name(self, name: str, user: str = "system") -> DeviceGroup | None:
        """根据名称获取设备分组"""
        return await self.dao.get_by_field("name", name)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_groups(self, keyword: str, user: str = "system") -> list[DeviceGroup]:
        """搜索设备分组"""
        return await self.dao.list_by_filters(filters={"name__icontains": keyword})


class DeviceService(BaseService[Device, DeviceDAO]):
    """设备服务类"""

    def __init__(self):
        super().__init__(DeviceDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """设备创建数据校验"""
        if not data.get("name"):
            raise ValueError("设备名称不能为空")
        if not data.get("management_ip"):
            raise ValueError("设备管理IP地址不能为空")
        if not data.get("device_model_id"):
            raise ValueError("设备型号ID不能为空")

        # 检查IP地址是否已存在
        existing = await self.dao.get_by_field("management_ip", data["management_ip"])
        if existing:
            raise ValueError(f"管理IP地址 '{data['management_ip']}' 已存在")

        # 检查设备名称是否已存在
        existing_name = await self.dao.get_by_field("name", data["name"])
        if existing_name:
            raise ValueError(f"设备名称 '{data['name']}' 已存在")

    async def _validate_update_data(self, data: dict, existing: Device) -> None:
        """设备更新数据校验"""
        if "management_ip" in data and data["management_ip"] != existing.management_ip:
            # 检查新IP地址是否已存在
            existing_device = await self.dao.get_by_field("management_ip", data["management_ip"])
            if existing_device:
                raise ValueError(f"管理IP地址 '{data['management_ip']}' 已存在")

        if "name" in data and data["name"] != existing.name:
            # 检查新设备名称是否已存在
            existing_device = await self.dao.get_by_field("name", data["name"])
            if existing_device:
                raise ValueError(f"设备名称 '{data['name']}' 已存在")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_ip(self, management_ip: str, user: str = "system") -> Device | None:
        """根据管理IP地址获取设备"""
        return await self.dao.get_by_field("management_ip", management_ip)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_name(self, name: str, user: str = "system") -> Device | None:
        """根据名称获取设备"""
        return await self.dao.get_by_field("name", name)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_area(self, area_id: int, user: str = "system") -> list[Device]:
        """获取指定区域的所有设备"""
        return await self.dao.list_by_filters(filters={"area_id": area_id})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_group(self, group_id: int, user: str = "system") -> list[Device]:
        """获取指定分组的所有设备"""
        return await self.dao.list_by_filters(filters={"device_group_id": group_id})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_status(self, status: str, user: str = "system") -> list[Device]:
        """根据状态获取设备"""
        return await self.dao.list_by_filters(filters={"status": status})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_devices(self, keyword: str, user: str = "system") -> list[Device]:
        """搜索设备"""
        search_result = await self.dao.search_devices(keyword=keyword)
        return search_result.get("items", []) if isinstance(search_result, dict) else search_result

    @system_log(LogConfig(log_args=True))
    async def get_device_statistics(self, user: str = "system") -> dict[str, Any]:
        """获取设备统计信息"""
        status_stats = await self.dao.get_device_status_count()
        total_count = await self.dao.count()
        return {
            "total": total_count,
            "status_breakdown": status_stats,
        }

    @system_log(LogConfig(log_args=True))
    async def update_device_status(self, device_id: int, status: str, user: str = "system") -> Device | None:
        """更新设备状态"""
        return await self.dao.update_device_status(device_id, status)
