"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_operations.py
@DateTime: 2025-06-17
@Docs: 配置操作基础类
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConfigStatus(str, Enum):
    """配置状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLBACK = "rollback"


class ConfigOperationType(str, Enum):
    """配置操作类型"""

    BACKUP = "backup"
    DEPLOY = "deploy"
    DIFF = "diff"
    ROLLBACK = "rollback"
    VALIDATE = "validate"


class ConfigOperation(BaseModel):
    """配置操作基础模型"""

    operation_id: str = Field(description="操作ID")
    device_id: int = Field(description="设备ID")
    operation_type: ConfigOperationType = Field(description="操作类型")
    status: ConfigStatus = Field(default=ConfigStatus.PENDING, description="操作状态")
    config_content: str | None = Field(None, description="配置内容")
    backup_path: str | None = Field(None, description="备份路径")
    error_message: str | None = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class ConfigDiff(BaseModel):
    """配置差异模型"""

    device_id: int = Field(description="设备ID")
    current_config: str = Field(description="当前配置")
    target_config: str = Field(description="目标配置")
    diff_lines: list[str] = Field(description="差异行")
    additions: list[str] = Field(default_factory=list, description="新增行")
    deletions: list[str] = Field(default_factory=list, description="删除行")
    changes: list[str] = Field(default_factory=list, description="修改行")


class ConfigBackupResult(BaseModel):
    """配置备份结果"""

    device_id: int = Field(description="设备ID")
    backup_path: str = Field(description="备份文件路径")
    config_content: str = Field(description="配置内容")
    backup_time: datetime = Field(default_factory=datetime.now, description="备份时间")
    file_size: int = Field(description="文件大小")
    checksum: str | None = Field(None, description="文件校验和")


class ConfigDeployResult(BaseModel):
    """配置部署结果"""

    device_id: int = Field(description="设备ID")
    operation_id: str = Field(description="操作ID")
    success: bool = Field(description="是否成功")
    deployed_commands: list[str] = Field(description="已部署命令")
    failed_commands: list[str] = Field(default_factory=list, description="失败命令")
    error_details: dict[str, str] = Field(default_factory=dict, description="错误详情")
    deploy_time: datetime = Field(default_factory=datetime.now, description="部署时间")


class ConfigValidationResult(BaseModel):
    """配置验证结果"""

    device_id: int = Field(description="设备ID")
    is_valid: bool = Field(description="配置是否有效")
    syntax_errors: list[str] = Field(default_factory=list, description="语法错误")
    warnings: list[str] = Field(default_factory=list, description="警告信息")
    validation_time: datetime = Field(default_factory=datetime.now, description="验证时间")


class ConfigOperations:
    """配置操作工具类"""

    @staticmethod
    def generate_config_diff(current: str, target: str) -> ConfigDiff:
        """生成配置差异

        Args:
            current: 当前配置
            target: 目标配置

        Returns:
            ConfigDiff: 配置差异对象
        """
        current_lines = current.splitlines()
        target_lines = target.splitlines()

        # 简单的差异比较（实际生产中可以使用更复杂的diff算法）
        additions = []
        deletions = []
        changes = []

        # 找出新增和删除的行
        current_set = set(current_lines)
        target_set = set(target_lines)

        additions = list(target_set - current_set)
        deletions = list(current_set - target_set)

        # 生成差异行（简化版）
        diff_lines = []
        for line in deletions:
            diff_lines.append(f"- {line}")
        for line in additions:
            diff_lines.append(f"+ {line}")

        return ConfigDiff(
            device_id=0,  # 会在调用时设置
            current_config=current,
            target_config=target,
            diff_lines=diff_lines,
            additions=additions,
            deletions=deletions,
            changes=changes,
        )

    @staticmethod
    def validate_config_syntax(config_content: str, platform: str = "generic") -> ConfigValidationResult:
        """验证配置语法

        Args:
            config_content: 配置内容
            platform: 平台类型

        Returns:
            ConfigValidationResult: 验证结果
        """
        syntax_errors = []
        warnings = []

        # 基础验证规则（可根据平台扩展）
        lines = config_content.splitlines()

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue

            # 检查基本语法错误
            if line.endswith(" "):
                warnings.append(f"Line {i}: Trailing whitespace")

            # 平台特定验证
            if platform.lower() in ["h3c", "huawei"]:
                if line.startswith("interface") and not line.replace("interface", "").strip():
                    syntax_errors.append(f"Line {i}: Interface name missing")

        return ConfigValidationResult(
            device_id=0,  # 会在调用时设置
            is_valid=len(syntax_errors) == 0,
            syntax_errors=syntax_errors,
            warnings=warnings,
        )

    @staticmethod
    def normalize_config(config_content: str, platform: str = "generic") -> str:
        """标准化配置内容

        Args:
            config_content: 原始配置内容
            platform: 平台类型

        Returns:
            str: 标准化后的配置内容
        """
        lines = config_content.splitlines()
        normalized_lines = []

        for line in lines:
            # 移除行尾空白
            line = line.rstrip()

            # 跳过空行
            if not line:
                continue

            # 跳过注释行（根据平台调整）
            if line.strip().startswith(("#", "!")):
                continue

            normalized_lines.append(line)

        return "\n".join(normalized_lines)
