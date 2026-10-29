# 开发决策记录（ADR）

记录会影响后续实现的关键取舍。新增决策请追加，不覆盖历史。

---

## ADR-001 · 设备身份：MVP 阶段一台设备只选一种接入方式

**状态**：已采纳（MVP）

**背景**：同一台 NAS 可能同时被 SNMP 与 DSM API 看到；同一台 PC 可能同时有
node_exporter 与 WoL。若按「集成 + key」生成 `device_id`，同一物理设备会出现多条记录。

**决策**：

1. MVP 阶段，一台物理设备只配置一个负责采集的集成实例；由用户选择接入方式
   （例如 NAS 选 DSM 或 SNMP，而不是两者同时启用）。
2. `DeviceDescriptor` 新增 `identity` 字段（`mac:…` / `serial:…`），用于：
   - 拓扑层把邻居表里的 MAC 对应到设备；
   - 未来做跨集成归并时的匹配键。
3. `device_id` 采用 `<integration>.<instance>.<key>`，其中 `instance` 为集成实例名，
   用于隔离同一集成的多个实例（如两台 OpenWrt 路由器）；单实例场景下退化为
   `<integration>.<key>`。本期不引入全局设备表。

**后果**：

- 实现简单，不会在早期引入复杂的归并逻辑。
- 同一设备多协议接入会显示为两条记录，这是已知限制，UI/文档需说明。
- 未来升级路径：在 `devices.identity` 上做归并，`device_id` 保持不变，
  通过新的「设备绑定」表把多个 binding 指向同一物理设备。

---

## ADR-002 · Wake-on-LAN：暂不作为独立集成落地

**状态**：已采纳（延后）

**背景**：WoL 是动作，不是采集协议。PC 的状态通常由 node_exporter 采集，
若 `wakeonlan` 作为独立集成，会再注册一台同名设备，与监控设备重复。

**决策**：本期不实现 `wakeonlan` 集成。等 ADR-001 的身份归并落地后，二选一：

- **方案 A（推荐）**：`wakeonlan` 作为 companion 集成，向已有设备挂载一个
  `button` 实体，不注册新设备；
- **方案 B**：由宿主类集成（如负责该 PC 的集成）内建 WoL 能力。

**后果**：`ActionGateway` 的写路径仍然只有测试覆盖，等第一个真实动作集成接入后
再做端到端验证。

---

## ADR-003 · 当前状态与历史分离

**状态**：已采纳（MVP）

**决策**：

- `entity_states`：每个实体一行，保存最新状态，供 API 与前端读取；
- 历史时序仍留在 `app/history`（尚未实现），按 D4 的 7 天 TTL 设计；
- 运行期热路径优先读内存 `StateStore`，数据库作为持久化副本。

**后果**：重启后能从数据库恢复最新状态；历史查询与降采样后续单独实现。

---

## ADR-004 · 集成实例配置暂存 SQLite（明文）

**状态**：临时方案

**背景**：集成实例需要 host / 用户名 / 密码等配置。

**决策**：MVP 阶段把实例配置以 JSON 存入 `integration_instances.config`，
依赖宿主机文件权限保护 `data/home_hub.db`。**这不是最终方案。**

**后续**：引入密钥加密（如 Fernet + 环境变量主密钥）或外部 secret provider，
并在此文档补充 ADR。不要把生产凭据用于当前实现。

---

## ADR-005 · 数据库迁移

**状态**：待办

**现状**：仍使用 `Base.metadata.create_all`；新增表可以自动创建，但字段变更不会迁移。

**计划**：设备域稳定后引入 Alembic，首个迁移基线覆盖现有四张表 + 设备域表。
在此之前，schema 变更需要手动处理，且不应存在生产数据。

---

## ADR-006 · 历史只记录真实变化

**状态**：已采纳（MVP）

**决策**：

- `HistoryRecorder` 订阅 `StateChangedEvent`，仅当值或属性发生变化时写入
  `entity_history`；首次出现也记录。
- 不做「每次轮询都记」的周期快照，避免 60 秒轮询把 SQLite 写满。
- 默认保留 7 天（`HISTORY_RETENTION_DAYS`），由定时任务清理。
- 删除集成实例时，其历史随之删除。

**后果**：长时间稳定的值不会产生心跳点；若未来需要“心跳/周期快照”，
在 recorder 里增加按时间间隔写入的规则即可，不影响查询接口。

---

## ADR-007 · 拓扑按链路聚合，而不是保存每次原始上报

**状态**：已采纳（MVP）

**决策**：

- `neighbor_links` 以 `(device_id, mac)` 为主键，一条链路一行；
  每次上报更新 `last_seen_at` 与字段，`first_seen_at` 保留首次时间。
- 图查询只看最近 `TOPOLOGY_ACTIVE_WINDOW_SECONDS` 内的链路，
  邻居消失后自然从图中淡出。
- 设备匹配使用 `devices.identity`（`mac:` 前缀）；匹配不到时以
  `mac:<mac>` 作为邻居节点展示，不丢数据。
- 超过保留期的链路由清理任务删除。

**后果**：不保留链路的完整历史变化（只保留首末时间）；若未来需要“邻居出现/消失
时间线”，再增加事件表，不影响当前图 API。

---

## ADR-008 · 告警只保留当前状态，按 fingerprint 去重

**状态**：已采纳（MVP）

**决策**：

- `alerts` 表以 Alertmanager 的 `fingerprint` 为主键；
  缺失时用 `labels` 的 SHA-256 兜底。
- firing / resolved 都更新同一行，`received_count` 记录投递次数；
- 保留 `starts_at` / `ends_at` / `resolved_at`，但不保留每次状态迁移的事件流；
- webhook 可选共享令牌（`ALERT_WEBHOOK_TOKEN`），为空时不校验。

**后果**：前端拿到的是“当前告警列表”，不是完整审计日志；需要审计时再加
`alert_events` 表。底座仍然不内置规则引擎（D3）。

---

## ADR-009 · Prometheus 指标按抓取实时生成

**状态**：已采纳（MVP）

**决策**：

- `/metrics` 每次抓取时查询 SQLite 生成文本，不维护进程内计数器；
- 实体最新值来自 `entity_states`，文本类实体只暴露 `homehub_entity_info`；
- 采集健康度来自 `integration_instances.last_error` / `last_success_at`。

**后果**：实现简单且重启不丢数据；抓取频率高时会给 SQLite 带来查询压力，
但家庭规模下可接受。若将来指标量变大，再考虑缓存或专用导出器。

---

## ADR-010 · 实例连接失败自动重试，连接过程串行化

**状态**：已采纳

**背景**：早期运行器在 `setup()` / `discover()` 失败时直接放弃实例，不调度轮询。
路由器或 exporter 若在服务启动时恰好离线，实例会一直失效，直到服务或实例被手动重启。

**决策**：

- 连接失败时实例仍保留在运行列表并调度轮询；每次轮询先尝试连接，成功后再采集；
  错误写入 `last_error`（`connect failed: ...`）。
- 每个运行实例持有一把连接锁：启动时的连接与调度器触发的第一次轮询不会并发连接，
  避免同一设备被两次注册。
- 连接期间实例被停止或删除，连接完成后立即关闭新建的集成对象，不留下泄漏的客户端。

**后果**：配置错误（如缺少 url）也会按间隔重试并持续记录错误；这是有意的，
错误在 `last_error` 与 `homehub_integration_healthy` 中可见，修正配置后 PATCH 即可恢复。
事件总线仍然只记录 handler 异常、不中断流程：持久化失败需要通过日志与指标发现，
这是后续需要补强的观测点。

---

## ADR-011 · 实时事件：传输无关 Hub + SSE 适配器

**状态**：已采纳

**决策**：

- 领域事件先进入 `RealtimeHub`，由订阅队列分发；SSE 只是其中一个传输适配器；
- 事件类型：`state_changed`、`device_availability`、`neighbor_report`、
  `device_registered`、`entity_registered`、`alert_received`；
- 告警落库后通过 `AlertReceivedEvent` 进入同一总线，不另建通知机制；
- 慢消费者队列满时丢弃最旧事件，保证实时性而不是阻塞生产端。

**后果**：将来换 WebSocket 只需替换 API 层适配器；北向事件结构保持稳定。

---

## ADR-012 · 动作审计持久化，异步 sink 不阻断动作

**状态**：已采纳

**决策**：

- `ActionGateway` 的审计 sink 改为异步接口；
- 运行时注入 `DatabaseAuditSink`，把允许/拒绝/失败写入 `action_audits`；
- 审计写失败只记录日志，不阻断动作本身；
- 提供 `GET /api/action-audits` 查询。

**后果**：写通道的每一次尝试都可追溯；代价是每个动作多一次数据库写入。

---

## ADR-013 · 实体级 attributes 作为协议扩展通道

**状态**：已采纳

**决策**：

- `EntityDescriptor.attributes` 是 JSON 扩展位，用于协议特有元数据
  （原始字段名、采样周期、展示精度等）；
- 北向原样透出，核心逻辑不依赖其内容；
- 不为单个协议新增核心表字段。

**后果**：南向差异不会逼着上层改表；但 attributes 不能承载核心语义，
否则前端与业务逻辑会重新耦合到具体协议。

---

## ADR-014 · 采集模式：poll / subscribe / hybrid

**状态**：已采纳

**背景**：`poll` 是"框架定时触发一次刷新"，不是协议本身。MQTT/HA 是推送型，
ONVIF 同时包含请求/响应、事件订阅与 RTSP 流；把推送型硬塞进 `poll` 会形成伪轮询。

**决策**：

- `IntegrationManifest.collection_mode` 声明 `poll` / `subscribe` / `hybrid`；
- `PollingIntegration` 只接受 `poll`，保持只读类型约束；
- `SubscribingIntegration` 接受 `subscribe`，`start()` 是长驻协程，`stop()` 清理；
- `HybridIntegration` 接受 `hybrid`，同时要求 `poll()` 与 `start()`；
- 运行器按模式决定：调度轮询任务、创建长驻 worker，或两者都做；
- 订阅 worker 退出/异常时按指数退避重连，健康状态写入实例；
- 订阅型的 `last_success_at` 表示"订阅循环已启动"，不是"收到最后一条消息"。

**后果**：北向事件/实体/API 不变；MQTT/ONVIF 可以按各自模式接入。
高频推送的批量写入仍未实现，是 MQTT 之前需要补的下一项。
