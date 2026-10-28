# alerting — 告警(外挂 Alertmanager 路线,决策 D3)

底座**不内置规则引擎**。告警规则与通知路由交给 Prometheus + Alertmanager：
底座只负责「暴露指标 + 接收告警 + 展示」。

## 链路（已实现）

1. `GET /metrics` 暴露设备/实体/采集健康度；
2. Prometheus 按规则触发 → Alertmanager 路由通知；
3. Alertmanager webhook 回调 `POST /api/alerts/webhook`；
4. 告警按 `fingerprint` 落库（`alerts` 表），支持查询与恢复状态。

## Webhook 配置

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

`ALERT_WEBHOOK_TOKEN` 为空时不校验（仅建议内网）；非空时接受：

- `Authorization: Bearer <token>`
- `X-Webhook-Token: <token>`

## 存储语义

表：`alerts`

- 主键：`fingerprint`（缺失时用 labels 的 SHA-256 兜底）；
- firing：更新状态、清除 `resolved_at`、`received_count += 1`；
- resolved：记录 `resolved_at`，保留 `ends_at`；
- Alertmanager 对未结束告警使用 `0001-01-01T00:00:00Z`，入库时归一为 `NULL`；
- 同一告警重复投递只更新，不会产生重复行。

## 查询

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/alerts` | 最近告警，可按 `status=firing|resolved` 过滤 |
| GET | `/api/alerts/{fingerprint}` | 单条告警 |

## 边界

- 不自建阈值规则 DSL；规则写在 Prometheus；
- 当前只保留告警的**最新状态**，不保留状态迁移时间线；
  需要审计时再加 `alert_events`；
- 实时推送前端尚未实现（WS/SSE 待定）。
