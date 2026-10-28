# prometheus — 底座指标暴露

以 **Prometheus 文本暴露格式 (0.0.4)** 输出底座自身指标,供 Prometheus 抓取、
Alertmanager 告警(决策 D3 的采集端)。

端点：`GET /metrics`

## 指标

| 指标 | 标签 | 说明 |
| --- | --- | --- |
| `homehub_build_info` | `version` | 版本信息，常量 1 |
| `homehub_device_up` | `device_id` `integration` `instance_name` `category` | 设备在线 1/0 |
| `homehub_device_info` | 同上 + `name` `manufacturer` `model` | 设备静态元数据，常量 1 |
| `homehub_entity_info` | `entity_id` `integration` `device_id` `domain` `name` `unit` | 实体元数据，常量 1 |
| `homehub_entity_state` | `entity_id` `integration` `device_id` `domain` `unit` | 数值/布尔实体的当前值 |
| `homehub_integration_enabled` | `instance_name` `integration` | 实例是否启用 |
| `homehub_integration_healthy` | `instance_name` `integration` | 已启用、无 `last_error` 且成功轮询过 = 1 |
| `homehub_integration_last_poll_timestamp_seconds` | `instance_name` `integration` | 最近一次轮询尝试时间 |
| `homehub_integration_last_success_timestamp_seconds` | `instance_name` `integration` | 最近一次成功时间 |

说明：

- 文本类实体（IP、固件版本等）只出现在 `homehub_entity_info`，不进入数值指标；
- 每次抓取实时查询 SQLite，不维护进程内计数器；
- 删除设备/实例后，对应 series 自动消失。

## Prometheus 抓取配置

```yaml
scrape_configs:
  - job_name: home-hub
    metrics_path: /metrics
    static_configs:
      - targets: ["127.0.0.1:8000"]
```

## 告警规则示例

```yaml
groups:
  - name: home-hub
    rules:
      - alert: HomeHubDeviceDown
        expr: homehub_device_up == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "设备离线：{{ $labels.name }}"

      - alert: HomeHubIntegrationUnhealthy
        expr: homehub_integration_healthy == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "集成采集异常：{{ $labels.instance_name }}"
```

## 与 prometheus_scrape 的区别

`export/prometheus` 是**底座对外暴露指标**；
`integrations/prometheus_scrape` 是**底座抓取设备 exporter**，方向相反。
