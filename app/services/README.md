# 服务层设计文档

## 概述

服务层（Service Layer）是网络自动化平台的核心业务逻辑层，位于控制器和数据访问层之间，负责处理复杂的业务逻辑、数据校验、权限控制和事务管理。

## 设计原则

### 1. 分层架构
```
Controller Layer (API/Web)
       ↓
Service Layer (Business Logic)
       ↓
Repository Layer (Data Access)
       ↓
Model Layer (Data Models)
```

### 2. 职责分离
- **Controller**: 处理HTTP请求、参数验证、响应格式化
- **Service**: 业务逻辑、数据校验、权限控制、事务管理
- **Repository**: 数据访问、查询优化、缓存管理
- **Model**: 数据定义、约束规则

### 3. 统一接口
所有服务类继承自 `BaseService`，提供统一的接口和行为：
- 标准化的CRUD操作
- 统一的参数校验
- 自动的日志记录
- 一致的错误处理

## 核心组件

### BaseService（服务基类）

`BaseService` 是所有业务服务的基类，提供通用功能：

```python
class BaseService(Generic[ModelType, DAOType]):
    """服务层基类"""
    
    def __init__(self, dao: DAOType):
        self.dao = dao
    
    # 基础CRUD操作
    async def create(self, data: dict, user: str = "system") -> ModelType
    async def get_by_id(self, resource_id: int, user: str = "system") -> ModelType | None
    async def update(self, resource_id: int, data: dict, user: str = "system") -> ModelType | None
    async def delete(self, resource_id: int, user: str = "system") -> bool
    
    # 批量操作
    async def list_all(self, user: str = "system") -> list[ModelType]
    async def get_paginated(self, page: int = 1, page_size: int = 20, user: str = "system") -> dict
    async def count(self, user: str = "system") -> int
    async def exists(self, resource_id: int, user: str = "system") -> bool
    
    # 钩子方法（子类可重写）
    async def _validate_create_data(self, data: dict) -> None
    async def _validate_update_data(self, data: dict, existing: ModelType) -> None
    async def _validate_delete(self, existing: ModelType, user: str) -> None
    async def _before_create(self, data: dict, user: str) -> dict
    async def _after_create(self, result: ModelType, data: dict, user: str) -> None
    # ... 更多钩子方法
```

### 功能特性

#### 1. 自动日志记录
所有服务方法都使用 `@system_log` 装饰器自动记录操作日志：

```python
@system_log(LogConfig(log_args=True, log_result=False))
async def create(self, data: dict, user: str = "system") -> ModelType:
    # 业务逻辑
```

#### 2. 数据校验
通过钩子方法实现业务数据校验：

```python
async def _validate_create_data(self, data: dict) -> None:
    """创建数据校验钩子"""
    if not data.get("name"):
        raise ValueError("名称不能为空")
    
    # 检查唯一性
    existing = await self.dao.get_by_field("name", data["name"])
    if existing:
        raise ValueError(f"名称 '{data['name']}' 已存在")
```

#### 3. 事务支持
通过钩子方法支持复杂的事务处理：

```python
async def _before_create(self, data: dict, user: str) -> dict:
    """创建前处理"""
    # 数据预处理
    data["created_by"] = user
    data["status"] = "PENDING"
    return data

async def _after_create(self, result: ModelType, data: dict, user: str) -> None:
    """创建后处理"""
    # 发送通知、更新缓存等
    await self._send_notification(result, user)
```

## 业务服务

### 设备相关服务

#### BrandService（品牌服务）
```python
class BrandService(BaseService[Brand, BrandDAO]):
    """设备品牌服务"""
    
    # 基础方法继承自BaseService
    # 扩展方法：
    async def get_by_name(self, name: str) -> Brand | None
    async def search_brands(self, keyword: str) -> list[Brand]
```

#### DeviceModelService（设备型号服务）
```python
class DeviceModelService(BaseService[DeviceModel, DeviceModelDAO]):
    """设备型号服务"""
    
    # 扩展方法：
    async def get_by_brand(self, brand_id: int) -> list[DeviceModel]
    async def search_models(self, keyword: str) -> list[DeviceModel]
```

#### DeviceService（设备服务）
```python
class DeviceService(BaseService[Device, DeviceDAO]):
    """设备服务"""
    
    # 扩展方法：
    async def get_by_ip(self, management_ip: str) -> Device | None
    async def get_by_area(self, area_id: int) -> list[Device]
    async def get_by_status(self, status: str) -> list[Device]
    async def search_devices(self, keyword: str) -> list[Device]
    async def get_device_statistics(self) -> dict[str, Any]
    async def update_device_status(self, device_id: int, status: str) -> Device | None
```

### 配置管理服务

#### ConfigTemplateService（配置模板服务）
```python
class ConfigTemplateService(BaseService[ConfigTemplate, ConfigTemplateDAO]):
    """配置模板服务"""
    
    # 扩展方法：
    async def get_by_name(self, name: str) -> ConfigTemplate | None
    async def get_by_type(self, template_type: str) -> list[ConfigTemplate]
    async def search_templates(self, keyword: str) -> list[ConfigTemplate]
```

### 监控相关服务

#### MonitorMetricService（监控指标服务）
```python
class MonitorMetricService(BaseService[MonitorMetric, MonitorMetricDAO]):
    """监控指标服务"""
    
    # 扩展方法：
    async def get_by_device(self, device_id: int, metric_type: str | None = None) -> list[MonitorMetric]
```

#### AlertService（告警服务）
```python
class AlertService(BaseService[Alert, AlertDAO]):
    """告警服务"""
    
    # 扩展方法：
    async def acknowledge_alert(self, alert_id: int, user: str) -> Alert | None
```

### 日志服务

#### OperationLogService（操作日志服务）
```python
class OperationLogService(BaseService[OperationLog, OperationLogDAO]):
    """操作日志服务"""
    
    # 扩展方法：
    async def get_by_user(self, user: str) -> list[OperationLog]
    async def get_by_resource(self, resource_type: str, resource_id: int | None = None) -> list[OperationLog]
    async def search_logs(self, **filters) -> dict[str, Any]
    async def get_operation_statistics(self) -> dict[str, Any]
```

#### SystemLogService（系统日志服务）
```python
class SystemLogService(BaseService[SystemLog, SystemLogDAO]):
    """系统日志服务"""
    
    # 扩展方法：
    async def get_by_level(self, level: str) -> list[SystemLog]
    async def get_by_module(self, module: str) -> list[SystemLog]
    async def search_logs(self, **filters) -> dict[str, Any]
    async def get_recent_errors(self, hours: int = 24) -> list[SystemLog]
```

## 使用方式

### 1. 直接实例化
```python
from app.services import BrandService

brand_service = BrandService()
brand = await brand_service.create({"name": "华为", "code": "HUAWEI"})
```

### 2. 工厂函数
```python
from app.services import get_brand_service

brand_service = get_brand_service()
brand = await brand_service.create({"name": "华为", "code": "HUAWEI"})
```

### 3. 依赖注入（推荐）
```python
class DeviceController:
    def __init__(self, device_service: DeviceService = None):
        self.device_service = device_service or get_device_service()
    
    async def create_device(self, device_data: dict) -> dict:
        device = await self.device_service.create(device_data, user="admin")
        return {"id": device.id, "name": device.name}
```

## 最佳实践

### 1. 错误处理
```python
try:
    device = await device_service.create(device_data)
except ValueError as e:
    # 业务逻辑错误
    return {"error": str(e)}
except Exception as e:
    # 系统错误
    logger.error(f"创建设备失败: {e}")
    return {"error": "系统错误"}
```

### 2. 事务处理
```python
async def _after_create(self, result: Device, data: dict, user: str) -> None:
    """设备创建后处理"""
    # 创建默认监控规则
    await self._create_default_monitors(result)
    
    # 记录操作日志
    await self._log_operation("CREATE", "Device", result.id, user)
    
    # 发送通知
    await self._notify_device_created(result, user)
```

### 3. 性能优化
```python
# 批量操作
devices = await device_service.get_by_area(area_id)

# 分页查询
page_result = await device_service.get_paginated(page=1, page_size=20)

# 条件查询
active_devices = await device_service.get_by_status("ONLINE")
```

### 4. 缓存策略
```python
# 在服务层实现缓存
@cache(ttl=300)  # 缓存5分钟
async def get_device_statistics(self) -> dict[str, Any]:
    return await self.dao.get_device_status_count()
```

## 扩展指南

### 1. 添加新服务
```python
from app.models.data_models import NewModel
from app.repositories import NewModelDAO
from .base_service import BaseService

class NewModelService(BaseService[NewModel, NewModelDAO]):
    """新模型服务"""
    
    def __init__(self):
        super().__init__(NewModelDAO())
    
    async def _validate_create_data(self, data: dict) -> None:
        """业务校验逻辑"""
        pass
    
    # 添加特定业务方法
    async def custom_method(self) -> Any:
        """自定义业务方法"""
        pass
```

### 2. 扩展基类功能
```python
class ExtendedBaseService(BaseService):
    """扩展的服务基类"""
    
    async def soft_delete(self, resource_id: int, user: str = "system") -> bool:
        """软删除"""
        return await self.dao.update_by_id(resource_id, is_deleted=True)
    
    async def restore(self, resource_id: int, user: str = "system") -> bool:
        """恢复删除的记录"""
        return await self.dao.update_by_id(resource_id, is_deleted=False)
```

### 3. 集成外部服务
```python
class DeviceService(BaseService[Device, DeviceDAO]):
    def __init__(self, notification_service=None):
        super().__init__(DeviceDAO())
        self.notification_service = notification_service
    
    async def _after_create(self, result: Device, data: dict, user: str) -> None:
        if self.notification_service:
            await self.notification_service.send_device_created(result)
```

## 测试策略

### 1. 单元测试
```python
import pytest
from app.services import BrandService

@pytest.fixture
async def brand_service():
    return BrandService()

async def test_create_brand(brand_service):
    data = {"name": "测试品牌", "code": "TEST"}
    brand = await brand_service.create(data)
    assert brand.name == "测试品牌"
    assert brand.code == "TEST"
```

### 2. 集成测试
```python
async def test_device_creation_workflow():
    # 创建品牌
    brand = await brand_service.create({"name": "华为", "code": "HUAWEI"})
    
    # 创建型号
    model = await model_service.create({
        "name": "S5700", 
        "brand_id": brand.id, 
        "device_type": "SWITCH"
    })
    
    # 创建设备
    device = await device_service.create({
        "name": "SW-001",
        "management_ip": "192.168.1.1",
        "device_model_id": model.id
    })
    
    assert device.name == "SW-001"
    assert device.device_model.name == "S5700"
```

## 总结

服务层设计遵循以下核心原则：

1. **单一职责**: 每个服务类专注于特定的业务领域
2. **开闭原则**: 通过钩子方法支持扩展，无需修改基类
3. **依赖倒置**: 依赖抽象（DAO接口）而不是具体实现
4. **接口隔离**: 提供细粒度的业务方法，避免胖接口
5. **DRY原则**: 通过基类消除重复代码

这种设计使得服务层具有良好的可维护性、可扩展性和可测试性，为网络自动化平台提供了稳定可靠的业务逻辑支撑。
