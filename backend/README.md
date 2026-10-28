# Home Hub 后端

FastAPI + SQLAlchemy (async) + SQLite。统一设备抽象与插件化集成的后端底座。

当前已打通的纵切：天气 / 家庭设置 / 授时 + **设备域平台地基**
（持久化、状态存储、实例运行器、动作网关、设备/实体/集成 API）+ **OpenWrt 只读集成**。

## 快速开始

```bash
cd backend

# 1. 安装依赖（含 dev 工具）
uv sync

# 2. 准备本地配置（.env 已被 .gitignore 忽略，不会入库）
cp .env.example .env
#    仅行政区搜索需要 AMAP_WEB_SERVICE_KEY，其余功能不依赖它

# 3. 启动
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动时会自动建表；首次天气采集与集成实例轮询都在后台执行，
**不阻塞服务可用**。天气按 `WEATHER_UPDATE_INTERVAL_MINUTES`（默认 10 分钟）刷新。

数据库默认位于 `backend/data/home_hub.db`。相对路径会按 `backend/` 解析，
因此从仓库根目录或 `backend/` 启动都指向同一个文件。

> 本仓库**不提交** `.env`、`data/*.db`、日志与 pid 文件。
> 如果曾经提交过，请轮换相关密钥（历史提交仍然可见）。

## 运行期结构

```
APScheduler
  ├── weather_update          天气刷新
  └── integration:<id>        每个集成实例的轮询任务
        │
        ▼
IntegrationRunner ──► Integration.poll()
        │                    │
        │                    ├─ register_device / register_entity
        │                    ├─ emit_state
        │                    ├─ emit_device_availability
        │                    └─ report_neighbors
        ▼
EventBus ──► PersistenceSubscriber ──► SQLite（设备/实体/状态）
        ├──► HistoryRecorder       ──► entity_history（变化才写）
        ├──► TopologyRecorder      ──► neighbor_links（按设备+MAC 聚合）
        └──► StateStore（内存最新状态）
```

- 设备 / 实体元数据：永久存 SQLite（D4）。
- 最新状态：`entity_states` 一行一个实体；历史时序在 `entity_history`。
- 历史只记录值和属性发生变化时的样本，避免轮询写满 SQLite。
- 邻居关系按 `(device_id, mac)` 聚合，拓扑只展示最近活跃窗口内的链路。
- 实例失败只影响自己：运行器记录 `last_error`，其他实例继续轮询。
- 删除实例会同时清理它产生的设备 / 实体 / 状态 / 历史 / 邻居链路。

## API 一览

### 基础

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/time` | 服务器时间戳 + 家庭时区 + 进程运行时长 |
| GET/PUT | `/api/settings/home` | 家庭设置（地点变化后自动刷新天气） |
| GET | `/api/settings/locations` | 高德行政区搜索 |
| GET | `/api/weather` | 当前天气 + 7 天预报（含 `fetched_at`） |
| POST | `/api/weather/refresh` | 立即刷新天气 |

### 集成

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/integrations/manifests` | 已注册的集成类型（能力、默认轮询间隔等） |
| GET | `/api/integrations` | 全部集成实例 |
| GET | `/api/integrations/{id}` | 实例详情（含 `last_error` 健康信息） |
| POST | `/api/integrations` | 创建并启动实例 |
| PATCH | `/api/integrations/{id}` | 修改配置 / 启停（启用状态会自动重启） |
| DELETE | `/api/integrations/{id}` | 停止并删除实例及其设备数据 |

创建 OpenWrt 实例示例：

```bash
curl -X POST http://127.0.0.1:8000/api/integrations \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "openwrt-main",
    "integration": "openwrt",
    "config": {
      "host": "192.168.1.1",
      "username": "root",
      "password": "your-password",
      "name": "客厅路由器"
    }
  }'
```

配置字段见 `app/integrations/openwrt/README.md`。

> `GET /api/integrations` 返回的 `config` 已对 `password` / `token` / `secret`
> 等敏感字段脱敏为 `***`。PATCH 更新时请重新提供完整配置，不要直接回传脱敏结果。

### 设备 / 实体

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/devices` | 设备列表（默认内嵌实体） |
| GET | `/api/devices/{device_id}` | 单设备 + 实体 |
| GET | `/api/entities` | 实体列表（可按 `device_id` / `integration` 过滤） |
| GET | `/api/entities/{entity_id}` | 单实体声明 |
| GET | `/api/entities/{entity_id}/state` | 最新状态（值 + 属性 + 观测时间） |
| GET | `/api/entities/{entity_id}/history` | 状态历史（默认最近 24h，`start`/`end`/`limit`） |

### 拓扑

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/topology` | 节点 + 边；`active_within_seconds` 控制活跃窗口 |

示例：

```bash
curl "http://127.0.0.1:8000/api/topology?active_within_seconds=600"
curl "http://127.0.0.1:8000/api/entities/<entity_id>/history?limit=200"
```

### 告警与导出

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/metrics` | Prometheus 文本指标（0.0.4） |
| POST | `/api/alerts/webhook` | Alertmanager webhook 接收 |
| GET | `/api/alerts` | 最近告警，可按 `status=firing|resolved` 过滤 |
| GET | `/api/alerts/{fingerprint}` | 单条告警 |

抓取与告警配置见：

- `app/export/prometheus/README.md`
- `app/alerting/README.md`

最小 Alertmanager 配置：

```yaml
receivers:
  - name: homehub
    webhook_configs:
      - url: http://127.0.0.1:8000/api/alerts/webhook
        send_resolved: true
        http_config:
          authorization:
            type: Bearer
            credentials: <ALERT_WEBHOOK_TOKEN>
```

ID 规则：

```
device_id = <integration>.<instance>.<device_key>
entity_id = <integration>.<instance>.<device_key>.<entity_key>
```

`instance` 是集成实例名，用于隔离同一集成的多个实例（例如两台路由器）。

### 错误约定

- 家庭位置未配置：`409`
- 尚无天气数据 / 设备 / 实体：`404`
- 高德 Key 未配置：`503`；上游服务异常：`502`
- 集成未注册 / 实例名冲突：`400` / `409`
- 历史查询 `start > end`：`400`
- Webhook 令牌错误：`401`
- 运行期未就绪：`503`

## 时间语义

- 数据库统一存 UTC（`app/core/db_types.py` 的 `UTCDateTime`）。
- 天气与家庭设置的时间按家庭时区输出（带 `+08:00` 等偏移）。
- `/api/time` 保持 UTC 时间戳 + 家庭时区名，供前端校时。
- 天气只返回今天及以后的预报，并提供 `fetched_at`。
- 设备 / 实体 / 历史 / 拓扑的时间保持 UTC（带偏移），与 `/api/time` 的时间戳配合使用。

## 目录结构

```
backend/
├── app/
│   ├── main.py              # 入口：lifespan、CORS、路由、Runtime
│   ├── api/                 # REST：weather / settings / time / integrations / devices
│   ├── core/                # 配置、异步数据库、UTC 时间类型、日志
│   ├── models/              # ORM：天气、设置、实例、设备、实体、状态、历史、邻居
│   ├── repositories/        # 数据访问层
│   ├── schemas/             # Pydantic 出入参
│   ├── services/            # 业务层
│   ├── tasks/               # APScheduler（天气 + 历史/邻居清理）
│   ├── collectors/          # 外部数据源（open-meteo / amap）
│   ├── utils/               # 坐标换算、时区工具
│   ├── domain/              # ★ 领域模型（Device / Entity / Capability / Event）
│   ├── plugins/             # ★ 契约、注册表、目录、状态表、运行器、持久化、ActionGateway
│   ├── integrations/        # ★ 南向集成（openwrt 已实现；其余占位）
│   ├── topology/            # ★ 邻居聚合 + 拓扑图构建（已实现）
│   ├── history/             # ★ 状态时序 + TTL（已实现）
│   ├── alerting/            # ★ Alertmanager webhook + 告警查询（已实现）
│   └── export/              # ★ 指标导出（prometheus 已实现；wot 占位）
├── tests/                   # pytest（契约 / 时间 / 持久化 / 运行器 / OpenWrt / 历史 / 拓扑）
├── data/                    # 本地 SQLite（不入库）
├── docs/DECISIONS.md        # 开发决策记录（仓库根 docs/）
└── pyproject.toml
```

## 开发

```bash
uv run pytest                 # 38 项
uv run ruff check app tests
uv run ruff format app tests
```

## 当前状态与下一步

- ✅ 天气 / 设置 / 授时链路；时间统一 UTC 存取。
- ✅ 插件契约、动作网关（集成级 + 实体级 + 归属校验）、事件总线。
- ✅ 设备域持久化、状态存储、实例运行器、集成实例 CRUD。
- ✅ 设备 / 实体 / 状态 / 历史只读 API。
- ✅ OpenWrt 只读集成（MockTransport 测试；待真机验证）。
- ✅ `history`：变化才写 + 7 天 TTL + 定时清理。
- ✅ `topology`：邻居聚合、身份匹配、图 API、活跃窗口。
- ✅ `export/prometheus`：`/metrics` 文本指标。
- ✅ `alerting`：Alertmanager webhook + 告警查询 + 可选共享令牌。
- ⬜ 第二类集成（MQTT / Home Assistant），需要订阅型基类。
- ⬜ Wake-on-LAN（按 ADR-002 延后到身份归并之后）。
- ⬜ `export/wot`（W3C WoT Thing Description）。
- ⬜ Alembic 迁移。
