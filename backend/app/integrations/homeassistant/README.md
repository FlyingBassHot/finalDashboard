# homeassistant — Home Assistant 桥接集成(P1 · 第二类 · 嫁接)

第二类设备的**桥接通道**(决策 D1):用户已有 Home Assistant 时,
把 HA 实体镜像为底座实体,复用其 2000+ 集成的设备覆盖面。

## 规划

- 长期令牌 + REST(/api/states)或 WebSocket 订阅实体状态
- 镜像映射:HA entity_id → 底座 Entity,HA domain → 能力类别
- 控制调用 HA service call(homeassistant.turn_on/off、light.turn_on 等)
  经 action_gateway

## 边界

- HA 是被桥接的南向系统,不是内部依赖;底座不要求部署 HA
  (直连场景走 `mqtt/` 集成)。
