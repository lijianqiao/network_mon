"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025-06-17
@Docs: 网络自动化平台数据模型定义，包含所有业务实体模型
"""

from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):
    """基础模型类

    提供所有业务模型的公共字段：
    - id: 主键
    - created_at: 创建时间
    - updated_at: 更新时间
    - is_deleted: 软删除标记
    """

    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间", index=True)
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间", index=True)
    is_deleted = fields.BooleanField(default=False, description="是否已删除", index=True)

    class Meta:  # type: ignore
        abstract = True


# ================================ 设备相关模型 ================================


class Brand(BaseModel):
    """设备品牌表

    管理网络设备的品牌信息，如华三、华为、思科等
    """

    name = fields.CharField(max_length=50, unique=True, description="品牌名称")  # 华三、华为、思科
    code = fields.CharField(max_length=20, unique=True, description="品牌代码", index=True)  # H3C、HUAWEI、CISCO
    description = fields.TextField(null=True, description="品牌描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "brands"


class DeviceType(BaseModel):
    """设备类型表

    定义不同品牌下的设备类型，如交换机、路由器、防火墙等
    """

    name = fields.CharField(max_length=50, description="设备类型名称")  # 交换机、路由器、防火墙
    code = fields.CharField(max_length=20, description="设备类型代码", index=True)  # SWITCH、ROUTER、FIREWALL
    brand = fields.ForeignKeyField("models.Brand", related_name="device_types", description="所属品牌")
    description = fields.TextField(null=True, description="设备类型描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "device_types"
        unique_together = (("brand", "code"),)  # 同一品牌下设备类型代码唯一
        indexes = [
            ("brand", "is_active"),  # 品牌+状态复合索引
        ]


class Area(BaseModel):
    """区域表

    管理设备部署的地理区域，支持层级结构
    """

    name = fields.CharField(max_length=100, unique=True, description="区域名称")  # 北京、上海、广州
    code = fields.CharField(max_length=20, unique=True, description="区域代码", index=True)  # BJ、SH、GZ
    parent = fields.ForeignKeyField("models.Area", null=True, related_name="children", description="父级区域")
    description = fields.TextField(null=True, description="区域描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "areas"
        indexes = [
            ("parent", "is_active"),  # 父级区域+状态复合索引
        ]


class DeviceGroup(BaseModel):
    """设备分组表

    对设备进行逻辑分组管理，便于批量操作
    """

    name = fields.CharField(max_length=100, description="分组名称", index=True)
    description = fields.TextField(null=True, description="分组描述")
    area = fields.ForeignKeyField("models.Area", related_name="device_groups", description="所属区域")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "device_groups"
        indexes = [
            ("area", "is_active"),  # 区域+状态复合索引
        ]


class Device(BaseModel):
    """设备表

    网络设备的核心信息表，包含设备基本信息、连接参数、状态等
    """

    name = fields.CharField(max_length=100, description="设备名称", index=True)
    hostname = fields.CharField(max_length=100, null=True, description="主机名", index=True)
    management_ip = fields.CharField(max_length=15, unique=True, description="管理IP地址")
    port = fields.IntField(default=22, description="连接端口")  # SSH端口
    account = fields.CharField(max_length=50, description="登录账号")
    password = fields.CharField(max_length=255, description="登录密码")  # AES加密存储
    enable_password = fields.CharField(max_length=255, null=True, description="特权模式密码")  # 特权密码
    connection_type = fields.CharField(max_length=20, default="ssh", description="连接类型", index=True)  # ssh/telnet
    brand = fields.ForeignKeyField("models.Brand", related_name="devices", description="设备品牌")
    device_type = fields.ForeignKeyField("models.DeviceType", related_name="devices", description="设备类型")
    area = fields.ForeignKeyField("models.Area", related_name="devices", description="所属区域")
    device_group = fields.ForeignKeyField(
        "models.DeviceGroup", null=True, related_name="devices", description="所属分组"
    )
    status = fields.CharField(
        max_length=20, default="unknown", description="设备状态", index=True
    )  # online/offline/error/unknown
    last_check_time = fields.DatetimeField(null=True, description="最后检查时间", index=True)
    version = fields.CharField(max_length=100, null=True, description="系统版本")  # 系统版本
    model = fields.CharField(max_length=100, null=True, description="设备型号", index=True)  # 设备型号
    serial_number = fields.CharField(max_length=100, null=True, description="序列号", index=True)  # 序列号
    description = fields.TextField(null=True, description="设备描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "devices"
        indexes = [
            ("brand", "device_type", "is_active"),  # 品牌+类型+状态复合索引
            ("area", "status"),  # 区域+状态复合索引
            ("device_group", "status"),  # 分组+状态复合索引
            ("last_check_time", "status"),  # 检查时间+状态复合索引
        ]


# ================================ 任务相关模型 ================================


class Task(BaseModel):
    """任务表

    管理各种网络自动化任务，包括命令执行、监控、配置变更、备份等
    """

    name = fields.CharField(max_length=100, description="任务名称", index=True)
    task_type = fields.CharField(max_length=50, description="任务类型", index=True)  # command/monitor/config/backup
    target_devices = fields.JSONField(description="目标设备列表")  # [device_id1, device_id2]
    params = fields.JSONField(description="任务参数")  # {"command": "show version"}
    status = fields.CharField(
        max_length=20, default="pending", description="任务状态", index=True
    )  # pending/running/completed/failed/cancelled
    creator = fields.CharField(max_length=50, null=True, description="创建人", index=True)  # 创建人
    scheduled_time = fields.DatetimeField(null=True, description="计划执行时间", index=True)  # 计划执行时间
    started_at = fields.DatetimeField(null=True, description="开始执行时间", index=True)
    completed_at = fields.DatetimeField(null=True, description="完成时间", index=True)
    progress = fields.IntField(default=0, description="执行进度")  # 进度百分比
    total_devices = fields.IntField(default=0, description="总设备数")  # 总设备数
    success_devices = fields.IntField(default=0, description="成功设备数")  # 成功设备数
    failed_devices = fields.IntField(default=0, description="失败设备数")  # 失败设备数
    error_message = fields.TextField(null=True, description="错误信息")

    class Meta:  # type: ignore
        table = "tasks"
        indexes = [
            ("task_type", "status"),  # 任务类型+状态复合索引
            ("creator", "created_at"),  # 创建人+创建时间复合索引
            ("status", "created_at"),  # 状态+创建时间复合索引
            ("scheduled_time", "status"),  # 计划时间+状态复合索引
        ]


class TaskResult(BaseModel):
    """任务结果表

    记录任务在每个设备上的执行结果和详细信息
    """

    task = fields.ForeignKeyField("models.Task", related_name="results", description="关联任务")
    device = fields.ForeignKeyField("models.Device", related_name="task_results", description="执行设备")
    status = fields.CharField(max_length=20, description="执行状态", index=True)  # success/failed/timeout
    output = fields.TextField(null=True, description="命令输出结果")  # 命令输出
    error_message = fields.TextField(null=True, description="错误信息")
    execution_time = fields.FloatField(null=True, description="执行耗时(秒)")  # 执行耗时(秒)
    started_at = fields.DatetimeField(null=True, description="开始执行时间", index=True)
    completed_at = fields.DatetimeField(null=True, description="完成时间", index=True)

    class Meta:  # type: ignore
        table = "task_results"
        unique_together = (("task", "device"),)  # 同一任务在同一设备上只能有一条记录
        indexes = [
            ("task", "status"),  # 任务+状态复合索引
            ("device", "status"),  # 设备+状态复合索引
            ("completed_at", "status"),  # 完成时间+状态复合索引
        ]


# ================================ 配置相关模型 ================================


class DeviceConfig(BaseModel):
    """设备配置表

    存储设备的各种配置信息，包括运行配置、启动配置、备份配置等
    """

    device = fields.ForeignKeyField("models.Device", related_name="configs", description="关联设备")
    config_type = fields.CharField(max_length=50, description="配置类型", index=True)  # running/startup/backup
    content = fields.TextField(description="配置内容")  # 配置内容
    version = fields.CharField(max_length=50, null=True, description="配置版本号")  # 配置版本
    size = fields.IntField(null=True, description="配置大小(字节)")  # 配置大小(字节)
    backup_time = fields.DatetimeField(auto_now_add=True, description="备份时间", index=True)
    is_current = fields.BooleanField(default=False, description="是否为当前配置", index=True)  # 是否为当前配置
    creator = fields.CharField(max_length=50, null=True, description="创建人", index=True)
    description = fields.TextField(null=True, description="配置描述")

    class Meta:  # type: ignore
        table = "device_configs"
        indexes = [
            ("device", "config_type", "is_current"),  # 设备+配置类型+当前配置复合索引
            ("device", "backup_time"),  # 设备+备份时间复合索引
            ("creator", "backup_time"),  # 创建人+备份时间复合索引
        ]


class ConfigTemplate(BaseModel):
    """配置模板表

    管理各种配置模板，支持变量替换，便于批量配置部署
    """

    name = fields.CharField(max_length=100, unique=True, description="模板名称")
    brand = fields.ForeignKeyField("models.Brand", null=True, related_name="config_templates", description="适用品牌")
    device_type = fields.ForeignKeyField(
        "models.DeviceType", null=True, related_name="config_templates", description="适用设备类型"
    )
    template_type = fields.CharField(max_length=50, description="模板类型", index=True)  # init/security/vlan/routing
    content = fields.TextField(description="模板内容")  # 模板内容,支持变量替换
    variables = fields.JSONField(null=True, description="模板变量定义")  # 模板变量定义
    description = fields.TextField(null=True, description="模板描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "config_templates"
        indexes = [
            ("brand", "device_type", "template_type"),  # 品牌+设备类型+模板类型复合索引
            ("template_type", "is_active"),  # 模板类型+状态复合索引
        ]


# ================================ 监控相关模型 ================================


class MonitorMetric(BaseModel):
    """监控指标表

    存储设备的各种监控指标数据，如CPU、内存、接口状态、温度等
    """

    device = fields.ForeignKeyField("models.Device", related_name="metrics", description="关联设备")
    metric_type = fields.CharField(
        max_length=50, description="指标类型", index=True
    )  # cpu/memory/interface/temperature
    metric_name = fields.CharField(max_length=100, description="指标名称", index=True)  # CPU使用率、内存使用率
    value = fields.FloatField(description="指标值")  # 指标值
    unit = fields.CharField(max_length=20, null=True, description="指标单位")  # %、MB、°C
    threshold_warning = fields.FloatField(null=True, description="告警阈值")  # 告警阈值
    threshold_critical = fields.FloatField(null=True, description="严重告警阈值")  # 严重告警阈值
    status = fields.CharField(
        max_length=20, default="normal", description="指标状态", index=True
    )  # normal/warning/critical
    collected_at = fields.DatetimeField(description="采集时间", index=True)  # 采集时间

    class Meta:  # type: ignore
        table = "monitor_metrics"
        indexes = [
            ("device", "metric_type", "collected_at"),  # 设备+指标类型+采集时间复合索引
            ("device", "metric_name", "collected_at"),  # 设备+指标名称+采集时间复合索引
            ("metric_type", "status", "collected_at"),  # 指标类型+状态+采集时间复合索引
            ("collected_at", "status"),  # 采集时间+状态复合索引
        ]


class Alert(BaseModel):
    """告警表

    管理系统产生的各种告警信息，包括阈值告警、状态告警、连接告警等
    """

    device = fields.ForeignKeyField("models.Device", related_name="alerts", description="关联设备")
    alert_type = fields.CharField(max_length=50, description="告警类型", index=True)  # threshold/status/connection
    severity = fields.CharField(max_length=20, description="告警级别", index=True)  # info/warning/critical
    title = fields.CharField(max_length=200, description="告警标题")
    message = fields.TextField(description="告警消息")
    metric_name = fields.CharField(max_length=100, null=True, description="相关指标名称", index=True)
    current_value = fields.FloatField(null=True, description="当前值")
    threshold_value = fields.FloatField(null=True, description="阈值")
    status = fields.CharField(
        max_length=20, default="active", description="告警状态", index=True
    )  # active/acknowledged/resolved
    acknowledged_by = fields.CharField(max_length=50, null=True, description="确认人", index=True)
    acknowledged_at = fields.DatetimeField(null=True, description="确认时间", index=True)
    resolved_at = fields.DatetimeField(null=True, description="解决时间", index=True)

    class Meta:  # type: ignore
        table = "alerts"
        indexes = [
            ("device", "status", "severity"),  # 设备+状态+级别复合索引
            ("alert_type", "status", "created_at"),  # 告警类型+状态+创建时间复合索引
            ("severity", "status", "created_at"),  # 级别+状态+创建时间复合索引
            ("acknowledged_by", "acknowledged_at"),  # 确认人+确认时间复合索引
        ]


# ================================ 用户管理模型 ================================


class User(BaseModel):
    """用户表

    系统用户信息管理，包含用户基本信息和认证相关字段
    """

    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=100, unique=True, description="邮箱地址")
    password_hash = fields.CharField(max_length=255, description="密码哈希")  # bcrypt哈希
    full_name = fields.CharField(max_length=100, null=True, description="真实姓名", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    is_superuser = fields.BooleanField(default=False, description="是否为超级管理员", index=True)
    last_login = fields.DatetimeField(null=True, description="最后登录时间", index=True)
    avatar_url = fields.CharField(max_length=500, null=True, description="头像URL")
    phone = fields.CharField(max_length=20, null=True, description="联系电话", index=True)
    department = fields.CharField(max_length=100, null=True, description="所属部门", index=True)

    class Meta:  # type: ignore
        table = "users"
        indexes = [
            ("department", "is_active"),  # 部门+状态复合索引
            ("is_superuser", "is_active"),  # 超管+状态复合索引
        ]


class Role(BaseModel):
    """角色表

    系统角色定义，用于权限管理和访问控制
    """

    name = fields.CharField(max_length=50, unique=True, description="角色名称")  # admin/operator/viewer
    code = fields.CharField(max_length=20, unique=True, description="角色代码", index=True)
    description = fields.TextField(null=True, description="角色描述")
    permissions = fields.JSONField(description="权限列表")  # 权限列表
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:  # type: ignore
        table = "roles"


class UserRole(BaseModel):
    """用户角色关联表

    用户与角色的多对多关联关系，支持用户拥有多个角色
    """

    user = fields.ForeignKeyField("models.User", related_name="user_roles", description="关联用户")
    role = fields.ForeignKeyField("models.Role", related_name="user_roles", description="关联角色")
    granted_by = fields.CharField(max_length=50, null=True, description="授权人", index=True)
    granted_at = fields.DatetimeField(auto_now_add=True, description="授权时间", index=True)

    class Meta:  # type: ignore
        table = "user_roles"
        unique_together = (("user", "role"),)  # 用户和角色的组合唯一
        indexes = [
            ("granted_by", "granted_at"),  # 授权人+授权时间复合索引
        ]


# ================================ 日志相关模型 ================================


class OperationLog(BaseModel):
    """操作日志表

    记录用户在系统中的各种操作行为，用于审计和问题追踪
    """

    user = fields.CharField(max_length=50, null=True, description="操作用户", index=True)  # 操作用户
    action = fields.CharField(max_length=100, description="操作动作", index=True)  # create_device/execute_task
    resource_type = fields.CharField(max_length=50, description="资源类型", index=True)  # device/task/config
    resource_id = fields.CharField(max_length=50, null=True, description="资源ID", index=True)  # 资源ID
    resource_name = fields.CharField(max_length=200, null=True, description="资源名称")  # 资源名称
    details = fields.JSONField(null=True, description="操作详情")  # 操作详情
    ip_address = fields.CharField(max_length=45, null=True, description="操作IP地址", index=True)  # 操作IP(支持IPv6)
    user_agent = fields.CharField(max_length=500, null=True, description="用户代理信息")  # 浏览器信息
    result = fields.CharField(max_length=20, default="success", description="操作结果", index=True)  # success/failed
    error_message = fields.TextField(null=True, description="错误信息")
    execution_time = fields.FloatField(null=True, description="执行耗时(秒)")  # 执行耗时(秒)

    class Meta:  # type: ignore
        table = "operation_logs"
        indexes = [
            ("user", "action", "created_at"),  # 用户+动作+时间复合索引
            ("resource_type", "resource_id", "created_at"),  # 资源类型+资源ID+时间复合索引
            ("action", "result", "created_at"),  # 动作+结果+时间复合索引
            ("ip_address", "created_at"),  # IP地址+时间复合索引
        ]


class SystemLog(BaseModel):
    """系统日志表

    记录系统运行过程中的各种日志信息，便于系统监控和问题排查
    """

    level = fields.CharField(max_length=10, description="日志级别", index=True)  # DEBUG/INFO/WARNING/ERROR
    logger_name = fields.CharField(max_length=100, description="日志记录器名称", index=True)  # 日志记录器名称
    module = fields.CharField(max_length=100, null=True, description="模块名称", index=True)  # 模块名称
    function_name = fields.CharField(max_length=100, null=True, description="函数名称")  # 函数名称
    line_number = fields.IntField(null=True, description="代码行号")  # 行号
    message = fields.TextField(description="日志消息内容")  # 日志消息
    exception_info = fields.TextField(null=True, description="异常信息")  # 异常信息
    extra_data = fields.JSONField(null=True, description="额外数据")  # 额外数据

    class Meta:  # type: ignore
        table = "system_logs"
        indexes = [
            ("level", "created_at"),  # 级别+时间复合索引
            ("logger_name", "level", "created_at"),  # 记录器+级别+时间复合索引
            ("module", "level", "created_at"),  # 模块+级别+时间复合索引
        ]


# ================================ 接口和文件模型 ================================


class DeviceInterface(BaseModel):
    """设备接口表

    存储网络设备的接口信息，包括物理接口和逻辑接口的详细配置
    """

    device = fields.ForeignKeyField("models.Device", related_name="interfaces", description="关联设备")
    name = fields.CharField(max_length=100, description="接口名称", index=True)  # GigabitEthernet1/0/1
    type = fields.CharField(max_length=50, description="接口类型", index=True)  # ethernet/serial/loopback
    status = fields.CharField(
        max_length=20, default="unknown", description="接口状态", index=True
    )  # up/down/admin-down
    admin_status = fields.CharField(max_length=20, default="up", description="管理状态", index=True)  # up/down
    description = fields.CharField(max_length=200, null=True, description="接口描述")
    ip_address = fields.CharField(max_length=15, null=True, description="IP地址", index=True)
    subnet_mask = fields.CharField(max_length=15, null=True, description="子网掩码")
    mac_address = fields.CharField(max_length=17, null=True, description="MAC地址", index=True)
    speed = fields.CharField(max_length=20, null=True, description="接口速率")  # 1000Mbps
    duplex = fields.CharField(max_length=10, null=True, description="双工模式")  # full/half
    vlan_id = fields.IntField(null=True, description="VLAN ID", index=True)
    last_check_time = fields.DatetimeField(null=True, description="最后检查时间", index=True)

    class Meta:  # type: ignore
        table = "device_interfaces"
        unique_together = (("device", "name"),)  # 同一设备上接口名称唯一
        indexes = [
            ("device", "type", "status"),  # 设备+类型+状态复合索引
            ("device", "vlan_id"),  # 设备+VLAN复合索引
            ("ip_address", "device"),  # IP地址+设备复合索引
            ("status", "last_check_time"),  # 状态+检查时间复合索引
        ]


class ConfigFile(BaseModel):
    """配置文件表

    管理设备相关的各种文件，包括配置文件、日志文件、固件文件等
    """

    device = fields.ForeignKeyField("models.Device", related_name="config_files", description="关联设备")
    filename = fields.CharField(max_length=255, description="文件名", index=True)
    file_type = fields.CharField(max_length=50, description="文件类型", index=True)  # config/log/firmware
    file_path = fields.CharField(max_length=500, description="文件存储路径")  # 文件存储路径
    file_size = fields.BigIntField(null=True, description="文件大小(字节)")  # 文件大小(字节)
    checksum = fields.CharField(max_length=64, null=True, description="文件校验码", index=True)  # MD5/SHA256校验码
    uploaded_by = fields.CharField(max_length=50, null=True, description="上传人", index=True)
    upload_time = fields.DatetimeField(auto_now_add=True, description="上传时间", index=True)
    description = fields.TextField(null=True, description="文件描述")

    class Meta:  # type: ignore
        table = "config_files"
        indexes = [
            ("device", "file_type", "upload_time"),  # 设备+文件类型+上传时间复合索引
            ("uploaded_by", "upload_time"),  # 上传人+上传时间复合索引
            ("file_type", "upload_time"),  # 文件类型+上传时间复合索引
        ]
