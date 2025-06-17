## **网络自动化平台设计方案**

### 1. 项目概述

本项目旨在构建一个现代化的网络自动化平台，核心功能包括：对多厂商网络设备（1000+网络设备（99%交换机，1%路由器）：85%-h3c、10%-huawei、3%-cisco、2%-其他）进行批量信息查询、配置变更、实时状态监控和远程CLI交互。


平台采用异步架构以确保高并发性能，并通过适配器模式优雅地解决多厂商环境的复杂性，最终通过Web界面和API提供服务。

### 2. 技术选型

* **核心框架**:
    * **任务编排**: `Nornir`
    * **设备连接**: `nornir-scrapli`、`scrapli`、`scrapli_community (h3c使用)`
    * **配置管理**: `scrapli-cfg`
    * **输出解析**: `ntc-templates` (TextFSM)
* **服务与交互**:
    * **Web框架**: `FastAPI`
    * **实时交互**: `WebSockets`
* **独立组件**:
    * **设备监控**: `SNMP` (使用 `pysnmp` 或类似库)

### 3. 核心设计原则

* **异步优先**: 整个技术栈基于 `asyncio`，确保高并发下的性能。
* **适配器模式**: 通过设备适配器优雅地处理多厂商差异，实现统一的操作入口。
* **关注点分离**: 将自动化任务执行、周期性监控和Web服务接口清晰分离。
* **声明式配置**: 优先使用 `scrapli-cfg` 进行配置变更，确保操作的安全性和可预测性。

### 4. 系统架构

```Plaintext
┌──────────────────┐      HTTP/WebSocket     ┌──────────────────────────────────┐
│  前端浏览器(用户)  ├─────────────────────────┤          FastAPI 后端服务          │
└──────────────────┘                         └──────────────────────────────────┘
                                                               │
           ┌───────────────────────────────────────────────────┴───────────────────────────────────────────────────┐
           │                                                                                                       │
┌───────────────────────┐                              ┌───────────────────────────┐                       ┌─────────────────────────┐
│ WebSocket CLI 处理模块  │                              │      API 服务模块 (Services)      │                       │   SNMP 监控模块 (独立进程)  │
└───────────────────────┘                              └───────────────────────────┘                       └─────────────────────────┘
           │                                                               │                                       │
           └────────────────────────┬────────────────────────────────────┘                                       │
                                    │                                                                          │ SNMP
                                    │ 调用                                                                         │
                           ┌────────▼──────────┐                                                                 │
                           │   核心任务执行器    │                                                                 │
                           │  (core.TaskRunner)  │                                                                 │
                           └────────▲──────────┘                                                                 │
                                    │                                                                          │
                                    │ 执行 (Nornir Task)                                                         │
                           ┌────────▼──────────┐                                                                 │
                           │    自动化任务      │                                                                 │
                           │  (tasks/*.py)     │                                                                 │
                           └────────▲──────────┘                                                                 │
                                    │                                                                          │
                                    │ 调用 (Adapter)                                                             │
                           ┌────────▼──────────┐                                                                 │
                                    │    设备适配器       │                                                                 │
                           │  (adapters/*.py)  │                                                                 │
                           └────────▲──────────┘                                                                 │
                                    │                                                                          │
                           ┌────────▼──────────┐          SSH/Telnet          ┌─────────────────────────┐
                           │    Scrapli 驱动     ├─────────────────────────────►      网络设备(交换机等)     │
                           └───────────────────┘                              └───────────▲─────────────┘
                                                                                         │
                                                                                         └──────────────────────────────┘
```

### 5. 模块化设计与核心代码

#### 5.1. 目录结构

```
app/web/
    ├── api/               # FastAPI路由
    └── ws/                # WebSocket处理
app/network/
    ├── core/
    │   ├── inventory.py       # 动态设备清单管理器
    │   └── runner.py          # Nornir任务执行器
    ├── adapters/
    │   ├── base.py            # 基础适配器接口
    │   ├── h3c.py             # 华三适配器
    │   └── huawei.py          # 华为适配器
    ├── tasks/
    │   ├── get_info.py        # 通用信息获取任务
    │   └── change_config.py   # 修改设备配置的任务
    ├── services/
    │   └── network_service.py # 封装业务逻辑供API调用
    ├── monitoring/
    │   └── snmp_poller.py     # SNMP轮询器
    └── web/
        ├── api/               # FastAPI路由
        └── ws/                # WebSocket处理
```

#### 5.2. 核心模块代码

**`app/network/core/inventory.py` - 动态设备清单**
```python
# app/network/core/inventory.py
from nornir.core.inventory import Inventory, Host
from typing import List, Dict, Any

# 假设此函数从你的SQLite数据库获取数据
async def get_devices_from_db(device_ids: List[int]) -> List[Dict[str, Any]]:
    # 在此实现数据库查询逻辑
    # 返回一个包含设备信息的字典列表
    # 示例: [{"id": 1, "name": "H3C-S5560", "ip_address": "192.168.1.1", "brand": "H3C", ...}]
    pass

class DynamicInventory:
    async def build(self, device_ids: List[int], password: str = None) -> Inventory:
        devices = await get_devices_from_db(device_ids)
        
        hosts = {}
        for device in devices:
            connection_extras = {}
            if device["brand"] == "H3C":
                # 为H3C设备自动禁用分页
                connection_extras["on_open"] = lambda conn: conn.send_command("screen-length disable")

            hosts[device["name"]] = Host(
                name=device["name"],
                hostname=device.get("ip_address"),
                username=device.get("username", "admin"),
                password=password or device.get("password"),
                platform=self._map_platform(device["brand"]),
                data={"device_id": device["id"], "brand": device["brand"]},
                connection_options={
                    "scrapli": {
                        "extras": connection_extras,
                        "timeout_ops": 60,
                    }
                }
            )
        return Inventory(hosts=hosts)
    
    def _map_platform(self, brand: str) -> str:
        return {
            "H3C": "hp_comware",
            "HUAWEI": "huawei_vrp",
            "CISCO": "cisco_iosxe"
        }.get(brand.upper(), "generic")
```

**`app/network/core/runner.py` - 核心任务执行器**
```python
# app/network/core/runner.py
import getpass
from nornir import InitNornir
from .inventory import DynamicInventory
from typing import Callable, List, Dict, Any

class TaskRunner:
    def __init__(self, use_manual_password: bool = True):
        self.inventory_manager = DynamicInventory()
        self.password = None
        if use_manual_password:
            try:
                self.password = getpass.getpass("请输入网络设备密码: ")
            except Exception as e:
                print(f"无法获取密码: {e}")
                self.password = None

    async def run(self, task_function: Callable, device_ids: List[int], **kwargs) -> Dict[str, Any]:
        inventory = await self.inventory_manager.build(device_ids, self.password)
        
        nr = InitNornir(
            inventory=inventory,
            runner={"plugin": "asyncio", "options": {"num_workers": 100}}
        )
        
        result = await nr.run(task=task_function, **kwargs)

        processed_results = {"success": {}, "failed": {}}
        for host, res in result.items():
            if res.failed:
                processed_results["failed"][host] = str(res.exception)
            else:
                processed_results["success"][host] = res.result
        
        return processed_results
```

**`app/network/adapters/base.py` & `app/network/adapters/h3c.py` - 设备适配器**
```python
# app/network/adapters/base.py
class BaseAdapter:
    def get_command(self, action: str, **params) -> str:
        raise NotImplementedError
    
    def parse(self, action: str, output: str) -> Dict:
        raise NotImplementedError

# app/network/adapters/h3c.py
from ntc_templates.parse import parse_output
from .base import BaseAdapter

class H3CAdapter(BaseAdapter):
    _COMMAND_MAP = {
        "get_version": "display version",
        "find_mac": "display mac-address | include {mac_address}",
    }
    
    def get_command(self, action: str, **params) -> str:
        command_template = self._COMMAND_MAP.get(action)
        if not command_template:
            raise ValueError(f"H3C适配器不支持的action: {action}")
        return command_template.format(**params)

    def parse(self, action: str, output: str) -> Dict:
        if not output:
            return {}
        try:
            if action == "get_version":
                return parse_output("hp_comware", "display version", output)[0]
            if action == "find_mac":
                parts = output.strip().split()
                return {"mac": parts[0], "vlan": parts[1], "interface": parts[3], "status": parts[2]}
        except (IndexError, AttributeError):
            return {"raw": output, "parsing_error": "无法解析输出"}
        return {"raw": output}
```

### 6. 核心业务流程示例

#### 6.1. 业务逻辑 (`tasks` 模块)

**`app/network/tasks/get_info.py` - 查询任务**
```python
# app/network/tasks/get_info.py
from nornir.core.task import Task, Result
from nornir_scrapli.tasks import send_command
from app.adapters import H3CAdapter, HuaweiAdapter # 导入所有适配器

ADAPTERS = {"H3C": H3CAdapter(), "HUAWEI": HuaweiAdapter()}

def get_info_task(task: Task, action: str, **params) -> Result:
    host = task.host
    brand = host.data["brand"]
    adapter = ADAPTERS.get(brand.upper())

    if not adapter:
        return Result(host=host, failed=True, exception=Exception(f"不支持的品牌: {brand}"))

    command = adapter.get_command(action, **params)
    cmd_result = task.run(task=send_command, command=command)
    parsed_data = adapter.parse(action, cmd_result.result)
    
    return Result(host=host, result=parsed_data)
```

#### 6.2. 服务层 (`services` 模块)

**`app/network/services/network_service.py` - 封装调用**
```python
# app/network/services/network_service.py
from app.core.runner import TaskRunner
from app.tasks.get_info import get_info_task
from typing import List, Dict, Any

class NetworkService:
    def __init__(self, use_manual_password: bool = True):
        self.runner = TaskRunner(use_manual_password=use_manual_password)

    async def find_mac_address(self, mac: str, device_ids: List[int]) -> Dict[str, Any]:
        """在指定设备上查找MAC地址"""
        # 清理MAC地址格式
        clean_mac = "".join(filter(str.isalnum, mac)).lower()
        formatted_mac = "-".join(clean_mac[i:i+4] for i in range(0, len(clean_mac), 4))

        results = await self.runner.run(
            task_function=get_info_task,
            device_ids=device_ids,
            action="find_mac",
            mac_address=formatted_mac
        )
        
        # 从结果中过滤出有效信息
        found_on = {}
        for host, data in results.get("success", {}).items():
            if data and data.get("interface"):
                found_on[host] = data
        
        return found_on
```

### 7. 独立模块说明

* **SNMP 监控模块 (`app/network/monitoring/snmp_poller.py`)**
    此模块应作为一个独立的后台进程运行（例如，使用 `systemd` 或 `supervisor` 管理）。它使用 `APScheduler` 等定时任务库，每2分钟执行一次轮询函数。该函数从数据库获取所有需要监控的设备IP，然后使用 `pysnmp` 库并发地向这些IP发送 SNMP `get` 请求（例如，查询 `sysUpTime` OID）。如果请求超时或失败，则认为设备离线，并更新数据库中的设备状态或发送告警。

* **WebSocket 实时CLI (`app/network/web/ws/`)**
    当用户通过Web界面连接到一个设备的CLI时，WebSocket后端会创建一个会话。用户输入的每一行命令，都会通过 `NetworkService` 调用 `TaskRunner`，执行一个简单的 `send_command` 任务。这个任务只针对单个设备，并将原始输出（`result.result`）直接通过WebSocket流式返回给前端的 `xterm.js` 终端，从而实现实时交互。

### 8. 总结

这份设计文档为你提供了一个完整、健壮且现代化的网络自动化平台蓝图。它架构清晰，职责分明，易于扩展和维护，能够高效地满足你提出的所有核心需求。