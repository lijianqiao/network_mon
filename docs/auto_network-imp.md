### **Nornir + Scrapli + TextFSM 方案评估与设计**

这套方案组合的核心优势在于：**并发性能**、**现代化的连接库**和 **标准化的数据结构**。下面我们从几个维度进行分析。

### 依赖

# 核心依赖 - 已安装
nornir==3.5.0
nornir-scrapli==2025.1.30
scrapli==2025.1.30
scrapli-community==2025.1.30
```python
uv add textfsm
uv add ntc-templates

# 其他依赖 - 已安装
uv add rich  # 美化输出
```

### **方案设计**

划分为以下几个逻辑模块，这会让代码结构更清晰，易于维护和扩展。

#### **模块一：库存加载模块 (Inventory Loader)**

**职责**:  
  1. 连接到 SQLite 数据库。  
  2. 查询设备信息表（IP、设备名、设备类型/平台、凭据等）。  
  3. 将查询到的数据转换成 Nornir Inventory 所需的特定字典格式。  
  4. 实现设备分组和过滤功能
  5. 支持设备健康状态检查和过滤

**实现思路**:  
  创建一个 load_from_db 函数。  
  此函数的核心是生成一个两层嵌套的字典：hosts 和 groups。  
  hosts 字典的键是设备名，值是包含该设备所有属性（hostname, platform, username, password等）的字典。  
  
  **平台映射优化**：
  ```python
  platform_mapping = {
      'h3c': 'hp_comware',      # H3C设备使用hp_comware
      'huawei': 'huawei_vrp',   # 华为VRP系统
      'cisco_ios': 'cisco_ios', # 思科IOS
      'cisco_iosxe': 'cisco_iosxe', # 思科IOS-XE
      'cisco_nxos': 'cisco_nxos'    # 思科NX-OS
  }
  ```
  
  **设备分组策略**：
  - 按品牌分组：h3c_devices, huawei_devices, cisco_devices
  - 按地域分组：beijing_devices, shanghai_devices
  - 按设备类型分组：switches, routers
  - 按在线状态分组：online_devices, offline_devices
  
  在初始化 Nornir 对象时，直接将这个函数生成的字典传给 inventory 参数。

#### **模块二：任务定义模块 (Task Definitions)**

**职责**:  
  1. 定义所有具体的网络操作，每一个操作都是一个独立的 Python 函数。  
  2. 这些函数都接受一个 Task 对象作为第一个参数。  
  3. 实现任务模板化，支持不同品牌的命令差异 
  4. 支持批量操作和条件执行

**实现思路**:  
  例如，创建一个 get_version.py 文件，里面定义一个 get_device_version(task: Task) -> Result 函数。  
  
  **命令模板化**：
  ```python
  VERSION_COMMANDS = {
      'hp_comware': 'display version',
      'huawei_vrp': 'display version',  
      'cisco_ios': 'show version',
      'cisco_iosxe': 'show version'
  }
  ```
  
  函数内部，根据设备平台选择合适的命令：
  ```python
  platform = task.host.platform
  command = VERSION_COMMANDS.get(platform, 'show version')
  result = task.run(task=nornir_scrapli.send_command, 
                   command=command, use_textfsm=True)
  ```
  
  **支持的任务类型**：
  - 信息收集：get_version, get_interfaces, get_mac_table
  - 配置操作：backup_config, push_config
  - 批量操作：batch_commands, conditional_execute
  - 监控检查：health_check, connectivity_test

#### **模块三：业务逻辑与执行模块 (Orchestrator)**

**职责**:  
  1. 作为程序的入口点 (main 函数)。  
  2. 初始化 Nornir，并调用"库存加载模块"来加载库存。  
  3. 提供一个用户交互界面（可以是简单的命令行参数），让用户选择要执行哪个任务（如 get_version），以及在哪些设备上执行（例如按设备类型、按位置等进行过滤）。  
  4. 调用 nr.run() 来执行"任务定义模块"中定义的任务。  
  5. 将 nr.run() 返回的结果传递给"结果处理模块"。  
  6. 实现进度显示和中断处理
  7. 支持并发数动态调整

**实现思路**:  
  使用 Python 的 argparse 库来解析命令行参数。  
  使用 nr.filter() 方法根据用户的输入筛选目标设备。  
  
  **性能优化配置**：
  ```python
  # 根据设备数量动态调整并发数
  device_count = len(filtered_hosts)
  num_workers = min(device_count, 50)  # 最多50个并发
  
  nr = InitNornir(
      inventory=inventory_dict,
      runner={
          "plugin": "threaded",
          "options": {
              "num_workers": num_workers,
          },
      },
  )
  ```
  
  **执行流程增强**：
  - 任务执行前的预检查
  - 实时进度显示（使用rich库）
  - 支持Ctrl+C优雅中断
  - 失败重试机制

#### **模块四：结果处理与输出模块 (Result Processor)**

**职责**:  
  1. 接收 Nornir 返回的 AggregatedResult 对象。  
  2. 遍历每个设备的结果，检查任务是否成功执行。  
  3. 从成功的结果中提取 TextFSM 解析后的结构化数据（通常是一个列表或字典）。  
  4. 将这些干净、标准化的数据进行格式化，并以用户需要的方式呈现。  
  5. 实现TextFSM模板回退机制
  6. 支持多种输出格式和数据存储

**实现思路**:  
  创建一个 process_results 函数，接收 AggregatedResult。  
  遍历 result 字典，result[hostname][0].result 存储的就是解析后的数据。  
  
  **TextFSM模板处理策略**：
  ```python
  # 模板优先级：自定义模板 → 官方模板 → 原始输出
  TEMPLATE_PATHS = [
      './custom_templates/',      # 自定义H3C模板
      'ntc_templates/templates/', # 官方模板
  ]
  ```
  
  **输出格式支持**：  
    - 终端表格显示（使用 rich 库）
    - JSON格式输出
    - 写入SQLite数据库  
    - 实时Web界面显示（可选）

#### **模块五：配置与异常处理模块 (Configuration & Exception Handler)** **[新增]**

**职责**:  
  1. 管理全局配置参数（超时时间、重试次数、日志级别等）  
  2. 处理各种网络异常和设备异常  
  3. 提供统一的日志记录和监控功能  
  4. 实现连接池管理和资源优化  

**实现思路**:  
  **配置管理**：
  ```python
  DEFAULT_CONFIG = {
      'connection_timeout': 30,
      'command_timeout': 60, 
      'max_retries': 3,
      'retry_delay': 5,
      'log_level': 'INFO',
      'max_concurrent_connections': 50
  }
  ```
  
  **异常处理策略**：
  - 连接超时：自动重试3次，记录失败设备
  - 认证失败：记录并跳过，不重试
  - 命令执行失败：记录错误信息，继续其他设备
  - 解析失败：回退到原始输出
  
  **日志和监控**：
  - 详细的执行日志（成功/失败统计）
  - 性能监控（执行时间、成功率）
  - 异常告警机制
  - 设备连接状态监控

#### **模块六：模板管理模块 (Template Manager)** **[新增]**

**职责**:  
  1. 管理TextFSM模板库  
  2. 为H3C设备提供自定义模板支持  
  3. 实现模板的动态加载和缓存  
  4. 提供模板测试和验证功能  

**实现思路**:  
  **H3C设备专用模板**：
  ```
  app/network/templates/
  ├── hp_comware_display_version.textfsm
  ├── hp_comware_display_interface.textfsm  
  ├── hp_comware_display_mac-address.textfsm
  └── hp_comware_display_ip_routing-table.textfsm
  ```
  
  **模板管理功能**：
  - 模板有效性检查
  - 模板性能测试
  - 模板版本管理
  - 自动模板更新

### **整体架构优势**

1. **模块化设计**：各模块职责清晰，易于维护和扩展
2. **品牌兼容性**：特别优化了H3C设备支持
3. **性能优化**：动态并发控制，连接池复用
4. **异常处理**：完善的错误处理和重试机制  
5. **可扩展性**：支持新的设备品牌和命令类型
6. **用户友好**：丰富的输出格式和进度显示
