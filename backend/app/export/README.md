# export — 北向导出层

对外(第三方系统)的**可选**出口,全部从 `app/domain` / 数据库只读翻译,
不影响内部运行模型。

- `prometheus/` — 底座自身指标暴露(`GET /metrics`),已实现
- `wot/` — 实体 → W3C WoT Thing Description JSON(决策 D2),待实现
