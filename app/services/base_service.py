"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base_service.py
@DateTime: 2025-06-17
@Docs: 服务层基类，提供通用业务逻辑
"""

from typing import Any, Generic, TypeVar

from app.repositories.base_dao import BaseDAO
from app.utils import LogConfig, system_log

# 泛型类型变量
ModelType = TypeVar("ModelType")
DAOType = TypeVar("DAOType", bound=BaseDAO)


class BaseService(Generic[ModelType, DAOType]):
    """服务层基类

    提供通用的业务逻辑处理，包括：
    - 基础CRUD操作
    - 统一的日志记录
    - 统一的错误处理
    - 业务逻辑校验
    """

    def __init__(self, dao: DAOType):
        """初始化服务

        Args:
            dao: 数据访问对象
        """
        self.dao = dao

    @system_log(LogConfig(log_args=True, log_result=False))
    async def create(self, data: dict, user: str = "system") -> ModelType:
        """创建资源

        Args:
            data: 创建数据
            user: 操作用户

        Returns:
            创建的资源对象

        Raises:
            ValueError: 当数据无效时
        """
        # 基础数据校验
        await self._validate_create_data(data)

        # 创建前钩子
        data = await self._before_create(data, user)

        # 执行创建
        result = await self.dao.create(**data)

        # 创建后钩子
        await self._after_create(result, data, user)

        return result

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_id(self, resource_id: int, user: str = "system") -> ModelType | None:
        """根据ID获取资源

        Args:
            resource_id: 资源ID
            user: 操作用户

        Returns:
            资源对象或None
        """
        return await self.dao.get_by_id(resource_id)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def update(self, resource_id: int, data: dict, user: str = "system") -> ModelType | None:
        """更新资源

        Args:
            resource_id: 资源ID
            data: 更新数据
            user: 操作用户

        Returns:
            更新后的资源对象

        Raises:
            ValueError: 当数据无效时
            NotFoundError: 当资源不存在时
        """
        # 检查资源是否存在
        existing = await self.dao.get_by_id(resource_id)
        if not existing:
            raise ValueError(f"Resource with id {resource_id} not found")

        # 基础数据校验
        await self._validate_update_data(data, existing)

        # 更新前钩子
        data = await self._before_update(resource_id, data, existing, user)  # 执行更新
        result = await self.dao.update_by_id(resource_id, **data)

        # 更新后钩子
        if result:
            await self._after_update(result, data, existing, user)

        return result

    @system_log(LogConfig(log_args=True))
    async def delete(self, resource_id: int, user: str = "system") -> bool:
        """删除资源

        Args:
            resource_id: 资源ID
            user: 操作用户

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 当资源不存在时
        """
        # 检查资源是否存在
        existing = await self.dao.get_by_id(resource_id)
        if not existing:
            raise ValueError(f"Resource with id {resource_id} not found")

        # 删除前校验
        await self._validate_delete(existing, user)

        # 删除前钩子
        await self._before_delete(existing, user)

        # 执行删除
        result = await self.dao.delete_by_id(resource_id)

        # 删除后钩子
        await self._after_delete(existing, user)

        return result

    @system_log(LogConfig(log_args=True, log_result=False))
    async def list_all(self, user: str = "system") -> list[ModelType]:
        """获取所有资源

        Args:
            user: 操作用户

        Returns:
            资源列表
        """
        return await self.dao.list_all()

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_paginated(self, page: int = 1, page_size: int = 20, user: str = "system") -> dict[str, Any]:
        """分页获取资源

        Args:
            page: 页码
            page_size: 每页大小
            user: 操作用户

        Returns:
            分页结果
        """
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        return await self.dao.paginate(page, page_size)

    @system_log(LogConfig(log_args=True))
    async def count(self, user: str = "system") -> int:
        """获取资源总数

        Args:
            user: 操作用户

        Returns:
            资源总数
        """
        return await self.dao.count()

    @system_log(LogConfig(log_args=True))
    async def exists(self, resource_id: int, user: str = "system") -> bool:
        """检查资源是否存在

        Args:
            resource_id: 资源ID
            user: 操作用户

        Returns:
            是否存在
        """
        return await self.dao.exists_by_id(resource_id)

    # 钩子方法 - 子类可重写

    async def _validate_create_data(self, data: dict) -> None:
        """创建数据校验钩子

        Args:
            data: 创建数据

        Raises:
            ValueError: 当数据无效时
        """
        pass

    async def _validate_update_data(self, data: dict, existing: ModelType) -> None:
        """更新数据校验钩子

        Args:
            data: 更新数据
            existing: 现有资源

        Raises:
            ValueError: 当数据无效时
        """
        pass

    async def _validate_delete(self, existing: ModelType, user: str) -> None:
        """删除校验钩子

        Args:
            existing: 要删除的资源
            user: 操作用户

        Raises:
            ValueError: 当不允许删除时
        """
        pass

    async def _before_create(self, data: dict, user: str) -> dict:
        """创建前钩子

        Args:
            data: 创建数据
            user: 操作用户

        Returns:
            处理后的数据
        """
        return data

    async def _after_create(self, result: ModelType, data: dict, user: str) -> None:
        """创建后钩子

        Args:
            result: 创建结果
            data: 创建数据
            user: 操作用户
        """
        pass

    async def _before_update(self, resource_id: int, data: dict, existing: ModelType, user: str) -> dict:
        """更新前钩子

        Args:
            resource_id: 资源ID
            data: 更新数据
            existing: 现有资源
            user: 操作用户

        Returns:
            处理后的数据
        """
        return data

    async def _after_update(self, result: ModelType, data: dict, existing: ModelType, user: str) -> None:
        """更新后钩子

        Args:
            result: 更新结果
            data: 更新数据
            existing: 更新前的资源
            user: 操作用户
        """
        pass

    async def _before_delete(self, existing: ModelType, user: str) -> None:
        """删除前钩子

        Args:
            existing: 要删除的资源
            user: 操作用户
        """
        pass

    async def _after_delete(self, existing: ModelType, user: str) -> None:
        """删除后钩子

        Args:
            existing: 已删除的资源
            user: 操作用户
        """
        pass
