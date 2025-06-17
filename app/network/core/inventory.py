"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: inventory.py
@DateTime: 2025-06-17
@Docs: Nornir动态设备清单管理器
"""

from typing import Any

from app.models.data_models import Device


class DynamicInventory:
    """动态设备清单管理器

    从数据库动态构建Nornir Inventory，支持多厂商设备
    """

    def __init__(self):
        """初始化动态清单管理器"""
        self._platform_map = {
            "H3C": "hp_comware",
            "HUAWEI": "huawei_vrp",
            "CISCO": "cisco_iosxe",
            "JUNIPER": "juniper_junos",
        }

    async def build_from_device_ids(self, device_ids: list[int], password: str | None = None) -> dict[str, Any]:
        """根据设备ID列表构建Inventory配置

        Args:
            device_ids: 设备ID列表
            password: 设备登录密码（如果提供）

        Returns:
            Nornir Inventory配置字典

        Raises:
            ValueError: 当设备ID列表为空时
            RuntimeError: 当数据库查询失败时
        """
        if not device_ids:
            raise ValueError("设备ID列表不能为空")

        try:
            devices = await self._get_devices_from_db(device_ids)
            hosts = {}

            for device in devices:
                host_config = await self._build_host_config(device, password)
                hosts[device.name] = host_config

            return {
                "hosts": hosts,
                "defaults": {
                    "connection_options": {
                        "scrapli": {
                            "extras": {"timeout_socket": 30, "timeout_ops": 60, "auth_retry": 3, "transport": "ssh2"}
                        }
                    }
                },
            }

        except Exception as e:
            raise RuntimeError(f"构建设备清单失败: {str(e)}") from e

    async def build_from_filters(
        self,
        brand_ids: list[int] | None = None,
        area_ids: list[int] | None = None,
        group_ids: list[int] | None = None,
        is_active: bool = True,
        password: str | None = None,
    ) -> dict[str, Any]:
        """根据过滤条件构建Inventory配置

        Args:
            brand_ids: 品牌ID列表
            area_ids: 区域ID列表
            group_ids: 分组ID列表
            is_active: 是否只包含活跃设备
            password: 设备登录密码

        Returns:
            Nornir Inventory配置字典
        """
        try:
            devices = await self._get_devices_by_filters(
                brand_ids=brand_ids, area_ids=area_ids, group_ids=group_ids, is_active=is_active
            )

            hosts = {}
            for device in devices:
                host_config = await self._build_host_config(device, password)
                hosts[device.name] = host_config

            return {"hosts": hosts}

        except Exception as e:
            raise RuntimeError(f"根据过滤条件构建设备清单失败: {str(e)}") from e

    async def _get_devices_from_db(self, device_ids: list[int]) -> list[Device]:
        """从数据库获取指定ID的设备列表

        Args:
            device_ids: 设备ID列表

        Returns:
            设备对象列表
        """
        return (
            await Device.filter(id__in=device_ids, is_active=True)
            .prefetch_related("brand", "device_model", "area", "device_group")
            .all()
        )

    async def _get_devices_by_filters(
        self,
        brand_ids: list[int] | None = None,
        area_ids: list[int] | None = None,
        group_ids: list[int] | None = None,
        is_active: bool = True,
    ) -> list[Device]:
        """根据过滤条件从数据库获取设备列表

        Args:
            brand_ids: 品牌ID列表
            area_ids: 区域ID列表
            group_ids: 分组ID列表
            is_active: 是否只包含活跃设备

        Returns:
            设备对象列表
        """
        queryset = Device.filter(is_active=is_active)

        if brand_ids:
            queryset = queryset.filter(brand__id__in=brand_ids)
        if area_ids:
            queryset = queryset.filter(area__id__in=area_ids)
        if group_ids:
            queryset = queryset.filter(device_group__id__in=group_ids)

        return await queryset.prefetch_related("brand", "device_model", "area", "device_group").all()

    async def _build_host_config(self, device: Device, password: str | None) -> dict[str, Any]:
        """为单个设备构建Host配置

        Args:
            device: 设备对象
            password: 登录密码

        Returns:
            Host配置字典
        """
        # 获取品牌信息
        brand_code = device.brand.code.upper() if device.brand else "UNKNOWN"
        platform = self._get_platform(brand_code)

        # 构建连接配置
        connection_extras = {}

        # H3C设备特殊配置
        if brand_code == "H3C":
            connection_extras["on_open"] = [
                "screen-length disable",  # 禁用分页
                "undo terminal monitor",  # 禁用终端监控
            ]

        # 华为设备特殊配置
        elif brand_code == "HUAWEI":
            connection_extras["on_open"] = [
                "screen-length 0 temporary",  # 临时禁用分页
                "undo terminal monitor",  # 禁用终端监控
            ]

        return {
            "hostname": device.management_ip,
            "username": device.account,
            "password": password or device.password,
            "platform": platform,
            "port": device.port,
            "data": {
                "device_id": device.id,
                "brand": brand_code,
                "model": device.device_model.name if device.device_model else None,
                "area": device.area.name if device.area else None,
                "group": device.device_group.name if device.device_group else None,
                "description": device.description,
            },
            "connection_options": {
                "scrapli": {
                    "extras": connection_extras,
                    "timeout_socket": 30,
                    "timeout_ops": 60,
                    "auth_retry": 3,
                    "transport": "ssh2",
                }
            },
        }

    def _get_platform(self, brand_code: str) -> str:
        """根据品牌代码获取Scrapli平台标识

        Args:
            brand_code: 品牌代码

        Returns:
            平台标识字符串
        """
        return self._platform_map.get(brand_code, "generic")

    async def get_host_info(self, device_id: int) -> dict[str, Any] | None:
        """获取单个设备的Host信息（用于调试）

        Args:
            device_id: 设备ID

        Returns:
            设备信息字典或None
        """
        try:
            device = await Device.get_or_none(id=device_id, is_active=True).prefetch_related(
                "brand", "device_model", "area", "device_group"
            )

            if not device:
                return None

            return {
                "name": device.name,
                "hostname": device.management_ip,
                "platform": self._get_platform(device.brand.code.upper() if device.brand else "UNKNOWN"),
                "brand": device.brand.name if device.brand else None,
                "model": device.device_model.name if device.device_model else None,
                "area": device.area.name if device.area else None,
                "group": device.device_group.name if device.device_group else None,
            }

        except Exception as e:
            raise RuntimeError(f"获取设备信息失败: {str(e)}") from e
