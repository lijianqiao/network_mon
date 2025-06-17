# WebSocket CLI交互功能文档

## 概述

WebSocket CLI交互功能为网络自动化平台提供了实时的命令行界面，支持：

- 实时CLI会话管理
- 异步命令执行
- 流式输出展示
- 配置下发
- 多设备会话管理

## 架构设计

### 核心组件

1. **CLIConnection** - 设备连接管理
   - 基于scrapli的异步设备连接
   - 支持多种网络设备平台（Cisco、Huawei、Juniper等）
   - 连接池管理和保活机制

2. **CLISession** - 会话管理
   - 会话生命周期管理
   - 用户权限控制
   - 会话超时和清理

3. **CLIManager** - 统一管理接口
   - 提供统一的CLI操作接口
   - 会话统计和监控
   - 错误处理和日志记录

4. **WebSocket端点** - 实时通信
   - 双向消息传递
   - 流式数据输出
   - 连接状态管理

## API接口

### REST API

#### 1. 创建会话
```http
POST /api/v1/cli/sessions
Content-Type: application/json

{
    "device_id": 1,
    "user_id": "admin"
}
```

响应：
```json
{
    "message": "CLI会话创建成功",
    "data": {
        "success": true,
        "session_id": "uuid-string",
        "device_id": 1,
        "device_name": "switch-01",
        "device_ip": "192.168.1.1"
    }
}
```

#### 2. 执行命令
```http
POST /api/v1/cli/sessions/execute
Content-Type: application/json

{
    "session_id": "uuid-string",
    "command": "show version"
}
```

#### 3. 发送配置
```http
POST /api/v1/cli/sessions/configure
Content-Type: application/json

{
    "session_id": "uuid-string",
    "config_lines": [
        "interface GigabitEthernet0/1",
        "description test-port",
        "no shutdown"
    ]
}
```

#### 4. 列出会话
```http
GET /api/v1/cli/sessions?user_id=admin&device_id=1
```

#### 5. 关闭会话
```http
DELETE /api/v1/cli/sessions/{session_id}
```

### WebSocket API

WebSocket端点: `ws://host:port/ws/cli/{client_id}`

#### 消息格式

所有消息都使用JSON格式：

```json
{
    "action": "action_name",
    "data": {...}
}
```

#### 支持的操作

##### 1. 创建会话
```json
{
    "action": "create_session",
    "device_id": 1,
    "user_id": "admin"
}
```

##### 2. 执行命令
```json
{
    "action": "execute_command",
    "session_id": "uuid-string",
    "command": "show version"
}
```

##### 3. 交互式命令（流式输出）
```json
{
    "action": "execute_interactive_command",
    "session_id": "uuid-string",
    "command": "show tech-support"
}
```

##### 4. 发送配置
```json
{
    "action": "send_configuration",
    "session_id": "uuid-string",
    "config_lines": ["interface ge0/1", "no shutdown"]
}
```

##### 5. 关闭会话
```json
{
    "action": "close_session",
    "session_id": "uuid-string"
}
```

## 前端集成示例

### JavaScript WebSocket客户端

```javascript
class CLIWebSocketClient {
    constructor(baseUrl, clientId) {
        this.baseUrl = baseUrl;
        this.clientId = clientId;
        this.ws = null;
        this.sessions = new Map();
    }

    connect() {
        const wsUrl = `${this.baseUrl}/ws/cli/${this.clientId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket连接已关闭');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
    }

    createSession(deviceId, userId) {
        const message = {
            action: 'create_session',
            device_id: deviceId,
            user_id: userId
        };
        this.ws.send(JSON.stringify(message));
    }

    executeCommand(sessionId, command) {
        const message = {
            action: 'execute_command',
            session_id: sessionId,
            command: command
        };
        this.ws.send(JSON.stringify(message));
    }

    executeInteractiveCommand(sessionId, command) {
        const message = {
            action: 'execute_interactive_command',
            session_id: sessionId,
            command: command
        };
        this.ws.send(JSON.stringify(message));
    }

    handleMessage(message) {
        switch (message.type) {
            case 'session_created':
                this.onSessionCreated(message.result);
                break;
            case 'command_result':
                this.onCommandResult(message.result);
                break;
            case 'interactive_command_chunk':
                this.onInteractiveChunk(message.chunk);
                break;
            case 'error':
                this.onError(message.message);
                break;
        }
    }

    onSessionCreated(result) {
        if (result.success) {
            console.log('会话创建成功:', result.session_id);
            this.sessions.set(result.session_id, result);
        }
    }

    onCommandResult(result) {
        if (result.success) {
            console.log('命令输出:', result.output);
        } else {
            console.error('命令执行失败:', result.error);
        }
    }

    onInteractiveChunk(chunk) {
        if (chunk.success) {
            // 实时显示输出
            this.appendOutput(chunk.output);
        }
    }

    onError(error) {
        console.error('错误:', error);
    }

    appendOutput(text) {
        // 将输出添加到终端显示区域
        const terminal = document.getElementById('terminal-output');
        terminal.textContent += text + '\n';
        terminal.scrollTop = terminal.scrollHeight;
    }
}

// 使用示例
const client = new CLIWebSocketClient('ws://localhost:8000', 'client-001');
client.connect();

// 创建会话
client.createSession(1, 'admin');

// 执行命令
setTimeout(() => {
    client.executeCommand('session-id', 'show version');
}, 1000);
```

### React Hook示例

```jsx
import { useState, useEffect, useRef } from 'react';

export const useCLIWebSocket = (baseUrl, clientId) => {
    const [isConnected, setIsConnected] = useState(false);
    const [sessions, setSessions] = useState(new Map());
    const [messages, setMessages] = useState([]);
    const ws = useRef(null);

    useEffect(() => {
        const wsUrl = `${baseUrl}/ws/cli/${clientId}`;
        ws.current = new WebSocket(wsUrl);
        
        ws.current.onopen = () => {
            setIsConnected(true);
        };
        
        ws.current.onmessage = (event) => {
            const message = JSON.parse(event.data);
            setMessages(prev => [...prev, message]);
            
            if (message.type === 'session_created' && message.result.success) {
                setSessions(prev => new Map(prev.set(message.result.session_id, message.result)));
            }
        };
        
        ws.current.onclose = () => {
            setIsConnected(false);
        };
        
        return () => {
            ws.current?.close();
        };
    }, [baseUrl, clientId]);

    const sendMessage = (message) => {
        if (ws.current && isConnected) {
            ws.current.send(JSON.stringify(message));
        }
    };

    const createSession = (deviceId, userId) => {
        sendMessage({
            action: 'create_session',
            device_id: deviceId,
            user_id: userId
        });
    };

    const executeCommand = (sessionId, command) => {
        sendMessage({
            action: 'execute_command',
            session_id: sessionId,
            command: command
        });
    };

    return {
        isConnected,
        sessions,
        messages,
        createSession,
        executeCommand,
        sendMessage
    };
};
```

## 配置说明

### 会话配置

- **最大会话数**: 每个用户最多可创建5个并发会话
- **会话超时**: 30分钟无活动自动关闭
- **清理间隔**: 每分钟检查一次过期会话

### 设备连接配置

- **连接超时**: 30秒
- **命令超时**: 30秒
- **保活间隔**: 发送保活命令维持连接

## 安全考虑

1. **身份验证**: 建议在生产环境中添加JWT令牌验证
2. **权限控制**: 限制用户只能访问授权的设备
3. **会话隔离**: 不同用户的会话完全隔离
4. **审计日志**: 记录所有CLI操作用于审计

## 监控和调试

### 日志记录

所有CLI操作都会记录详细日志：

```python
logger.info(f"用户 {user_id} 在设备 {device_name} 上执行命令: {command}")
logger.info(f"会话 {session_id} 创建成功")
logger.error(f"设备连接失败: {error}")
```

### 统计信息

通过 `/api/v1/cli/statistics` 端点获取：

- 活跃会话数
- 用户分布
- 设备连接状态
- 错误统计

## 故障排除

### 常见问题

1. **连接失败**
   - 检查设备IP和凭据
   - 确认网络连通性
   - 查看设备SSH服务状态

2. **会话超时**
   - 调整会话超时配置
   - 检查网络稳定性
   - 确认设备响应正常

3. **WebSocket断开**
   - 检查网络连接
   - 确认代理配置
   - 查看服务器日志

### 调试模式

启用详细日志：

```python
import logging
logging.getLogger('scrapli').setLevel(logging.DEBUG)
```

## 性能优化

1. **连接池**: 复用设备连接减少开销
2. **异步处理**: 所有操作都是异步的
3. **内存管理**: 定期清理过期会话
4. **负载均衡**: 支持多实例部署

## 未来扩展

1. **命令历史**: 记录和回放命令历史
2. **脚本执行**: 支持批量脚本执行
3. **文件传输**: 支持配置文件上传下载
4. **协作模式**: 多用户共享会话
