# prometheus — 底座指标暴露

以 **Prometheus 文本暴露格式**输出底座自身指标,供 Prometheus 抓取、
Alertmanager 告警(决策 D3 的采集端)。

## 指标草案

- `homehub_device_up` — 设备在线状态
- `homehub_entity_state`(按实体类型) — 数值型实体当前值
- `homehub_integration_collect_success / duration` — 各集成采集健康度

## 说明

与 `integrations/prometheus_scrape`(南向抓设备 exporter)方向相反,
勿混淆。
