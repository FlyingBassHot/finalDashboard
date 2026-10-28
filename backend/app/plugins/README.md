# plugins — 插件运行时(框架)

集成(integration)的宿主框架,负责「注册 → 生命周期 → 调度 → 动作执行」。
本目录不含任何具体设备逻辑,具体集成在 `app/integrations/`。

## 已实现(基类阶段)

- **manifest.py** — IntegrationManifest 自描述(name 规范 / 能力边界 /
  默认轮询间隔,构造期校验)
- **contract.py** — Integration(ABC)+ PollingIntegration(第一类只读基类)
  + IntegrationContext(Protocol)+ ActionRequest / ActionResult。
  PollingIntegration 在三个位置强制「零写能力」:
  1. 子类 manifest 若声明写能力,类创建时即抛 `IntegrationConfigError`;
  2. 覆写 `execute_action` 直接抛 `UnsupportedActionError`;
  3. 注册表对 PollingIntegration 再做一次清单校验。
- **registry.py** — IntegrationRegistry 注册表 + `@register_integration` 装饰器;
  拒绝非 `Integration` 子类、重复注册与越权的只读集成
- **catalog.py** — EntityCatalog 设备 / 实体全局目录(内存实现,接口不变可换 DB);
  支持按前缀清理(实例删除时使用)
- **state_store.py** — 进程内最新状态表(热路径),重启由持久化层回填
- **context.py** — BaseIntegrationContext 框架默认上下文
  (声明规范化 → 目录登记 → 翻译为领域事件上总线);
  注入集成实例名,隔离同一集成的多个实例
- **persistence.py** — 事件 → SQLite 的订阅者:设备/实体声明、状态、上下线;
  启动时把库内数据回填到目录与状态表
- **runner.py** — 集成实例运行器:setup / discover / 轮询调度 / 异常隔离 /
  健康记录 / 删除时清理数据
- **runtime.py** — 运行期装配(目录 + 总线 + 持久化 + 状态表 + 运行器)
- **events.py(domain)** — 进程内事件总线;`subscribe(handler, event_type=...)`
  可按事件类型订阅,handler 异常互不影响
- **action_gateway.py** — **全底座唯一写通道**:集成级能力白名单、
  实体存在性、**实体归属集成**、实体级能力四道校验,异常归一,
  全程审计(允许 / 拒绝 / 失败均留痕)
测试:`tests/`(`uv run pytest`,38 项),覆盖清单校验、只读链路、
上下线去抖、四类拒绝路径、WoL 成功执行、跨集成越权、事件类型过滤、
持久化回填、运行器健康/异常隔离、OpenWrt ubus 报文、历史去重/TTL、
邻居聚合与拓扑构图、Prometheus 指标渲染、告警 webhook 生命周期与令牌校验。

## 待实现

- 实例级配置 schema(当前为自由 JSON,凭据明文,见 ADR-004)。
- 广播/订阅型集成基类(MQTT / HA 需要)。
- 审计落库(当前写日志)。
- 状态历史(history)与拓扑消费(topology)。

## 与现有代码的关系

`app/collectors/`(weather / amap)是早期的"数据源插件"雏形,
迁移为正式集成后走同一套契约(见 docs/ARCHITECTURE.md 演进路线)。
