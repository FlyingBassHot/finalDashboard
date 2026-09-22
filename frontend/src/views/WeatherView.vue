<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  CalendarDays,
  Clock,
  CloudSun as CloudSunIcon,
  Droplets,
  MapPin,
  RefreshCw,
  Settings as SettingsIcon,
  Sunrise,
  Sunset as SunsetIcon,
  Thermometer,
  Wind,
  WifiOff as WifiOffIcon,
} from 'lucide-vue-next'
import { useWeather } from '@/composables/useWeather'
import {
  forecastDayLabel,
  formatObservedAt,
  formatSunTime,
  formatTemperature,
  weatherIcon,
  weatherInfo,
} from '@/lib/weather'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Skeleton from '@/components/ui/Skeleton.vue'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const router = useRouter()
const weather = useWeather()

onMounted(() => {
  weather.load()
})

/* ---------- 页面状态 ---------- */
const view = computed(() => {
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

/** 位置显示名：省 市 区 */
const locationText = computed(() => {
  const loc = weather.state.data?.location
  if (!loc) return ''
  return [loc.province, loc.city, loc.district].filter(Boolean).join(' · ') || '未知位置'
})

/** 今日日出日落（daily[0]） */
const today = computed(() => weather.state.data?.daily?.[0] ?? null)

/* ---------- ECharts 温度趋势（真实数据） ---------- */
const chartOption = computed(() => {
  const daily = weather.state.data?.daily ?? []
  return {
    backgroundColor: 'transparent',
    grid: { left: 8, right: 8, top: 28, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,17,23,0.92)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      axisPointer: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
    },
    xAxis: {
      type: 'category',
      data: daily.map((d, i) => forecastDayLabel(d.date, i)),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748b', fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      min: (value: { min: number }) => Math.floor(value.min - 3),
      max: (value: { max: number }) => Math.ceil(value.max + 3),
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    series: [
      {
        name: '最高温',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: daily.map((d) => d.temperature_max),
        lineStyle: { width: 3, color: '#fbbf24' },
        itemStyle: { color: '#fbbf24', borderColor: '#0a0c10', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(251,191,36,0.25)' },
              { offset: 1, color: 'rgba(251,191,36,0)' },
            ],
          },
        },
      },
      {
        name: '最低温',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: daily.map((d) => d.temperature_min),
        lineStyle: { width: 3, color: '#22d3ee' },
        itemStyle: { color: '#22d3ee', borderColor: '#0a0c10', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34,211,238,0.2)' },
              { offset: 1, color: 'rgba(34,211,238,0)' },
            ],
          },
        },
      },
    ],
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="flex items-center gap-2.5">
          <h2 class="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
            天气站
          </h2>
          <Badge variant="default">真实数据</Badge>
        </div>
        <p class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
          <span class="inline-flex items-center gap-1.5">
            <MapPin class="size-3.5" />
            {{ weather.state.data ? locationText : '数据源 Open-Meteo' }}
          </span>
          <span v-if="weather.state.data" class="text-muted-foreground/50">·</span>
          <span v-if="weather.state.data" class="tabular-nums text-muted-foreground/80">
            {{ weather.state.data.location.timezone }}
          </span>
        </p>
      </div>
      <Button
        variant="gradient"
        :loading="weather.state.refreshing"
        :disabled="view.kind !== 'data'"
        @click="weather.refresh()"
      >
        <RefreshCw class="size-4" />
        {{ weather.state.refreshing ? '刷新中…' : '刷新天气' }}
      </Button>
    </div>

    <!-- 加载中 -->
    <div v-if="view.kind === 'loading'" class="space-y-6">
      <div class="glass-card relative overflow-hidden p-8">
        <div class="flex flex-col items-center gap-8 sm:flex-row sm:justify-center">
          <Skeleton class="size-28 rounded-3xl" />
          <div class="space-y-3">
            <Skeleton class="h-20 w-56" />
            <Skeleton class="h-5 w-36" />
          </div>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Skeleton v-for="i in 4" :key="i" class="h-28" />
      </div>
    </div>

    <!-- 未配置家庭位置 -->
    <div
      v-else-if="view.kind === 'unconfigured'"
      class="glass-card flex flex-col items-center justify-center gap-3 px-6 py-20 text-center"
    >
      <div class="flex size-16 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-300">
        <SettingsIcon class="size-8" />
      </div>
      <div>
        <p class="text-lg font-semibold text-text-primary">还没有设置家庭位置</p>
        <p class="mt-1 text-sm text-muted-foreground">
          前往设置页选择家庭所在的省市区，保存后即可获取该位置的实时天气
        </p>
      </div>
      <Button variant="gradient" @click="router.push('/settings')">
        <SettingsIcon class="size-4" />
        前往设置
      </Button>
    </div>

    <!-- 暂无天气数据 -->
    <div
      v-else-if="view.kind === 'empty'"
      class="glass-card flex flex-col items-center justify-center gap-3 px-6 py-20 text-center"
    >
      <div class="flex size-16 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400">
        <CloudSunIcon class="size-8" />
      </div>
      <div>
        <p class="text-lg font-semibold text-text-primary">暂无天气数据</p>
        <p class="mt-1 text-sm text-muted-foreground">点击按钮从 Open-Meteo 获取最新天气</p>
      </div>
      <Button variant="gradient" :loading="weather.state.refreshing" @click="weather.refresh()">
        <RefreshCw class="size-4" />
        获取天气数据
      </Button>
    </div>

    <!-- 网络错误 -->
    <div
      v-else-if="view.kind === 'error'"
      class="glass-card flex flex-col items-center justify-center gap-3 px-6 py-20 text-center"
    >
      <div class="flex size-16 items-center justify-center rounded-2xl bg-status-offline/10 text-status-offline">
        <WifiOffIcon class="size-8" />
      </div>
      <div>
        <p class="text-lg font-semibold text-text-primary">无法连接后端服务</p>
        <p class="mt-1 text-sm text-muted-foreground">{{ view.message }}</p>
      </div>
      <Button variant="secondary" :loading="weather.state.loading" @click="weather.reload()">
        <RefreshCw class="size-4" />
        重试
      </Button>
    </div>

    <!-- 数据展示 -->
    <template v-else-if="view.kind === 'data' && weather.state.data && info && icon">
      <!-- Hero -->
      <div class="glass-card relative overflow-hidden" :class="info.gradient">
        <div class="pointer-events-none absolute -left-20 -top-24 size-72 rounded-full bg-white/8 blur-3xl" />
        <div class="pointer-events-none absolute -bottom-28 right-10 size-64 rounded-full bg-black/15 blur-3xl" />

        <div class="relative px-6 py-10 sm:px-10 sm:py-12">
          <div class="flex flex-col items-center gap-8 text-center sm:flex-row sm:justify-between sm:text-left">
            <!-- 图标 + 温度 -->
            <div class="flex flex-col items-center gap-5 sm:flex-row sm:gap-8">
              <component
                :is="icon"
                class="size-24 animate-float sm:size-32"
                :class="info.glow"
                :style="{ filter: 'drop-shadow(0 0 32px currentColor)' }"
              />
              <div>
                <div class="flex items-baseline justify-center gap-1 sm:justify-start">
                  <span class="text-7xl font-bold tabular-nums tracking-tight text-white sm:text-8xl">
                    {{ formatTemperature(weather.state.data.current.temperature) }}
                  </span>
                  <span class="text-3xl font-semibold text-white/70">C</span>
                </div>
                <div class="mt-2 text-xl font-medium text-white/90">{{ info.label }}</div>
                <div class="mt-1.5 text-sm text-white/60">
                  观测于 {{ formatObservedAt(weather.state.data.current.observed_at) }}
                  <template v-if="weather.state.data.current.apparent_temperature !== null">
                    · 体感 {{ formatTemperature(weather.state.data.current.apparent_temperature) }}
                  </template>
                </div>
              </div>
            </div>

            <!-- 位置与日出日落 -->
            <div class="flex flex-col items-center gap-2 sm:items-end">
              <Badge variant="outline" class="border-white/15 bg-black/20 text-white/90">
                <MapPin class="size-3" />
                {{ weather.state.data.location.home_name }} · {{ locationText }}
              </Badge>
              <div class="flex items-center gap-2">
                <Badge
                  v-if="today"
                  variant="outline"
                  class="border-white/15 bg-black/20 text-white/90"
                >
                  <Sunrise class="size-3 text-amber-200" />
                  {{ formatSunTime(today.sunrise) }}
                </Badge>
                <Badge
                  v-if="today"
                  variant="outline"
                  class="border-white/15 bg-black/20 text-white/90"
                >
                  <SunsetIcon class="size-3 text-orange-200" />
                  {{ formatSunTime(today.sunset) }}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 详情卡 -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div class="glass-card p-5">
          <div class="flex items-center gap-2 text-xs text-muted-foreground">
            <Droplets class="size-4 text-cyan-400" />
            相对湿度
          </div>
          <div class="mt-3 text-3xl font-bold tabular-nums text-text-primary">
            {{ Math.round(weather.state.data.current.humidity) }}<span class="text-lg text-muted-foreground">%</span>
          </div>
          <div class="mt-1 text-xs text-muted-foreground/70">空气湿润度监测</div>
        </div>

        <div class="glass-card p-5">
          <div class="flex items-center gap-2 text-xs text-muted-foreground">
            <Wind class="size-4 text-violet-400" />
            风速
          </div>
          <div class="mt-3 text-3xl font-bold tabular-nums text-text-primary">
            {{ weather.state.data.current.wind_speed ?? '--' }}<span class="text-lg text-muted-foreground">km/h</span>
          </div>
          <div class="mt-1 text-xs text-muted-foreground/70">10 米高度风速</div>
        </div>

        <div class="glass-card p-5">
          <div class="flex items-center gap-2 text-xs text-muted-foreground">
            <Thermometer class="size-4 text-amber-400" />
            体感温度
          </div>
          <div class="mt-3 text-3xl font-bold tabular-nums text-text-primary">
            {{ weather.state.data.current.apparent_temperature !== null
              ? formatTemperature(weather.state.data.current.apparent_temperature)
              : '--' }}
          </div>
          <div class="mt-1 text-xs text-muted-foreground/70">综合湿度与风的体感</div>
        </div>

        <div class="glass-card p-5">
          <div class="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock class="size-4 text-emerald-400" />
            观测时间
          </div>
          <div class="mt-3 text-3xl font-bold tabular-nums text-text-primary">
            {{ formatObservedAt(weather.state.data.current.observed_at).split(' ')[1] }}
          </div>
          <div class="mt-1 text-xs text-muted-foreground/70">
            {{ formatObservedAt(weather.state.data.current.observed_at).split(' ')[0] }}
            {{ weather.state.data.current.is_day ? '· 白天' : '· 夜间' }}
          </div>
        </div>
      </div>
    </template>

    <!-- 未来 7 天预报（真实数据） -->
    <div v-if="view.kind === 'data' && weather.state.data">
      <div class="mb-3 flex items-center gap-2">
        <CalendarDays class="size-4 text-muted-foreground" />
        <h3 class="text-[15px] font-semibold text-text-primary">未来 7 天预报</h3>
        <Badge variant="default">真实数据</Badge>
      </div>

      <div class="glass-card p-5">
        <VChart class="h-56 w-full" :option="chartOption" autoresize />
      </div>

      <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        <div
          v-for="(day, i) in weather.state.data.daily"
          :key="day.date"
          class="glass-card flex flex-col items-center gap-1.5 p-4 text-center"
        >
          <span
            class="text-sm font-medium"
            :class="i === 0 ? 'text-cyan-400' : 'text-text-secondary'"
          >
            {{ forecastDayLabel(day.date, i) }}
          </span>
          <component
            :is="weatherIcon(day.weather_code, true)"
            class="size-7"
            :class="weatherInfo(day.weather_code).glow"
          />
          <span class="text-xs text-muted-foreground">{{ weatherInfo(day.weather_code).label }}</span>
          <div class="mt-1 flex items-baseline gap-2 text-sm tabular-nums">
            <span class="font-bold text-amber-300">{{ Math.round(day.temperature_max) }}°</span>
            <span class="text-muted-foreground">{{ Math.round(day.temperature_min) }}°</span>
          </div>
          <span
            v-if="day.precipitation_probability !== null"
            class="inline-flex items-center gap-1 text-[11px] text-sky-300/90"
          >
            <Droplets class="size-3" />
            {{ Math.round(day.precipitation_probability) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
