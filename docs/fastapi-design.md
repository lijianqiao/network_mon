# FastAPI项目架构设计

## 1. 项目骨架（已完成）

基于现有的 FastAPI 项目模板，已包含：
- 核心配置（config.py, events.py, exceptions.py, middleware.py）
- 数据库连接（Tortoise ORM + PostgreSQL）
- 日志系统（loguru）
- 基础工具函数

## 2. 数据模型设计

### 核心实体关系
```
Brand (品牌) ─┐
              ├─> Device (设备) ──> DeviceConfig (配置)
DeviceType ───┘        │              │
                       │              └─> ConfigTemplate (模板)
Area (区域) ───────────┤
                       │
DeviceGroup ───────────┤
                       │
                       ├─> Task (任务) ──> TaskResult (任务结果)
                       │
                       ├─> MonitorMetric (监控指标)
                       │
                       └─> Alert (告警)
```

### 完整数据模型定义

#### 基础模型
```python
# models/base.py
from tortoise.models import Model
from tortoise import fields

class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)
    
    class Meta:
        abstract = True
```

#### 设备相关模型
```python
# models/device.py
class Brand(BaseModel):
    """设备品牌表"""
    name = fields.CharField(max_length=50, unique=True)           # 华三、华为、思科
    code = fields.CharField(max_length=20, unique=True)           # H3C、HUAWEI、CISCO
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "brands"

class DeviceType(BaseModel):
    """设备类型表"""
    name = fields.CharField(max_length=50)                        # 交换机、路由器、防火墙
    code = fields.CharField(max_length=20)                        # SWITCH、ROUTER、FIREWALL
    brand = fields.ForeignKeyField("models.Brand", related_name="device_types")
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "device_types"
        unique_together = (("brand", "code"),)

class Area(BaseModel):
    """区域表"""
    name = fields.CharField(max_length=100, unique=True)          # 北京、上海、广州
    code = fields.CharField(max_length=20, unique=True)           # BJ、SH、GZ
    parent = fields.ForeignKeyField("models.Area", null=True, related_name="children")
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "areas"

class DeviceGroup(BaseModel):
    """设备分组表"""
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    area = fields.ForeignKeyField("models.Area", related_name="device_groups")
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "device_groups"

class Device(BaseModel):
    """设备表"""
    name = fields.CharField(max_length=100)
    hostname = fields.CharField(max_length=100, null=True)
    management_ip = fields.CharField(max_length=15, unique=True)
    port = fields.IntField(default=22)                            # SSH端口
    account = fields.CharField(max_length=50)
    password = fields.CharField(max_length=255)                   # AES加密存储
    enable_password = fields.CharField(max_length=255, null=True) # 特权密码
    connection_type = fields.CharField(max_length=20, default="ssh") # ssh/telnet
    brand = fields.ForeignKeyField("models.Brand", related_name="devices")
    device_type = fields.ForeignKeyField("models.DeviceType", related_name="devices")
    area = fields.ForeignKeyField("models.Area", related_name="devices")
    device_group = fields.ForeignKeyField("models.DeviceGroup", null=True, related_name="devices")
    status = fields.CharField(max_length=20, default="unknown")   # online/offline/error/unknown
    last_check_time = fields.DatetimeField(null=True)
    version = fields.CharField(max_length=100, null=True)         # 系统版本
    model = fields.CharField(max_length=100, null=True)           # 设备型号
    serial_number = fields.CharField(max_length=100, null=True)   # 序列号
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "devices"
```

#### 任务相关模型
```python
# models/task.py
class Task(BaseModel):
    """任务表"""
    name = fields.CharField(max_length=100)
    task_type = fields.CharField(max_length=50)                   # command/monitor/config/backup
    target_devices = fields.JSONField()                           # [device_id1, device_id2]
    params = fields.JSONField()                                   # {"command": "show version"}
    status = fields.CharField(max_length=20, default="pending")   # pending/running/completed/failed/cancelled
    creator = fields.CharField(max_length=50, null=True)          # 创建人
    scheduled_time = fields.DatetimeField(null=True)              # 计划执行时间
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    progress = fields.IntField(default=0)                         # 进度百分比
    total_devices = fields.IntField(default=0)                    # 总设备数
    success_devices = fields.IntField(default=0)                  # 成功设备数
    failed_devices = fields.IntField(default=0)                   # 失败设备数
    error_message = fields.TextField(null=True)
    
    class Meta:
        table = "tasks"

class TaskResult(BaseModel):
    """任务结果表"""
    task = fields.ForeignKeyField("models.Task", related_name="results")
    device = fields.ForeignKeyField("models.Device", related_name="task_results")
    status = fields.CharField(max_length=20)                      # success/failed/timeout
    output = fields.TextField(null=True)                          # 命令输出
    error_message = fields.TextField(null=True)
    execution_time = fields.FloatField(null=True)                 # 执行耗时(秒)
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "task_results"
        unique_together = (("task", "device"),)
```

#### 配置相关模型
```python
# models/config.py
class DeviceConfig(BaseModel):
    """设备配置表"""
    device = fields.ForeignKeyField("models.Device", related_name="configs")
    config_type = fields.CharField(max_length=50)                 # running/startup/backup
    content = fields.TextField()                                  # 配置内容
    version = fields.CharField(max_length=50, null=True)          # 配置版本
    size = fields.IntField(null=True)                            # 配置大小(字节)
    backup_time = fields.DatetimeField(auto_now_add=True)
    is_current = fields.BooleanField(default=False)              # 是否为当前配置
    creator = fields.CharField(max_length=50, null=True)
    description = fields.TextField(null=True)
    
    class Meta:
        table = "device_configs"

class ConfigTemplate(BaseModel):
    """配置模板表"""
    name = fields.CharField(max_length=100, unique=True)
    brand = fields.ForeignKeyField("models.Brand", null=True, related_name="config_templates")
    device_type = fields.ForeignKeyField("models.DeviceType", null=True, related_name="config_templates")
    template_type = fields.CharField(max_length=50)               # init/security/vlan/routing
    content = fields.TextField()                                  # 模板内容,支持变量替换
    variables = fields.JSONField(null=True)                       # 模板变量定义
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "config_templates"
```

#### 监控相关模型
```python
# models/monitor.py
class MonitorMetric(BaseModel):
    """监控指标表"""
    device = fields.ForeignKeyField("models.Device", related_name="metrics")
    metric_type = fields.CharField(max_length=50)                 # cpu/memory/interface/temperature
    metric_name = fields.CharField(max_length=100)                # CPU使用率、内存使用率
    value = fields.FloatField()                                   # 指标值
    unit = fields.CharField(max_length=20, null=True)             # %、MB、°C
    threshold_warning = fields.FloatField(null=True)              # 告警阈值
    threshold_critical = fields.FloatField(null=True)             # 严重告警阈值
    status = fields.CharField(max_length=20, default="normal")    # normal/warning/critical
    collected_at = fields.DatetimeField()                         # 采集时间
    
    class Meta:
        table = "monitor_metrics"

class Alert(BaseModel):
    """告警表"""
    device = fields.ForeignKeyField("models.Device", related_name="alerts")
    alert_type = fields.CharField(max_length=50)                  # threshold/status/connection
    severity = fields.CharField(max_length=20)                    # info/warning/critical
    title = fields.CharField(max_length=200)
    message = fields.TextField()
    metric_name = fields.CharField(max_length=100, null=True)
    current_value = fields.FloatField(null=True)
    threshold_value = fields.FloatField(null=True)
    status = fields.CharField(max_length=20, default="active")    # active/acknowledged/resolved
    acknowledged_by = fields.CharField(max_length=50, null=True)
    acknowledged_at = fields.DatetimeField(null=True)
    resolved_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "alerts"
```

#### 用户管理模型
```python
# models/user.py
class User(BaseModel):
    """用户表"""
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    password_hash = fields.CharField(max_length=255)               # bcrypt哈希
    full_name = fields.CharField(max_length=100, null=True)
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    last_login = fields.DatetimeField(null=True)
    avatar_url = fields.CharField(max_length=500, null=True)
    phone = fields.CharField(max_length=20, null=True)
    department = fields.CharField(max_length=100, null=True)
    
    class Meta:
        table = "users"

class Role(BaseModel):
    """角色表"""
    name = fields.CharField(max_length=50, unique=True)            # admin/operator/viewer
    code = fields.CharField(max_length=20, unique=True)
    description = fields.TextField(null=True)
    permissions = fields.JSONField()                               # 权限列表
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "roles"

class UserRole(BaseModel):
    """用户角色关联表"""
    user = fields.ForeignKeyField("models.User", related_name="user_roles")
    role = fields.ForeignKeyField("models.Role", related_name="user_roles")
    granted_by = fields.CharField(max_length=50, null=True)
    granted_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "user_roles"
        unique_together = (("user", "role"),)
```

#### 系统日志模型
```python
# models/log.py
class OperationLog(BaseModel):
    """操作日志表"""
    user = fields.CharField(max_length=50, null=True)             # 操作用户
    action = fields.CharField(max_length=100)                     # create_device/execute_task
    resource_type = fields.CharField(max_length=50)               # device/task/config
    resource_id = fields.CharField(max_length=50, null=True)      # 资源ID
    resource_name = fields.CharField(max_length=200, null=True)   # 资源名称
    details = fields.JSONField(null=True)                         # 操作详情
    ip_address = fields.CharField(max_length=45, null=True)       # 操作IP
    user_agent = fields.CharField(max_length=500, null=True)      # 浏览器信息
    result = fields.CharField(max_length=20, default="success")   # success/failed
    error_message = fields.TextField(null=True)
    execution_time = fields.FloatField(null=True)                 # 执行耗时(秒)
    
    class Meta:
        table = "operation_logs"

class SystemLog(BaseModel):
    """系统日志表"""
    level = fields.CharField(max_length=10)                       # DEBUG/INFO/WARNING/ERROR
    logger_name = fields.CharField(max_length=100)                # 日志记录器名称
    module = fields.CharField(max_length=100, null=True)          # 模块名称
    function_name = fields.CharField(max_length=100, null=True)   # 函数名称
    line_number = fields.IntField(null=True)                      # 行号
    message = fields.TextField()                                  # 日志消息
    exception_info = fields.TextField(null=True)                  # 异常信息
    extra_data = fields.JSONField(null=True)                      # 额外数据
    
    class Meta:
        table = "system_logs"
```

#### 接口与文件模型
```python
# models/interface.py
class DeviceInterface(BaseModel):
    """设备接口表"""
    device = fields.ForeignKeyField("models.Device", related_name="interfaces")
    name = fields.CharField(max_length=100)                       # GigabitEthernet1/0/1
    type = fields.CharField(max_length=50)                        # ethernet/serial/loopback
    status = fields.CharField(max_length=20, default="unknown")   # up/down/admin-down
    admin_status = fields.CharField(max_length=20, default="up")  # up/down
    description = fields.CharField(max_length=200, null=True)
    ip_address = fields.CharField(max_length=15, null=True)
    subnet_mask = fields.CharField(max_length=15, null=True)
    mac_address = fields.CharField(max_length=17, null=True)
    speed = fields.CharField(max_length=20, null=True)            # 1000Mbps
    duplex = fields.CharField(max_length=10, null=True)           # full/half
    vlan_id = fields.IntField(null=True)
    last_check_time = fields.DatetimeField(null=True)
    
    class Meta:
        table = "device_interfaces"
        unique_together = (("device", "name"),)

class ConfigFile(BaseModel):
    """配置文件表"""
    device = fields.ForeignKeyField("models.Device", related_name="config_files")
    filename = fields.CharField(max_length=255)
    file_type = fields.CharField(max_length=50)                   # config/log/firmware
    file_path = fields.CharField(max_length=500)                  # 文件存储路径
    file_size = fields.BigIntField(null=True)                     # 文件大小(字节)
    checksum = fields.CharField(max_length=64, null=True)         # MD5/SHA256校验码
    uploaded_by = fields.CharField(max_length=50, null=True)
    upload_time = fields.DatetimeField(auto_now_add=True)
    description = fields.TextField(null=True)
    
    class Meta:
        table = "config_files"
```

## 3. 数据校验模型

### 基础Schema
```python
# schemas/base.py
class BaseSchema(BaseModel):
    """基础Schema"""
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    
class PaginationResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
```

### 设备相关Schema
```python
# schemas/device.py
class BrandResponse(BaseSchema):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool

class DeviceTypeResponse(BaseSchema):
    id: int
    name: str
    code: str
    brand: BrandResponse
    description: Optional[str] = None

class AreaResponse(BaseSchema):
    id: int
    name: str
    code: str
    parent_id: Optional[int] = None
    description: Optional[str] = None

class DeviceCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, max_length=100)
    management_ip: str = Field(..., pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    port: int = Field(22, ge=1, le=65535)
    account: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    enable_password: Optional[str] = None
    connection_type: str = Field("ssh", pattern="^(ssh|telnet)$")
    brand_id: int = Field(..., gt=0)
    device_type_id: int = Field(..., gt=0)
    area_id: int = Field(..., gt=0)
    device_group_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None

class DeviceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, max_length=100)
    port: Optional[int] = Field(None, ge=1, le=65535)
    account: Optional[str] = Field(None, min_length=1, max_length=50)
    password: Optional[str] = Field(None, min_length=1)
    enable_password: Optional[str] = None
    connection_type: Optional[str] = Field(None, pattern="^(ssh|telnet)$")
    area_id: Optional[int] = Field(None, gt=0)
    device_group_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceResponse(BaseSchema):
    id: int
    name: str
    hostname: Optional[str]
    management_ip: str
    port: int
    account: str
    connection_type: str
    brand: BrandResponse
    device_type: DeviceTypeResponse
    area: AreaResponse
    status: str
    last_check_time: Optional[datetime]
    version: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DeviceListFilter(BaseSchema):
    """设备列表过滤参数"""
    brand_id: Optional[int] = None
    device_type_id: Optional[int] = None
    area_id: Optional[int] = None
    device_group_id: Optional[int] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = Field(None, description="搜索设备名称、IP、主机名")
```

### 任务相关Schema
```python
# schemas/task.py
class TaskCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    task_type: str = Field(..., pattern="^(command|monitor|config|backup)$")
    target_devices: List[int] = Field(..., min_items=1, description="目标设备ID列表")
    params: Dict[str, Any] = Field(..., description="任务参数")
    scheduled_time: Optional[datetime] = None

class TaskUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    scheduled_time: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed|cancelled)$")

class TaskResponse(BaseSchema):
    id: int
    name: str
    task_type: str
    target_devices: List[int]
    params: Dict[str, Any]
    status: str
    creator: Optional[str]
    scheduled_time: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: int
    total_devices: int
    success_devices: int
    failed_devices: int
    error_message: Optional[str]
    created_at: datetime

class TaskResultResponse(BaseSchema):
    id: int
    task_id: int
    device_id: int
    device_name: str
    status: str
    output: Optional[str]
    error_message: Optional[str]
    execution_time: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class CommandTaskParams(BaseSchema):
    """命令执行任务参数"""
    command: str = Field(..., min_length=1, description="要执行的命令")
    timeout: int = Field(30, ge=1, le=300, description="超时时间(秒)")
    enable_mode: bool = Field(False, description="是否进入特权模式")

class ConfigTaskParams(BaseSchema):
    """配置任务参数"""
    template_id: Optional[int] = None
    config_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    backup_before: bool = Field(True, description="配置前是否备份")
```

### 用户相关Schema
```python
# schemas/user.py
class UserCreate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    department: Optional[str] = Field(None, max_length=100)

class UserResponse(BaseSchema):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    phone: Optional[str]
    department: Optional[str]
    roles: List[str] = []  # 角色名称列表
    created_at: datetime

class UserLogin(BaseSchema):
    username: str
    password: str

class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
```

## 4. 数据访问层模式

### Repository模式
```python
# repositories/device_repository.py
class DeviceRepository:
    async def create(self, device_data: dict) -> Device:
        return await Device.create(**device_data)
    
    async def get_by_id(self, device_id: int) -> Optional[Device]:
        return await Device.get_or_none(id=device_id).prefetch_related("brand", "area")
    
    async def list_with_filters(self, **filters) -> List[Device]:
        query = Device.all()
        if filters.get("brand_id"):
            query = query.filter(brand_id=filters["brand_id"])
        return await query.prefetch_related("brand", "device_type", "area")
```

## 5. 服务层设计

### 业务逻辑封装
```python
# services/device_service.py
class DeviceService:
    def __init__(self):
        self.repo = DeviceRepository()
        self.crypto = CryptoService()
        self.logger = get_logger(__name__)
    
    async def create_device(self, device_data: DeviceCreate, creator: str) -> DeviceResponse:
        """创建设备"""
        # 验证IP是否已存在
        existing = await self.repo.get_by_management_ip(device_data.management_ip)
        if existing:
            raise ValueError(f"设备IP {device_data.management_ip} 已存在")
        
        # 密码加密
        encrypted_password = self.crypto.encrypt(device_data.password)
        if device_data.enable_password:
            encrypted_enable_password = self.crypto.encrypt(device_data.enable_password)
        else:
            encrypted_enable_password = None
            
        device_dict = device_data.model_dump(exclude={"password", "enable_password"})
        device_dict.update({
            "password": encrypted_password,
            "enable_password": encrypted_enable_password
        })
        
        device = await self.repo.create(device_dict)
        
        # 记录操作日志
        await self._log_operation("create_device", creator, device.id, device.name)
        
        return await self.get_device(device.id)
    
    async def get_device_credentials(self, device_id: int) -> dict:
        """获取解密后的设备认证信息，供网络模块使用"""
        device = await self.repo.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
            
        credentials = {
            "host": device.management_ip,
            "username": device.account,
            "password": self.crypto.decrypt(device.password),
            "port": device.port,
            "device_type": device.device_type.code,
            "platform": device.brand.code.lower()
        }
        
        if device.enable_password:
            credentials["secret"] = self.crypto.decrypt(device.enable_password)
            
        return credentials
    
    async def update_device_status(self, device_id: int, status: str, 
                                  version: str = None, model: str = None) -> None:
        """更新设备状态和信息"""
        update_data = {
            "status": status,
            "last_check_time": datetime.now()
        }
        if version:
            update_data["version"] = version
        if model:
            update_data["model"] = model
            
        await self.repo.update(device_id, update_data)
        
        # 通知WebSocket模块
        await self._notify_status_change(device_id, status)
    
    async def _log_operation(self, action: str, user: str, resource_id: int, resource_name: str):
        """记录操作日志"""
        # TODO: 实现操作日志记录
        pass
    
    async def _notify_status_change(self, device_id: int, status: str):
        """通知设备状态变化"""
        # TODO: 集成事件总线
        pass

# services/task_service.py
class TaskService:
    def __init__(self):
        self.task_repo = TaskRepository()
        self.device_service = DeviceService()
        self.network_adapter = NetworkAdapter()  # 网络模块适配器
        
    async def create_task(self, task_data: TaskCreate, creator: str) -> TaskResponse:
        """创建任务"""
        # 验证目标设备
        devices = await self.device_service.get_devices_by_ids(task_data.target_devices)
        if len(devices) != len(task_data.target_devices):
            raise ValueError("部分目标设备不存在")
        
        # 验证任务参数
        self._validate_task_params(task_data.task_type, task_data.params)
        
        task_dict = task_data.model_dump()
        task_dict.update({
            "creator": creator,
            "total_devices": len(task_data.target_devices),
            "status": "pending"
        })
        
        task = await self.task_repo.create(task_dict)
        
        # 如果是立即执行的任务，加入执行队列
        if not task_data.scheduled_time:
            await self._execute_task_async(task.id)
            
        return TaskResponse.model_validate(task)
    
    async def execute_task(self, task_id: int) -> None:
        """执行任务"""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
            
        if task.status != "pending":
            raise ValueError(f"任务状态为 {task.status}，无法执行")
        
        # 更新任务状态
        await self.task_repo.update(task_id, {
            "status": "running",
            "started_at": datetime.now()
        })
        
        try:
            # 获取设备认证信息
            devices_creds = []
            for device_id in task.target_devices:
                creds = await self.device_service.get_device_credentials(device_id)
                creds["device_id"] = device_id
                devices_creds.append(creds)
            
            # 调用网络模块执行任务
            results = await self.network_adapter.execute_task(
                task.task_type, 
                devices_creds, 
                task.params
            )
            
            # 保存执行结果
            success_count = 0
            for result in results:
                await self._save_task_result(task_id, result)
                if result["status"] == "success":
                    success_count += 1
            
            # 更新任务状态
            await self.task_repo.update(task_id, {
                "status": "completed",
                "completed_at": datetime.now(),
                "progress": 100,
                "success_devices": success_count,
                "failed_devices": len(results) - success_count
            })
            
        except Exception as e:
            await self.task_repo.update(task_id, {
                "status": "failed",
                "completed_at": datetime.now(),
                "error_message": str(e)
            })
            raise
    
    def _validate_task_params(self, task_type: str, params: dict):
        """验证任务参数"""
        if task_type == "command":
            CommandTaskParams.model_validate(params)
        elif task_type == "config":
            ConfigTaskParams.model_validate(params)
        # 其他任务类型验证...

# services/user_service.py
class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.auth = AuthService()
        
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        if await self.repo.get_by_username(user_data.username):
            raise ValueError(f"用户名 {user_data.username} 已存在")
        if await self.repo.get_by_email(user_data.email):
            raise ValueError(f"邮箱 {user_data.email} 已存在")
        
        # 密码哈希
        password_hash = self.auth.hash_password(user_data.password)
        
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["password_hash"] = password_hash
        
        user = await self.repo.create(user_dict)
        return await self.get_user_with_roles(user.id)
    
    async def authenticate(self, username: str, password: str) -> Optional[UserResponse]:
        """用户认证"""
        user = await self.repo.get_by_username(username)
        if not user or not user.is_active:
            return None
            
        if not self.auth.verify_password(password, user.password_hash):
            return None
            
        # 更新最后登录时间
        await self.repo.update(user.id, {"last_login": datetime.now()})
        
        return await self.get_user_with_roles(user.id)

# services/monitor_service.py
class MonitorService:
    def __init__(self):
        self.metric_repo = MonitorMetricRepository()
        self.alert_repo = AlertRepository()
        self.device_service = DeviceService()
        
    async def collect_device_metrics(self, device_id: int) -> List[MonitorMetricResponse]:
        """采集设备监控指标"""
        creds = await self.device_service.get_device_credentials(device_id)
        
        # 调用网络模块采集指标
        metrics_data = await self.network_adapter.collect_metrics(creds)
        
        metrics = []
        for metric_data in metrics_data:
            metric_data["device_id"] = device_id
            metric_data["collected_at"] = datetime.now()
            
            # 检查告警阈值
            await self._check_threshold(device_id, metric_data)
            
            metric = await self.metric_repo.create(metric_data)
            metrics.append(metric)
        
        return metrics
    
    async def _check_threshold(self, device_id: int, metric_data: dict):
        """检查告警阈值"""
        if metric_data.get("threshold_critical") and metric_data["value"] >= metric_data["threshold_critical"]:
            await self._create_alert(device_id, metric_data, "critical")
        elif metric_data.get("threshold_warning") and metric_data["value"] >= metric_data["threshold_warning"]:
            await self._create_alert(device_id, metric_data, "warning")
```

## 6. 依赖注入

### FastAPI依赖
```python
# dependencies/device.py
async def get_device_service() -> DeviceService:
    return DeviceService()

async def get_valid_device(
    device_id: int,
    service: DeviceService = Depends(get_device_service)
) -> Device:
    device = await service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
```

## 7. API路由设计

### RESTful API结构
```python
# api/v1/devices.py
@router.post("/", response_model=DeviceResponse, status_code=201)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    service: DeviceService = Depends(get_device_service)
):
    """创建设备"""
    return await service.create_device(device_data, current_user.username)

@router.get("/", response_model=PaginationResponse[DeviceResponse])
async def list_devices(
    pagination: PaginationParams = Depends(),
    filters: DeviceListFilter = Depends(),
    service: DeviceService = Depends(get_device_service)
):
    """设备列表（支持分页和过滤）"""
    return await service.list_devices(pagination, filters)

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device: Device = Depends(get_valid_device)
):
    """获取设备详情"""
    return DeviceResponse.model_validate(device)

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    service: DeviceService = Depends(get_device_service)
):
    """更新设备"""
    return await service.update_device(device_id, device_data, current_user.username)

@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    service: DeviceService = Depends(get_device_service)
):
    """删除设备"""
    await service.delete_device(device_id, current_user.username)

@router.post("/{device_id}/test-connection")
async def test_device_connection(
    device_id: int,
    service: DeviceService = Depends(get_device_service)
):
    """测试设备连接"""
    result = await service.test_connection(device_id)
    return {"status": result["status"], "message": result["message"]}

# api/v1/tasks.py
@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """创建任务"""
    return await service.create_task(task_data, current_user.username)

@router.get("/", response_model=PaginationResponse[TaskResponse])
async def list_tasks(
    pagination: PaginationParams = Depends(),
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    service: TaskService = Depends(get_task_service)
):
    """任务列表"""
    filters = {"task_type": task_type, "status": status}
    return await service.list_tasks(pagination, filters)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service)
):
    """获取任务详情"""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.get("/{task_id}/results", response_model=List[TaskResultResponse])
async def get_task_results(
    task_id: int,
    service: TaskService = Depends(get_task_service)
):
    """获取任务执行结果"""
    return await service.get_task_results(task_id)

@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """取消任务"""
    await service.cancel_task(task_id, current_user.username)
    return {"message": "任务已取消"}

@router.post("/{task_id}/retry")
async def retry_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """重试任务"""
    new_task = await service.retry_task(task_id, current_user.username)
    return {"message": "任务已重新提交", "new_task_id": new_task.id}

# api/v1/auth.py
@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    service: UserService = Depends(get_user_service)
):
    """用户登录"""
    user = await service.authenticate(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # TODO: 实现token黑名单
    return {"message": "登出成功"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

# api/v1/monitor.py
@router.get("/devices/{device_id}/metrics")
async def get_device_metrics(
    device_id: int,
    metric_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    service: MonitorService = Depends(get_monitor_service)
):
    """获取设备监控指标"""
    return await service.get_device_metrics(
        device_id, metric_type, start_time, end_time
    )

@router.post("/devices/{device_id}/collect")
async def collect_device_metrics(
    device_id: int,
    service: MonitorService = Depends(get_monitor_service)
):
    """手动采集设备指标"""
    metrics = await service.collect_device_metrics(device_id)
    return {"message": f"采集到 {len(metrics)} 个指标"}

@router.get("/alerts")
async def list_alerts(
    pagination: PaginationParams = Depends(),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    device_id: Optional[int] = None,
    service: MonitorService = Depends(get_monitor_service)
):
    """告警列表"""
    filters = {"severity": severity, "status": status, "device_id": device_id}
    return await service.list_alerts(pagination, filters)

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    service: MonitorService = Depends(get_monitor_service)
):
    """确认告警"""
    await service.acknowledge_alert(alert_id, current_user.username)
    return {"message": "告警已确认"}

# api/v1/config.py
@router.post("/devices/{device_id}/backup")
async def backup_device_config(
    device_id: int,
    current_user: User = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service)
):
    """备份设备配置"""
    config = await service.backup_device_config(device_id, current_user.username)
    return {"message": "配置备份成功", "config_id": config.id}

@router.get("/devices/{device_id}/configs")
async def list_device_configs(
    device_id: int,
    config_type: Optional[str] = None,
    service: ConfigService = Depends(get_config_service)
):
    """设备配置历史"""
    return await service.list_device_configs(device_id, config_type)

@router.get("/templates", response_model=List[ConfigTemplateResponse])
async def list_config_templates(
    brand_id: Optional[int] = None,
    device_type_id: Optional[int] = None,
    template_type: Optional[str] = None,
    service: ConfigService = Depends(get_config_service)
):
    """配置模板列表"""
    filters = {
        "brand_id": brand_id,
        "device_type_id": device_type_id,
        "template_type": template_type
    }
    return await service.list_templates(filters)
```

## 8. 核心设计原则

### 架构特点
- **分层架构**: API -> Service -> Repository -> Model
- **依赖注入**: 便于测试和解耦
- **数据验证**: Pydantic确保数据安全
- **异步处理**: 全异步支持高并发
- **密码安全**: AES加密存储敏感信息

### 关键配置
```python
# core/config.py
class Settings(BaseSettings):
    # 数据库配置
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # 加密密钥
    SECRET_KEY: str  # 用于设备密码加密
    
    # Redis配置（任务队列和缓存）
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
```

## 9. 与其他模块集成点

### 网络模块接口
```python
# adapters/network_adapter.py
class NetworkAdapter:
    """网络自动化模块适配器"""
    
    async def get_devices_for_network(self, device_ids: List[int]) -> List[dict]:
        """为网络自动化模块提供设备信息"""
        service = DeviceService()
        devices = []
        for device_id in device_ids:
            creds = await service.get_device_credentials(device_id)
            device_info = await service.get_device(device_id)
            devices.append({
                "id": device_id,
                "name": device_info.name,
                "hostname": device_info.hostname,
                "brand": device_info.brand.code,
                "device_type": device_info.device_type.code,
                "credentials": creds,
                "connection_params": {
                    "host": creds["host"],
                    "port": creds["port"],
                    "username": creds["username"],
                    "password": creds["password"],
                    "platform": creds["platform"],
                    "device_type": creds["device_type"]
                }
            })
        return devices
    
    async def execute_task(self, task_type: str, devices: List[dict], params: dict) -> List[dict]:
        """执行网络任务"""
        # 调用网络模块的任务执行器
        from network_automation import TaskExecutor
        
        executor = TaskExecutor()
        return await executor.execute_batch_task(task_type, devices, params)
    
    async def test_device_connectivity(self, device_creds: dict) -> dict:
        """测试设备连通性"""
        from network_automation import DeviceConnector
        
        connector = DeviceConnector()
        return await connector.test_connection(device_creds)
    
    async def collect_device_metrics(self, device_creds: dict) -> List[dict]:
        """采集设备监控指标"""
        from network_automation import MetricCollector
        
        collector = MetricCollector()
        return await collector.collect_metrics(device_creds)
    
    async def backup_device_config(self, device_creds: dict) -> str:
        """备份设备配置"""
        from network_automation import ConfigManager
        
        manager = ConfigManager()
        return await manager.backup_config(device_creds)
    
    async def push_device_config(self, device_creds: dict, config_content: str) -> dict:
        """推送设备配置"""
        from network_automation import ConfigManager
        
        manager = ConfigManager()
        return await manager.push_config(device_creds, config_content)
```

### WebSocket模块接口
```python
# adapters/websocket_adapter.py
class WebSocketAdapter:
    """WebSocket模块适配器"""
    
    async def notify_device_status_change(self, device_id: int, status: str):
        """通知设备状态变化"""
        from websocket_server import EventBroadcaster
        
        broadcaster = EventBroadcaster()
        await broadcaster.broadcast_device_event({
            "type": "device_status_changed",
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    async def notify_task_progress(self, task_id: int, progress: int, message: str = None):
        """通知任务进度"""
        from websocket_server import EventBroadcaster
        
        broadcaster = EventBroadcaster()
        await broadcaster.broadcast_task_event({
            "type": "task_progress",
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def notify_new_alert(self, alert_data: dict):
        """通知新告警"""
        from websocket_server import EventBroadcaster
        
        broadcaster = EventBroadcaster()
        await broadcaster.broadcast_alert_event({
            "type": "new_alert",
            "alert": alert_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_terminal_session(self, device_id: int, user_id: int) -> str:
        """获取设备终端会话"""
        from websocket_server import TerminalManager
        
        # 获取设备认证信息
        service = DeviceService()
        creds = await service.get_device_credentials(device_id)
        
        manager = TerminalManager()
        session_id = await manager.create_session(device_id, user_id, creds)
        return session_id
```

### 事件总线集成
```python
# events/event_bus.py
class EventBus:
    """事件总线，用于模块间解耦通信"""
    
    def __init__(self):
        self.handlers = defaultdict(list)
        self.websocket_adapter = WebSocketAdapter()
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        self.handlers[event_type].append(handler)
    
    async def publish(self, event_type: str, data: dict):
        """发布事件"""
        # 执行所有订阅者的处理函数
        for handler in self.handlers[event_type]:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"事件处理失败: {event_type}, {str(e)}")
        
        # 特定事件自动推送到WebSocket
        if event_type in ["device.status.changed", "task.progress", "alert.created"]:
            await self._handle_websocket_event(event_type, data)
    
    async def _handle_websocket_event(self, event_type: str, data: dict):
        """处理WebSocket事件推送"""
        if event_type == "device.status.changed":
            await self.websocket_adapter.notify_device_status_change(
                data["device_id"], data["status"]
            )
        elif event_type == "task.progress":
            await self.websocket_adapter.notify_task_progress(
                data["task_id"], data["progress"], data.get("message")
            )
        elif event_type == "alert.created":
            await self.websocket_adapter.notify_new_alert(data)

# 全局事件总线实例
event_bus = EventBus()

# 在服务中使用事件总线
class DeviceService:
    async def update_device_status(self, device_id: int, status: str):
        # 更新数据库
        await self.repo.update(device_id, {"status": status})
        
        # 发布状态变化事件
        await event_bus.publish("device.status.changed", {
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.now()
        })
```

### 数据同步接口
```python
# sync/data_sync.py
class DataSyncService:
    """数据同步服务，用于模块间数据一致性"""
    
    async def sync_device_info_to_network(self, device_id: int):
        """同步设备信息到网络模块"""
        device_service = DeviceService()
        device_info = await device_service.get_device(device_id)
        
        # 同步到网络模块的设备清单
        from network_automation import InventoryManager
        inventory = InventoryManager()
        await inventory.update_device_info(device_id, {
            "name": device_info.name,
            "hostname": device_info.hostname,
            "management_ip": device_info.management_ip,
            "brand": device_info.brand.code,
            "device_type": device_info.device_type.code,
            "area": device_info.area.name,
            "is_active": device_info.is_active
        })
    
    async def sync_task_results_from_network(self, task_id: int, results: List[dict]):
        """从网络模块同步任务结果"""
        task_service = TaskService()
        
        for result in results:
            await task_service.save_task_result(task_id, result)
        
        # 更新任务整体状态
        await task_service.update_task_status(task_id, results)
```

### API网关集成
```python
# gateway/api_gateway.py
class APIGateway:
    """API网关，统一对外提供服务"""
    
    def __init__(self):
        self.fastapi_router = APIRouter()
        self.network_router = APIRouter()
        self.websocket_router = APIRouter()
    
    def setup_routes(self):
        """设置路由"""
        # FastAPI模块路由
        self.fastapi_router.include_router(
            devices_router, prefix="/api/v1/devices", tags=["设备管理"]
        )
        self.fastapi_router.include_router(
            tasks_router, prefix="/api/v1/tasks", tags=["任务管理"]
        )
        
        # 网络模块路由
        self.network_router.include_router(
            network_tasks_router, prefix="/api/v1/network", tags=["网络自动化"]
        )
        
        # WebSocket路由
        self.websocket_router.include_router(
            websocket_router, prefix="/ws", tags=["实时通信"]
        )
    
    async def health_check(self):
        """健康检查"""
        return {
            "status": "healthy",
            "modules": {
                "fastapi": await self._check_fastapi_health(),
                "network": await self._check_network_health(),
                "websocket": await self._check_websocket_health()
            },
            "timestamp": datetime.now().isoformat()
        }
```

这个设计保持了FastAPI的最佳实践，结构清晰，便于与网络自动化和WebSocket模块集成。
