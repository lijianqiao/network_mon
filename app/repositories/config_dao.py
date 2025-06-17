"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_dao.py
@DateTime: 2025-06-17
@Docs: 配置模板相关的数据访问层
"""

from typing import Any

from app.models.data_models import ConfigTemplate

from .base_dao import BaseDAO


class ConfigTemplateDAO(BaseDAO[ConfigTemplate]):
    """配置模板DAO"""

    def __init__(self):
        super().__init__(ConfigTemplate)

    async def get_by_name(self, name: str) -> ConfigTemplate | None:
        """根据模板名称获取配置模板"""
        return await self.get_by_field("name", name)

    async def list_by_brand(self, brand_id: int) -> list[ConfigTemplate]:
        """获取指定品牌的配置模板"""
        return await self.list_by_filters(
            filters={"brand_id": brand_id, "is_deleted": False, "is_active": True},
            prefetch_related=["brand"],
            order_by=["template_type", "name"],
        )

    async def list_by_device_type(self, device_type: str) -> list[ConfigTemplate]:
        """获取指定设备类型的配置模板"""
        return await self.list_by_filters(
            filters={"device_type": device_type, "is_deleted": False, "is_active": True},
            prefetch_related=["brand"],
            order_by=["brand__name", "name"],
        )

    async def list_by_template_type(self, template_type: str) -> list[ConfigTemplate]:
        """获取指定模板类型的配置模板"""
        return await self.list_by_filters(
            filters={"template_type": template_type, "is_deleted": False, "is_active": True},
            prefetch_related=["brand"],
            order_by=["brand__name", "name"],
        )

    async def search_templates(
        self,
        keyword: str | None = None,
        brand_id: int | None = None,
        device_type: str | None = None,
        template_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """搜索配置模板"""
        filters: dict[str, Any] = {"is_deleted": False}

        if brand_id:
            filters["brand_id"] = brand_id
        if device_type:
            filters["device_type"] = device_type
        if template_type:
            filters["template_type"] = template_type

        # 如果有关键词，使用复杂查询
        if keyword:
            from tortoise.expressions import Q

            query = self.model.filter(**filters).filter(
                Q(name__icontains=keyword) | Q(description__icontains=keyword) | Q(content__icontains=keyword)
            )

            # 计算总数
            total = await query.count()

            # 分页查询
            offset = (page - 1) * page_size
            items = await (
                query.prefetch_related("brand").offset(offset).limit(page_size).order_by("template_type", "name")
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
                prefetch_related=["brand"],
                order_by=["template_type", "name"],
            )

    async def get_templates_by_brand_and_type(
        self, brand_id: int | None = None, device_type: str | None = None
    ) -> list[ConfigTemplate]:
        """根据品牌和设备类型获取匹配的模板"""
        filters: dict[str, Any] = {"is_deleted": False, "is_active": True}

        # 优先级查询：完全匹配 > 品牌匹配 > 通用模板
        queries = []

        # 1. 完全匹配（品牌和设备类型都匹配）
        if brand_id and device_type:
            queries.append(self.model.filter(brand_id=brand_id, device_type=device_type, **filters))

        # 2. 品牌匹配，设备类型为空（通用于该品牌的所有设备类型）
        if brand_id:
            queries.append(self.model.filter(brand_id=brand_id, device_type__isnull=True, **filters))

        # 3. 通用模板（品牌和设备类型都为空）
        queries.append(self.model.filter(brand_id__isnull=True, device_type__isnull=True, **filters))

        # 按优先级合并结果
        all_templates = []
        for query in queries:
            templates = await query.prefetch_related("brand").order_by("template_type", "name")
            all_templates.extend(templates)

        # 去重（保持优先级顺序）
        seen = set()
        unique_templates = []
        for template in all_templates:
            if template.id not in seen:
                seen.add(template.id)
                unique_templates.append(template)

        return unique_templates

    async def get_template_count_by_type(self) -> dict[str, int]:
        """按模板类型统计模板数量"""
        return await self.get_count_by_status("template_type")

    async def get_template_usage_stats(self) -> list[dict[str, Any]]:
        """获取模板使用统计"""
        # 这里可以根据业务需求统计模板的使用情况
        # 比如关联操作日志表，统计每个模板的使用次数
        return await (
            ConfigTemplate.all()
            .filter(is_deleted=False)
            .prefetch_related("brand")
            .values(
                "id", "name", "template_type", "device_type", "brand__name", "brand__code", "is_active", "created_at"
            )
        )
