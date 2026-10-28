# history — 传感器时序历史(决策 D4)

实体状态(传感器、指标)的时间序列记录。

## 存储(已实现)

- 表：`entity_history`
- 一行 = 一次**真实变化**（首值也会记录）
- 字段：`entity_id` / `value` / `attributes` / `observed_at` / `recorded_at`
- 索引：`(entity_id, observed_at)`
- 保留期：默认 **7 天**（`HISTORY_RETENTION_DAYS`）

写入路径：

```
Integration.poll() → context.emit_state()
  → StateChangedEvent
    → HistoryRecorder
      → 值与属性都没变：跳过
      → 否则 append 一行
```

只记变化而不是每次轮询都记，避免 60 秒轮询把 SQLite 写满。
代价是长时间稳定的值不会产生“心跳点”；需要时可在后续加周期快照。

## 查询

`GET /api/entities/{entity_id}/history`

| 参数 | 说明 |
| --- | --- |
| `start` / `end` | ISO 时间；缺省查询最近 24 小时 |
| `limit` | 1～5000，默认 1000；取最近 N 条后按时间升序返回 |

时间以 UTC 输出（带 `Z` / 偏移），与 `/api/entities/{id}/state` 一致。

## 清理

`app/tasks/history_task.py` 由 APScheduler 周期执行：

- 删除 `observed_at < now - HISTORY_RETENTION_DAYS` 的样本；
- 同时清理过期的 `neighbor_links`（见 `app/topology`）。

## 边界

- 不做降采样聚合（天级均值等），将来作为可选项；
- SQLite 单文件扛不住之前不引入时序数据库；若切换，仅替换本模块。
- 删除集成实例时，它产生的历史会一并删除（与设备/实体一致）。
