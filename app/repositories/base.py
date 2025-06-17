"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025-06-17
@Docs: 数据访问层基类，提供通用的CRUD操作
"""

from typing import Any, Generic, TypeVar

from tortoise.exceptions import DoesNotExist
from tortoise.models import Model
from tortoise.queryset import QuerySet

ModelType = TypeVar("ModelType", bound=Model)


class BaseDAO(Generic[ModelType]):
    """数据访问层基类

    提供通用的增删改查、计数、是否存在等方法
    所有具体的DAO类都应该继承此基类
    """

    def __init__(self, model: type[ModelType]):
        """初始化DAO

        Args:
            model: 对应的Tortoise ORM模型类
        """
        self.model = model

    async def create(self, **kwargs) -> ModelType:
        """创建单个记录

        Args:
            **kwargs: 创建记录的字段值

        Returns:
            创建的模型实例
        """
        return await self.model.create(**kwargs)

    async def bulk_create(self, objects: list[dict[str, Any]]) -> list[ModelType]:
        """批量创建记录

        Args:
            objects: 要创建的记录列表

        Returns:
            创建的模型实例列表
        """
        instances = [self.model(**obj) for obj in objects]
        await self.model.bulk_create(instances)
        return instances

    async def get_by_id(self, id: int) -> ModelType | None:
        """根据ID获取记录

        Args:
            id: 记录ID

        Returns:
            模型实例或None
        """
        try:
            return await self.model.get(id=id)
        except DoesNotExist:
            return None

    async def get_or_404(self, id: int) -> ModelType:
        """根据ID获取记录，不存在则抛出异常

        Args:
            id: 记录ID

        Returns:
            模型实例

        Raises:
            DoesNotExist: 记录不存在
        """
        return await self.model.get(id=id)

    async def get_by_field(self, field_name: str, value: Any) -> ModelType | None:
        """根据指定字段获取记录

        Args:
            field_name: 字段名
            value: 字段值

        Returns:
            模型实例或None
        """
        try:
            return await self.model.get(**{field_name: value})
        except DoesNotExist:
            return None

    async def get_by_filters(self, **filters) -> ModelType | None:
        """根据过滤条件获取单个记录

        Args:
            **filters: 过滤条件

        Returns:
            模型实例或None
        """
        try:
            return await self.model.get(**filters)
        except DoesNotExist:
            return None

    async def list_all(self, prefetch_related: list[str] | None = None) -> list[ModelType]:
        """获取所有记录

        Args:
            prefetch_related: 预加载的关联字段列表

        Returns:
            模型实例列表
        """
        queryset = self.model.all()
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return await queryset

    async def list_by_filters(
        self,
        filters: dict[str, Any] | None = None,
        prefetch_related: list[str] | None = None,
        order_by: list[str] | None = None,
    ) -> list[ModelType]:
        """根据过滤条件获取记录列表

        Args:
            filters: 过滤条件字典
            prefetch_related: 预加载的关联字段列表
            order_by: 排序字段列表

        Returns:
            模型实例列表
        """
        queryset = self.model.all()

        if filters:
            queryset = queryset.filter(**filters)

        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        if order_by:
            queryset = queryset.order_by(*order_by)

        return await queryset

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: dict[str, Any] | None = None,
        prefetch_related: list[str] | None = None,
        order_by: list[str] | None = None,
    ) -> dict[str, Any]:
        """分页查询

        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            filters: 过滤条件字典
            prefetch_related: 预加载的关联字段列表
            order_by: 排序字段列表

        Returns:
            包含分页信息的字典
        """
        queryset = self.model.all()

        if filters:
            queryset = queryset.filter(**filters)

        if order_by:
            queryset = queryset.order_by(*order_by)

        # 计算总数
        total = await queryset.count()

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取当前页数据
        page_queryset = queryset.offset(offset).limit(page_size)
        if prefetch_related:
            page_queryset = page_queryset.prefetch_related(*prefetch_related)

        items = await page_queryset

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

    async def update_by_id(self, id: int, **kwargs) -> ModelType | None:
        """根据ID更新记录

        Args:
            id: 记录ID
            **kwargs: 更新的字段值

        Returns:
            更新后的模型实例或None
        """
        instance = await self.get_by_id(id)
        if instance:
            await instance.update_from_dict(kwargs).save()
            await instance.refresh_from_db()
            return instance
        return None

    async def update_by_filters(self, filters: dict[str, Any], **kwargs) -> int:
        """根据过滤条件批量更新记录

        Args:
            filters: 过滤条件字典
            **kwargs: 更新的字段值

        Returns:
            更新的记录数量
        """
        return await self.model.filter(**filters).update(**kwargs)

    async def delete_by_id(self, id: int) -> bool:
        """根据ID删除记录

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        instance = await self.get_by_id(id)
        if instance:
            await instance.delete()
            return True
        return False

    async def soft_delete_by_id(self, id: int) -> bool:
        """根据ID软删除记录（标记为已删除）

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        return await self.update_by_id(id, is_deleted=True) is not None

    async def delete_by_filters(self, **filters) -> int:
        """根据过滤条件批量删除记录

        Args:
            **filters: 过滤条件

        Returns:
            删除的记录数量
        """
        return await self.model.filter(**filters).delete()

    async def soft_delete_by_filters(self, **filters) -> int:
        """根据过滤条件批量软删除记录

        Args:
            **filters: 过滤条件

        Returns:
            删除的记录数量
        """
        return await self.model.filter(**filters).update(is_deleted=True)

    async def count(self, **filters) -> int:
        """统计记录数量

        Args:
            **filters: 过滤条件

        Returns:
            记录数量
        """
        return await self.model.filter(**filters).count()

    async def exists(self, **filters) -> bool:
        """检查记录是否存在

        Args:
            **filters: 过滤条件

        Returns:
            是否存在
        """
        return await self.model.filter(**filters).exists()

    async def exists_by_id(self, id: int) -> bool:
        """检查指定ID的记录是否存在

        Args:
            id: 记录ID

        Returns:
            是否存在
        """
        return await self.exists(id=id)

    async def get_active_records(self, **filters) -> list[ModelType]:
        """获取活跃记录（未删除且启用的记录）

        Args:
            **filters: 额外的过滤条件

        Returns:
            模型实例列表
        """
        base_filters = {"is_deleted": False}
        # 如果模型有is_active字段，也加入过滤条件
        if hasattr(self.model, "is_active"):
            base_filters["is_active"] = True

        base_filters.update(filters)
        return await self.list_by_filters(base_filters)

    async def get_count_by_status(self, status_field: str) -> dict[str, int]:
        """按状态字段统计记录数量

        Args:
            status_field: 状态字段名

        Returns:
            状态与数量的映射字典
        """
        from tortoise.functions import Count

        result = await self.model.all().group_by(status_field).annotate(count=Count("id")).values(status_field, "count")
        return {item[status_field]: item["count"] for item in result}

    def get_queryset(self) -> QuerySet:
        """获取基础查询集，用于自定义复杂查询

        Returns:
            QuerySet对象
        """
        return self.model.all()

    def filter(self, **filters) -> QuerySet:
        """获取过滤后的查询集

        Args:
            **filters: 过滤条件

        Returns:
            QuerySet对象
        """
        return self.model.filter(**filters)
