# Home Hub 框架设计（中间层与北向）

> 目标：把**稳定的契约、数据流和扩展点**固定下来，让南向协议的不确定性停留在
> 适配器内部，不向上层扩散。

## 1. 设计原则

1. **南向只做翻译**：集成只负责把协议数据翻译成 Device / Entity / State / Event，
   不直接写数据库、不直接写 API、不依赖其他集成。
2. **北向只依赖领域结果**：API、SSE、Prometheus、告警都消费统一实体模型或领域事件，
   不知道 ubus、SNMP、MQTT 的存在。
3. **写操作只有一条通道**：`API → ActionGateway → Integration`，能力白名单 + 审计。
4. **协议差异放在扩展字段**：实体级 `attributes`（JSON）承载协议特有元数据，
   核心表结构不因单个协议变化。
5. **增量演进**：北向字段只增不删；破坏性变更走新的 API 版本。

## 2. 分层与依赖方向

```
┌──────────────────────────────────────────────────────────┐
│ 北向：REST / SSE / Prometheus / Alertmanager webhook      │
│  api/  export/  alerting/  realtime/                     │
└──────────────────────────┬───────────────────────────────┘
                           │ 只读数据库 / 订阅事件
┌──────────────────────────▼───────────────────────────────┐
│ 服务与运行时                                              │
│  services/ repositories/ schemas/                        │
│  domain/ plugins/ history/ topology/                     │
└──────────────────────────┬───────────────────────────────┘
                           │ 契约：Integration / Context
┌──────────────────────────▼───────────────────────────────┐
│ 南向集成（按协议）                                         │
│  integrations/openwrt/ prometheus_scrape/ snmp/ mqtt/... │
└──────────────────────────────────────────────────────────┘
```

依赖规则：

- `integrations/*` 只能依赖 `domain`、`plugins.contract`、`plugins.manifest`、
  `plugins.errors`，**不得**导入 `api`、`services`、`repositories`。
- `api/*` 不导入任何 `integrations/*`；`main.py` 作为组合根负责注册内置集成。
- 协议特有字段进入 `EntityDescriptor.attributes`，不要新增核心列。

## 3. 中间层契约

### 3.1 领域对象

| 对象 | 作用 | 稳定性 |
| --- | --- | --- |
| `DeviceDescriptor` | 设备静态元数据 + `identity`（MAC/序列号） | 稳定 |
| `EntityDescriptor` | 实体声明：domain、unit、capability、attributes | 稳定 |
| `EntityState` | 状态快照：value、attributes、observed_at | 稳定 |
| `Capability` | 写能力白名单：readonly / on_off / set_level / action | 可扩展枚举 |
| `Neighbor` | 邻居记录，供拓扑归并 | 稳定 |
| `DomainEvent` | 状态、上下线、注册、邻居、告警 | 只增字段 |

### 3.2 集成契约

```
Integration
├── manifest: IntegrationManifest   # 名称、能力、类别、默认轮询间隔
├── setup()                         # 连接 / 认证
├── discover() -> [DeviceDescriptor]
├── poll()                          # 周期采集
├── execute_action(ActionRequest)   # 可选，写操作
└── close()
```

采集模式由 `IntegrationManifest.collection_mode` 声明：

- `PollingIntegration` → `poll`，类型层强制只读；
- `SubscribingIntegration` → `subscribe`，`start()` 是长驻协程；
- `HybridIntegration` → `hybrid`，同时支持 `poll()` 与 `start()`（如 ONVIF）。

三者产生的领域事件相同，**北向不需要改**。`ActionGateway` 仍然负责写能力校验。

### 3.3 ID 与实例

```
device_id = <integration>.<instance>.<device_key>
entity_id = <integration>.<instance>.<device_key>.<entity_key>
```

`instance` 隔离同一协议的多个实例（两台路由器、两台 NAS）。
`identity` 目前只用于**拓扑匹配**，不做设备行合并（ADR-001）。

## 4. 数据流

```
APScheduler
  └─ integration:<id> → IntegrationRunner
       ├─ 未连接时先重试 setup + discover（ADR-010）
       └─ Integration.poll()
            ├─ register_device / register_entity
            ├─ emit_state
            ├─ emit_device_availability
            └─ report_neighbors
                 ↓
             EventBus
            ├─ PersistenceSubscriber → devices / entities / entity_states
            ├─ HistoryRecorder      → entity_history
            ├─ TopologyRecorder     → neighbor_links
            └─ RealtimeHub          → SSE 订阅者
```

北向读取：

- REST 读 SQLite（设备、实体、状态、历史、拓扑、告警、审计）。
- `/metrics` 每次抓取实时读 SQLite。
- `/api/events` 从 `RealtimeHub` 读事件队列。
- Alertmanager webhook 写 `alerts`，同时发 `AlertReceivedEvent` 到 SSE。

## 5. 北向契约

### 5.1 REST

- 出入参全部是显式 Pydantic 模型，不直接返回 ORM 行。
- 错误码约定：`400` 参数/范围、`403` 能力拒绝、`404` 不存在、
  `409` 实例未运行/名称冲突、`502` 上游设备失败、`503` 未配置/未就绪。
- 列表接口目前按家庭规模设计（简单 `limit`）；数据量大时再加游标分页。
- 当前 `/api` 视为 v1；破坏性变更通过 `/api/v2` 并行挂载，不静默改字段。

### 5.2 实时事件（SSE）

`GET /api/events?types=state_changed,device_availability`

事件格式：

```
event: state_changed
data: {"type":"state_changed","occurred_at":"...","source":"openwrt","data":{...}}
```

事件类型：`state_changed`、`device_availability`、`neighbor_report`、
`device_registered`、`entity_registered`、`alert_received`。

`RealtimeHub` 与传输解耦：将来换 WebSocket 只替换 API 层适配器，
`serialize_event` 与订阅者不变。

### 5.3 动作与审计

- `POST /api/entities/{id}/actions`：唯一写入口。
- 请求体：`{action, capability, params}`。
- 网关四道校验：集成 manifest → 实体存在 → 实体归属 → 实体能力。
- 结果与拒绝全部写入 `action_audits`，并可通过 `GET /api/action-audits` 查询。
- 审计写失败只记录日志，不阻断动作（可观测性优先，不牺牲可用性）。

## 6. 灵活性与扩展点

| 不确定性 | 当前处理 | 未来扩展 | 是否影响北向 |
| --- | --- | --- | --- |
| 推送型协议（MQTT/HA） | `SubscribingIntegration` + runner 任务监管 | 补高频事件缓冲，再实现具体适配器 | 否，事件相同 |
| 一台设备多协议 | 一台设备选一个监控集成 | 全局设备 + binding 表，按 `identity` 归并 | 是，但可增量加 `bindings` 字段 |
| 协议特有字段 | `EntityDescriptor.attributes` | 保持 JSON 透出 | 否 |
| 新能力类型 | `Capability` 枚举 | 增加枚举值，网关自动生效 | 否 |
| 集成配置差异 | manifest + 自由 JSON | 每个集成声明 config schema | 否，API 只做校验 |
| 实时通道 | SSE + RealtimeHub | WebSocket 复用 Hub | 否 |
| 存储规模 | SQLite | 只替换 repositories/history | 否 |
| schema 变更 | `create_all` | Alembic（待补） | 否，但需迁移纪律 |

### 新增一个南向集成的步骤

1. 在 `app/integrations/<name>/` 实现合适的基类：
   `PollingIntegration` / `SubscribingIntegration` / `HybridIntegration`。
2. 定义 `manifest`（能力、类别、`collection_mode`、默认轮询间隔）。
3. `discover()` 返回初始设备；`poll()` 或 `start()` 注册实体、
   上报状态/可用性/邻居。
4. 实体 key、unit、domain 尽量复用已有约定（如 `uptime`、`memory_usage`）。
5. 用固定报文 + `MockTransport` 写测试，不依赖真实设备。
6. **不需要**改 API、数据库、前端；如果需要，说明契约设计有问题。

## 7. 当前完成度

### 中间层

- ✅ 领域模型、能力、事件总线
- ✅ 插件契约、注册表、目录、上下文、状态表
- ✅ 持久化、历史、拓扑、运行器（连接重试 + 并发保护）
- ✅ 动作网关 + 持久化审计
- ✅ 订阅 / 混合型集成基类 + runner 长驻任务监管/重连
- ⬜ 高频推送事件缓冲（批量写入）
- ⬜ 每集成配置 schema
- ⬜ 全局设备身份/绑定表
- ⬜ Alembic 迁移

### 北向

- ✅ 设备 / 实体 / 状态 / 历史 / 拓扑 API
- ✅ 集成实例 CRUD
- ✅ 动作 API + 审计查询
- ✅ SSE 实时事件
- ✅ Prometheus `/metrics`
- ✅ Alertmanager webhook + 告警查询
- ⬜ 鉴权
- ⬜ WoT 导出
- ⬜ 前端接入
- ⬜ API v2 的正式版本策略（当前 `/api` 视为 v1）

### 南向（只作为契约验证）

- ✅ `openwrt`（ubus，MockTransport）
- ✅ `prometheus_scrape`（exporter，模拟端点）
- ⬜ SNMP / DSM / ONVIF / MQTT / HA / WoL

## 8. 为什么先做北向和中间层

南向的真实行为（字段差异、认证、ACL、厂商裁剪）必须靠真机实践才能确定；
但**设备/实体/状态/事件/动作/审计**这些契约可以先稳定下来，并用 fake 集成验证。

只要上层只依赖这些契约，后续无论接 SNMP、DSM 还是 MQTT，都不需要重写 API、
数据库或前端；需要调整的只有适配器和少量扩展点。

## 9. 需要保持的纪律

1. 集成不直接写 DB / API；只通过 `IntegrationContext`。
2. 北向不直接导入集成；只读领域结果。
3. 新字段优先放 `attributes`，不要为单个协议改核心表。
4. 事件字段只增不删；SSE 客户端忽略未知字段。
5. 每次 schema 变更都要有迁移方案（Alembic 补齐前手动记录）。
6. 新增集成必须带固定报文测试，不依赖真实设备才能跑 CI。
