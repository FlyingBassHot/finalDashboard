# Home Hub 前端

家庭设备仪表盘前端 —— Vue 3 + TypeScript + Vite + Tailwind CSS v4 + radix-vue (shadcn 风格) + ECharts。

## 快速开始

```bash
# 1. 安装依赖（已安装可跳过）
npm install

# 2. 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

开发服务器已配置 Vite 代理：`/api/*` 会转发到 `http://127.0.0.1:8000`，
所以**开发前需要先启动后端**：

```bash
cd ../backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 常用命令

| 命令 | 说明 |
| --- | --- |
| `npm run dev` | 启动开发服务器（热更新） |
| `npm run typecheck` | TypeScript 类型检查（vue-tsc） |
| `npm run build` | 生产构建，产物输出到 `dist/` |
| `npm run preview` | 本地预览生产构建产物 |

## 目录结构

```
src/
├── api/               # 后端接口封装（axios 客户端 + 各模块 API）
│   ├── client.ts      #   全局客户端、错误统一处理
│   ├── weather.ts     #   天气接口（当前天气 + 7 天预报 / 刷新）
│   ├── settings.ts    #   设置接口（家庭设置 / 行政区搜索 / 更新）
│   └── time.ts        #   时间接口（服务器时间 / 时区 / 运行时长）
├── components/
│   ├── ui/            # 基础组件库（Button / Card / Badge / Input / Avatar / DropdownMenu / Separator / Skeleton / Switch）
│   ├── layout/        # 布局（AppLayout / AppSidebar / AppHeader / HeaderClock）
│   ├── dashboard/     # 仪表盘组件（StatCard / DeviceCard / ClockCard）
│   ├── clock/         # 时钟模块
│   │   ├── ClockDisplay.vue   # 统一外壳（按 size 渲染选中的面孔）
│   │   ├── registry.ts        # 面孔注册表 ← 插件化入口
│   │   ├── faces/             # 面孔实现（DigitalFace / FlipFace / AnalogFace）
│   │   ├── WorldClockCard.vue # 世界时钟
│   │   ├── SunProgressCard.vue# 今日日照进度环（复用天气数据）
│   │   └── StopwatchCard.vue  # 秒表 / 倒计时
│   └── settings/      # 设置组件（SelectField 自定义下拉 / ClockPrefsCard 时钟偏好）
├── composables/       # 全局状态（useWeather / useUi / useClock / useClockPrefs），模块级单例
├── config/            # 导航配置（nav）与占位模块配置（modules）
├── data/              # 占位数据（devices）
├── lib/               # 工具（utils / weather 天气码映射 / clock 时区与时长格式化）
├── router/            # 路由（含布局路由与懒加载）
└── views/             # 页面（Dashboard / Weather / Clock / Settings / 模块占位页）
```

## 时钟模块

- **时间来源**：启动时请求一次 `GET /api/time` 校准本机时钟偏差，之后用
  `Date.now() + offset` 本地走时（断网也能走），并每 10 分钟/切回前台重新校准。
  所有时间按**家庭时区**（后端 `home_settings.timezone`）渲染，因此多设备显示一致，
  且不受客户端时区设置影响。校时状态在时钟页与首页卡片上可见。
- **插件化面孔**：新增一种时钟样式只需两步 ——
  ① 在 `src/components/clock/faces/` 写一个接收 `ClockFaceProps`
  （`time / size / showSeconds / hour12`）的组件；
  ② 在 `src/components/clock/registry.ts` 的 `CLOCK_FACES` 里加一行。
  详情页的样式切换器与设置页的偏好选项会自动出现新面孔，无需改动其它代码。
- **偏好存储**：面孔、12/24 小时制、显示秒、世界时钟城市等存在浏览器
  `localStorage`（`homehub:clock-prefs`），不写入服务器数据库。
  存储层是适配器（`setClockPrefsStorage`），将来要改成后端存储只需替换该适配器。
- **深链指定样式**：`/clock?face=analog`（可选 digital / flip / analog）可临时
  锁定面孔而不改动偏好，适合壁挂屏固定 URL 展示。
- **集成位置**：侧边栏「总览 → 时钟」、顶栏迷你钟（`lg` 以上显示）、首页时钟卡片。

## 前后端对接说明

- **设置 → 位置（已对接）**：`GET /api/settings/home` 读取家庭设置；
  `GET /api/settings/locations?keywords=…&subdistrict=N` 搜索行政区（支持
  名称或 adcode，`subdistrict=1` 时携带下级列表，用于设置页省→市→区级联）；
  `PUT /api/settings/home` 保存设置 —— 后端保存成功后会**立即按新位置刷新天气**。
- **天气（已对接）**：`GET /api/weather` 返回当前天气 + 真实 7 天预报；
  `POST /api/weather/refresh` 触发后端从 Open-Meteo 拉取。
  位置未配置时后端返回 409，前端天气页/仪表盘会引导用户前往设置页。
  WMO 天气代码 → 中文描述/图标/主题色的映射在 `src/lib/weather.ts`
  （含 `is_day` 昼夜图标切换）。
- **时间（已对接）**：`GET /api/time` 返回服务器时间戳、家庭时区与进程运行时长
  （只读接口，不修改任何数据）；时钟页的「今日日照」复用天气模块的
  `sunrise` / `sunset`，无需额外接口。
- **设备模块（占位）**：`src/data/devices.ts` 为占位数据，后端接口就绪后，
  在 `src/api/` 新增接口封装，替换 `src/data/devices.ts` 的数据来源即可。


## 部署提示

- 生产构建后，可将 `dist/` 交由后端（FastAPI）托管，或配置同源反向代理；
  后端已支持 CORS（`backend/.env` 中的 `CORS_ORIGINS`，逗号分隔）。
- 深色主题为当前唯一主题，主题变量集中在 `src/style.css` 的 `@theme` 中。

