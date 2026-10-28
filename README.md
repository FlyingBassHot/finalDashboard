# finalDashboard · Home Hub

开源家庭设备**通用底座**:统一设备抽象(HA 风格 Entity)+ 插件化南向集成
(MQTT discovery / Home Assistant / OpenWrt ubus / SNMP / Prometheus exporter /
ONVIF / DSM / Wake-on-LAN)。状态检测、性能监控、网络拓扑、事件告警
(Prometheus + Alertmanager 外挂),及受限的基础控制(开关/调节)。
无侵入:设备侧零安装,只走行业标准端点。

## 快速开始

- 后端:`cd backend && uv sync && cp .env.example .env && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 前端:`cd frontend && npm install && npm run dev`(Vite 代理 `/api` → 127.0.0.1:8000)

> 后端测试:`cd backend && uv run pytest`;静态检查:`uv run ruff check app tests`。
> `.env`、`data/*.db` 与日志均为本地文件,不会提交到仓库。

## 文档导航

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 架构决策与目录总览(**先读这个**)
- [docs/DECISIONS.md](docs/DECISIONS.md) — 开发决策记录(设备身份 / WoL / 存储)
- [backend/README.md](backend/README.md) — 后端模块与 API
- [frontend/README.md](frontend/README.md) — 前端结构与对接说明
- 集成契约与各集成边界:`backend/app/integrations/README.md`

## 核心边界

- 第一类(开源 OS 设备):**只读**监控 + Wake-on-LAN 唯一安全动作
- 第二类(厂商智能设备):状态展示 + 基础开关/调节
- 存储:元数据永久 SQLite;传感器时序 SQLite + TTL(原始采样 7 天)
- 对外:可选导出 W3C WoT TD(JSON),内部不依赖它
