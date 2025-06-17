# 网络自动化平台

本项目是一个使用 FastAPI 和现代 Python 技术栈构建的高性能网络自动化平台。它旨在为网络工程师提供一个强大、可扩展的工具集，以简化和自动化日常的网络设备管理任务。

## ✨ 核心功能

- **多厂商设备支持**: 通过可插拔的适配器模式，轻松管理 H3C, Huawei, Cisco 等主流网络设备。
- **配置管理**: 提供配置备份、比对、下发和回滚的全生命周期管理。
- **自动化任务引擎**: 强大的任务执行器，支持批量执行信息查询、配置变更等操作。
- **实时监控与告警**: 集成 SNMP 服务，实现对设备状态和关键性能指标的实时监控。
- **远程CLI交互**: 通过 WebSocket 提供一个安全的、交互式的远程命令行界面，方便进行实时调试和操作。
- **RESTful API**: 提供一套完整、设计良好的 RESTful API，方便与第三方系统（如CMDB、监控系统）集成。
- **动态设备清单**: 与数据库无缝集成，动态加载设备信息，无需维护静态 inventory 文件。

## 🚀 技术栈

- **后端**: [FastAPI](https://fastapi.tiangolo.com/) - 高性能的现代Python Web框架
- **数据验证**: [Pydantic V2](https://docs.pydantic.dev/latest/) - 高效的数据解析与验证
- **异步ORM**: [Tortoise ORM](https://tortoise.github.io/) - 优雅、易于使用的异步ORM
- **设备交互**: [Scrapli](https://github.com/carlmontanari/scrapli) - 专为网络设备设计的快速、健壮的SSH/Telnet客户端
- **输出解析**: [ntc-templates (TextFSM)](https://github.com/networktocode/ntc-templates) - 结构化解析CLI输出
- **数据库**: [PostgreSQL](https://www.postgresql.org/) (通过 `asyncpg` 驱动)
- **依赖管理**: [Uvicorn](https://www.uvicorn.org/), [Gunicorn](https://gunicorn.org/)
- **任务调度**: (可集成 [Celery](https://docs.celeryq.dev/en/stable/) 或 [ARQ](https://arq-docs.helpmanual.io/))

## 🏗️ 项目结构

项目采用分层架构，确保代码的松耦合和高内聚。

```
network_mon/
├── app/
│   ├── core/         # FastAPI核心配置 (中间件, 异常处理等)
│   ├── db/           # 数据库连接与模型定义
│   ├── models/       # Pydantic 数据模型
│   ├── network/      # ⭐ 网络自动化核心
│   │   ├── adapters/ # 多厂商设备适配器 (H3C, Huawei, Cisco)
│   │   ├── cli/      # WebSocket CLI 实现
│   │   ├── config/   # 配置管理 (scrapli-cfg)
│   │   ├── core/     # 核心组件 (任务执行器, 设备清单)
│   │   ├── tasks/    # 具体网络任务实现
│   ├── repositories/ # 数据访问层 (DAO)
│   ├── services/     # 业务逻辑层
│   ├── schemas/      # API输入/输出模式
│   ├── web/          # API路由和WebSocket端点
│   └── utils/        # 通用工具 (日志等)
├── docs/             # 项目文档
├── logs/             # 日志文件
├── migrations/       # 数据库迁移
├── run.py            # 项目启动脚本
└── README.md         # 你正在看的这个文件
```

## 🛠️ 安装与运行

1.  **克隆项目**:
    ```bash
    # github
    git clone https://github.com/lijianqiao/network_mon.git
    # gitee
    git clone https://gitee.com/lijianqiao/network_mon.git
    cd network_mon
    ```

2.  **安装依赖**:
    (建议在Python虚拟环境中使用)
    ```bash
    # pip
    pip install -r requirements.txt
    # uv
    uv sync
    ```

3.  **配置环境变量**:
    复制 `.env.example` 为 `.env` 并根据你的环境配置数据库连接等信息。

4.  **运行数据库迁移**:
    ```bash
    aerich upgrade
    ```

5.  **启动应用**:
    ```bash
    python run.py
    ```
    应用将在 `http://127.0.0.1:8000` 启动。

## ⚙️ API 使用示例

### 示例1：获取设备版本信息

你可以通过 `POST` 请求到 `/api/v1/automation/run-task` 来执行一个网络任务。

**请求**:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/automation/run-task" \
-H "Content-Type: application/json" \
-d '{
  "task_name": "get_version",
  "device_id": "your_device_id_from_db"
}'
```

**响应**:

```json
{
  "success": true,
  "task_id": "uuid-for-this-task",
  "device_id": "your_device_id_from_db",
  "command": "display version",
  "raw_output": "<...设备返回的原始输出...>",
  "parsed_data": {
    "raw": "<...>",
    "parsed": [
      {
        "vrp_version": "8.191",
        "full_version": "CE6850 V200R019C10SPC800",
        "uptime": "2 weeks, 4 days, 21 hours, 3 minutes"
      }
    ],
    "method": "fallback",
    "action": "get_version"
  },
  "execution_time": 1.2345
}
```

### 示例2：查询指定接口的详细信息

**请求**:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/automation/run-task" \
-H "Content-Type: application/json" \
-d '{
  "task_name": "get_interface_detail",
  "device_id": "your_device_id_from_db",
  "task_params": {
    "interface": "GigabitEthernet0/0/1"
  }
}'
```

## 🤝 贡献

欢迎提交 PR 和 Issue 来改进此项目！

## 📄 许可证

本项目采用 MIT 许可证。
