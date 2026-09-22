<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  CheckCircle2,
  Clock,
  Hash,
  Link2,
  RefreshCw,
  Server,
  Settings2,
  ShieldCheck,
  WifiOff,
} from 'lucide-vue-next'
import { useClock } from '@/composables/useClock'
import { useClockPrefs } from '@/composables/useClockPrefs'
import { CLOCK_FACES } from '@/components/clock/registry'
import ClockDisplay from '@/components/clock/ClockDisplay.vue'
import WorldClockCard from '@/components/clock/WorldClockCard.vue'
import SunProgressCard from '@/components/clock/SunProgressCard.vue'
import StopwatchCard from '@/components/clock/StopwatchCard.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Switch from '@/components/ui/Switch.vue'
import { formatDuration, utcOffsetText } from '@/lib/clock'

const { time, state, uptimeSeconds, offsetText, sync } = useClock()
const { prefs, setFace, update } = useClockPrefs()
const route = useRoute()

/** 支持用 ?face=analog 这样的深链临时指定面孔（壁挂屏可直接锁定样式，不写入偏好） */
const urlFace = computed(() => {
  const value = route.query.face
  const id = typeof value === 'string' ? value : ''
  return CLOCK_FACES.some((face) => face.id === id) ? id : ''
})

onMounted(() => {
  // useClock 在首次调用时已自动启动并校时
})

/** 今日是当年第几天 / 第几周 */
const dayOfYear = computed(() => {
  const { year, month, day } = time.value
  const start = Date.UTC(year, 0, 1)
  const current = Date.UTC(year, month - 1, day)
  return Math.floor((current - start) / 86_400_000) + 1
})

const weekOfYear = computed(() => Math.ceil(dayOfYear.value / 7))

const infoRows = computed(() => [
  { label: '家庭时区', value: state.timezone || '--', mono: true },
  { label: 'UTC 偏移', value: utcOffsetText(time.value.date, state.timezone), mono: true },
  { label: '时间来源', value: state.serverReachable ? '服务器校时' : '本机系统时间', mono: false },
  { label: '校时偏差', value: offsetText.value, mono: true },
  {
    label: '服务器运行时长',
    value: state.serverReachable ? formatDuration(uptimeSeconds.value) : '--',
    mono: true,
  },
  {
    label: '今日进度',
    value: `${time.value.year} 年第 ${dayOfYear.value} 天 · 第 ${weekOfYear.value} 周`,
    mono: false,
  },
  {
    label: 'Unix 时间戳',
    value: String(Math.floor(time.value.date.getTime() / 1000)),
    mono: true,
  },
])

const syncBadge = computed(() => {
  if (state.syncState === 'syncing') return { variant: 'secondary' as const, text: '校时中…' }
  if (state.serverReachable) return { variant: 'online' as const, text: `已同步 ${offsetText.value}` }
  return { variant: 'warning' as const, text: '本地时间' }
})
</script>

<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="flex items-center gap-2.5">
          <h2 class="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">时钟</h2>
          <Badge :variant="syncBadge.variant">
            <component
              :is="state.serverReachable ? ShieldCheck : WifiOff"
              class="size-3"
            />
            {{ syncBadge.text }}
          </Badge>
        </div>
        <p class="mt-1.5 flex items-center gap-1.5 text-sm text-muted-foreground">
          <Clock class="size-3.5" />
          {{ state.timezone }} ·
          {{ utcOffsetText(time.date, state.timezone) }} ·
          {{ state.serverReachable ? '所有设备显示一致' : '未连接后端，显示本机时间' }}
        </p>
      </div>
      <Button
        variant="secondary"
        :loading="state.syncing"
        @click="sync()"
      >
        <RefreshCw class="size-4" />
        重新校时
      </Button>
    </div>

    <!-- Hero 时钟 -->
    <div class="glass-card relative overflow-hidden">
      <div class="pointer-events-none absolute -right-20 -top-24 size-72 rounded-full bg-cyan-500/10 blur-3xl" />
      <div class="pointer-events-none absolute -bottom-24 -left-16 size-64 rounded-full bg-violet-500/10 blur-3xl" />

      <div class="relative px-6 py-10 sm:px-10 sm:py-12">
        <div class="flex justify-center">
          <ClockDisplay size="lg" :face="urlFace" />
        </div>

        <div class="mt-6 text-center">
          <p class="text-sm text-text-secondary">{{ time.dateFullText }}</p>
          <p class="mt-1 text-xs text-muted-foreground">
            {{ time.period }} · 第 {{ time.hours24 }} 时
          </p>
          <p
            v-if="urlFace"
            class="mt-2 inline-flex items-center gap-1.5 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2.5 py-1 text-[11px] text-cyan-300"
          >
            <Link2 class="size-3" />
            URL 指定样式（未保存到偏好）
          </p>
        </div>

        <!-- 样式切换器（插件化面孔） -->
        <div class="mx-auto mt-8 max-w-2xl">
          <div class="mb-2.5 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Settings2 class="size-3.5" />
            时钟样式
          </div>
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <button
              v-for="face in CLOCK_FACES"
              :key="face.id"
              class="rounded-xl border px-4 py-3 text-left transition-all"
              :class="
                prefs.face === face.id
                  ? 'border-cyan-400/40 bg-cyan-500/10 ring-1 ring-inset ring-cyan-400/20'
                  : 'border-white/5 bg-card/40 hover:border-white/15'
              "
              @click="setFace(face.id)"
            >
              <span class="flex items-center gap-1.5 text-sm font-medium text-text-primary">
                <CheckCircle2
                  class="size-3.5"
                  :class="prefs.face === face.id ? 'text-cyan-400' : 'text-transparent'"
                />
                {{ face.name }}
              </span>
              <span class="mt-0.5 block pl-5 text-[11px] leading-snug text-muted-foreground">
                {{ face.description }}
              </span>
            </button>
          </div>

          <!-- 快捷偏好 -->
          <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <Switch
              :model-value="prefs.hour12"
              label="12 小时制"
              description="关闭则使用 24 小时制"
              @update:model-value="update('hour12', $event)"
            />
            <Switch
              :model-value="prefs.showSeconds"
              label="显示秒"
              @update:model-value="update('showSeconds', $event)"
            />
          </div>
          <p class="mt-3 text-center text-[11px] text-muted-foreground/60">
            偏好保存在本机浏览器（localStorage），不经过服务器
          </p>
        </div>
      </div>
    </div>

    <!-- 世界时钟 + 日照 -->
    <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <WorldClockCard />
      <SunProgressCard />
    </div>

    <!-- 计时工具 + 时间信息 -->
    <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <StopwatchCard />

      <div class="glass-card flex flex-col p-5 sm:p-6">
        <div class="mb-5 flex items-center gap-2.5">
          <div class="flex size-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
            <Hash class="size-5" />
          </div>
          <div>
            <h3 class="text-[15px] font-semibold text-text-primary">时间信息</h3>
            <p class="text-xs text-muted-foreground">时区、校时与运行状态</p>
          </div>
        </div>

        <dl class="flex-1 space-y-2.5">
          <div
            v-for="row in infoRows"
            :key="row.label"
            class="flex items-center justify-between gap-3 border-b border-white/5 pb-2.5 last:border-0"
          >
            <dt class="shrink-0 text-xs text-muted-foreground">{{ row.label }}</dt>
            <dd
              class="truncate text-xs text-text-secondary"
              :class="row.mono ? 'font-mono tabular-nums' : ''"
            >
              {{ row.value }}
            </dd>
          </div>
        </dl>

        <div
          class="mt-5 flex items-start gap-2 rounded-xl border border-white/5 bg-card/40 px-4 py-3 text-[11px] leading-relaxed text-muted-foreground"
        >
          <Server class="mt-0.5 size-3.5 shrink-0 text-cyan-400" />
          <span>
            时间来自后端 <span class="font-mono">GET /api/time</span>：启动时校准一次本机偏差，
            之后本地走时并每 10 分钟重新校准；即使某台设备系统时间不准，显示的时间依然正确。
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
