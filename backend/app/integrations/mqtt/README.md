# mqtt — MQTT + Home Assistant discovery 集成(P0 · 第二类 · 直连)

第二类设备的**直连通道**(决策 D1):遵循 **Home Assistant MQTT discovery**
主题约定(`homeassistant/<component>/<id>/config`)。Zigbee2MQTT、Tasmota、
ESPHome 等主流开源方案都原生说这套协议,无需为每家固件写适配。

## 规划

- 订阅 discovery 主题 → 自动注册实体(声明能力)
- 订阅 state 主题 → 实体状态(经 `app/history` 入库)
- 发布 command 主题 → 开关/调节(经 action_gateway,仅对声明了
  on_off / set_level 能力的实体)

## 边界

- 控制仅限基础开关/调节;不做场景编排、不做群组自造规则。
