"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_tasks.py
@DateTime: 2025-06-17
@Docs: 配置管理任务实现
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from scrapli import AsyncScrapli
from scrapli_cfg import AsyncScrapliCfg

from app.models.data_models import Device
from app.network.adapters.h3c import H3CAdapter
from app.utils.logger import logger

from .config_operations import (
    ConfigBackupResult,
    ConfigDeployResult,
    ConfigDiff,
    ConfigOperations,
)


class ConfigTask:
    """配置任务基类"""

    def __init__(self, device: Device, backup_dir: str = "./config_backups"):
        """初始化配置任务

        Args:
            device: 设备对象
            backup_dir: 备份目录
        """
        self.device = device
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> H3CAdapter:
        """获取设备适配器"""
        # 基于设备品牌关系获取厂商信息
        if hasattr(self.device, "brand") and self.device.brand:
            brand_name = self.device.brand.name.lower()
            if brand_name in ["h3c", "huawei"]:
                return H3CAdapter()
        # 可以扩展其他厂商适配器
        return H3CAdapter()  # 默认使用H3C适配器

    def _get_scrapli_connection_args(self) -> dict[str, Any]:
        """获取scrapli连接参数"""
        platform_map = {
            "h3c": "huawei_vrp",
            "huawei": "huawei_vrp",
            "cisco": "cisco_iosxe",
            "juniper": "juniper_junos",
        }

        # 默认平台
        platform = "huawei_vrp"
        if hasattr(self.device, "brand") and self.device.brand:
            platform = platform_map.get(self.device.brand.name.lower(), "huawei_vrp")

        return {
            "host": self.device.management_ip,
            "auth_username": self.device.account,
            "auth_password": self.device.password,
            "auth_strict_key": False,
            "platform": platform,
            "transport": "asyncssh",
            "timeout_socket": 30,
            "timeout_transport": 30,
        }

    def _generate_backup_filename(self, suffix: str = "") -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hostname = self.device.hostname or self.device.name
        if suffix:
            return f"{hostname}_{timestamp}_{suffix}.cfg"
        return f"{hostname}_{timestamp}.cfg"

    def _calculate_checksum(self, content: str) -> str:
        """计算内容校验和"""
        return hashlib.md5(content.encode()).hexdigest()


class ConfigBackupTask(ConfigTask):
    """配置备份任务"""

    async def execute(self) -> ConfigBackupResult:
        """执行配置备份"""
        operation_id = str(uuid.uuid4())
        hostname = self.device.hostname or self.device.name
        logger.info(f"开始备份设备 {hostname} 配置，操作ID: {operation_id}")

        try:
            conn_args = self._get_scrapli_connection_args()

            async with AsyncScrapli(**conn_args) as conn:
                # 获取配置内容
                response = await conn.send_command("display current-configuration")
                config_content = response.result

                if not config_content:
                    raise ValueError("获取到的配置内容为空")

                # 标准化配置内容
                brand_name = "generic"
                if hasattr(self.device, "brand") and self.device.brand:
                    brand_name = self.device.brand.name.lower()

                normalized_config = ConfigOperations.normalize_config(config_content, brand_name)

                # 保存到文件
                backup_filename = self._generate_backup_filename("backup")
                backup_path = self.backup_dir / backup_filename

                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(normalized_config)

                # 计算文件信息
                file_size = backup_path.stat().st_size
                checksum = self._calculate_checksum(normalized_config)

                logger.info(f"设备 {hostname} 配置备份完成，文件: {backup_path}")

                return ConfigBackupResult(
                    device_id=self.device.id,
                    backup_path=str(backup_path),
                    config_content=normalized_config,
                    file_size=file_size,
                    checksum=checksum,
                )

        except Exception as e:
            logger.error(f"设备 {hostname} 配置备份失败: {e}")
            raise


class ConfigDeployTask(ConfigTask):
    """配置部署任务"""

    def __init__(self, device: Device, config_content: str, backup_dir: str = "./config_backups"):
        """初始化配置部署任务

        Args:
            device: 设备对象
            config_content: 要部署的配置内容
            backup_dir: 备份目录
        """
        super().__init__(device, backup_dir)
        self.config_content = config_content

    async def execute(self, dry_run: bool = False) -> ConfigDeployResult:
        """执行配置部署

        Args:
            dry_run: 是否只是测试而不实际部署

        Returns:
            ConfigDeployResult: 部署结果
        """
        operation_id = str(uuid.uuid4())
        hostname = self.device.hostname or self.device.name
        logger.info(f"开始部署配置到设备 {hostname}，操作ID: {operation_id}")

        try:
            # 先备份当前配置
            backup_task = ConfigBackupTask(self.device, str(self.backup_dir))
            backup_result = await backup_task.execute()
            logger.info(f"部署前备份完成: {backup_result.backup_path}")

            # 验证配置语法
            brand_name = "generic"
            if hasattr(self.device, "brand") and self.device.brand:
                brand_name = self.device.brand.name.lower()

            validation = ConfigOperations.validate_config_syntax(self.config_content, brand_name)

            if not validation.is_valid:
                raise ValueError(f"配置语法验证失败: {validation.syntax_errors}")

            if validation.warnings:
                logger.warning(f"配置验证警告: {validation.warnings}")

            conn_args = self._get_scrapli_connection_args()

            # 如果是dry_run，只返回预期结果
            if dry_run:
                commands = self.config_content.splitlines()
                return ConfigDeployResult(
                    device_id=self.device.id,
                    operation_id=operation_id,
                    success=True,
                    deployed_commands=commands,
                    failed_commands=[],
                    error_details={},
                )

            # 使用scrapli-cfg进行配置部署
            async with AsyncScrapliCfg(conn=AsyncScrapli(**conn_args), dedicated_connection=True) as cfg_conn:
                # 加载配置
                response = await cfg_conn.load_config(config=self.config_content)

                if not response.failed:
                    # 提交配置
                    commit_response = await cfg_conn.commit_config()

                    if commit_response.failed:
                        raise ValueError(f"配置提交失败: {commit_response.result}")

                    deployed_commands = self.config_content.splitlines()

                    logger.info(f"设备 {hostname} 配置部署成功")

                    return ConfigDeployResult(
                        device_id=self.device.id,
                        operation_id=operation_id,
                        success=True,
                        deployed_commands=deployed_commands,
                        failed_commands=[],
                        error_details={},
                    )
                else:
                    raise ValueError(f"配置加载失败: {response.result}")

        except Exception as e:
            logger.error(f"设备 {hostname} 配置部署失败: {e}")

            return ConfigDeployResult(
                device_id=self.device.id,
                operation_id=operation_id,
                success=False,
                deployed_commands=[],
                failed_commands=self.config_content.splitlines(),
                error_details={"error": str(e)},
            )


class ConfigDiffTask(ConfigTask):
    """配置差异比较任务"""

    def __init__(self, device: Device, target_config: str, backup_dir: str = "./config_backups"):
        """初始化配置差异比较任务

        Args:
            device: 设备对象
            target_config: 目标配置内容
            backup_dir: 备份目录
        """
        super().__init__(device, backup_dir)
        self.target_config = target_config

    async def execute(self) -> ConfigDiff:
        """执行配置差异比较"""
        hostname = self.device.hostname or self.device.name
        logger.info(f"开始比较设备 {hostname} 配置差异")

        try:
            # 获取当前配置
            backup_task = ConfigBackupTask(self.device, str(self.backup_dir))
            backup_result = await backup_task.execute()
            current_config = backup_result.config_content

            # 生成差异
            diff_result = ConfigOperations.generate_config_diff(current_config, self.target_config)
            diff_result.device_id = self.device.id

            logger.info(f"设备 {hostname} 配置差异比较完成")
            return diff_result

        except Exception as e:
            logger.error(f"设备 {hostname} 配置差异比较失败: {e}")
            raise


class ConfigRollbackTask(ConfigTask):
    """配置回滚任务"""

    def __init__(self, device: Device, backup_path: str, backup_dir: str = "./config_backups"):
        """初始化配置回滚任务

        Args:
            device: 设备对象
            backup_path: 备份文件路径
            backup_dir: 备份目录
        """
        super().__init__(device, backup_dir)
        self.backup_path = Path(backup_path)

    async def execute(self) -> ConfigDeployResult:
        """执行配置回滚"""
        operation_id = str(uuid.uuid4())
        hostname = self.device.hostname or self.device.name
        logger.info(f"开始回滚设备 {hostname} 配置，操作ID: {operation_id}")

        try:
            # 验证备份文件是否存在
            if not self.backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {self.backup_path}")

            # 读取备份配置
            with open(self.backup_path, encoding="utf-8") as f:
                backup_config = f.read()

            # 使用部署任务执行回滚
            deploy_task = ConfigDeployTask(self.device, backup_config, str(self.backup_dir))
            result = await deploy_task.execute()

            # 更新操作ID为回滚操作
            result.operation_id = operation_id

            logger.info(f"设备 {hostname} 配置回滚完成")
            return result

        except Exception as e:
            logger.error(f"设备 {hostname} 配置回滚失败: {e}")
            raise
