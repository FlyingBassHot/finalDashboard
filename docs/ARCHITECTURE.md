# Home Hub 架构总览

> 开源家庭设备底座:统一设备抽象 + 插件化集成。
> 状态检测、性能监控、网络拓扑、事件告警,及受限的基础控制。

> 框架的中间层 / 北向契约与扩展点见 [FRAMEWORK.md](FRAMEWORK.md)。

## 1. 定位

不做高度定制的自用玩具,做**通用底座**:符合形状的设备都能接入。
核心资产是抽象与接口契约,功能全部以集成(插件)形式挂在契约之下。
最大化复用行业认可的开源与工业标准,**不自造协议/规则**。

## 2. 设备模型与功能边界

| | 第一类 · 开源 OS 设备 | 第二类 · 厂商智能设备 |
| --- | --- | --- |
| 典型 | NAS、OpenWrt、摄像头、Linux PC | 灯光、开关、插座、传感器 |
| 系统访问 | 有 root(能做,但刻意少做) | 闭源固件(只能说设备暴露的协议) |
| 能力边界 | **只读**:状态检测、性能监控、网络拓扑、事件告警 | readonly + on_off + set_level |
| 例外动作 | Wake-on-LAN(网络层原语,唯一安全动作) | — |

边界哲学:**读总是安全的,写必须最小化**,由插件的能力声明 +
action_gateway 白名单在框架层强制,不靠自觉。

## 3. 架构决策记录(已拍板)

| # | 决策 | 内容 |
| --- | --- | --- |
| D1 | 第二类设备通道 | **双适配器并存**:`mqtt/`(MQTT + HA discovery 直连)与 `homeassistant/`(嫁接已有 HA 实例),用户按场景选择 |
| D2 | 内部模型与导出 | 内部为 **HA 风格 Entity**;`export/wot/` **仅在导出时**自动翻译为 W3C WoT TD JSON 供第三方消费,不作为内部运行模型 |
| D3 | 告警 | **外挂 Prometheus Alertmanager 路线**:底座暴露 `/metrics`(`export/prometheus/`),规则与通知路由在 Alertmanager 侧,webhook 回调 `app/alerting` 落库展示;底座不内置规则引擎 |
| D4 | 存储 | 设备/实体/配置元数据**永久存 SQLite,无老化**;传感器时序默认写 SQLite,**开启 TTL 自动删除,原始采样保留 7 天**;将来换存储只动 `app/history` |
| D5 | 无侵入 | 设备侧零安装,只走设备本就有的标准端点(ubus / SNMP / exporter / DSM / ONVIF / MQTT / HA API) |

## 4. 数据流

```
南向集成(适配器,不自造规则)
  integrations/{openwrt,snmp,prometheus_scrape,synology_dsm,onvif,wakeonlan,mqtt,homeassistant}
        │  (契约: plugins/contract → domain Entity)
        ▼
domain(统一领域模型:Device / Entity / Capability / Event)
        │
        ├─→ models(SQLite 元数据,永久)          ← repositories / services
        ├─→ history(传感器时序,SQLite + TTL 7 天)
        ├─→ topology(邻居数据整合 → 设备关系图)
        ├─→ api(REST:设备/实体/动作/拓扑/告警)
        ├─→ export/wot(WoT TD JSON,可选导出)
        ├─→ export/prometheus(/metrics)──→ Prometheus + Alertmanager ──webhook──→ alerting
        └─→ 实时推送(前端状态更新,通道待定:WS/SSE)
```

动作(写)只有一条通道:**api → plugins/action_gateway(能力白名单+审计)→ 集成**。

## 5. 目录结构

### backend

```
backend/app/
├── main.py            # 入口(现有)
├── core/              # 配置、数据库(现有)
├── domain/            # ★ 运行时领域模型:Device/Entity/Capability/Event
├── plugins/           # ★ 插件框架:契约、注册表、调度、action_gateway
├── integrations/      # ★ 南向集成(每目录一个,适配器并存)
│   ├── openwrt/  snmp/  prometheus_scrape/  synology_dsm/  onvif/   # 第一类(只读)
│   ├── wakeonlan/                                                    # 第一类(唯一动作)
│   └── mqtt/  homeassistant/                                         # 第二类(状态+基础控制)
├── topology/          # ★ 网络拓扑(邻居整合 + 图构建)
├── history/           # ★ 传感器时序(SQLite + TTL 7 天)
├── alerting/          # ★ Alertmanager webhook 接收 + 告警事件
├── export/            # ★ 北向导出:wot/(WoT TD) + prometheus/(/metrics)
├── api/               # REST 路由(现有 weather/settings/time + 将来设备域)
├── models/            # ORM(现有三表 + 将来设备域新表)
├── repositories/  schemas/  services/                                # 现有分层
├── tasks/             # APScheduler(现有天气任务 + 将来 TTL 清理)
├── collectors/        # 现有 weather/amap(待迁为正式集成,暂不动)
└── utils/             # 工具(现有)
```

### frontend

```
frontend/src/
├── api/               # 现有 + 将来 devices/integrations/topology/alerts/realtime
├── components/
│   ├── ui/  layout/  dashboard/  clock/  settings/   # 现有
│   ├── devices/       # ★ 能力驱动渲染
│   │   └── entity-cards/   # ★ 卡片实现(对齐 clock faces 插件化模式)
│   ├── topology/      # ★ 拓扑图
│   └── alerts/        # ★ 告警组件
├── composables/       # 现有 + 将来 useDevices/useAlerts/useRealtime
├── config/            # nav/modules(现有,设备模块上线后由真实数据驱动)
├── data/              # devices.ts mock(待 api/devices.ts 替换)
├── lib/               # 工具 + 将来 capability 映射
├── router/            # 现有(将来注册 /devices /topology /alerts)
└── views/
    ├── (现有平铺页面,不动)
    ├── devices/       # ★ 列表 / 设备详情 / 实体详情
    ├── topology/      # ★ 拓扑页
    └── alerts/        # ★ 告警中心
```

## 6. REST

已实现：

- `GET /api/devices` / `GET /api/devices/{device_id}`
- `GET /api/entities` / `GET /api/entities/{entity_id}`
- `GET /api/entities/{entity_id}/state`
- `GET /api/entities/{entity_id}/history`
- `GET /api/topology`
- `POST /api/entities/{entity_id}/actions` / `GET /api/action-audits`
- `GET /api/events`（SSE）
- `POST /api/alerts/webhook` / `GET /api/alerts` / `GET /api/alerts/{fingerprint}`
- `GET /metrics`（Prometheus 文本）
- `GET /api/integrations/manifests`
- `GET/POST /api/integrations`、`GET/PATCH/DELETE /api/integrations/{id}`
- 天气 / 设置 / 授时（见 backend/README.md）

规划：

- `POST /api/entities/{id}/actions`（唯一写入口，走 action_gateway）
- `GET /api/export/wot`
- 实时：WS 或 SSE（待方案确认）

## 7. 演进路线(现有代码零破坏)

1. **✅ 已完成**:骨架与领域基类(`domain` 全套运行时抽象 +
   `plugins` 契约 / 注册表 / 目录 / 上下文 / ActionGateway)。
2. **✅ 已完成**:持久化层(设备 / 实体 / 集成实例 / 最新状态 ORM + repositories)、
   状态表、实例运行器(轮询调度、异常隔离、健康记录)、集成实例 CRUD 与
   设备/实体只读 API。
3. **✅ 已完成**:首个集成 `integrations/openwrt`(P0,只读),
   已用 MockTransport 覆盖 ubus 报文;待真机验证。
4. **✅ 已完成**:`topology`(邻居聚合 + 图 API)与 `history`
   (变化才写 + 7 天 TTL + 定时清理)。
5. **✅ 已完成**:`export/prometheus`(`/metrics`) → Alertmanager →
   `alerting` webhook 落库与查询闭环。
6. **✅ 已完成**:第二个接入方式 `prometheus_scrape`（node_exporter 抓取，第一类只读）；
   运行器补上连接失败自动重试（ADR-010）。
7. **✅ 已完成（北向/中间层框架）**:动作 API + 持久化审计、SSE 实时事件、
   实体扩展字段；契约与扩展点见 `docs/FRAMEWORK.md`。
8. **✅ 已完成**:订阅 / 混合型集成生命周期（`collection_mode` + runner 任务监管/重连）。
9. **下一步**:高频推送事件缓冲与每集成 config schema；之后再做 `snmp` / `mqtt`。
10. **存量迁移**:`collectors/`(weather / amap)改造为正式集成,走同一契约;
   `frontend/src/data/devices.ts` mock 替换为真实 API。
