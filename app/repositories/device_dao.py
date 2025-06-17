"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_dao.py
@DateTime: 2025-06-17
@Docs: 设备相关模型的数据访问层
"""

from typing import Any

from app.models.data_models import Area, Brand, Device, DeviceGroup, DeviceModel

from .base_dao import BaseDAO


class BrandDAO(BaseDAO[Brand]):
    """品牌DAO"""

    def __init__(self):
        super().__init__(Brand)

    async def get_by_code(self, code: str) -> Brand | None:
        """根据品牌代码获取品牌"""
        return await self.get_by_field("code", code)

    async def get_by_name(self, name: str) -> Brand | None:
        """根据品牌名称获取品牌"""
        return await self.get_by_field("name", name)

    async def list_active_brands(self) -> list[Brand]:
        """获取所有活跃的品牌"""
        return await self.get_active_records()

    async def get_brands_with_device_count(self) -> list[dict[str, Any]]:
        """获取品牌及其设备数量统计"""
        from tortoise.functions import Count

        return await (
            Brand.all()
            .filter(is_deleted=False)
            .annotate(device_count=Count("devices"))
            .values("id", "name", "code", "description", "is_active", "device_count")
        )


class DeviceModelDAO(BaseDAO[DeviceModel]):
    """设备型号DAO"""

    def __init__(self):
        super().__init__(DeviceModel)

    async def get_by_brand_and_name(self, brand_id: int, name: str) -> DeviceModel | None:
        """根据品牌和型号名称获取设备型号"""
        return await self.get_by_filters(brand_id=brand_id, name=name)

    async def list_by_brand(self, brand_id: int) -> list[DeviceModel]:
        """获取指定品牌的所有型号"""
        return await self.list_by_filters(
            filters={"brand_id": brand_id, "is_deleted": False, "is_active": True},
            prefetch_related=["brand"],
            order_by=["name"],
        )

    async def list_by_device_type(self, device_type: str) -> list[DeviceModel]:
        """获取指定设备类型的所有型号"""
        return await self.list_by_filters(
            filters={"device_type": device_type, "is_deleted": False, "is_active": True},
            prefetch_related=["brand"],
            order_by=["brand__name", "name"],
        )

    async def get_models_with_device_count(self) -> list[dict[str, Any]]:
        """获取型号及其设备数量统计"""
        from tortoise.functions import Count

        return await (
            DeviceModel.all()
            .filter(is_deleted=False)
            .prefetch_related("brand")
            .annotate(device_count=Count("devices"))
            .values(
                "id", "name", "device_type", "description", "is_active", "brand__name", "brand__code", "device_count"
            )
        )


class AreaDAO(BaseDAO[Area]):
    """区域DAO"""

    def __init__(self):
        super().__init__(Area)

    async def get_by_code(self, code: str) -> Area | None:
        """根据区域代码获取区域"""
        return await self.get_by_field("code", code)

    async def get_by_name(self, name: str) -> Area | None:
        """根据区域名称获取区域"""
        return await self.get_by_field("name", name)

    async def list_root_areas(self) -> list[Area]:
        """获取所有根区域（无父级）"""
        return await self.list_by_filters(
            filters={"parent": None, "is_deleted": False, "is_active": True}, order_by=["name"]
        )

    async def list_child_areas(self, parent_id: int) -> list[Area]:
        """获取指定父区域的子区域"""
        return await self.list_by_filters(
            filters={"parent_id": parent_id, "is_deleted": False, "is_active": True}, order_by=["name"]
        )

    async def get_area_tree(self) -> list[dict[str, Any]]:
        """获取区域树结构"""
        # 获取所有活跃区域
        areas = await self.list_by_filters(
            filters={"is_deleted": False, "is_active": True}, order_by=["parent_id", "name"]
        )

        # 构建树结构
        area_dict = {}
        root_areas = []

        # 先创建所有节点
        for area in areas:
            # 获取父级ID（如果是外键字段，需要通过_id访问）
            parent_id = getattr(area, "parent_id", None)
            area_dict[area.id] = {
                "id": area.id,
                "name": area.name,
                "code": area.code,
                "description": area.description,
                "parent_id": parent_id,
                "children": [],
            }

        # 构建父子关系
        for area in areas:
            area_data = area_dict[area.id]
            parent_id = getattr(area, "parent_id", None)
            if parent_id:
                parent = area_dict.get(parent_id)
                if parent:
                    parent["children"].append(area_data)
            else:
                root_areas.append(area_data)

        return root_areas

    async def get_areas_with_device_count(self) -> list[dict[str, Any]]:
        """获取区域及其设备数量统计"""
        from tortoise.functions import Count

        return await (
            Area.all()
            .filter(is_deleted=False)
            .annotate(device_count=Count("devices"))
            .values("id", "name", "code", "description", "is_active", "parent_id", "device_count")
        )


class DeviceGroupDAO(BaseDAO[DeviceGroup]):
    """设备分组DAO"""

    def __init__(self):
        super().__init__(DeviceGroup)

    async def list_by_area(self, area_id: int) -> list[DeviceGroup]:
        """获取指定区域的所有分组"""
        return await self.list_by_filters(
            filters={"area_id": area_id, "is_deleted": False, "is_active": True},
            prefetch_related=["area"],
            order_by=["name"],
        )

    async def get_by_area_and_name(self, area_id: int, name: str) -> DeviceGroup | None:
        """根据区域和分组名称获取设备分组"""
        return await self.get_by_filters(area_id=area_id, name=name)

    async def get_groups_with_device_count(self) -> list[dict[str, Any]]:
        """获取分组及其设备数量统计"""
        from tortoise.functions import Count

        return await (
            DeviceGroup.all()
            .filter(is_deleted=False)
            .prefetch_related("area")
            .annotate(device_count=Count("devices"))
            .values("id", "name", "description", "is_active", "area__name", "area__code", "device_count")
        )


class DeviceDAO(BaseDAO[Device]):
    """设备DAO"""

    def __init__(self):
        super().__init__(Device)

    async def get_by_management_ip(self, management_ip: str) -> Device | None:
        """根据管理IP获取设备"""
        return await self.get_by_field("management_ip", management_ip)

    async def get_by_hostname(self, hostname: str) -> Device | None:
        """根据主机名获取设备"""
        return await self.get_by_field("hostname", hostname)

    async def list_by_brand(self, brand_id: int) -> list[Device]:
        """获取指定品牌的所有设备"""
        return await self.list_by_filters(
            filters={"brand_id": brand_id, "is_deleted": False},
            prefetch_related=["brand", "device_model", "area", "device_group"],
            order_by=["name"],
        )

    async def list_by_area(self, area_id: int) -> list[Device]:
        """获取指定区域的所有设备"""
        return await self.list_by_filters(
            filters={"area_id": area_id, "is_deleted": False},
            prefetch_related=["brand", "device_model", "area", "device_group"],
            order_by=["name"],
        )

    async def list_by_group(self, group_id: int) -> list[Device]:
        """获取指定分组的所有设备"""
        return await self.list_by_filters(
            filters={"device_group_id": group_id, "is_deleted": False},
            prefetch_related=["brand", "device_model", "area", "device_group"],
            order_by=["name"],
        )

    async def list_by_status(self, status: str) -> list[Device]:
        """获取指定状态的所有设备"""
        return await self.list_by_filters(
            filters={"status": status, "is_deleted": False},
            prefetch_related=["brand", "device_model", "area", "device_group"],
            order_by=["name"],
        )

    async def get_device_status_count(self) -> dict[str, int]:
        """获取设备状态统计"""
        return await self.get_count_by_status("status")

    async def search_devices(
        self,
        keyword: str | None = None,
        brand_id: int | None = None,
        area_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """搜索设备"""
        filters: dict[str, Any] = {"is_deleted": False}

        if brand_id:
            filters["brand_id"] = brand_id
        if area_id:
            filters["area_id"] = area_id
        if status:
            filters["status"] = status

        # 如果有关键词，使用复杂查询
        if keyword:
            from tortoise.expressions import Q

            query = self.model.filter(**filters).filter(
                Q(name__icontains=keyword)
                | Q(hostname__icontains=keyword)
                | Q(management_ip__icontains=keyword)
                | Q(description__icontains=keyword)
            )

            # 计算总数
            total = await query.count()

            # 分页查询
            offset = (page - 1) * page_size
            items = await (
                query.prefetch_related("brand", "device_model", "area", "device_group")
                .offset(offset)
                .limit(page_size)
                .order_by("name")
            )

            # 计算分页信息
            total_pages = (total + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        else:
            return await self.paginate(
                page=page,
                page_size=page_size,
                filters=filters,
                prefetch_related=["brand", "device_model", "area", "device_group"],
                order_by=["name"],
            )

    async def get_devices_for_monitoring(self) -> list[Device]:
        """获取需要监控的设备（活跃且启用的设备）"""
        return await self.get_active_records()

    async def update_device_status(self, device_id: int, status: str, **kwargs) -> Device | None:
        """更新设备状态及其他信息"""
        update_data = {"status": status}
        update_data.update(kwargs)
        return await self.update_by_id(device_id, **update_data)

    async def batch_update_device_status(self, device_ids: list[int], status: str) -> int:
        """批量更新设备状态"""
        return await self.update_by_filters(filters={"id__in": device_ids}, status=status)
