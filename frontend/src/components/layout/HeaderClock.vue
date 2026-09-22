<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Clock } from 'lucide-vue-next'
import { useClock } from '@/composables/useClock'
import { useClockPrefs } from '@/composables/useClockPrefs'

const router = useRouter()
const { time, state } = useClock()
const { prefs } = useClockPrefs()

const hourText = computed(() =>
  prefs.hour12 ? String(time.value.hours12).padStart(2, '0') : time.value.hourText,
)

const title = computed(
  () => `${time.value.dateFullText} ${state.timezone}${state.serverReachable ? ' · 已校时' : ' · 本机时间'}`,
)
</script>

<template>
  <button
    class="hidden items-center gap-2 rounded-full border border-white/8 bg-card/60 px-3 py-1.5 transition-colors hover:border-cyan-400/30 hover:bg-card lg:flex"
    :title="title"
    @click="router.push('/clock')"
  >
    <Clock class="size-3.5 text-cyan-400" />
    <span class="text-sm font-semibold tabular-nums text-text-primary">
      {{ hourText }}:{{ time.minuteText }}
    </span>
    <span v-if="prefs.showSeconds" class="text-xs tabular-nums text-muted-foreground">
      {{ time.secondText }}
    </span>
  </button>
</template>
