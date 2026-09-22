# Home Hub 后端

FastAPI + SQLAlchemy (async) + SQLite 的家庭设备后端。

## 快速开始

```bash
# 1. 安装依赖（uv 或 pip，依赖见 pyproject.toml）
uv sync

# 2. 配置环境变量（参考 .env，需自行填入 AMAP_WEB_SERVICE_KEY）
#    .env 示例见仓库；数据库默认 data/home_hub.db

# 3. 启动
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动时自动建表、尝试刷新一次天气（失败不阻塞启动）、并按
`WEATHER_UPDATE_INTERVAL_MINUTES`（默认 10 分钟）定时刷新。

## 模块与调用链

```
设置模块（地点） ──►  天气模块
  /api/settings         GET/PUT /api/settings/home
                        决定家庭位置（省市区 + GCJ02/WGS84 坐标 + 时区）
                        │
                        ▼
  /api/weather          GET /api/weather      ← 当前天气 + 7 天预报
                        POST /api/weather/refresh
```

- 家庭位置保存在 `home_settings` 表（单例 id=1），坐标存双份：
  **GCJ02**（高德，供地图类功能）与 **WGS84**（Open-Meteo 等国际服务）。
  更新设置（PUT）后会自动按新位置立即刷新一次天气，失败不阻塞保存。
- 行政区划来自高德行政区 API，后端已完成 GCJ02 → WGS84 换算
  （`app/utils/coordinate.py`）。

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/time` | 服务器时间戳 + 家庭时区 + 进程运行时长（只读，不写库） |
| GET | `/api/settings/home` | 获取家庭设置（不存在时自动创建默认行） |
| PUT | `/api/settings/home` | 更新家庭设置（地点变化后自动刷新天气） |
| GET | `/api/settings/locations?keywords=…&subdistrict=N` | 行政区搜索（名称或 adcode，`subdistrict=1` 携带下级列表） |
| GET | `/api/weather` | 当前天气 + 7 天预报（含日出日落、降水概率） |
| POST | `/api/weather/refresh` | 立即从 Open-Meteo 拉取并入库 |

天气接口在家庭位置未配置时返回 `409`，尚未有天气数据时返回 `404`。

`/api/time` 仅使用内存中的进程启动时刻与已有的 `home_settings.timezone`，
**不涉及任何表结构变更**；前端用它校准各显示设备的时间。

## 目录结构

```
app/
├── api/            # 路由层（weather / settings / time）
├── collectors/     # 外部数据源（open-meteo / amap 行政区）
├── core/           # 配置、异步数据库
├── models/         # SQLAlchemy 模型（home_settings / weather_current / weather_daily）
├── repositories/   # 数据访问层
├── schemas/        # Pydantic 出入参
├── services/       # 业务层
├── tasks/          # 调度任务（定时刷新天气）
└── utils/          # 坐标换算等
```
