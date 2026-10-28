# alerts — 告警组件

渲染告警事件(消费 `GET /api/alerts` 与实时推送)。

## 规划

- AlertList / AlertBadge(firing / resolved 状态)
- 级别着色复用现有 status 色体系(`style.css` 中 status-* 变量)
- 触达渠道由 Alertmanager 侧负责,前端只做展示与确认
