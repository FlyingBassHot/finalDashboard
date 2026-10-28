# plugins — 插件运行时(框架)

集成(integration)的宿主框架,负责「注册 → 生命周期 → 调度 → 动作执行」。
本目录不含任何具体设备逻辑,具体集成在 `app/integrations/`。

## 已实现(基类阶段)

- **manifest.py** — IntegrationManifest 自描述(name 规范 / 能力边界 /
  默认轮询间隔,构造期校验)
- **contract.py** — Integration(ABC)+ PollingIntegration(第一类只读基类,
  动作被硬拒绝)+ IntegrationContext(Protocol)+ ActionRequest / ActionResult
- **registry.py** — IntegrationRegistry 注册表 + `@register_integration` 装饰器
- **catalog.py** — EntityCatalog 设备 / 实体全局目录(内存实现,接口不变可换 DB)
- **context.py** — BaseIntegrationContext 框架默认上下文
  (声明规范化 → 目录登记 → 翻译为领域事件上总线)
- **action_gateway.py** — **全底座唯一写通道**:集成级 + 实体级双重白名单、
  异常归一、全程审计(允许 / 拒绝 / 失败均留痕)

冒烟测试:`test/test_contract.py`(含"只读集成动作被类型级拒绝"的验证)。

## 待实现

- **scheduler** — 集成实例级的轮询调度(实例运行器)。
  复用现有 `app/tasks/scheduler.py` 的 APScheduler 单例,不另起调度器。
- 实例生命周期管理(启动 / 停用 / 健康度)。

## 与现有代码的关系

`app/collectors/`(weather / amap)是早期的"数据源插件"雏形,
迁移为正式集成后走同一套契约(见 docs/ARCHITECTURE.md 演进路线)。
