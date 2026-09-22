<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Moon, Sun, Sunrise, Sunset } from 'lucide-vue-next'
import { useClock } from '@/composables/useClock'
import { useWeather } from '@/composables/useWeather'
import { formatDurationShort, nowMinutesOfDay, timeOfDayMinutes } from '@/lib/clock'
import { formatSunTime } from '@/lib/weather'
import Badge from '@/components/ui/Badge.vue'

const { time } = useClock()
const weather = useWeather()

onMounted(() => {
  weather.load()
})

const today = computed(() => weather.state.data?.daily?.[0] ?? null)

const sunriseMinutes = computed(() => timeOfDayMinutes(today.value?.sunrise ?? null))
const sunsetMinutes = computed(() => timeOfDayMinutes(today.value?.sunset ?? null))
const nowMinutes = computed(() => nowMinutesOfDay(time.value))

type Phase = 'unknown' | 'before' | 'day' | 'after'

const phase = computed<Phase>(() => {
  const rise = sunriseMinutes.value
  const set = sunsetMinutes.value
  if (rise === null || set === null) return 'unknown'
  if (nowMinutes.value < rise) return 'before'
  if (nowMinutes.value >= set) return 'after'
  return 'day'
})

/** 白天进度 0 - 1 */
const progress = computed(() => {
  const rise = sunriseMinutes.value
  const set = sunsetMinutes.value
  if (phase.value !== 'day' || rise === null || set === null) return 0
  return Math.min(1, Math.max(0, (nowMinutes.value - rise) / (set - rise)))
})

const RADIUS = 54
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const dashOffset = computed(() => CIRCUMFERENCE * (1 - progress.value))

const headline = computed(() => {
  const rise = sunriseMinutes.value
  const set = sunsetMinutes.value

  if (phase.value === 'unknown') return '暂无日照数据'
  if (phase.value === 'before' && rise !== null) {
    return `距日出 ${formatDurationShort((rise - nowMinutes.value) * 60)}`
  }
  if (phase.value === 'after' && rise !== null) {
    const untilTomorrow = 24 * 60 - nowMinutes.value + rise
    return `已入夜 · 距明日日出 ${formatDurationShort(untilTomorrow * 60)}`
  }
  if (set !== null) {
    return `距日落 ${formatDurationShort((set - nowMinutes.value) * 60)}`
  }
  return '白天'
})

const locationText = computed(() => {
  const loc = weather.state.data?.location
  if (!loc) return ''
  return [loc.home_name, loc.province, loc.city, loc.district].filter(Boolean).join(' · ')
})
</script>

<template>
  <div class="glass-card flex flex-col p-5 sm:p-6">
    <div class="mb-5 flex items-center gap-2.5">
      <div class="flex size-10 items-center justify-center rounded-xl bg-amber-500/15 text-amber-400">
        <Sun class="size-5" />
      </div>
      <div class="min-w-0 flex-1">
        <h3 class="text-[15px] font-semibold text-text-primary">今日日照</h3>
        <p class="truncate text-xs text-muted-foreground">{{ locationText || '等待天气数据' }}</p>
      </div>
      <Badge variant="preview">真实数据</Badge>
    </div>

    <div class="flex flex-1 flex-col items-center gap-6 sm:flex-row sm:justify-center sm:gap-8">
      <!-- 进度环 -->
      <div class="relative">
        <svg class="size-36 -rotate-90" viewBox="0 0 128 128">
          <circle
            cx="64"
            cy="64"
            :r="RADIUS"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            stroke-width="9"
          />
          <circle
            cx="64"
            cy="64"
            :r="RADIUS"
            fill="none"
            stroke="url(#sun-ring)"
            stroke-width="9"
            stroke-linecap="round"
            :stroke-dasharray="CIRCUMFERENCE"
            :stroke-dashoffset="dashOffset"
            class="transition-[stroke-dashoffset] duration-500 ease-out"
          />
          <defs>
            <linearGradient id="sun-ring" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#fbbf24" />
              <stop offset="100%" stop-color="#22d3ee" />
            </linearGradient>
          </defs>
        </svg>

        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <component
            :is="phase === 'day' ? Sun : Moon"
            class="size-5"
            :class="phase === 'day' ? 'text-amber-300' : 'text-slate-300'"
          />
          <span class="mt-1 text-xl font-bold tabular-nums text-text-primary">
            {{ Math.round(progress * 100) }}%
          </span>
          <span class="text-[10px] text-muted-foreground">白天进度</span>
        </div>
      </div>

      <!-- 日照信息 -->
      <div class="w-full max-w-56 space-y-3">
        <div class="flex items-center gap-2.5 rounded-xl border border-white/5 bg-card/40 px-3.5 py-2.5">
          <Sunrise class="size-4 shrink-0 text-amber-300" />
          <span class="text-xs text-muted-foreground">日出</span>
          <span class="ml-auto text-sm font-semibold tabular-nums text-text-primary">
            {{ formatSunTime(today?.sunrise ?? null) }}
          </span>
        </div>
        <div class="flex items-center gap-2.5 rounded-xl border border-white/5 bg-card/40 px-3.5 py-2.5">
          <Sunset class="size-4 shrink-0 text-orange-300" />
          <span class="text-xs text-muted-foreground">日落</span>
          <span class="ml-auto text-sm font-semibold tabular-nums text-text-primary">
            {{ formatSunTime(today?.sunset ?? null) }}
          </span>
        </div>
        <p class="text-center text-xs text-cyan-300/90">{{ headline }}</p>
      </div>
    </div>
  </div>
</template>
