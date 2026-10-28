# prometheus_scrape — exporter 抓取集成(P1 · 第一类 · 只读)

抓取设备上已暴露的 **Prometheus 文本格式端点**(node_exporter 等),
复用 Prometheus 生态的语义,不自造指标格式。

## 规划

- 周期抓取 `/metrics`,解析为实体状态(按 metric family 映射)
- 常见映射:node_load1 / node_memory_* / node_filesystem_* → 各 Entity
- 与 `app/export/prometheus`(底座自身对外暴露)是两个方向,互不混淆

## 边界

- 只读抓取,不下发任何东西。
- Linux PC / NAS 上已有 exporter 即可接入;没有 exporter 的设备走 SNMP 或系统 API。
