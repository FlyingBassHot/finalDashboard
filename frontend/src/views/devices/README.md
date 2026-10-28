# views/devices — 设备页面

设备域页面,全部由统一实体数据驱动(消费 `src/api/devices.ts` 将来封装)。

## 规划页面与路由

| 页面 | 路由 | 内容 |
| --- | --- | --- |
| DevicesView | `/devices` | 全设备列表(按房间/类别/状态过滤) |
| DeviceDetailView | `/devices/:id` | 设备信息 + 实体卡片网格 |
| EntityDetailView | `/entities/:id` | 单实体详情 + 历史曲线(读 history API) |

> 现有 `DashboardView` 的设备区(占位 mock)后续切换到同一数据源;
> `router/index.ts` 届时按上表注册,现阶段不动现有路由。
