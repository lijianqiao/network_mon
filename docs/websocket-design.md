# WebSocket实时交互设计

## 1. 设计目标

- **实时终端**: 提供类似SSH客户端的Web终端体验
- **任务监控**: 实时显示批量任务执行进度
- **状态推送**: 设备状态变化的实时通知
- **多会话**: 支持同时连接多个设备

## 2. 模块结构

```
app/websocket/
├── core/                   # 核心功能
│   ├── manager.py         # 连接管理器
│   ├── terminal.py        # 终端会话
│   └── events.py          # 事件系统
├── handlers/              # 消息处理器
│   ├── terminal_handler.py    # 终端消息处理
│   ├── task_handler.py        # 任务监控处理
│   └── notification_handler.py # 通知处理
└── routers/               # WebSocket路由
    ├── terminal.py        # 终端路由
    ├── monitor.py         # 监控路由
    └── notification.py    # 通知路由
```

## 3. 连接管理器

### 管理所有WebSocket连接
```python
# core/manager.py
class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._user_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None):
        """建立连接"""
        await websocket.accept()
        self._connections[connection_id] = websocket
        
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)
    
    async def disconnect(self, connection_id: str):
        """断开连接"""
        if connection_id in self._connections:
            del self._connections[connection_id]
            
        # 清理用户连接映射
        for user_id, conn_ids in self._user_connections.items():
            conn_ids.discard(connection_id)
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """发送消息到指定连接"""
        websocket = self._connections.get(connection_id)
        if websocket:
            await websocket.send_json(message)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """广播消息给用户的所有连接"""
        conn_ids = self._user_connections.get(user_id, set())
        for conn_id in conn_ids:
            await self.send_to_connection(conn_id, message)

# 全局连接管理器实例
connection_manager = ConnectionManager()
```

## 4. 终端会话管理

### 设备终端会话
```python
# core/terminal.py
class TerminalSession:
    def __init__(self, device_id: int, connection_id: str):
        self.device_id = device_id
        self.connection_id = connection_id
        self.device_connection = None
        self.command_history = []
        self.is_connected = False
    
    async def connect_device(self):
        """连接到网络设备"""
        try:
            # 从FastAPI模块获取设备认证信息
            creds = await get_device_credentials(self.device_id)
            
            # 建立设备连接
            from network.connectors.pool import get_connection
            self.device_connection = await get_connection(creds)
            self.is_connected = True
            
            # 发送连接成功消息
            await connection_manager.send_to_connection(self.connection_id, {
                "type": "terminal_connected",
                "device_id": self.device_id,
                "message": f"Connected to {creds['host']}"
            })
            
        except Exception as e:
            await connection_manager.send_to_connection(self.connection_id, {
                "type": "terminal_error", 
                "error": str(e)
            })
    
    async def execute_command(self, command: str):
        """执行命令"""
        if not self.is_connected:
            await self.connect_device()
        
        try:
            # 记录命令历史
            self.command_history.append(command)
            
            # 发送命令执行开始消息
            await connection_manager.send_to_connection(self.connection_id, {
                "type": "command_start",
                "command": command
            })
            
            # 执行命令
            result = await self.device_connection.send_command(command)
            
            # 发送命令结果
            await connection_manager.send_to_connection(self.connection_id, {
                "type": "command_output",
                "command": command,
                "output": result.result,
                "status": "success"
            })
            
        except Exception as e:
            await connection_manager.send_to_connection(self.connection_id, {
                "type": "command_output",
                "command": command,
                "output": str(e),
                "status": "error"
            })
    
    async def cleanup(self):
        """清理会话"""
        if self.device_connection:
            await self.device_connection.close()
        self.is_connected = False

# 全局会话管理
terminal_sessions: Dict[str, TerminalSession] = {}
```

## 5. WebSocket路由

### 终端路由
```python
# routers/terminal.py
@router.websocket("/terminal/{device_id}")
async def terminal_endpoint(websocket: WebSocket, device_id: int):
    connection_id = str(uuid.uuid4())
    
    try:
        # 建立WebSocket连接
        await connection_manager.connect(websocket, connection_id)
        
        # 创建终端会话
        session = TerminalSession(device_id, connection_id)
        terminal_sessions[connection_id] = session
        
        # 消息循环
        async for message in websocket.iter_text():
            data = json.loads(message)
            await handle_terminal_message(data, session)
            
    except WebSocketDisconnect:
        # 清理会话
        if connection_id in terminal_sessions:
            await terminal_sessions[connection_id].cleanup()
            del terminal_sessions[connection_id]
        await connection_manager.disconnect(connection_id)

async def handle_terminal_message(data: dict, session: TerminalSession):
    """处理终端消息"""
    message_type = data.get("type")
    
    if message_type == "command":
        command = data.get("command", "")
        await session.execute_command(command)
    
    elif message_type == "connect":
        await session.connect_device()
    
    elif message_type == "get_history":
        await connection_manager.send_to_connection(session.connection_id, {
            "type": "command_history",
            "history": session.command_history
        })
```

### 任务监控路由
```python
# routers/monitor.py
@router.websocket("/monitor/tasks")
async def task_monitor_endpoint(websocket: WebSocket, user_id: str = None):
    connection_id = str(uuid.uuid4())
    
    try:
        await connection_manager.connect(websocket, connection_id, user_id)
        
        # 发送当前任务状态
        await send_current_task_status(connection_id)
        
        # 保持连接监听
        async for message in websocket.iter_text():
            data = json.loads(message)
            await handle_monitor_message(data, connection_id)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)

async def handle_monitor_message(data: dict, connection_id: str):
    """处理监控消息"""
    if data.get("type") == "subscribe_task":
        task_id = data.get("task_id")
        # 订阅特定任务的更新
        await subscribe_task_updates(connection_id, task_id)
```

## 6. 事件系统

### 实时事件推送
```python
# core/events.py
class EventBus:
    def __init__(self):
        self._subscribers = {}
    
    def subscribe(self, event_type: str, callback):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def publish(self, event_type: str, data: dict):
        """发布事件"""
        subscribers = self._subscribers.get(event_type, [])
        for callback in subscribers:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

# 全局事件总线
event_bus = EventBus()

# 任务状态变化事件处理
async def on_task_status_changed(data: dict):
    """任务状态变化时推送更新"""
    task_id = data["task_id"] 
    status = data["status"]
    progress = data.get("progress", 0)
    
    # 广播给所有监控任务的连接
    message = {
        "type": "task_update",
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "timestamp": datetime.now().isoformat()
    }
    
    # 这里可以进一步优化，只发送给订阅了该任务的连接
    for conn_id in connection_manager._connections:
        await connection_manager.send_to_connection(conn_id, message)

# 注册事件处理器
event_bus.subscribe("task.status.changed", on_task_status_changed)
```

## 7. 消息格式规范

### 标准消息格式
```json
// 终端相关消息
{
    "type": "command",
    "command": "display interface brief",
    "session_id": "uuid"
}

{
    "type": "command_output", 
    "command": "display interface brief",
    "output": "Interface output...",
    "status": "success|error"
}

// 任务监控消息
{
    "type": "task_update",
    "task_id": 123,
    "status": "running|completed|failed",
    "progress": 75,
    "current_device": "switch-01",
    "total_devices": 10,
    "completed_devices": 7
}

// 设备状态通知
{
    "type": "device_status",
    "device_id": 456,
    "status": "online|offline|error", 
    "timestamp": "2025-06-17T10:30:00Z"
}
```

## 8. 前端集成建议

### 终端组件
```javascript
// 使用xterm.js库实现终端界面
const terminal = new Terminal({
    cursorBlink: true,
    theme: {
        background: '#1e1e1e',
        foreground: '#ffffff'
    }
});

// WebSocket连接
const ws = new WebSocket(`ws://localhost:8000/ws/terminal/${deviceId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'command_output') {
        terminal.write(data.output);
    }
};

// 发送命令
terminal.onData((data) => {
    if (data === '\r') {  // 回车键
        const command = getCurrentCommand();
        ws.send(JSON.stringify({
            type: 'command',
            command: command
        }));
    }
});
```

## 9. 与其他模块集成

### 从FastAPI模块获取数据
```python
# 设备认证信息
async def get_device_credentials(device_id: int) -> dict:
    from services.device_service import DeviceService
    service = DeviceService()
    return await service.get_device_credentials(device_id)

# 任务状态更新
async def update_task_progress(task_id: int, progress: int, current_device: str = None):
    await event_bus.publish("task.status.changed", {
        "task_id": task_id,
        "progress": progress,
        "current_device": current_device,
        "status": "running"
    })
```

### 网络模块集成
```python
# 在网络任务执行时推送进度
class NetworkTaskExecutor:
    async def execute_with_progress(self, task_id: int, device_ids: List[int], commands: List[str]):
        total_devices = len(device_ids)
        
        for i, device_id in enumerate(device_ids):
            # 执行网络操作
            await self.execute_device_commands(device_id, commands)
            
            # 推送进度更新
            progress = int((i + 1) / total_devices * 100)
            await update_task_progress(task_id, progress, f"device-{device_id}")
```

## 10. 关键设计原则

- **连接管理**: 统一管理所有WebSocket连接
- **会话隔离**: 每个终端会话独立管理
- **事件驱动**: 基于事件系统的松耦合架构
- **消息规范**: 标准化的消息格式
- **错误处理**: 完善的异常处理和恢复机制
- **性能优化**: 连接复用和消息压缩

这个设计提供了完整的实时交互体验，支持终端操作、任务监控和状态通知，与FastAPI和网络自动化模块无缝集成。
