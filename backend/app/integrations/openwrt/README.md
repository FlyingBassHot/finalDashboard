# openwrt — OpenWrt 集成(P0 · 第一类 · 只读)

通过 **ubus / rpcd JSON-RPC**(luci-rpc 兼容端点)采集 OpenWrt 系信息,
设备零安装(固件自带 rpcd)。

## 采集范围

- `system` board / info:型号、固件、运行时长、负载、内存
- `network.interface` / `network.device`:接口与链路状态
- `iwinfo`:无线客户端、信号质量
- `luci-rpc` 邻居/ARP 数据 → 上报 `app/topology` 供拓扑构建

## 边界

- **只读**。不通过 ubus 下发配置(不改防火墙、不改网络设置)。
- 认证走 rpcd 的 ACL 用户(建议只读组),凭据加密存储。

## 状态

骨架占位,待方案与契约确定后实现。
