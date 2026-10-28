# entity-cards — 能力驱动的实体卡片(插件化)

对齐本项目时钟模块已验证的插件化模式
(`components/clock/registry.ts + faces/`):**新增一种卡片 = 实现组件 + 注册一行**。

## 规划卡片(按 HA domain 语义)

| 卡片 | 实体类型 | 能力 |
| --- | --- | --- |
| SensorCard | sensor | readonly |
| BinarySensorCard | binary_sensor | readonly(在线/离线等) |
| SwitchCard | switch | on_off |
| LightCard | light | on_off + set_level |
| NumberCard | number | set_level |
| InfoCard | 设备级只读信息(型号/固件/运行时长) | readonly |

## 注册表(将来)

`registry.ts`:实体 domain → 卡片组件映射;
能力映射辅助(`src/lib/capability.ts` 将来)统一判定可渲染类型与可控操作。

## 边界

- 卡片只发「动作请求」(经 action 通道),不直接持有任何设备协议概念
  (MQTT/HA/SNMP 等词不应出现在这一层)。
