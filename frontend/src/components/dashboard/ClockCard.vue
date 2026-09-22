<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, ArrowRight, Clock } from 'lucide-vue-next'
import { useClock } from '@/composables/useClock'
import { useClockPrefs } from '@/composables/useClockPrefs'
import { formatDurationShort, utcOffsetText } from '@/lib/clock'
import ClockDisplay from '@/components/clock/ClockDisplay.vue'

const router = useRouter()
const { time, state, uptimeSeconds } = useClock()
const { prefs } = useClockPrefs()

const uptimeText = computed(() =>
  state.serverReachable ? formatDurationShort(uptimeSeconds.value) : '',
)
</script>

<template>
  <div class="glass-card relative overflow-hidden p-5">
    <!-- 顶部氛围线 -->
    <div
      class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent"
    />

    <div class="mb-4 flex items-center justify-between gap-2">
      <h3 class="flex items-center gap-2 text-[15px] font-semibold text-text-primary">
        <Clock class="size-4 text-cyan-400" />
        时钟
      </h3>
      <button
        class="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-cyan-400"
        @click="router.push('/clock')"
      >
        详情
        <ArrowRight class="size-3" />
      </button>
    </div>

    <div class="py-1">
      <ClockDisplay size="sm" />
    </div>

    <div class="mt-3 space-y-1 text-center">
      <div class="text-sm text-text-secondary">{{ time.dateFullText }}</div>
      <div class="text-[11px] text-muted-foreground">
        {{ state.timezone }} · {{ utcOffsetText(time.date, state.timezone) }}
      </div>
    </div>

    <div
      v-if="prefs.showUptime && uptimeText"
      class="mt-4 flex items-center justify-center gap-1.5 border-t border-white/5 pt-3 text-[11px] text-muted-foreground/80"
    >
      <Activity class="size-3 text-emerald-400" />
      服务已运行 {{ uptimeText }}
    </div>
  </div>
</template>
