"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_service.py
@DateTime: 2025-06-17
@Docs: 配置模板业务服务层
"""

from app.models.data_models import ConfigTemplate
from app.repositories import ConfigTemplateDAO
from app.utils import LogConfig, system_log

from .base_service import BaseService


class ConfigTemplateService(BaseService[ConfigTemplate, ConfigTemplateDAO]):
    """配置模板服务类"""

    def __init__(self):
        super().__init__(ConfigTemplateDAO())

    async def _validate_create_data(self, data: dict) -> None:
        """配置模板创建数据校验"""
        if not data.get("name"):
            raise ValueError("模板名称不能为空")
        if not data.get("content"):
            raise ValueError("模板内容不能为空")
        if not data.get("template_type"):
            raise ValueError("模板类型不能为空")

        # 检查名称是否已存在
        existing = await self.dao.get_by_field("name", data["name"])
        if existing:
            raise ValueError(f"模板名称 '{data['name']}' 已存在")

    async def _validate_update_data(self, data: dict, existing: ConfigTemplate) -> None:
        """配置模板更新数据校验"""
        if "name" in data and data["name"] != existing.name:
            # 检查新名称是否已存在
            existing_template = await self.dao.get_by_field("name", data["name"])
            if existing_template:
                raise ValueError(f"模板名称 '{data['name']}' 已存在")

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_name(self, name: str, user: str = "system") -> ConfigTemplate | None:
        """根据名称获取配置模板"""
        return await self.dao.get_by_field("name", name)

    @system_log(LogConfig(log_args=True, log_result=False))
    async def get_by_type(self, template_type: str, user: str = "system") -> list[ConfigTemplate]:
        """根据类型获取配置模板"""
        return await self.dao.list_by_filters(filters={"template_type": template_type})

    @system_log(LogConfig(log_args=True, log_result=False))
    async def search_templates(self, keyword: str, user: str = "system") -> list[ConfigTemplate]:
        """搜索配置模板"""
        return await self.dao.list_by_filters(filters={"name__icontains": keyword})
