"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_manager.py
@DateTime: 2025-06-17
@Docs: 网络设备管理器
"""

import uuid
from datetime import datetime
from typing import Any


class NetworkDevice:
    """网络设备模型"""

    def __init__(
        self,
        device_id: str,
        ip: str,
        hostname: str | None = None,
        device_type: str = "unknown",
        location: str | None = None,
        status: str = "unknown",
        last_seen: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = device_id
        self.ip = ip
        self.hostname = hostname
        self.device_type = device_type
        self.location = location
        self.status = status
        self.last_seen = last_seen
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


class SimpleDeviceManager:
    """简化的设备管理器（内存存储）

    用于演示和开发，生产环境应该集成实际的数据库DAO
    """

    def __init__(self):
        """初始化设备管理器"""
        self._devices: dict[str, NetworkDevice] = {}

        # 添加一些示例设备
        self._init_sample_devices()

    def _init_sample_devices(self):
        """初始化示例设备"""
        sample_devices = [
            {
                "device_id": "dev-001",
                "ip": "192.168.1.1",
                "hostname": "Core-Router-01",
                "device_type": "h3c",
                "location": "机房A",
                "status": "online",
            },
            {
                "device_id": "dev-002",
                "ip": "192.168.1.10",
                "hostname": "Access-Switch-01",
                "device_type": "h3c",
                "location": "机房A",
                "status": "online",
            },
            {
                "device_id": "dev-003",
                "ip": "192.168.1.20",
                "hostname": "Firewall-01",
                "device_type": "h3c",
                "location": "机房B",
                "status": "offline",
            },
        ]
        for device_data in sample_devices:
            device = NetworkDevice(
                device_id=device_data["device_id"],
                ip=device_data["ip"],
                hostname=device_data.get("hostname"),
                device_type=device_data.get("device_type", "unknown"),
                location=device_data.get("location"),
                status=device_data.get("status", "unknown"),
            )
            self._devices[device.id] = device

    async def get_devices(self) -> list[NetworkDevice]:
        """获取所有设备"""
        return list(self._devices.values())

    async def get_device_by_id(self, device_id: str) -> NetworkDevice | None:
        """根据ID获取设备"""
        return self._devices.get(device_id)

    async def create_device(self, device_data: dict[str, Any]) -> NetworkDevice:
        """创建设备"""
        device_id = device_data.get("id") or str(uuid.uuid4())
        device = NetworkDevice(
            device_id=device_id,
            ip=device_data["ip"],
            hostname=device_data.get("hostname"),
            device_type=device_data.get("device_type", "unknown"),
            location=device_data.get("location"),
            status=device_data.get("status", "unknown"),
        )
        self._devices[device_id] = device
        return device

    async def update_device(self, device_id: str, update_data: dict[str, Any]) -> NetworkDevice | None:
        """更新设备"""
        device = self._devices.get(device_id)
        if not device:
            return None

        # 更新字段
        for key, value in update_data.items():
            if hasattr(device, key) and key != "id":  # 不允许更新ID
                setattr(device, key, value)

        device.updated_at = datetime.now()
        return device

    async def delete_device(self, device_id: str) -> bool:
        """删除设备"""
        if device_id in self._devices:
            del self._devices[device_id]
            return True
        return False

    async def get_devices_by_type(self, device_type: str) -> list[NetworkDevice]:
        """根据设备类型获取设备"""
        return [device for device in self._devices.values() if device.device_type == device_type]

    async def get_devices_by_location(self, location: str) -> list[NetworkDevice]:
        """根据位置获取设备"""
        return [device for device in self._devices.values() if device.location == location]

    async def get_devices_by_status(self, status: str) -> list[NetworkDevice]:
        """根据状态获取设备"""
        return [device for device in self._devices.values() if device.status == status]

    async def update_device_status(self, device_id: str, status: str) -> bool:
        """更新设备状态"""
        device = self._devices.get(device_id)
        if device:
            device.status = status
            device.last_seen = datetime.now() if status == "online" else device.last_seen
            device.updated_at = datetime.now()
            return True
        return False

    async def get_status_summary(self) -> dict[str, Any]:
        """获取设备状态汇总"""
        all_devices = list(self._devices.values())
        total_devices = len(all_devices)

        # 按状态统计
        online_devices = len([d for d in all_devices if d.status == "online"])
        offline_devices = len([d for d in all_devices if d.status == "offline"])
        unknown_devices = len([d for d in all_devices if d.status == "unknown"])

        # 按类型统计
        by_type = {}
        for device in all_devices:
            device_type = device.device_type or "unknown"
            by_type[device_type] = by_type.get(device_type, 0) + 1

        # 按位置统计
        by_location = {}
        for device in all_devices:
            location = device.location or "未知位置"
            by_location[location] = by_location.get(location, 0) + 1

        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "unknown_devices": unknown_devices,
            "by_type": by_type,
            "by_location": by_location,
        }
