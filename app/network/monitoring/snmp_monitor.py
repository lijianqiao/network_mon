"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: snmp_monitor.py
@DateTime: 2025-06-17
@Docs: SNMP监控服务
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from app.models.data_models import Device
from app.services.device_service import DeviceService
from app.utils.logger import logger

from .snmp_collector import SNMPCollector


class SNMPMonitor:
    """SNMP监控服务

    定时轮询设备的SNMP数据，检测异常并触发告警
    """

    def __init__(self, poll_interval: int = 60, alert_thresholds: dict[str, float] | None = None):
        """初始化SNMP监控服务

        Args:
            poll_interval: 轮询间隔（秒）
            alert_thresholds: 告警阈值配置
        """
        self.poll_interval = poll_interval
        self.alert_thresholds = alert_thresholds or {"cpu_usage": 80.0, "memory_usage": 85.0, "interface_down_count": 2}

        self.device_service = DeviceService()
        self.snmp_collector = SNMPCollector()
        self.monitoring_data: dict[int, dict[str, Any]] = {}
        self.alerts: list[dict[str, Any]] = []
        self.is_running = False
        self._monitor_task: asyncio.Task | None = None

    async def start_monitoring(self) -> None:
        """开始监控"""
        if self.is_running:
            logger.warning("SNMP监控服务已经在运行")
            return

        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"SNMP监控服务已启动，轮询间隔: {self.poll_interval} 秒")

    async def stop_monitoring(self) -> None:
        """停止监控"""
        if not self.is_running:
            logger.warning("SNMP监控服务未在运行")
            return

        self.is_running = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("SNMP监控服务已停止")

    async def _monitor_loop(self) -> None:
        """监控主循环"""
        logger.info("SNMP监控主循环开始")

        while self.is_running:
            try:
                # 获取所有激活的设备
                devices = await self.device_service.list_all()
                active_devices = [d for d in devices if d.is_active]

                logger.info(f"开始监控 {len(active_devices)} 个设备")

                # 并发监控所有设备
                tasks = []
                for device in active_devices:
                    task = asyncio.create_task(self._monitor_single_device(device))
                    tasks.append(task)

                # 等待所有监控任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果和异常
                success_count = 0
                error_count = 0

                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_count += 1
                        logger.error(f"监控设备 {active_devices[i].id} 失败: {result}")
                    else:
                        success_count += 1

                logger.info(f"监控周期完成，成功: {success_count}, 失败: {error_count}")

                # 等待下一个轮询周期
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("监控循环被取消")
                break
            except Exception as e:
                logger.error(f"监控循环发生错误: {e}")
                await asyncio.sleep(10)  # 错误时短暂等待后重试

    async def _monitor_single_device(self, device: Device) -> dict[str, Any]:
        """监控单个设备

        Args:
            device: 设备对象

        Returns:
            dict: 监控结果
        """
        try:
            # 收集SNMP数据
            monitoring_data = await self.snmp_collector.collect_all_metrics(device)

            # 存储监控数据
            self.monitoring_data[device.id] = monitoring_data

            # 检查告警条件
            alerts = self._check_alerts(device, monitoring_data)

            # 存储告警
            for alert in alerts:
                self.alerts.append(alert)
                logger.warning(f"设备 {device.id} 触发告警: {alert['message']}")

            return {"device_id": device.id, "success": True, "monitoring_data": monitoring_data, "alerts": alerts}

        except Exception as e:
            logger.error(f"监控设备 {device.id} 失败: {e}")
            return {"device_id": device.id, "success": False, "error": str(e)}

    def _check_alerts(self, device: Device, data: dict[str, Any]) -> list[dict[str, Any]]:
        """检查告警条件

        Args:
            device: 设备对象
            data: 监控数据

        Returns:
            list: 告警列表
        """
        alerts = []
        timestamp = datetime.now()

        # 检查性能指标告警
        if "performance_metrics" in data and "performance_metrics" in data["performance_metrics"]:
            metrics = data["performance_metrics"]["performance_metrics"]

            # CPU使用率告警
            if metrics.get("cpu_usage") and metrics["cpu_usage"] > self.alert_thresholds["cpu_usage"]:
                alerts.append(
                    {
                        "device_id": device.id,
                        "alert_type": "cpu_high",
                        "severity": "warning",
                        "message": f"CPU使用率过高: {metrics['cpu_usage']}%",
                        "value": metrics["cpu_usage"],
                        "threshold": self.alert_thresholds["cpu_usage"],
                        "timestamp": timestamp.isoformat(),
                    }
                )

            # 内存使用率告警
            if metrics.get("memory_usage") and metrics["memory_usage"] > self.alert_thresholds["memory_usage"]:
                alerts.append(
                    {
                        "device_id": device.id,
                        "alert_type": "memory_high",
                        "severity": "warning",
                        "message": f"内存使用率过高: {metrics['memory_usage']}%",
                        "value": metrics["memory_usage"],
                        "threshold": self.alert_thresholds["memory_usage"],
                        "timestamp": timestamp.isoformat(),
                    }
                )

        # 检查接口状态告警
        if "interface_info" in data and "interfaces" in data["interface_info"]:
            interfaces = data["interface_info"]["interfaces"]
            down_interfaces = [iface for iface in interfaces if iface.get("ifOperStatus") == 2]

            if len(down_interfaces) > self.alert_thresholds["interface_down_count"]:
                alerts.append(
                    {
                        "device_id": device.id,
                        "alert_type": "interface_down",
                        "severity": "critical",
                        "message": f"多个接口处于Down状态: {len(down_interfaces)} 个",
                        "value": len(down_interfaces),
                        "threshold": self.alert_thresholds["interface_down_count"],
                        "timestamp": timestamp.isoformat(),
                        "details": [iface["ifDescr"] for iface in down_interfaces],
                    }
                )

        return alerts

    def get_device_status(self, device_id: int) -> dict[str, Any] | None:
        """获取设备当前状态

        Args:
            device_id: 设备ID

        Returns:
            dict: 设备状态信息，如果不存在返回None
        """
        return self.monitoring_data.get(device_id)

    def get_all_device_status(self) -> dict[int, dict[str, Any]]:
        """获取所有设备状态

        Returns:
            dict: 所有设备状态信息
        """
        return self.monitoring_data.copy()

    def get_recent_alerts(self, hours: int = 24, device_id: int | None = None) -> list[dict[str, Any]]:
        """获取最近的告警

        Args:
            hours: 时间范围（小时）
            device_id: 可选，过滤指定设备的告警

        Returns:
            list: 告警列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_alerts = []
        for alert in self.alerts:
            alert_time = datetime.fromisoformat(alert["timestamp"])

            # 时间范围过滤
            if alert_time < cutoff_time:
                continue

            # 设备过滤
            if device_id is not None and alert["device_id"] != device_id:
                continue

            filtered_alerts.append(alert)

        # 按时间倒序排列
        filtered_alerts.sort(key=lambda x: x["timestamp"], reverse=True)

        return filtered_alerts

    def get_monitoring_statistics(self) -> dict[str, Any]:
        """获取监控统计信息

        Returns:
            dict: 统计信息
        """
        total_devices = len(self.monitoring_data)
        recent_alerts = self.get_recent_alerts(hours=1)

        # 按设备分组统计告警
        device_alert_count = {}
        for alert in recent_alerts:
            device_id = alert["device_id"]
            device_alert_count[device_id] = device_alert_count.get(device_id, 0) + 1

        # 按告警类型统计
        alert_type_count = {}
        for alert in recent_alerts:
            alert_type = alert["alert_type"]
            alert_type_count[alert_type] = alert_type_count.get(alert_type, 0) + 1

        return {
            "total_monitored_devices": total_devices,
            "is_running": self.is_running,
            "poll_interval": self.poll_interval,
            "recent_alerts_1h": len(recent_alerts),
            "device_alert_count": device_alert_count,
            "alert_type_count": alert_type_count,
            "alert_thresholds": self.alert_thresholds,
        }

    def update_alert_thresholds(self, thresholds: dict[str, float]) -> None:
        """更新告警阈值

        Args:
            thresholds: 新的阈值配置
        """
        self.alert_thresholds.update(thresholds)
        logger.info(f"告警阈值已更新: {self.alert_thresholds}")

    def clear_old_data(self, hours: int = 24) -> None:
        """清理旧数据

        Args:
            hours: 保留时间（小时）
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 清理旧告警
        self.alerts = [alert for alert in self.alerts if datetime.fromisoformat(alert["timestamp"]) >= cutoff_time]

        logger.info(f"已清理 {hours} 小时前的旧数据")
