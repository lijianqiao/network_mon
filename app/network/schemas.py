"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: schemas.py
@DateTime: 2025/06/17 21:14:29
@Docs: 数据模型和验证
"""

from pydantic import BaseModel, Field


# 请求模型
class CreateSessionRequest(BaseModel):
    """创建会话请求"""

    device_id: int
    user_id: str | None = None


class ExecuteCommandRequest(BaseModel):
    """执行命令请求"""

    session_id: str
    command: str


class SendConfigurationRequest(BaseModel):
    """发送配置请求"""

    session_id: str
    config_lines: list[str]


class CloseSessionRequest(BaseModel):
    """关闭会话请求"""

    session_id: str


class ConfigBackupRequest(BaseModel):
    """配置备份请求模型"""

    device_ids: list[int] = Field(description="设备ID列表")


class ConfigDeployRequest(BaseModel):
    """配置部署请求模型"""

    device_id: int = Field(description="设备ID")
    config_content: str = Field(description="配置内容")
    dry_run: bool = Field(default=False, description="是否为测试部署")


class ConfigDiffRequest(BaseModel):
    """配置差异比较请求模型"""

    device_id: int = Field(description="设备ID")
    target_config: str = Field(description="目标配置内容")


class ConfigRollbackRequest(BaseModel):
    """配置回滚请求模型"""

    device_id: int = Field(description="设备ID")
    backup_path: str = Field(description="备份文件路径")


class MonitoringStartRequest(BaseModel):
    """监控启动请求模型"""

    poll_interval: int = Field(default=60, description="轮询间隔（秒）", ge=10, le=3600)


class ThresholdUpdateRequest(BaseModel):
    """阈值更新请求模型"""

    cpu_usage: float | None = Field(None, description="CPU使用率阈值", ge=0, le=100)
    memory_usage: float | None = Field(None, description="内存使用率阈值", ge=0, le=100)
    interface_down_count: int | None = Field(None, description="接口Down数量阈值", ge=0)
