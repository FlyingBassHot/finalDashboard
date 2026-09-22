<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  Clock,
  CloudSun as CloudSunIcon,
  Droplets,
  HardDrive,
  MapPin,
  MonitorCheck,
  RefreshCw,
  Settings as SettingsIcon,
  Thermometer,
  ThermometerSun,
  Wifi,
  WifiOff as WifiOffIcon,
  Wind,
} from 'lucide-vue-next'
import { useWeather } from '@/composables/useWeather'
import {
  weatherIcon,
  weatherInfo,
  formatTemperature,
  formatObservedAt,
} from '@/lib/weather'
import { DEVICES } from '@/data/devices'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import DeviceCard from '@/components/dashboard/DeviceCard.vue'
import ClockCard from '@/components/dashboard/ClockCard.vue'

const router = useRouter()
const weather = useWeather()

onMounted(() => {
  weather.load()
})

/* ---------- 问候语 ---------- */
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 11) return '早上好'
  if (hour >= 11 && hour < 13) return '中午好'
  if (hour >= 13 && hour < 18) return '下午好'
  return '晚上好'
})

const todayText = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
})

/* ---------- 统计数据 ---------- */
const onlineCount = computed(() => DEVICES.filter((d) => d.status === 'online').length)

const stats = computed(() => [
  {
    icon: MonitorCheck,
    tint: 'bg-cyan-500/15 text-cyan-400',
    label: '在线设备',
    value: `${onlineCount.value} / ${DEVICES.length}`,
    sub: '台设备在线运行',
  },
  {
    icon: ThermometerSun,
    tint: 'bg-amber-500/15 text-amber-400',
    label: '当前温度',
    value: weather.state.data
      ? formatTemperature(weather.state.data.current.temperature)
      : '--°',
    sub: weather.state.data
      ? `${weatherInfo(weather.state.data.current.weather_code).label}${weather.state.data.current.apparent_temperature !== null ? ` · 体感 ${formatTemperature(weather.state.data.current.apparent_temperature)}` : ''}`
      : '暂无天气数据',
  },
  {
    icon: Wifi,
    tint: 'bg-violet-500/15 text-violet-400',
    label: '家庭网络',
    value: '正常',
    sub: '千兆宽带 · 延迟 12ms',
  },
  {
    icon: HardDrive,
    tint: 'bg-emerald-500/15 text-emerald-400',
    label: 'NAS 存储',
    value: '62%',
    sub: '已用 1.24 TB / 2 TB',
    progress: 62,
  },
])

/* ---------- 天气卡片状态 ---------- */
const weatherView = computed(() => {
  const s = weather.state
  if (s.loading && !s.data) return { kind: 'loading' as const }
  if (s.error === 'unconfigured') return { kind: 'unconfigured' as const }
  if (s.error === 'empty') return { kind: 'empty' as const }
  if (s.error && !s.data) return { kind: 'error' as const, message: s.error.replace(/^error:/, '') }
  if (s.data) return { kind: 'data' as const }
  return { kind: 'idle' as const }
})

const info = computed(() =>
  weather.state.data ? weatherInfo(weather.state.data.current.weather_code) : null,
)

const icon = computed(() =>
  weather.state.data
    ? weatherIcon(weather.state.data.current.weather_code, weather.state.data.current.is_day)
    : null,
)

const locationText = computed(() => {
  const loc = weather.state.data?.location
  if (!loc) return ''
  return [loc.province, loc.city, loc.district].filter(Boolean).join(' · ') || '未知位置'
})
</script>

<template>
  <div class="space-y-6">
    <!-- 欢迎区 -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          {{ greeting }}，<span class="text-gradient">欢迎回家</span> 👋
        </h2>
        <p class="mt-1.5 text-sm text-muted-foreground">
          {{ todayText }} · 一切尽在掌握
        </p>
      </div>
      <Badge variant="outline" class="hidden sm:inline-flex">
        <span class="size-1.5 rounded-full bg-status-online animate-pulse-ring" />
        本地服务已连接
      </Badge>
    </div>

    <!-- 统计卡 -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard v-for="s in stats" :key="s.label" v-bind="s" />
    </div>

    <!-- 天气 + 设备 -->
    <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <!-- 实时天气卡片（真实数据） -->
      <div class="xl:col-span-2">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="flex items-center gap-2 text-[15px] font-semibold text-text-primary">
            实时天气
            <Badge variant="default">真实数据</Badge>
          </h3>
        </div>

        <!-- 加载中 -->
        <div v-if="weatherView.kind === 'loading'" class="glass-card relative overflow-hidden p-6">
          <div class="flex flex-col gap-6 sm:flex-row sm:items-center">
            <Skeleton class="size-20 rounded-2xl" />
            <div class="flex-1 space-y-3">
              <Skeleton class="h-14 w-40" />
              <Skeleton class="h-4 w-52" />
              <Skeleton class="h-4 w-64" />
            </div>
          </div>
        </div>

        <!-- 未配置位置 -->
        <div
          v-else-if="weatherView.kind === 'unconfigured'"
          class="glass-card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center"
        >
          <div class="flex size-14 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-300">
            <SettingsIcon class="size-7" />
          </div>
          <div>
            <p class="font-semibold text-text-primary">还没有设置家庭位置</p>
            <p class="mt-1 text-sm text-muted-foreground">
              前往设置页选择省市区，保存后自动获取该位置天气
            </p>
          </div>
          <Button variant="gradient" @click="router.push('/settings')">
            <SettingsIcon class="size-4" />
            前往设置
          </Button>
        </div>

        <!-- 暂无数据 -->
        <div
          v-else-if="weatherView.kind === 'empty'"
          class="glass-card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center"
        >
          <div class="flex size-14 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400">
            <CloudSunIcon class="size-7" />
          </div>
          <div>
            <p class="font-semibold text-text-primary">暂无天气数据</p>
            <p class="mt-1 text-sm text-muted-foreground">
              点击下方按钮，从 Open-Meteo 拉取家庭位置的实时天气
            </p>
          </div>
          <Button variant="gradient" :loading="weather.state.refreshing" @click="weather.refresh()">
            <RefreshCw class="size-4" />
            立即获取天气
          </Button>
        </div>

        <!-- 网络错误 -->
        <div
          v-else-if="weatherView.kind === 'error'"
          class="glass-card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center"
        >
          <div class="flex size-14 items-center justify-center rounded-2xl bg-status-offline/10 text-status-offline">
            <WifiOffIcon class="size-7" />
          </div>
          <div>
            <p class="font-semibold text-text-primary">无法连接后端服务</p>
            <p class="mt-1 text-sm text-muted-foreground">{{ weatherView.message }}</p>
          </div>
          <Button variant="secondary" :loading="weather.state.loading" @click="weather.reload()">
            <RefreshCw class="size-4" />
            重试
          </Button>
        </div>

        <!-- 数据展示 -->
        <div
          v-else-if="weatherView.kind === 'data' && weather.state.data && info && icon"
          class="glass-card relative overflow-hidden"
          :class="info.gradient"
        >
          <!-- 装饰光斑 -->
          <div
            class="pointer-events-none absolute -right-16 -top-16 size-56 rounded-full bg-white/8 blur-3xl"
          />
          <div
            class="pointer-events-none absolute -bottom-24 left-1/3 size-48 rounded-full bg-black/15 blur-3xl"
          />

          <div class="relative p-6 sm:p-7">
            <!-- 顶栏 -->
            <div class="flex flex-wrap items-center gap-2">
              <Badge variant="outline" class="border-white/15 bg-black/20 text-white/90">
                <span class="size-1.5 rounded-full bg-emerald-400 animate-pulse-ring" />
                实时监测
              </Badge>
              <Badge variant="outline" class="border-white/15 bg-black/20 text-white/90">
                <MapPin class="size-3" />
                {{ weather.state.data.location.home_name }} · {{ locationText }}
              </Badge>
              <button
                class="ml-auto flex items-center gap-1.5 rounded-lg border border-white/15 bg-black/20 px-3 py-1.5 text-xs font-medium text-white/90 transition-colors hover:bg-black/35 disabled:opacity-50"
                :disabled="weather.state.refreshing"
                @click="weather.refresh()"
              >
                <RefreshCw class="size-3.5" :class="{ 'animate-spin': weather.state.refreshing }" />
                {{ weather.state.refreshing ? '刷新中…' : '刷新数据' }}
              </button>
            </div>

            <!-- 主体 -->
            <div class="mt-6 flex flex-col gap-6 sm:flex-row sm:items-center">
              <component
                :is="icon"
                class="size-20 shrink-0 animate-float sm:size-24"
                :class="info.glow"
                :style="{ filter: 'drop-shadow(0 0 24px currentColor)' }"
              />
              <div class="flex-1">
                <div class="flex items-baseline gap-1">
                  <span class="text-6xl font-bold tabular-nums tracking-tight text-white sm:text-7xl">
                    {{ formatTemperature(weather.state.data.current.temperature) }}
                  </span>
                  <span class="text-2xl font-semibold text-white/80">C</span>
                </div>
                <div class="mt-1 text-lg font-medium text-white/90">
                  {{ info.label }}
                  <template v-if="weather.state.data.current.apparent_temperature !== null">
                    <span class="text-sm text-white/60">
                      · 体感 {{ formatTemperature(weather.state.data.current.apparent_temperature) }}
                    </span>
                  </template>
                </div>
              </div>
              <button
                class="group flex items-center gap-2 self-start rounded-xl border border-white/15 bg-black/20 px-4 py-2.5 text-sm font-medium text-white/90 transition-all hover:bg-black/35 sm:self-center"
                @click="router.push('/weather')"
              >
                查看详情
                <ArrowRight
                  class="size-4 transition-transform duration-200 group-hover:translate-x-0.5"
                />
              </button>
            </div>

            <!-- 指标 -->
            <div
              class="mt-6 grid grid-cols-2 gap-3 border-t border-white/10 pt-5 sm:grid-cols-4"
            >
              <div class="flex items-center gap-2.5">
                <span class="flex size-8 items-center justify-center rounded-lg bg-white/10 text-white/80">
                  <Droplets class="size-4" />
                </span>
                <div class="leading-tight">
                  <div class="text-[11px] text-white/60">相对湿度</div>
                  <div class="text-sm font-semibold tabular-nums text-white">
                    {{ Math.round(weather.state.data.current.humidity) }}%
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2.5">
                <span class="flex size-8 items-center justify-center rounded-lg bg-white/10 text-white/80">
                  <Wind class="size-4" />
                </span>
                <div class="leading-tight">
                  <div class="text-[11px] text-white/60">风速</div>
                  <div class="text-sm font-semibold tabular-nums text-white">
                    {{ weather.state.data.current.wind_speed ?? '--' }} km/h
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2.5">
                <span class="flex size-8 items-center justify-center rounded-lg bg-white/10 text-white/80">
                  <Thermometer class="size-4" />
                </span>
                <div class="leading-tight">
                  <div class="text-[11px] text-white/60">体感温度</div>
                  <div class="text-sm font-semibold tabular-nums text-white">
                    {{ weather.state.data.current.apparent_temperature !== null
                      ? formatTemperature(weather.state.data.current.apparent_temperature)
                      : '--' }}
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2.5">
                <span class="flex size-8 items-center justify-center rounded-lg bg-white/10 text-white/80">
                  <Clock class="size-4" />
                </span>
                <div class="leading-tight">
                  <div class="text-[11px] text-white/60">观测时间</div>
                  <div class="text-sm font-semibold text-white">
                    {{ formatObservedAt(weather.state.data.current.observed_at) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 时钟 + 设备状态 -->
      <div class="space-y-6">
        <!-- 时钟卡片（面孔跟随用户偏好） -->
        <ClockCard />

        <!-- 设备状态 -->
        <div>
          <div class="mb-3 flex items-center justify-between">
            <h3 class="flex items-center gap-2 text-[15px] font-semibold text-text-primary">
              设备状态
            </h3>
            <Badge variant="preview">预览数据</Badge>
          </div>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <DeviceCard v-for="d in DEVICES" :key="d.id" :device="d" />
          </div>
          <p class="mt-3 text-center text-xs text-muted-foreground/70">
            设备数据为占位展示 · 待后端接口接入后自动替换
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
