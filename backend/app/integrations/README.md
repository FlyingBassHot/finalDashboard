# integrations — 南向集成(适配器)

每个子目录是一个集成,实现 `app/plugins/contract`。适配器**并存**(决策 D1):
第二类设备的 MQTT 直连与 Home Assistant 桥同时支持,用户按场景选择。

## 开发约定

1. 实现插件契约(连接管理、发现实体、拉取/订阅状态、受控动作);
2. manifest 声明能力边界(readonly / on_off / set_level / action);
3. 产出的实体统一为 HA 风格 Entity(交给 `app/domain`);
4. 协议适配不自造规则:只用设备侧本来就有的标准端点(无侵入)。

## 集成清单

### 第一类 · 开源 OS 设备(只读为主)

| 目录 | 对象 | 协议 | 能力 | 优先级 |
| --- | --- | --- | --- | --- |
| `openwrt/` | OpenWrt/ImmortalWrt 路由器 | ubus / rpcd JSON-RPC | readonly + 上报邻居表供拓扑 | P0 |
| `snmp/` | 任何开启 SNMP 的设备(NAS/路由器/交换机) | SNMP v2c/v3 标准 MIB | readonly | P1 |
| `prometheus_scrape/` | Linux PC / NAS(node_exporter 等) | Prometheus 文本端点抓取 | readonly | P1 |
| `synology_dsm/` | Synology NAS | DSM 官方 API | readonly | P2 |
| `onvif/` | ONVIF 摄像头 | ONVIF Profile S | readonly(不控流、不控云台) | P2 |
| `wakeonlan/` | 任意支持 WoL 的主机 | Magic Packet | **action(唯一安全动作)** | P1 |

> 边界:第一类原则上不做配置修改与深度控制。Wake-on-LAN 是网络层原语,
> 作为 Ping 检测失败后的闭环唤醒动作,是唯一例外。

### 第二类 · 厂商智能设备(状态展示 + 基础控制)

| 目录 | 对象 | 协议 | 能力 | 优先级 |
| --- | --- | --- | --- | --- |
| `mqtt/` | Zigbee2MQTT / Tasmota / ESPHome 等 | MQTT + Home Assistant discovery 主题约定 | readonly / on_off / set_level | P0 |
| `homeassistant/` | 已有 Home Assistant 实例 | HA REST/WebSocket API(桥接镜像) | readonly / on_off / set_level | P1 |

> 优先级为建议值,待总体方案确认后调整。
