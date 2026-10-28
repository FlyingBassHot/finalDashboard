# snmp — SNMP 通用集成(P1 · 第一类 · 只读)

行内最通用的网络设备监控标准。NAS / 路由器 / 交换机开 SNMP 即接入,零安装。

## 规划

- SNMP v2c(community)/ v3(USM 认证)
- 标准 MIB 起步:IF-MIB(接口流量)、HOST-RESOURCES-MIB(存储/进程)、
  ENTITY-MIB(硬件实体)
- OID → Entity 映射表做成集成内配置,不硬编码设备型号

## 边界

- 只读(GET / GETBULK),不做 SET。
- v3 优先,凭据加密存储。
