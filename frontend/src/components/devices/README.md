# devices — 设备域通用渲染

按**能力(capability)驱动**渲染,不为具体设备型号写定制组件 ——
这是"通用底座"理念在前端的表现。

## 结构

- `entity-cards/` — 实体卡片实现(能力 → 卡片,插件化注册)
- (将来)`DeviceCard` 重构 — 由真实设备数据驱动,替换 `src/data/devices.ts` mock

## 原则

- 新设备类型接入**不新增页面代码**,只出现新实体 → 自动落到既有卡片
- 卡片实现放 `entity-cards/`,注册关系对齐 clock 模块的
  `registry.ts + faces/` 插件化先例
