# 网络自动化设计

## 1. 技术选型说明

- **Nornir**: 网络自动化框架，提供设备清单管理和并发执行
- **Scrapli**: 高性能SSH连接库，支持异步操作
- **scrapli_community**: 扩展更多设备驱动支持
- **ntc-templates**: TextFSM模板库，用于解析设备输出

## 2. 模块结构

```
app/network/
├── core/                   # 核心功能
│   ├── inventory.py       # 动态设备清单
│   └── executor.py        # 任务执行器
├── adapters/              # 设备适配器
│   ├── base.py           # 基础适配器
│   ├── h3c.py            # 华三适配器
│   └── huawei.py         # 华为适配器
├── connectors/            # 连接管理
│   └── pool.py           # 连接池
└── templates/             # 命令模板
    ├── h3c.json          # 华三命令模板
    └── huawei.json       # 华为命令模板
```

## 3. 动态设备清单

### 从数据库构建Nornir清单
```python
# app/network/inventory.py
class DynamicInventory:
    async def build_inventory(self, device_ids: List[int]) -> Inventory:
        # 从FastAPI模块获取设备信息
        devices = await get_devices_for_network(device_ids)
        
        hosts = {}
        for device in devices:
            hosts[device["name"]] = Host(
                name=device["name"],
                hostname=device["credentials"]["host"],
                username=device["credentials"]["username"],
                password=device["credentials"]["password"],
                platform=self._map_platform(device["brand"]),
                data={"device_id": device["id"], "brand": device["brand"]}
            )
        
        return Inventory(hosts=hosts)
    
    def _map_platform(self, brand: str) -> str:
        """映射品牌到Scrapli平台"""
        return {
            "H3C": "hp_comware",
            "HUAWEI": "huawei_vrp",
            "CISCO": "cisco_iosxe"
        }.get(brand, "linux")
```

## 4. 任务执行器

### 统一的命令执行接口
```python
# app/network/executor.py  
class NetworkExecutor:
    def __init__(self):
        self.inventory_manager = DynamicInventory()
    
    async def execute_commands(
        self, 
        device_ids: List[int], 
        commands: List[str]
    ) -> Dict[str, Any]:
        # 构建设备清单
        inventory = await self.inventory_manager.build_inventory(device_ids)
        
        # 初始化Nornir
        nr = InitNornir(
            inventory=inventory,
            runner={"plugin": "threaded", "options": {"num_workers": 10}}
        )
        
        # 执行命令
        result = nr.run(task=self._send_commands, commands=commands)
        return self._process_results(result)
    
    def _send_commands(self, task: Task, commands: List[str]) -> Result:
        results = []
        for cmd in commands:
            result = task.run(send_command, command=cmd)
            results.append({"command": cmd, "output": result.result})
        return Result(host=task.host, result=results)
```

## 5. 设备适配器

### 品牌特定的命令和解析
```python
# adapters/base.py
class BaseAdapter:
    def get_command(self, action: str, **params) -> str:
        """获取特定品牌的命令"""
        raise NotImplementedError
    
    def parse_output(self, action: str, output: str) -> dict:
        """解析命令输出"""
        raise NotImplementedError

# adapters/h3c.py
class H3CAdapter(BaseAdapter):
    COMMANDS = {
        "show_version": "display version",
        "show_interfaces": "display interface brief", 
        "show_mac": "display mac-address vlan {vlan_id}",
        "show_arp": "display arp | include {ip_address}"
    }
    
    def get_command(self, action: str, **params) -> str:
        template = self.COMMANDS.get(action, "")
        return template.format(**params)
    
    def parse_output(self, action: str, output: str) -> dict:
        # 使用ntc-templates解析
        from ntc_templates.parse import parse_output
        return parse_output(
            platform="hp_comware", 
            command=action.replace("_", " "), 
            data=output
        ) or {"raw": output}
```

## 6. 命令模板系统

### JSON格式的命令模板
```json
// templates/h3c.json
{
    "查询版本信息": {
        "command": "display version",
        "description": "获取设备版本信息",
        "parser": "hp_comware_display_version"
    },
    "查询接口状态": {
        "command": "display interface {interface}",
        "parameters": {
            "interface": {"type": "string", "required": true}
        },
        "description": "查询指定接口状态"
    },
    "查询MAC地址": {
        "command": "display mac-address vlan {vlan_id}",
        "parameters": {
            "vlan_id": {"type": "integer", "required": true}
        }
    }
}
```

## 7. 连接池管理

### 复用SSH连接提升性能
```python
# connectors/pool.py
class ConnectionPool:
    def __init__(self, max_connections_per_host: int = 2):
        self._pools = {}
        self._max_connections = max_connections_per_host
    
    async def get_connection(self, host_config: dict) -> AsyncScrapli:
        host_key = f"{host_config['host']}:{host_config.get('port', 22)}"
        
        # 尝试从池中获取现有连接
        if host_key in self._pools and not self._pools[host_key].empty():
            conn = await self._pools[host_key].get()
            if await self._is_alive(conn):
                return conn
        
        # 创建新连接
        return await self._create_connection(host_config)
    
    async def return_connection(self, host_key: str, conn: AsyncScrapli):
        if await self._is_alive(conn):
            await self._pools[host_key].put(conn)
        else:
            await conn.close()
```

## 8. 高级功能

### 模板化命令执行
```python
class TemplateExecutor:
    def __init__(self):
        self.adapters = {
            "H3C": H3CAdapter(),
            "HUAWEI": HuaweiAdapter()
        }
    
    async def execute_template_command(
        self, 
        action: str, 
        device_ids: List[int],
        params: dict = None
    ) -> dict:
        """执行模板化命令"""
        inventory = await self.inventory_manager.build_inventory(device_ids)
        results = {"success": {}, "failed": {}}
        
        for host_name, host in inventory.hosts.items():
            brand = host.data["brand"]
            adapter = self.adapters.get(brand)
            
            if not adapter:
                results["failed"][host_name] = f"Unsupported brand: {brand}"
                continue
            
            try:
                # 获取命令
                command = adapter.get_command(action, **(params or {}))
                
                # 执行命令  
                executor = NetworkExecutor()
                result = await executor.execute_commands([host.data["device_id"]], [command])
                
                # 解析结果
                if result["success"]:
                    output = list(result["success"].values())[0][0]["output"]
                    parsed = adapter.parse_output(action, output)
                    results["success"][host_name] = {
                        "command": command,
                        "parsed_data": parsed
                    }
                
            except Exception as e:
                results["failed"][host_name] = str(e)
        
        return results
```

## 9. 批量操作示例

### 常用网络操作
```python
class NetworkOperations:
    def __init__(self):
        self.template_executor = TemplateExecutor()
    
    async def batch_show_version(self, device_ids: List[int]):
        """批量查询设备版本"""
        return await self.template_executor.execute_template_command(
            "show_version", device_ids
        )
    
    async def batch_show_interface(self, device_ids: List[int], interface: str):
        """批量查询接口状态"""
        return await self.template_executor.execute_template_command(
            "show_interface_detail", 
            device_ids, 
            {"interface": interface}
        )
    
    async def search_mac_address(self, device_ids: List[int], vlan_id: int):
        """批量查询指定VLAN的MAC地址表"""
        return await self.template_executor.execute_template_command(
            "show_mac", 
            device_ids, 
            {"vlan_id": vlan_id}
        )
```

## 10. 与FastAPI集成

### 网络操作API
```python
# services/network_service.py
class NetworkService:
    def __init__(self):
        self.operations = NetworkOperations()
    
    async def execute_network_task(self, task_data: dict) -> dict:
        """执行网络任务"""
        task_type = task_data["task_type"]
        device_ids = task_data["target_devices"] 
        params = task_data.get("params", {})
        
        if task_type == "batch_command":
            commands = params["commands"]
            executor = NetworkExecutor()
            return await executor.execute_commands(device_ids, commands)
        
        elif task_type == "template_command":
            action = params["action"]
            template_params = params.get("template_params", {})
            template_executor = TemplateExecutor()
            return await template_executor.execute_template_command(
                action, device_ids, template_params
            )
```

## 11. 关键设计原则

- **异步优先**: 全异步操作支持高并发
- **连接复用**: 连接池减少建连开销
- **适配器模式**: 优雅处理多品牌设备差异
- **模板化**: 标准化常用网络操作
- **错误处理**: 完善的异常处理和日志记录
- **可扩展**: 易于添加新品牌和新功能

这个设计充分利用了Nornir和Scrapli的优势，同时保持了代码的简洁性和可维护性。
