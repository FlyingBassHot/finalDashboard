# OpenWrt 集成（P0 · 第一类 · 只读）

通过固件自带的 **ubus / rpcd JSON-RPC** 采集系统、接口与无线客户端信息，
并上报邻居表供拓扑使用。不通过 ubus 下发任何配置（无侵入）。

## 状态

已实现，使用 `httpx.MockTransport` 对 ubus 报文做了完整单测；
**尚未在真实路由器上验证**，首次接入时请优先检查 `last_error` 与实体值。

## 配置

集成实例的 `config`（创建实例时传入）：

```json
{
  "host": "192.168.1.1",
  "scheme": "http",
  "username": "root",
  "password": "***",
  "verify_tls": true,
  "timeout": 10,
  "device_key": "main",
  "name": "客厅路由器"
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `host` | ✅ | 路由器地址，可带 `http://` / `https://` |
| `scheme` | | `http`（默认）/ `https` |
| `username` / `password` | | rpcd 登录凭据；留空则走匿名会话 |
| `verify_tls` | | HTTPS 证书校验，默认 `true` |
| `timeout` | | 单次 ubus 请求超时（秒），默认 10 |
| `device_key` | | 设备 key，默认 `main` |
| `name` | | 展示名，默认取 board hostname |

## 采集的实体

| entity key | domain | 单位 / 值 | 来源 |
| --- | --- | --- | --- |
| `uptime` | sensor | s | `system.info` |
| `load_1m` | sensor | 1 分钟负载 | `system.info` |
| `memory_total` | sensor | MB | `system.info` |
| `memory_used` | sensor | MB | `system.info` |
| `memory_usage` | sensor | % | `system.info` |
| `firmware` | sensor | 文本 | `system.board` |
| `wan_up` | binary_sensor | bool | `network.interface.dump` |
| `wan_ip` | sensor | 文本 | `network.interface.dump` |
| `wlan_clients` | sensor | 个 | `iwinfo.devices` + `iwinfo.assoclist` |

可选调用（`iwinfo` / `luci-rpc`）失败时只降级，不影响整次采集。

## 邻居上报

合并以下来源，按 MAC 去重后通过 `report_neighbors` 上报：

- `luci-rpc.getHostHints` — 主机名 / IP
- `luci-rpc.getDHCPLeases` — DHCP 租约
- `iwinfo.assoclist` — 无线客户端（标记 `is_wireless=true`）

## 边界

- 只读：`manifest.capabilities = {readonly}`，继承 `PollingIntegration`，
  任何动作请求都会被网关拒绝。
- 认证走 rpcd ACL；建议为本集成单独创建只读用户。
- 不在设备侧安装任何 agent。

## 测试

```bash
cd backend
uv run pytest tests/test_openwrt.py
```
