"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: data_models.py
@DateTime: 2025-06-17
@Docs: 网络自动化平台核心数据模型，简化设计只保留必要功能
"""

from tortoise import fields
from tortoise.models import Model

from .data_enum import (
    ActionEnum,
    AlertStatusEnum,
    AlertTypeEnum,
    ConnectionTypeEnum,
    DeviceStatusEnum,
    DeviceTypeEnum,
    LogLevelEnum,
    MetricStatusEnum,
    MetricTypeEnum,
    OperationResultEnum,
    ResourceTypeEnum,
    SeverityEnum,
    TemplateTypeEnum,
)


class BaseModel(Model):
    """基础模型类

    提供所有业务模型的公共字段
    """

    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间", db_index=True)
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    is_deleted = fields.BooleanField(default=False, description="是否已删除", db_index=True)

    class Meta:  # type: ignore
        abstract = True


# ================================ 设备相关模型 ================================


class Brand(BaseModel):
    """设备品牌表"""

    name = fields.CharField(max_length=50, unique=True, description="品牌名称")  # 华三、华为、思科
    code = fields.CharField(max_length=20, unique=True, description="品牌代码", db_index=True)  # H3C、HUAWEI、CISCO
    description = fields.TextField(null=True, description="品牌描述")
    is_active = fields.BooleanField(default=True, description="是否启用", db_index=True)

    class Meta:  # type: ignore
        table = "brands"
        table_description = "设备品牌表"
        indexes = [("name", "is_active")]


class DeviceModel(BaseModel):
    """设备型号表"""

    name = fields.CharField(max_length=100, description="型号名称", db_index=True)  # S5560-32C-EI
    brand = fields.ForeignKeyField("models.Brand", related_name="device_models", description="所属品牌")
    device_type = fields.CharEnumField(DeviceTypeEnum, description="设备类型", db_index=True)
    description = fields.TextField(null=True, description="型号描述")
    is_active = fields.BooleanField(default=True, description="是否启用", db_index=True)

    class Meta:  # type: ignore
        table = "device_models"
        table_description = "设备型号表"
        unique_together = (("brand", "name"),)
        indexes = [("brand", "device_type")]


class Area(BaseModel):
    """区域表"""

    name = fields.CharField(max_length=100, unique=True, description="区域名称")  # 北京、上海、广州
    code = fields.CharField(max_length=20, unique=True, description="区域代码", db_index=True)  # BJ、SH、GZ
    parent = fields.ForeignKeyField("models.Area", null=True, related_name="children", description="父级区域")
    description = fields.TextField(null=True, description="区域描述")
    is_active = fields.BooleanField(default=True, description="是否启用", db_index=True)

    class Meta:  # type: ignore
        table = "areas"
        table_description = "区域表"
        indexes = [("parent", "name")]


class DeviceGroup(BaseModel):
    """设备分组表"""

    name = fields.CharField(max_length=100, description="分组名称", db_index=True)
    description = fields.TextField(null=True, description="分组描述")
    area = fields.ForeignKeyField("models.Area", related_name="device_groups", description="所属区域")
    is_active = fields.BooleanField(default=True, description="是否启用", db_index=True)

    class Meta:  # type: ignore
        table = "device_groups"
        table_description = "设备分组表"
        indexes = [("area", "name")]


class Device(BaseModel):
    """设备表"""

    name = fields.CharField(max_length=100, description="设备名称", db_index=True)
    hostname = fields.CharField(max_length=100, null=True, description="主机名")
    management_ip = fields.CharField(max_length=15, unique=True, description="管理IP地址")
    port = fields.IntField(default=22, description="连接端口")
    account = fields.CharField(max_length=50, description="登录账号")
    password = fields.CharField(max_length=255, description="登录密码")  # AES加密存储
    enable_password = fields.CharField(max_length=255, null=True, description="特权模式密码")
    connection_type = fields.CharEnumField(ConnectionTypeEnum, default=ConnectionTypeEnum.SSH, description="连接类型")
    brand = fields.ForeignKeyField("models.Brand", related_name="devices", description="设备品牌")
    device_model = fields.ForeignKeyField(
        "models.DeviceModel", null=True, related_name="devices", description="设备型号"
    )
    area = fields.ForeignKeyField("models.Area", related_name="devices", description="所属区域")
    device_group = fields.ForeignKeyField(
        "models.DeviceGroup", null=True, related_name="devices", description="所属分组"
    )
    status = fields.CharEnumField(
        DeviceStatusEnum, default=DeviceStatusEnum.UNKNOWN, description="设备状态", db_index=True
    )
    last_check_time = fields.DatetimeField(null=True, description="最后检查时间", db_index=True)
    version = fields.CharField(max_length=100, null=True, description="系统版本")
    serial_number = fields.CharField(max_length=100, null=True, description="序列号")
    description = fields.TextField(null=True, description="设备描述")
    is_active = fields.BooleanField(default=True, description="是否启用", db_index=True)

    class Meta:  # type: ignore
        table = "devices"
        table_description = "设备表"
        indexes = [
            ("brand", "status"),
            ("area", "status"),
            ("device_group", "status"),
        ]


# ================================ 配置模板 ================================


class ConfigTemplate(BaseModel):
    """配置模板表"""

    name = fields.CharField(max_length=100, unique=True, description="模板名称")
    brand = fields.ForeignKeyField("models.Brand", null=True, related_name="config_templates", description="适用品牌")
    device_type = fields.CharEnumField(DeviceTypeEnum, null=True, description="适用设备类型", db_index=True)
    template_type = fields.CharEnumField(TemplateTypeEnum, description="模板类型", db_index=True)
    content = fields.TextField(description="模板内容")  # 支持变量替换
    variables = fields.JSONField(null=True, description="模板变量定义")
    description = fields.TextField(null=True, description="模板描述")
    is_active = fields.BooleanField(default=True, description="是否启用", db_index=True)

    class Meta:  # type: ignore
        table = "config_templates"
        table_description = "配置模板表"
        indexes = [("brand", "template_type")]


# ================================ 监控相关模型 ================================


class MonitorMetric(BaseModel):
    """监控指标表"""

    device = fields.ForeignKeyField("models.Device", related_name="metrics", description="关联设备")
    metric_type = fields.CharEnumField(MetricTypeEnum, description="指标类型", db_index=True)
    metric_name = fields.CharField(max_length=100, description="指标名称")  # CPU使用率、内存使用率
    value = fields.FloatField(description="指标值")
    unit = fields.CharField(max_length=20, null=True, description="指标单位")  # %、MB、°C
    threshold_warning = fields.FloatField(null=True, description="告警阈值")
    threshold_critical = fields.FloatField(null=True, description="严重告警阈值")
    status = fields.CharEnumField(MetricStatusEnum, default=MetricStatusEnum.NORMAL, description="指标状态", db_index=True)
    collected_at = fields.DatetimeField(description="采集时间", db_index=True)

    class Meta:  # type: ignore
        table = "monitor_metrics"
        table_description = "监控指标表"
        indexes = [
            ("device", "metric_type", "collected_at"),
            ("status", "collected_at"),
        ]


class Alert(BaseModel):
    """告警表"""

    device = fields.ForeignKeyField("models.Device", related_name="alerts", description="关联设备")
    alert_type = fields.CharEnumField(AlertTypeEnum, description="告警类型", db_index=True)
    severity = fields.CharEnumField(SeverityEnum, description="告警级别", db_index=True)
    title = fields.CharField(max_length=200, description="告警标题")
    message = fields.TextField(description="告警消息")
    metric_name = fields.CharField(max_length=100, null=True, description="相关指标名称")
    current_value = fields.FloatField(null=True, description="当前值")
    threshold_value = fields.FloatField(null=True, description="阈值")
    status = fields.CharEnumField(AlertStatusEnum, default=AlertStatusEnum.ACTIVE, description="告警状态", db_index=True)
    acknowledged_by = fields.CharField(max_length=50, null=True, description="确认人")
    acknowledged_at = fields.DatetimeField(null=True, description="确认时间")
    resolved_at = fields.DatetimeField(null=True, description="解决时间")

    class Meta:  # type: ignore
        table = "alerts"
        table_description = "告警表"
        unique_together = (("device", "title", "created_at"),)  # 同一设备同一时间的告警标题唯一
        indexes = [
            ("device", "status"),
            ("severity", "status", "created_at"),
        ]


# ================================ 日志相关模型 ================================


class OperationLog(BaseModel):
    """操作日志表"""

    user = fields.CharField(max_length=50, null=True, description="操作用户", db_index=True)
    action = fields.CharEnumField(ActionEnum, description="操作动作", db_index=True)
    resource_type = fields.CharEnumField(ResourceTypeEnum, description="资源类型", db_index=True)
    resource_id = fields.CharField(max_length=50, null=True, description="资源ID")
    resource_name = fields.CharField(max_length=200, null=True, description="资源名称")
    details = fields.JSONField(null=True, description="操作详情")
    ip_address = fields.CharField(max_length=45, null=True, description="操作IP地址")
    result = fields.CharEnumField(
        OperationResultEnum, default=OperationResultEnum.SUCCESS, description="操作结果", db_index=True
    )
    error_message = fields.TextField(null=True, description="错误信息")
    execution_time = fields.FloatField(null=True, description="执行耗时(秒)")

    class Meta:  # type: ignore
        table = "operation_logs"
        table_description = "操作日志表"
        indexes = [
            ("user", "created_at"),
            ("action", "result", "created_at"),
        ]


class SystemLog(BaseModel):
    """系统日志表"""

    level = fields.CharEnumField(LogLevelEnum, description="日志级别", db_index=True)
    logger_name = fields.CharField(max_length=100, description="日志记录器名称")
    module = fields.CharField(max_length=100, null=True, description="模块名称", db_index=True)
    message = fields.TextField(description="日志消息内容")
    exception_info = fields.TextField(null=True, description="异常信息")
    extra_data = fields.JSONField(null=True, description="额外数据")

    class Meta:  # type: ignore
        table = "system_logs"
        table_description = "系统日志表"
        indexes = [
            ("level", "created_at"),
            ("module", "level", "created_at"),
        ]
