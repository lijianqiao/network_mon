# 数据访问层（DAO）设计文档

## 概述

本项目的数据访问层（DAO）基于Tortoise ORM实现，提供了统一的数据库操作接口。通过继承`BaseDAO`基类，所有具体的DAO类都拥有完整的CRUD操作能力，同时支持复杂查询、分页、统计等功能。

## 设计特点

### 1. 统一的基类设计
- `BaseDAO[ModelType]`：泛型基类，提供通用的数据库操作方法
- 类型安全：使用Python 3.10+的类型注解，确保编译时类型检查
- 异步支持：所有操作都是异步的，适合高并发场景

### 2. 完整的CRUD操作
- **创建（Create）**：`create()`, `bulk_create()`
- **读取（Read）**：`get_by_id()`, `list_all()`, `list_by_filters()`, `paginate()`
- **更新（Update）**：`update_by_id()`, `update_by_filters()`
- **删除（Delete）**：`delete_by_id()`, `soft_delete_by_id()`, `delete_by_filters()`

### 3. 高级功能
- 分页查询：`paginate()`
- 计数统计：`count()`, `get_count_by_status()`
- 存在性检查：`exists()`, `exists_by_id()`
- 软删除支持：`soft_delete_by_id()`, `soft_delete_by_filters()`
- 活跃记录过滤：`get_active_records()`

## 文件结构

```
app/repositories/
├── __init__.py                # 模块导出和便捷函数
├── base_dao.py               # 基础DAO类
├── device_dao_v2.py          # 设备相关DAO
├── config_dao.py             # 配置模板DAO
├── monitor_dao.py            # 监控和告警DAO
└── log_dao.py                # 日志相关DAO
```

## DAO类列表

### 设备相关
- `BrandDAO`：品牌管理
- `DeviceModelDAO`：设备型号管理
- `AreaDAO`：区域管理，支持树形结构
- `DeviceGroupDAO`：设备分组管理
- `DeviceDAO`：设备管理，支持复杂搜索

### 配置管理
- `ConfigTemplateDAO`：配置模板管理，支持按品牌和设备类型筛选

### 监控告警
- `MonitorMetricDAO`：监控指标管理，支持时间范围查询和统计
- `AlertDAO`：告警管理，支持状态变更和批量操作

### 日志管理
- `OperationLogDAO`：操作日志管理，支持用户活动统计
- `SystemLogDAO`：系统日志管理，支持错误日志分析

## 使用示例

### 基本CRUD操作

```python
from app.repositories import get_brand_dao

# 获取DAO实例
brand_dao = get_brand_dao()

# 创建记录
brand = await brand_dao.create(
    name="华三",
    code="H3C",
    description="华三通信技术有限公司"
)

# 查询记录
brand = await brand_dao.get_by_id(1)
brand = await brand_dao.get_by_code("H3C")
brands = await brand_dao.list_active_brands()

# 更新记录
updated_brand = await brand_dao.update_by_id(1, description="新的描述")

# 删除记录
success = await brand_dao.delete_by_id(1)
success = await brand_dao.soft_delete_by_id(1)  # 软删除
```

### 分页查询

```python
from app.repositories import get_device_dao

device_dao = get_device_dao()

# 分页查询设备
result = await device_dao.paginate(
    page=1,
    page_size=20,
    filters={"is_deleted": False, "is_active": True},
    prefetch_related=["brand", "area"],
    order_by=["name"]
)

print(f"总数: {result['total']}")
print(f"当前页: {result['page']}")
print(f"设备列表: {result['items']}")
```

### 复杂搜索

```python
# 设备搜索
search_result = await device_dao.search_devices(
    keyword="交换机",
    brand_id=1,
    area_id=2,
    status="ONLINE",
    page=1,
    page_size=10
)

# 告警搜索
alert_result = await alert_dao.search_alerts(
    keyword="CPU",
    severity="CRITICAL",
    status="ACTIVE",
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    page=1,
    page_size=20
)
```

### 统计功能

```python
# 设备状态统计
status_stats = await device_dao.get_device_status_count()
# 结果：{"ONLINE": 150, "OFFLINE": 20, "UNKNOWN": 5}

# 告警统计
alert_stats = await alert_dao.get_alert_statistics(days=30)
print(f"总告警数: {alert_stats['total_alerts']}")
print(f"活跃告警数: {alert_stats['active_alerts']}")

# 用户活动统计
user_stats = await operation_log_dao.get_user_activity_stats(days=30)
```

### 批量操作

```python
# 批量创建
brands_data = [
    {"name": "华为", "code": "HUAWEI"},
    {"name": "思科", "code": "CISCO"},
]
created_brands = await brand_dao.bulk_create(brands_data)

# 批量更新
updated_count = await brand_dao.update_by_filters(
    filters={"is_active": False},
    is_active=True
)

# 批量删除
deleted_count = await brand_dao.delete_by_filters(is_deleted=True)
```

## 最佳实践

### 1. 错误处理

```python
from tortoise.exceptions import DoesNotExist

try:
    device = await device_dao.get_or_404(device_id)
except DoesNotExist:
    # 处理记录不存在的情况
    return {"error": "设备不存在"}
```

### 2. 事务处理

```python
from tortoise.transactions import in_transaction

async def create_device_with_metrics():
    async with in_transaction():
        # 创建设备
        device = await device_dao.create(...)
        
        # 创建初始监控指标
        await metric_dao.create(device_id=device.id, ...)
        
        # 如果任何操作失败，会自动回滚
```

### 3. 性能优化

```python
# 使用预加载避免N+1查询
devices = await device_dao.list_by_filters(
    filters={"is_active": True},
    prefetch_related=["brand", "area", "device_group"]
)

# 使用索引字段进行查询
device = await device_dao.get_by_field("management_ip", "192.168.1.1")
```

### 4. 内存管理

```python
# 大数据量查询时使用限制
large_dataset = await device_dao.list_by_filters(
    filters={"is_active": True},
    order_by=["created_at"]
)[:1000]  # 限制返回数量

# 定期清理旧数据
await metric_dao.clean_old_metrics(days=30)
await alert_dao.clean_old_alerts(days=90)
```

## 扩展指南

### 添加新的DAO类

1. 继承`BaseDAO`并指定模型类型：
```python
class NewModelDAO(BaseDAO[NewModel]):
    def __init__(self):
        super().__init__(NewModel)
```

2. 添加业务特定的方法：
```python
async def get_by_custom_field(self, value: str) -> NewModel | None:
    return await self.get_by_field("custom_field", value)
```

3. 在`__init__.py`中导出新DAO类

### 添加复杂查询方法

```python
async def complex_query(self, **params) -> list[Model]:
    queryset = self.get_queryset()
    
    # 添加复杂的过滤条件
    if params.get("date_range"):
        start, end = params["date_range"]
        queryset = queryset.filter(created_at__range=[start, end])
    
    # 添加聚合查询
    if params.get("include_stats"):
        from tortoise.functions import Count
        queryset = queryset.annotate(related_count=Count("related_field"))
    
    return await queryset
```

## 注意事项

1. **数据库连接**：确保在使用DAO之前已正确初始化Tortoise ORM连接
2. **事务管理**：复杂操作时使用事务确保数据一致性
3. **性能监控**：大数据量操作时注意查询性能和内存使用
4. **错误处理**：适当处理数据库异常和业务逻辑错误
5. **类型安全**：充分利用类型注解进行编译时检查

## 总结

本DAO设计提供了完整、类型安全、高性能的数据访问层，支持复杂的业务场景和查询需求。通过统一的接口设计，开发者可以轻松进行数据库操作，同时保持代码的可维护性和可扩展性。
