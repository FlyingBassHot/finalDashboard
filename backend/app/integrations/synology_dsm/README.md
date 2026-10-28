# synology_dsm — Synology DSM 集成(P2 · 第一类 · 只读)

通过 DSM 官方 API 读取 NAS 状态。设备零安装(DSM 自带 API)。

## 规划

- DSM Auth API 会话认证 → entry.cgi 查询
- 存储池/卷容量、系统健康、CPU/内存、磁盘 SMART 概要

## 边界

- 只读。不做 DSM 配置变更、不做开关机。
