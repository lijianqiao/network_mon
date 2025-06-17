# FastAPI 网络自动化平台设计

## 1. 项目骨架（已完成）

基于现有的 FastAPI 项目模板，已包含：
- 核心配置（config.py, events.py, exceptions.py, middleware.py）
- 数据库连接（Tortoise ORM + PostgreSQL）
- 日志系统（loguru）
- 基础工具函数

## 2. 简化数据模型设计

### 核心实体关系
```
Brand (品牌) ─┐
              ├─> DeviceModel (型号) ─┐
              │                      ├─> Device (设备) ──> MonitorMetric (监控指标)
              └─> ConfigTemplate ────┘        │              │
                                              │              └─> Alert (告警)
Area (区域) ──┐                               │
              ├─> DeviceGroup (分组) ─────────┤
              └─> Device ─────────────────────┘
                      │
                      └─> OperationLog (操作日志)

SystemLog (系统日志)
```

### 核心模型定义

#### 基础模型
```python
class BaseModel(Model):
    """基础模型类，提供公共字段"""
    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间", index=True)
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    is_deleted = fields.BooleanField(default=False, description="是否已删除", index=True)
```

#### 设备相关模型
```python
class Brand(BaseModel):
    """设备品牌表 - 华三、华为、思科等"""
    name = fields.CharField(max_length=50, unique=True, description="品牌名称")
    code = fields.CharField(max_length=20, unique=True, description="品牌代码", index=True)
    description = fields.TextField(null=True, description="品牌描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

class DeviceModel(BaseModel):
    """设备型号表 - 具体的设备型号信息"""
    name = fields.CharField(max_length=100, description="型号名称", index=True)
    brand = fields.ForeignKeyField("models.Brand", related_name="device_models")
    device_type = fields.CharField(max_length=50, description="设备类型", index=True)  # switch/router/firewall
    description = fields.TextField(null=True, description="型号描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

class Area(BaseModel):
    """区域表 - 支持层级结构的地理区域"""
    name = fields.CharField(max_length=100, unique=True, description="区域名称")
    code = fields.CharField(max_length=20, unique=True, description="区域代码", index=True)
    parent = fields.ForeignKeyField("models.Area", null=True, related_name="children")
    description = fields.TextField(null=True, description="区域描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

class DeviceGroup(BaseModel):
    """设备分组表 - 便于批量操作的逻辑分组"""
    name = fields.CharField(max_length=100, description="分组名称", index=True)
    description = fields.TextField(null=True, description="分组描述")
    area = fields.ForeignKeyField("models.Area", related_name="device_groups")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

class Device(BaseModel):
    """设备表 - 网络设备核心信息"""
    name = fields.CharField(max_length=100, description="设备名称", index=True)
    hostname = fields.CharField(max_length=100, null=True, description="主机名")
    management_ip = fields.CharField(max_length=15, unique=True, description="管理IP地址")
    port = fields.IntField(default=22, description="连接端口")
    account = fields.CharField(max_length=50, description="登录账号")
    password = fields.CharField(max_length=255, description="登录密码")  # AES加密存储
    enable_password = fields.CharField(max_length=255, null=True, description="特权模式密码")
    connection_type = fields.CharField(max_length=20, default="ssh", description="连接类型")
    brand = fields.ForeignKeyField("models.Brand", related_name="devices")
    device_model = fields.ForeignKeyField("models.DeviceModel", null=True, related_name="devices")
    area = fields.ForeignKeyField("models.Area", related_name="devices")
    device_group = fields.ForeignKeyField("models.DeviceGroup", null=True, related_name="devices")
    status = fields.CharField(max_length=20, default="unknown", description="设备状态", index=True)
    last_check_time = fields.DatetimeField(null=True, description="最后检查时间", index=True)
    version = fields.CharField(max_length=100, null=True, description="系统版本")
    serial_number = fields.CharField(max_length=100, null=True, description="序列号")
    description = fields.TextField(null=True, description="设备描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
```

#### 配置模板
```python
class ConfigTemplate(BaseModel):
    """配置模板表 - 支持变量替换的配置模板"""
    name = fields.CharField(max_length=100, unique=True, description="模板名称")
    brand = fields.ForeignKeyField("models.Brand", null=True, related_name="config_templates")
    device_type = fields.CharField(max_length=50, null=True, description="适用设备类型", index=True)
    template_type = fields.CharField(max_length=50, description="模板类型", index=True)  # init/security/vlan/routing
    content = fields.TextField(description="模板内容")  # 支持变量替换
    variables = fields.JSONField(null=True, description="模板变量定义")
    description = fields.TextField(null=True, description="模板描述")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
```

#### 监控相关模型
```python
class MonitorMetric(BaseModel):
    """监控指标表 - 设备性能指标数据"""
    device = fields.ForeignKeyField("models.Device", related_name="metrics")
    metric_type = fields.CharField(max_length=50, description="指标类型", index=True)  # cpu/memory/interface/temperature
    metric_name = fields.CharField(max_length=100, description="指标名称")
    value = fields.FloatField(description="指标值")
    unit = fields.CharField(max_length=20, null=True, description="指标单位")  # %、MB、°C
    threshold_warning = fields.FloatField(null=True, description="告警阈值")
    threshold_critical = fields.FloatField(null=True, description="严重告警阈值")
    status = fields.CharField(max_length=20, default="normal", description="指标状态", index=True)
    collected_at = fields.DatetimeField(description="采集时间", index=True)

class Alert(BaseModel):
    """告警表 - 系统告警信息管理"""
    device = fields.ForeignKeyField("models.Device", related_name="alerts")
    alert_type = fields.CharField(max_length=50, description="告警类型", index=True)  # threshold/status/connection
    severity = fields.CharField(max_length=20, description="告警级别", index=True)  # info/warning/critical
    title = fields.CharField(max_length=200, description="告警标题")
    message = fields.TextField(description="告警消息")
    metric_name = fields.CharField(max_length=100, null=True, description="相关指标名称")
    current_value = fields.FloatField(null=True, description="当前值")
    threshold_value = fields.FloatField(null=True, description="阈值")
    status = fields.CharField(max_length=20, default="active", description="告警状态", index=True)
    acknowledged_by = fields.CharField(max_length=50, null=True, description="确认人")
    acknowledged_at = fields.DatetimeField(null=True, description="确认时间")
    resolved_at = fields.DatetimeField(null=True, description="解决时间")
```

#### 日志相关模型
```python
class OperationLog(BaseModel):
    """操作日志表 - 用户操作审计"""
    user = fields.CharField(max_length=50, null=True, description="操作用户", index=True)
    action = fields.CharField(max_length=100, description="操作动作", index=True)  # create_device/execute_command
    resource_type = fields.CharField(max_length=50, description="资源类型", index=True)  # device/template/alert
    resource_id = fields.CharField(max_length=50, null=True, description="资源ID")
    resource_name = fields.CharField(max_length=200, null=True, description="资源名称")
    details = fields.JSONField(null=True, description="操作详情")
    ip_address = fields.CharField(max_length=45, null=True, description="操作IP地址")
    result = fields.CharField(max_length=20, default="success", description="操作结果", index=True)
    error_message = fields.TextField(null=True, description="错误信息")
    execution_time = fields.FloatField(null=True, description="执行耗时(秒)")

class SystemLog(BaseModel):
    """系统日志表 - 系统运行日志"""
    level = fields.CharField(max_length=10, description="日志级别", index=True)  # DEBUG/INFO/WARNING/ERROR
    logger_name = fields.CharField(max_length=100, description="日志记录器名称")
    module = fields.CharField(max_length=100, null=True, description="模块名称", index=True)
    message = fields.TextField(description="日志消息内容")
    exception_info = fields.TextField(null=True, description="异常信息")
    extra_data = fields.JSONField(null=True, description="额外数据")
```

## 3. 简化功能特性

### 移除的功能
- **用户管理和权限系统** - 简化为基于IP的访问控制
- **任务管理系统** - 直接执行命令，不需要复杂的任务队列
- **设备接口管理** - 通过命令获取，不存储
- **文件管理系统** - 配置备份通过模板管理
- **设备配置存储** - 实时获取，不存储历史配置

### 保留的核心功能
1. **设备管理** - 设备信息、品牌型号、区域分组
2. **配置模板** - 模板管理和变量替换
3. **监控告警** - 性能指标采集和告警
4. **操作审计** - 操作日志和系统日志

## 4. 性能优化

### 索引策略
- **时间字段索引**：created_at, collected_at, last_check_time
- **状态字段索引**：is_active, status, severity
- **复合索引**：
  - (device, metric_type, collected_at) - 监控数据查询
  - (brand, status) - 设备品牌状态查询
  - (area, status) - 区域设备状态查询

### 查询优化
- **设备列表**：按区域、分组、状态过滤
- **监控数据**：按设备、指标类型、时间范围查询
- **告警信息**：按设备、级别、状态过滤
- **日志查询**：按用户、操作类型、时间范围

## 5. API设计简化

### 核心API端点
```
GET /api/v1/devices              # 设备列表
POST /api/v1/devices             # 创建设备
GET /api/v1/devices/{id}         # 设备详情
PUT /api/v1/devices/{id}         # 更新设备
DELETE /api/v1/devices/{id}      # 删除设备
POST /api/v1/devices/{id}/test   # 测试设备连接

GET /api/v1/brands               # 品牌列表
GET /api/v1/device-models        # 型号列表
GET /api/v1/areas                # 区域列表
GET /api/v1/device-groups        # 分组列表

GET /api/v1/config-templates     # 配置模板列表
POST /api/v1/config-templates    # 创建模板
POST /api/v1/devices/{id}/config # 应用配置模板

GET /api/v1/monitor/metrics      # 监控指标
GET /api/v1/alerts               # 告警列表
PUT /api/v1/alerts/{id}/ack      # 确认告警

GET /api/v1/logs/operations      # 操作日志
GET /api/v1/logs/system          # 系统日志
```

## 6. 数据表总数：10张

1. **brands** - 设备品牌表
2. **device_models** - 设备型号表  
3. **areas** - 区域表
4. **device_groups** - 设备分组表
5. **devices** - 设备表
6. **config_templates** - 配置模板表
7. **monitor_metrics** - 监控指标表
8. **alerts** - 告警表
9. **operation_logs** - 操作日志表
10. **system_logs** - 系统日志表

这个简化版本专注于网络自动化的核心功能，去除了过度设计的部分，更加实用和高效。
