"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: snmp_service.py
@DateTime: 2025-06-17
@Docs: SNMP监控服务API
"""

from typing import Any

from app.utils.logger import logger

from .snmp_monitor import SNMPMonitor


class SNMPService:
    """SNMP监控服务API

    提供SNMP监控的服务接口
    """

    def __init__(self):
        """初始化SNMP服务"""
        self.monitor = SNMPMonitor()
        logger.info("SNMP监控服务初始化完成")

    async def start_monitoring(self, poll_interval: int | None = None) -> dict[str, Any]:
        """启动监控服务

        Args:
            poll_interval: 可选，轮询间隔（秒）

        Returns:
            dict: 启动结果
        """
        try:
            if poll_interval:
                self.monitor.poll_interval = poll_interval

            await self.monitor.start_monitoring()

            return {
                "success": True,
                "message": "SNMP监控服务启动成功",
                "poll_interval": self.monitor.poll_interval,
                "alert_thresholds": self.monitor.alert_thresholds,
            }

        except Exception as e:
            logger.error(f"启动SNMP监控服务失败: {e}")
            return {"success": False, "message": f"启动失败: {str(e)}"}

    async def stop_monitoring(self) -> dict[str, Any]:
        """停止监控服务

        Returns:
            dict: 停止结果
        """
        try:
            await self.monitor.stop_monitoring()

            return {"success": True, "message": "SNMP监控服务停止成功"}

        except Exception as e:
            logger.error(f"停止SNMP监控服务失败: {e}")
            return {"success": False, "message": f"停止失败: {str(e)}"}

    def get_monitoring_status(self) -> dict[str, Any]:
        """获取监控状态

        Returns:
            dict: 监控状态信息
        """
        return {
            "is_running": self.monitor.is_running,
            "poll_interval": self.monitor.poll_interval,
            "alert_thresholds": self.monitor.alert_thresholds,
            "monitored_devices": len(self.monitor.monitoring_data),
            "statistics": self.monitor.get_monitoring_statistics(),
        }

    def get_device_metrics(self, device_id: int) -> dict[str, Any]:
        """获取设备监控指标

        Args:
            device_id: 设备ID

        Returns:
            dict: 设备监控指标
        """
        device_status = self.monitor.get_device_status(device_id)

        if not device_status:
            return {"success": False, "message": f"设备 {device_id} 监控数据不存在"}

        return {"success": True, "device_id": device_id, "data": device_status}

    def get_all_device_metrics(self) -> dict[str, Any]:
        """获取所有设备监控指标

        Returns:
            dict: 所有设备监控指标
        """
        all_status = self.monitor.get_all_device_status()

        return {"success": True, "total_devices": len(all_status), "devices": all_status}

    def get_alerts(self, hours: int = 24, device_id: int | None = None) -> dict[str, Any]:
        """获取告警信息

        Args:
            hours: 时间范围（小时）
            device_id: 可选，过滤指定设备的告警

        Returns:
            dict: 告警信息
        """
        alerts = self.monitor.get_recent_alerts(hours=hours, device_id=device_id)

        return {
            "success": True,
            "total_alerts": len(alerts),
            "time_range_hours": hours,
            "device_id": device_id,
            "alerts": alerts,
        }

    def update_thresholds(self, thresholds: dict[str, float]) -> dict[str, Any]:
        """更新告警阈值

        Args:
            thresholds: 新的阈值配置

        Returns:
            dict: 更新结果
        """
        try:
            self.monitor.update_alert_thresholds(thresholds)

            return {"success": True, "message": "告警阈值更新成功", "new_thresholds": self.monitor.alert_thresholds}

        except Exception as e:
            logger.error(f"更新告警阈值失败: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}

    def cleanup_old_data(self, hours: int = 24) -> dict[str, Any]:
        """清理旧数据

        Args:
            hours: 保留时间（小时）

        Returns:
            dict: 清理结果
        """
        try:
            self.monitor.clear_old_data(hours=hours)

            return {"success": True, "message": f"已清理 {hours} 小时前的旧数据"}

        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return {"success": False, "message": f"清理失败: {str(e)}"}


# 全局SNMP服务实例
snmp_service = SNMPService()
