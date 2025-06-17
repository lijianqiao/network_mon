# 网络设备管理系统设计文档

## 1. 项目概述

### 1.1 项目背景
开发一个基于Nornir + Scrapli + scrapli_community + ntc-templates管理网络设备的web系统，支持1000+多台网络设备的统一管理，包括批量查询、快速修改设备配置、实时监控设备状态等功能。

### 1.2 技术栈
- **开发语言**：Python 3.13+
- **web框架**：Fastapi 0.115.12
- **网络自动化**：Nornir、Scrapli、scrapli_community、ntc-templates
- **数据库**：Postgresql
- **异步处理**：asyncio
- **加密**：cryptography

### 1.3 项目目标
- 支持多种品牌网络设备（华三、华为、思科等）
- 实现设备的区域化管理（单层结构）
- 提供批量操作和实时监控功能
- 支持CLI命令行操作
- 基本的用户名密码认证

## 2. 项目结构

```
network_mon/
├── run.py                      # 应用程序入口
├── requirements.txt            # 项目依赖
├── .gitinore                   # git忽略文件
├── .env                        # 环境变量文件
├── pyproject.toml              # uv 配置文件
├── README.md                   # 项目说明文件
├── app/
│   ├── core/                   # 核心配置
│   │   ├── config.py
│   │   ├── events.py
│   │   └── exceptions.py
│   ├── db/                     # 数据库
│   │   ├── connection.py
│   │   └── router.py
│   ├── models/                 # 数据模型
│   ├── schemas/                # API数据校验
│   ├── services/               # 业务逻辑
│   │   ├── device_service.py
│   │   ├── command_service.py
│   │   ├── config_service.py
│   │   ├── monitor_service.py
│   │   └── task_service.py
│   ├── api/                    # API路由
│   │   └── v1/
│   ├── network/                # 网络自动化
│   │   ├── adapters/          # 设备适配器
│   │   ├── connectors/        # 连接管理
│   │   └── templates/         # 命令模板
│   └── utils/                  # 工具模块
├── tests/                      # 测试文件
├── docs/                       # 文档
└── logs/                       # 日志文件
```

## 3. 系统架构设计

### 3.1 总体架构
系统采用分层架构设计，主要包含以下模块：
- **api路由层**：基于fastapi的web界面
- **业务服务层**：设备管理、批量操作、监控等核心功能
- **数据访问层**：postgresql数据库操作封装
- **网络通信层**：基于Nornir和Scrapli的设备连接管理

### 3.2 核心组件
- **设备管理器**：负责设备信息的增删改查
- **批量操作引擎**：处理多设备并发操作
- **监控调度器**：实现设备状态的定时检测
- **命令适配器**：针对不同品牌设备的命令抽象
- **认证管理器**：处理静态密码和OPT动态密码
- **任务队列管理器**：异步任务调度和执行

## 4. 数据库设计

### 4.1 基础表结构规范
所有表都包含以下基础字段：
```
- id: 主键，自增整数
- created_at: 创建时间
- updated_at: 更新时间
```

### 4.2 品牌表 (brands)
```
字段设计：
- id, created_at, updated_at (基类字段)
- brand_name: 品牌名称（华三/华为/思科等）
- brand_code: 品牌编码（H3C/HUAWEI/CISCO等）
- description: 品牌描述
- is_active: 是否启用
```

### 4.3 设备类型表 (device_types)
```
字段设计：
- id, created_at, updated_at (基类字段)
- type_name: 类型名称（交换机/路由器/防火墙等）
- type_code: 类型编码（SWITCH/ROUTER/FIREWALL等）
- description: 类型描述
- is_active: 是否启用
```

### 4.4 设备型号表 (device_models)
```
字段设计：
- id, created_at, updated_at (基类字段)
- brand_id: 关联品牌ID（外键）
- type_id: 关联设备类型ID（外键）
- model_name: 型号名称（S5820V2-52P-LI等）
- model_code: 型号编码
- description: 型号描述
- is_active: 是否启用
```

### 4.5 区域表 (areas)
```
字段设计：
- id, created_at, updated_at (基类字段)
- area_name: 区域名称
- area_code: 区域编码
- snmp_community: SNMP团体名
- description: 区域描述
- contact_person: 联系人
- contact_phone: 联系电话
```

### 4.6 设备表 (devices)
```
字段设计：
- id, created_at, updated_at (基类字段)
- brand_id: 关联品牌ID（外键）
- type_id: 关联设备类型ID（外键）
- model_id: 关联型号ID（外键）
- area_id: 关联区域ID（外键）
- name: 设备名称
- management_ip: 管理IP地址
- serial_number: 序列号
- rack_position: 机架位置
- account: 登录账号
- password: 静态密码（加密存储）
- opt_enabled: 是否启用OPT动态密码
- snmp_enabled: 是否启用SNMP
- status: 设备状态（在线/离线/异常）
- monitoring_enabled: 是否启用监控
- monitoring_interval: 监控间隔（分钟）
- last_monitor_time: 最后监控时间
- remarks: 备注信息
```

### 4.7 设备监控历史表 (device_monitor_history)
```
字段设计：
- id, created_at, updated_at (基类字段)
- device_id: 关联设备ID（外键）
- status: 检查时的状态（在线/离线/异常）
- response_time: 响应时间（ms）
- error_message: 错误信息
- check_method: 检查方式（ping/snmp/ssh）
```

### 4.8 任务队列表 (task_queue)
```
字段设计：
- id, created_at, updated_at (基类字段)
- task_type: 任务类型（批量查询/配置修改/监控检查等）
- target_devices: 目标设备ID列表（JSON格式）
- task_params: 任务参数（JSON格式，存储命令、配置等）
- status: 任务状态（待执行/执行中/已完成/失败）
- priority: 任务优先级（1-10，默认5）
- timeout_seconds: 超时时间（默认300秒）
- retry_count: 当前重试次数（默认0）
- max_retries: 最大重试次数（默认3）
- started_at: 开始执行时间
- completed_at: 完成时间
- result: 执行结果（JSON格式）
```

### 4.9 命令模板表 (command_templates)
```
字段设计：
- id, created_at, updated_at (基类字段)
- template_name: 模板名称
- template_category: 模板分类
- brand_id: 关联品牌ID（外键）
- type_id: 关联设备类型ID（外键）
- command_template: 命令模板
- parameter_schema: 参数结构定义（JSON）
- output_parser: 输出解析规则
- description: 模板描述
```

### 4.10 操作日志表 (operation_logs)
```
字段设计：
- id, created_at, updated_at (基类字段)
- device_id: 关联设备ID（外键）
- operation_type: 操作类型
- command: 执行命令
- result: 执行结果
- operator: 操作人员
```

### 4.15 表关系设计
```
主要外键关系：
- devices.brand_id → brands.id
- devices.type_id → device_types.id  
- devices.model_id → device_models.id
- devices.area_id → areas.id
- device_models.brand_id → brands.id
- device_models.type_id → device_types.id
- device_monitor_history.device_id → devices.id
- device_configs.device_id → devices.id
- task_results.task_id → task_queue.id
- task_results.device_id → devices.id
- command_templates.brand_id → brands.id
- command_templates.type_id → device_types.id
- operation_logs.device_id → devices.id
```

### 4.12 设备分组表 (device_groups) - 简化分组管理
```
字段设计：
- id, created_at, updated_at (基类字段)
- group_name: 分组名称
- description: 分组描述
- device_ids: 设备ID列表（JSON格式）
```

### 4.13 设备配置表 (device_configs) - 配置管理
```
字段设计：
- id, created_at, updated_at (基类字段)
- device_id: 关联设备ID（外键）
- config_type: 配置类型（running/startup/backup）
- config_content: 配置内容
- config_hash: 配置哈希值（用于检测变化）
- is_current: 是否当前配置
```

### 4.14 任务执行结果详情表 (task_results)
```
字段设计：
- id, created_at, updated_at (基类字段)
- task_id: 关联任务ID（外键）
- device_id: 关联设备ID（外键）
- status: 执行状态（success/failed/timeout）
- command: 执行的命令
- output: 命令输出
- error_message: 错误信息
- execution_time: 执行时间（秒）
```

## 5. 功能模块设计

### 5.1 设备管理模块
**位置**：`services/device_service.py` + `api/device_routes.py`

**核心功能**：
- 品牌、类型、型号的基础数据管理
- 设备信息的录入、编辑、删除
- 设备按区域管理（单层结构）
- 设备分组管理
- 设备导入导出（支持Excel/CSV格式）
- 设备信息批量更新

**技术实现**：
- FastAPI路由提供RESTful API接口
- 支持设备列表的多条件筛选和分页
- 实现设备信息的表单化编辑
- 支持按品牌、类型、区域、状态等条件筛选

### 5.2 批量查询模块
**位置**：`services/command_service.py` + `api/command_routes.py`

**核心功能**：
- MAC地址批量查询
- 接口状态批量检查
- 配置信息批量获取
- 自定义命令批量执行

**技术实现**：
- 使用命令模板系统，根据设备品牌自动匹配命令
- 利用Nornir的并发执行机制
- 查询任务加入任务队列异步执行
- 查询结果的格式化展示和导出

### 5.3 配置修改模块
**位置**：`services/config_service.py` + `api/config_routes.py`

**核心功能**：
- VLAN配置批量修改
- 接口描述批量更新
- 访问控制列表配置
- 路由配置管理
- 配置备份和查看

**技术实现**：
- 基于命令模板的批量操作
- 配置变更任务队列化处理
- 配置变更前自动备份
- 操作结果的实时反馈

### 5.4 实时监控模块
**位置**：`services/monitor_service.py` + `api/monitor_routes.py`

**核心功能**：
- 设备在线状态监控
- 监控历史数据管理
- 基础告警机制
- 监控任务调度

**技术实现**：
- 使用asyncio实现定时任务调度
- 监控任务通过任务队列执行
- 监控结果存储到监控历史表
- WebSocket推送实时状态更新

### 5.5 任务管理模块
**位置**：`services/task_service.py` + `api/task_routes.py`

**核心功能**：
- 任务队列管理
- 任务状态跟踪
- 任务结果查看
- 任务执行统计

**技术实现**：
- 任务队列的优先级调度
- 基于Celery的异步任务执行
- 任务执行进度的实时更新
- 失败任务的重试机制

### 5.6 CLI命令行模块 - 基于WebSocket实现
**位置**：`services/cli_service.py` + `api/websocket_routes.py`

**核心功能**：
- Web终端界面（类似SSH终端体验）
- 实时命令执行和输出流
- 命令历史记录和自动补全
- 多设备并发终端会话
- 命令执行进度实时显示

**技术实现**：
- **WebSocket连接**：实现双向实时通信
- **终端会话管理**：每个连接维护独立的会话状态
- **命令解析器**：支持内置命令和设备命令
- **输出流处理**：实时推送命令执行结果
- **会话持久化**：命令历史和会话状态保存

**WebSocket消息格式**：
```json
{
    "type": "command",
    "data": {
        "device_id": 123,
        "command": "display interface",
        "session_id": "uuid"
    }
}

{
    "type": "output",
    "data": {
        "session_id": "uuid",
        "content": "命令输出内容",
        "status": "running|success|error"
    }
}
```

**前端集成**：
- 使用xterm.js等终端库提供原生终端体验
- 支持终端快捷键和鼠标操作
- 实时显示命令执行状态和进度

## 6. 命令模板系统设计

### 6.1 模板文件结构

### 6.2 模板参数化机制
命令模板支持参数占位符，例如：
```json
{
    "template_name": "查询MAC地址",
    "template_category": "查询类",
    "command_template": "display mac-address | include {mac_address}",
    "parameter_schema": {
        "mac_address": {
            "type": "string",
            "required": true,
            "description": "要查询的MAC地址"
        }
    },
    "output_parser": "regex: ^(\\S+)\\s+(\\S+)\\s+(\\S+)\\s+(\\S+)$"
}
```

### 6.3 模板使用流程
1. 用户选择功能（如查询MAC地址）
2. 系统根据目标设备的品牌和类型匹配对应模板
3. 用户输入所需参数
4. 系统将参数填入模板生成实际命令
5. 命令执行任务加入任务队列
6. 根据解析规则处理执行结果

### 6.4 输出解析系统
每个命令模板配置相应的输出解析规则，用于：
- 提取关键信息
- 格式化显示结果
- 错误信息识别
- 结构化数据存储

## 7. 网络连接架构

### 7.1 连接器层次结构
```
BaseConnector (基础连接器)
├── SSHConnector (SSH连接器)
├── SNMPConnector (SNMP连接器)
└── TelnetConnector (Telnet连接器)
```

### 7.2 设备适配器层次结构
```
BaseAdapter (基础适配器)
├── H3CAdapter (华三适配器)
├── HuaweiAdapter (华为适配器)
└── CiscoAdapter (思科适配器)
```

### 7.3 连接管理
- 连接池管理，复用连接资源
- 超时和重试机制
- 并发连接数控制
- 连接状态监控

## 8. 安全设计 - 简化版本

### 8.1 基础密码管理
**位置**：`utils/crypto.py`

- 静态密码采用AES-256加密存储
- 设备认证使用用户名密码方式
- 密码输入界面的基础安全保护
- API接口的简单token认证

### 8.2 基础访问控制
- 敏感操作的确认机制
- 操作日志的完整记录
- 基本的API访问限制

## 9. 性能优化 - 最小化方案

### 9.1 并发处理
- 使用连接池管理设备连接（每设备最多2个SSH连接）
- Nornir并发工作线程限制（20个worker）
- 超时处理和重试机制
- 基于优先级的任务调度

### 9.2 数据库优化
- 关键字段的索引设计
- 监控历史数据的定期清理（保留3个月）
- 数据库连接池管理
- 分页查询优化

### 9.3 缓存优化
- Redis缓存设备在线状态（5分钟TTL）
- 命令模板启动时加载到内存
- 设备基础信息缓存（30分钟TTL）
- 频繁查询结果的短期缓存

## 10. 日志和监控

### 10.1 日志系统
**位置**：`utils/logger.py`

- 分级日志记录（DEBUG/INFO/WARNING/ERROR）
- 日志文件轮转
- 操作审计日志
- 性能监控日志

### 10.2 监控指标
- 任务执行统计
- 设备连接成功率
- 系统资源使用情况
- 用户操作频率

## 11. 扩展性设计

### 11.1 设备品牌扩展
- 通过品牌表和命令模板表支持新品牌
- 插件化的设备适配器架构
- 标准化的设备抽象接口
- 新品牌设备的快速接入流程

### 11.2 功能模块扩展
- 模块化的系统架构
- 标准化的接口定义
- 基于任务队列的功能扩展
- 第三方插件的集成支持

### 11.3 数据库扩展
- 预留扩展字段设计
- 版本迁移机制
- 数据备份和恢复
- 多数据库支持能力

## 12. 数据库索引设计

### 12.1 必需索引
```sql
-- 设备表索引
CREATE INDEX idx_devices_management_ip ON devices(management_ip);
CREATE INDEX idx_devices_brand_type ON devices(brand_id, type_id);
CREATE INDEX idx_devices_area ON devices(area_id);
CREATE INDEX idx_devices_status ON devices(status);

-- 任务队列索引
CREATE INDEX idx_task_queue_status ON task_queue(status);
CREATE INDEX idx_task_queue_priority ON task_queue(priority, created_at);

-- 监控历史索引
CREATE INDEX idx_device_monitor_device_time ON device_monitor_history(device_id, created_at);

-- 操作日志索引
CREATE INDEX idx_operation_logs_device_time ON operation_logs(device_id, created_at);

-- 配置表索引
CREATE INDEX idx_device_configs_device_type ON device_configs(device_id, config_type);
```

## 13. 技术栈确认

### 13.1 核心依赖
```python
# Web框架
fastapi[standard]
uvicorn[standard]

# 数据库
tortoise-orm[asyncpg]
aerich  # 数据库迁移

# 网络自动化
nornir
scrapli
scrapli-community
ntc-templates

# 任务队列和缓存
celery
redis[hiredis]

# 工具库
cryptography  # 密码加密
pandas       # 数据处理
openpyxl    # Excel导入导出
loguru      # 日志
```

### 13.2 项目结构优化

**核心特点：**
- 单层区域管理，简化组织结构
- 基础的用户名密码认证，去除复杂的权限控制
- 保留CLI模块，提供灵活的设备操作方式
- 配置备份机制，确保操作安全性
- 基于任务队列的异步处理，支持大规模设备管理

**技术优势：**
- FastAPI + Nornir + Scrapli现代化技术栈
- PostgreSQL数据库保证数据一致性
- Redis缓存提升系统性能
- Celery任务队列支持高并发操作

该设计确保系统的稳定性、高效性和可维护性，同时为后续功能扩展预留了足够的空间。