# alerting — 告警(外挂 Alertmanager 路线,决策 D3)

底座**不内置规则引擎**。告警规则与通知路由交给 Prometheus + Alertmanager 生态:
底座只负责「暴露指标 + 接收告警 + 展示」。

## 链路

1. 底座在 `app/export/prometheus` 暴露 `/metrics`(设备在线状态、实体值、
   采集健康度)
2. Prometheus 抓取并按规则触发 → Alertmanager 路由通知
3. Alertmanager webhook 回调本模块 `POST /api/alerts/webhook`
4. 告警事件入库 + 实时推送前端(`views/alerts`)

## 边界

- 不自建阈值规则 DSL;确需简单本地规则的场景,后续单独决策。
