# prometheus_scrape — Prometheus exporter 抓取（第一类 · 只读）

抓取 node_exporter 等标准 `/metrics` 端点，只读采集主机状态。设备侧无需安装任何新组件：
exporter 本来就暴露这些指标。

## 状态

已实现，使用固定的 node_exporter 风格报文做了单测，并在本机模拟 exporter 完成端到端验证
（离线可见、恢复后自动接入、与 OpenWrt 邻居表做身份匹配）。**尚未在真实 NAS / PC 上验证。**

## 配置

```json
{
  "url": "http://192.168.1.20:9100/metrics",
  "device_key": "main",
  "name": "NAS-01",
  "mac": "aa:bb:cc:dd:ee:02",
  "category": "nas",
  "disk_mountpoint": "/",
  "bearer_token": "***",
  "verify_tls": true,
  "timeout": 10
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `url` | ✅ | 完整地址，必须带 `http://` 或 `https://` |
| `device_key` | | 设备 key，默认 `main` |
| `name` | | 展示名，默认取 URL 主机名 |
| `mac` | | 网卡 MAC。填写后写入设备 `identity`，路由器的邻居表即可把它归并为同一台设备 |
| `category` | | `computer`（默认）或 `nas` |
| `disk_mountpoint` | | 统计哪个挂载点的磁盘，默认 `/` |
| `bearer_token` | | 若 exporter 开启了鉴权，填写 Bearer Token（响应中自动脱敏） |
| `verify_tls` / `timeout` | | HTTPS 证书校验与超时（秒） |

## 采集的实体

实体 key 与 OpenWrt 集成一致，前端卡片可以直接复用：

| entity key | 单位 | 来源指标 |
| --- | --- | --- |
| `uptime` | s | `node_time_seconds - node_boot_time_seconds` |
| `load_1m` | — | `node_load1` |
| `memory_total` / `memory_used` | MB | `node_memory_MemTotal_bytes` / `MemAvailable` |
| `memory_usage` | % | 由上两项计算 |
| `disk_total` | MB | `node_filesystem_size_bytes{mountpoint=...}` |
| `disk_usage` | % | `size` 与 `avail` 计算 |
| `os_version` | — | `node_os_info{name, version}` |

说明：

- 指标缺失时跳过对应实体，不影响其他实体；
- `MB` 实际按 MiB（1024² 字节）计算，与 OpenWrt 保持一致；
- CPU 使用率需要对计数器求速率，单次抓取无法得到，暂未实现。

## 可用性

- 抓取成功 → 设备 `available = true`；
- 抓取失败 → 设备 `available = false`，错误写入实例的 `last_error`，并按轮询间隔自动重试；
- exporter 启动前就创建实例也可以：设备会先以不可用状态出现，exporter 上线后自动接入。

## 边界

- 只读：不向 exporter 写入任何内容；
- 不做 `/metrics` 之外的抓取（例如 SNMP、ssh）；
- 不提供 exporter 的端口发现，需要用户明确填写 URL。

## 测试

```bash
cd backend
uv run pytest tests/test_prometheus_scrape.py
```
