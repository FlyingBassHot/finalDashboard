# domain — 统一领域模型(运行时)

底座的核心抽象层,定义「设备 / 实体 / 能力 / 事件」的**运行时契约**。
所有集成(integrations)产出的数据最终都被翻译成这里的对象;
所有北向出口(api / export / alerting)消费的也都是这里的对象。

## 内部模型:Home Assistant 风格 Entity(决策 D2)

- **Device**:物理设备的聚合根(一台 NAS、一个 Zigbee 网关下的一个灯)。
- **Entity**:设备暴露的一个可观测/可操作单元(sensor、binary_sensor、
  switch、light、number……沿用 HA 的 domain 语义)。
- **Capability**:能力声明。集成在注册实体时必须声明能力类别,
  框架据此做统一白名单与审计:
  - `readonly`:只读(传感器、指标、状态)
  - `on_off`:开关(第二类设备)
  - `set_level`:调节(亮度、色温、数值)
  - `action`:离散安全动作(如 Wake-on-LAN)
- **EntityState**:实体状态(值 + 属性 + 时间戳),变更时发出领域事件。
- **DomainEvent**:状态变更、设备上下线等,供实时推送与告警链路消费。

## 边界

- 本层是**纯运行时抽象**,不是 ORM 表(models/ 负责持久化),
  也不是 API 出参(schemas/ 负责序列化)。
- **WoT Thing Description 不进入本层**(仅 `app/export/wot` 做导出时翻译)。

## 已实现

- `capability.py` — Capability 枚举(READONLY / ON_OFF / SET_LEVEL / ACTION)+ 写能力集合
- `state.py` — EntityState 不可变状态快照
- `entity.py` — EntityDescriptor 声明(entity_id 三段式)
- `device.py` — DeviceCategory + DeviceDescriptor
- `events.py` — DomainEvent 家族 + 进程内 EventBus(异步顺序分发)
- `topology.py` — Neighbor 邻居记录

冒烟测试:`test/test_contract.py`
