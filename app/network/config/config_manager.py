"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_manager_fixed.py
@DateTime: 2025-06-17
@Docs: 配置管理器，统一处理配置管理操作
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.device_service import DeviceService
from app.utils.logger import logger

from .config_operations import ConfigOperationType, ConfigStatus
from .config_tasks import (
    ConfigBackupTask,
    ConfigDeployTask,
    ConfigDiffTask,
    ConfigRollbackTask,
)


class ConfigOperation:
    """简化的配置操作记录"""

    def __init__(self, operation_id: str, device_id: int, operation_type: ConfigOperationType):
        self.operation_id = operation_id
        self.device_id = device_id
        self.operation_type = operation_type
        self.status = ConfigStatus.PENDING
        self.config_content: str | None = None
        self.backup_path: str | None = None
        self.error_message: str | None = None
        self.created_at = datetime.now()
        self.completed_at: datetime | None = None
        self.metadata: dict[str, Any] = {}


class ConfigManager:
    """配置管理器

    提供统一的配置管理接口，包括备份、部署、差异比较、回滚等功能
    """

    def __init__(self, backup_dir: str = "./config_backups"):
        """初始化配置管理器

        Args:
            backup_dir: 备份文件目录
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.device_service = DeviceService()
        self._operations: dict[str, ConfigOperation] = {}

    async def backup_device_config(self, device_id: int) -> dict[str, Any]:
        """备份单个设备配置

        Args:
            device_id: 设备ID

        Returns:
            dict: 备份结果
        """
        # 获取设备信息
        device = await self.device_service.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")

        # 创建备份任务
        backup_task = ConfigBackupTask(device, str(self.backup_dir))

        # 记录操作
        operation = ConfigOperation(
            operation_id=f"backup_{device_id}_{int(datetime.now().timestamp())}",
            device_id=device_id,
            operation_type=ConfigOperationType.BACKUP,
        )
        operation.status = ConfigStatus.RUNNING
        self._operations[operation.operation_id] = operation

        try:
            # 执行备份
            result = await backup_task.execute()

            # 更新操作状态
            operation.status = ConfigStatus.SUCCESS
            operation.backup_path = result.backup_path
            operation.completed_at = datetime.now()
            operation.metadata = {"file_size": result.file_size, "checksum": result.checksum}

            logger.info(f"设备 {device_id} 配置备份完成: {result.backup_path}")

            return {
                "operation_id": operation.operation_id,
                "device_id": device_id,
                "backup_path": result.backup_path,
                "file_size": result.file_size,
                "checksum": result.checksum,
                "backup_time": result.backup_time.isoformat(),
            }

        except Exception as e:
            # 更新操作状态
            operation.status = ConfigStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()

            logger.error(f"设备 {device_id} 配置备份失败: {e}")
            raise

    async def backup_multiple_devices(self, device_ids: list[int]) -> dict[str, Any]:
        """批量备份多个设备配置

        Args:
            device_ids: 设备ID列表

        Returns:
            dict: 批量备份结果
        """
        logger.info(f"开始批量备份 {len(device_ids)} 个设备的配置")

        # 创建异步任务
        tasks = []
        for device_id in device_ids:
            task = asyncio.create_task(self.backup_device_config(device_id))
            tasks.append((device_id, task))

        # 等待所有任务完成
        results = []
        errors = []

        for device_id, task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                errors.append({"device_id": device_id, "error": str(e)})

        logger.info(f"批量备份完成，成功: {len(results)}, 失败: {len(errors)}")

        return {
            "total": len(device_ids),
            "success": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    async def deploy_config(self, device_id: int, config_content: str, dry_run: bool = False) -> dict[str, Any]:
        """部署配置到设备

        Args:
            device_id: 设备ID
            config_content: 配置内容
            dry_run: 是否只是测试而不实际部署

        Returns:
            dict: 部署结果
        """
        # 获取设备信息
        device = await self.device_service.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")

        # 创建部署任务
        deploy_task = ConfigDeployTask(device, config_content, str(self.backup_dir))

        # 记录操作
        operation = ConfigOperation(
            operation_id=f"deploy_{device_id}_{int(datetime.now().timestamp())}",
            device_id=device_id,
            operation_type=ConfigOperationType.DEPLOY,
        )
        operation.status = ConfigStatus.RUNNING
        operation.config_content = config_content
        self._operations[operation.operation_id] = operation

        try:
            # 执行部署
            result = await deploy_task.execute(dry_run=dry_run)

            # 更新操作状态
            if result.success:
                operation.status = ConfigStatus.SUCCESS
            else:
                operation.status = ConfigStatus.FAILED
                operation.error_message = str(result.error_details)

            operation.completed_at = datetime.now()
            operation.metadata = {
                "deployed_commands": len(result.deployed_commands),
                "failed_commands": len(result.failed_commands),
                "dry_run": dry_run,
            }

            logger.info(f"设备 {device_id} 配置部署{'(测试)' if dry_run else ''}完成: {result.success}")

            return {
                "operation_id": operation.operation_id,
                "device_id": device_id,
                "success": result.success,
                "deployed_commands": result.deployed_commands,
                "failed_commands": result.failed_commands,
                "error_details": result.error_details,
                "deploy_time": result.deploy_time.isoformat(),
                "dry_run": dry_run,
            }

        except Exception as e:
            # 更新操作状态
            operation.status = ConfigStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()

            logger.error(f"设备 {device_id} 配置部署失败: {e}")
            raise

    async def compare_config(self, device_id: int, target_config: str) -> dict[str, Any]:
        """比较设备当前配置与目标配置的差异

        Args:
            device_id: 设备ID
            target_config: 目标配置内容

        Returns:
            dict: 差异比较结果
        """
        # 获取设备信息
        device = await self.device_service.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")

        # 创建差异比较任务
        diff_task = ConfigDiffTask(device, target_config, str(self.backup_dir))

        # 记录操作
        operation = ConfigOperation(
            operation_id=f"diff_{device_id}_{int(datetime.now().timestamp())}",
            device_id=device_id,
            operation_type=ConfigOperationType.DIFF,
        )
        operation.status = ConfigStatus.RUNNING
        operation.config_content = target_config
        self._operations[operation.operation_id] = operation

        try:
            # 执行差异比较
            result = await diff_task.execute()

            # 更新操作状态
            operation.status = ConfigStatus.SUCCESS
            operation.completed_at = datetime.now()
            operation.metadata = {
                "additions": len(result.additions),
                "deletions": len(result.deletions),
                "changes": len(result.changes),
            }

            logger.info(f"设备 {device_id} 配置差异比较完成")

            return {
                "operation_id": operation.operation_id,
                "device_id": device_id,
                "current_config": result.current_config,
                "target_config": result.target_config,
                "diff_lines": result.diff_lines,
                "additions": result.additions,
                "deletions": result.deletions,
                "changes": result.changes,
            }

        except Exception as e:
            # 更新操作状态
            operation.status = ConfigStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()

            logger.error(f"设备 {device_id} 配置差异比较失败: {e}")
            raise

    async def rollback_config(self, device_id: int, backup_path: str) -> dict[str, Any]:
        """回滚设备配置到指定备份

        Args:
            device_id: 设备ID
            backup_path: 备份文件路径

        Returns:
            dict: 回滚结果
        """
        # 获取设备信息
        device = await self.device_service.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")

        # 验证备份文件
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")

        # 创建回滚任务
        rollback_task = ConfigRollbackTask(device, backup_path, str(self.backup_dir))

        # 记录操作
        operation = ConfigOperation(
            operation_id=f"rollback_{device_id}_{int(datetime.now().timestamp())}",
            device_id=device_id,
            operation_type=ConfigOperationType.ROLLBACK,
        )
        operation.status = ConfigStatus.RUNNING
        operation.backup_path = backup_path
        self._operations[operation.operation_id] = operation

        try:
            # 执行回滚
            result = await rollback_task.execute()

            # 更新操作状态
            if result.success:
                operation.status = ConfigStatus.SUCCESS
            else:
                operation.status = ConfigStatus.FAILED
                operation.error_message = str(result.error_details)

            operation.completed_at = datetime.now()
            operation.metadata = {
                "backup_path": backup_path,
                "deployed_commands": len(result.deployed_commands),
                "failed_commands": len(result.failed_commands),
            }

            logger.info(f"设备 {device_id} 配置回滚完成: {result.success}")

            return {
                "operation_id": operation.operation_id,
                "device_id": device_id,
                "success": result.success,
                "backup_path": backup_path,
                "deployed_commands": result.deployed_commands,
                "failed_commands": result.failed_commands,
                "error_details": result.error_details,
                "rollback_time": result.deploy_time.isoformat(),
            }

        except Exception as e:
            # 更新操作状态
            operation.status = ConfigStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()

            logger.error(f"设备 {device_id} 配置回滚失败: {e}")
            raise

    def get_operation_status(self, operation_id: str) -> dict[str, Any] | None:
        """获取操作状态

        Args:
            operation_id: 操作ID

        Returns:
            dict: 操作状态信息，如果操作不存在返回None
        """
        operation = self._operations.get(operation_id)
        if not operation:
            return None

        return {
            "operation_id": operation.operation_id,
            "device_id": operation.device_id,
            "operation_type": operation.operation_type.value,
            "status": operation.status.value,
            "created_at": operation.created_at.isoformat(),
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "error_message": operation.error_message,
            "metadata": operation.metadata,
        }

    def list_operations(self, device_id: int | None = None) -> list[dict[str, Any]]:
        """列出操作记录

        Args:
            device_id: 可选，过滤指定设备的操作

        Returns:
            list: 操作记录列表
        """
        operations = list(self._operations.values())

        if device_id is not None:
            operations = [op for op in operations if op.device_id == device_id]

        # 按创建时间倒序排列
        operations.sort(key=lambda x: x.created_at, reverse=True)

        return [
            {
                "operation_id": op.operation_id,
                "device_id": op.device_id,
                "operation_type": op.operation_type.value,
                "status": op.status.value,
                "created_at": op.created_at.isoformat(),
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "error_message": op.error_message,
                "metadata": op.metadata,
            }
            for op in operations
        ]

    def list_backups(self, device_id: int | None = None) -> list[dict[str, Any]]:
        """列出备份文件

        Args:
            device_id: 可选，过滤指定设备的备份

        Returns:
            list: 备份文件列表
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.cfg"):
            try:
                # 解析文件名获取设备信息
                # 格式: hostname_timestamp_suffix.cfg
                parts = backup_file.stem.split("_")
                if len(parts) >= 2:
                    # 获取文件信息
                    stat = backup_file.stat()

                    backup_info = {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size": stat.st_size,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }

                    # 如果指定了设备ID，则需要匹配
                    if device_id is not None:
                        # 这里可以根据实际需求实现设备ID与文件名的匹配逻辑
                        # 暂时添加所有备份文件
                        pass

                    backups.append(backup_info)

            except Exception as e:
                logger.warning(f"解析备份文件 {backup_file} 失败: {e}")
                continue
        # 按修改时间倒序排列，确保以字符串类型排序，避免类型错误
        backups.sort(key=lambda x: x["modified_time"], reverse=True)
        return backups
