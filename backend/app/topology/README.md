# topology — 网络拓扑(第一类功能边界之一)

整合各集成上报的网络邻居数据，构建「网关 / 设备 / 关系」图，不做任何网络控制。

## 数据来源

- `openwrt` 集成上报的 `luci-rpc` 主机提示 / DHCP 租约 / `iwinfo` 无线客户端
- 将来：`snmp` 的 FDB / 邻居表、mDNS/UPnP 被动发现（仅发现，不扫描）

## 存储(已实现)

表：`neighbor_links`

- 主键：`(device_id, mac)` —— 一条链路一行，不按每次上报堆行
- 字段：`ip` / `hostname` / `interface` / `source` / `is_wireless`
- `first_seen_at` / `last_seen_at`
- 每次上报更新 `last_seen_at` 与字段；消失的邻居不再更新

## 图构建

`GET /api/topology`

- 只取最近 `TOPOLOGY_ACTIVE_WINDOW_SECONDS`（默认 600 秒）内出现过的链路；
- 节点：
  - `kind=device`：来自 `devices` 表；
  - `kind=neighbor`：没有匹配到设备的邻居，ID 为 `mac:<mac>`；
- 匹配规则：`devices.identity` 形如 `mac:aa:bb:…` 的邻居归并到该设备；
- 边：`source`（上报设备）→ `target`（邻居/匹配设备），携带接口、
  是否无线、发现来源、最后可见时间；
- self-loop 在构图阶段过滤。

响应示例：

```json
{
  "nodes": [
    {"id": "openwrt.home.main", "kind": "device", "name": "客厅路由器", "mac": "aa:bb:cc:dd:ee:00", "available": true},
    {"id": "mac:aa:bb:cc:dd:ee:01", "kind": "neighbor", "name": "laptop", "mac": "aa:bb:cc:dd:ee:01", "ip": "192.168.1.10"}
  ],
  "edges": [
    {"source": "openwrt.home.main", "target": "mac:aa:bb:cc:dd:ee:01", "interface": "wlan0", "is_wireless": true, "discovery_source": "iwinfo", "last_seen_at": "…"}
  ],
  "generated_at": "…",
  "active_within_seconds": 600
}
```

## 清理

`neighbor_links.last_seen_at` 超过 `HISTORY_RETENTION_DAYS`（默认 7 天）后由
`app/tasks/history_task.py` 删除。

## 边界

- 只读：不扫描、不探测、不下发任何网络配置；
- 多协议同一设备的归并依赖 `identity`（见 docs/DECISIONS.md ADR-001）；
  匹配不到时以 `mac:` 节点展示，不丢数据；
- 拓扑图目前按请求实时构建，没有单独的快照表；规模变大后再考虑缓存/快照。
