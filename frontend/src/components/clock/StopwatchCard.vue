<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Flag, Pause, Play, RotateCcw, Timer, TimerReset } from 'lucide-vue-next'
import { formatStopwatch } from '@/lib/clock'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Input from '@/components/ui/Input.vue'

type Tab = 'stopwatch' | 'countdown'

const tab = ref<Tab>('stopwatch')

/* ---------------- 秒表 ---------------- */
const swRunning = ref(false)
const swElapsed = ref(0)
const swLaps = ref<number[]>([])
let swTimer: number | null = null
let swBase = 0
let swStartedAt = 0

function swTick() {
  swElapsed.value = swBase + (Date.now() - swStartedAt)
}

function swStart() {
  if (swRunning.value) return
  swRunning.value = true
  swStartedAt = Date.now()
  swTimer = window.setInterval(swTick, 50)
}

function swPause() {
  if (!swRunning.value) return
  swRunning.value = false
  swBase = swElapsed.value
  if (swTimer !== null) {
    window.clearInterval(swTimer)
    swTimer = null
  }
}

function swReset() {
  swPause()
  swBase = 0
  swElapsed.value = 0
  swLaps.value = []
}

function swLap() {
  if (swElapsed.value === 0) return
  swLaps.value = [swElapsed.value, ...swLaps.value].slice(0, 4)
}

/* ---------------- 倒计时 ---------------- */
const cdMinutes = ref(5)
const cdSeconds = ref(0)
const cdRunning = ref(false)
const cdRemaining = ref(5 * 60 * 1000)
const cdTotal = ref(5 * 60 * 1000)
const cdFinished = ref(false)
let cdTimer: number | null = null
let cdEndsAt = 0

function clampInput() {
  cdMinutes.value = Math.min(999, Math.max(0, Math.floor(Number(cdMinutes.value) || 0)))
  cdSeconds.value = Math.min(59, Math.max(0, Math.floor(Number(cdSeconds.value) || 0)))
}

watch([cdMinutes, cdSeconds], () => {
  clampInput()
  if (cdRunning.value) return
  cdTotal.value = (cdMinutes.value * 60 + cdSeconds.value) * 1000
  cdRemaining.value = cdTotal.value
  cdFinished.value = false
})

function cdTick() {
  cdRemaining.value = Math.max(0, cdEndsAt - Date.now())
  if (cdRemaining.value <= 0) {
    cdPause()
    cdFinished.value = true
  }
}

function cdStart() {
  if (cdRunning.value || cdRemaining.value <= 0) return
  cdFinished.value = false
  cdRunning.value = true
  cdEndsAt = Date.now() + cdRemaining.value
  cdTimer = window.setInterval(cdTick, 100)
}

function cdPause() {
  if (!cdRunning.value) return
  cdRunning.value = false
  if (cdTimer !== null) {
    window.clearInterval(cdTimer)
    cdTimer = null
  }
}

function cdReset() {
  cdPause()
  cdFinished.value = false
  cdTotal.value = (cdMinutes.value * 60 + cdSeconds.value) * 1000
  cdRemaining.value = cdTotal.value
}

const cdProgress = computed(() => {
  if (cdTotal.value <= 0) return 0
  return Math.min(1, Math.max(0, 1 - cdRemaining.value / cdTotal.value))
})

/** 秒表与倒计时共用一个秒级显示 */
const swDisplay = computed(() => formatStopwatch(swElapsed.value))
const cdDisplay = computed(() => formatStopwatch(cdRemaining.value))

function resetAll() {
  swReset()
  cdReset()
}

onBeforeUnmount(() => {
  if (swTimer !== null) window.clearInterval(swTimer)
  if (cdTimer !== null) window.clearInterval(cdTimer)
})

const presets = [1, 3, 5, 10, 25]

function applyPreset(minutes: number) {
  cdPause()
  cdMinutes.value = minutes
  cdSeconds.value = 0
  cdTotal.value = minutes * 60 * 1000
  cdRemaining.value = cdTotal.value
  cdFinished.value = false
}

function onMinutesInput(value: string) {
  cdMinutes.value = Number(value) || 0
}

function onSecondsInput(value: string) {
  cdSeconds.value = Number(value) || 0
}
</script>

<template>
  <div class="glass-card flex flex-col p-5 sm:p-6">
    <div class="mb-5 flex items-center gap-2.5">
      <div class="flex size-10 items-center justify-center rounded-xl bg-violet-500/15 text-violet-400">
        <Timer class="size-5" />
      </div>
      <div class="flex-1">
        <h3 class="text-[15px] font-semibold text-text-primary">计时工具</h3>
        <p class="text-xs text-muted-foreground">秒表与倒计时</p>
      </div>
      <Badge :variant="tab === 'stopwatch' ? 'default' : 'secondary'">
        {{ tab === 'stopwatch' ? '秒表' : '倒计时' }}
      </Badge>
    </div>

    <!-- 切换 -->
    <div class="mb-5 grid grid-cols-2 gap-1 rounded-xl border border-white/5 bg-card/40 p-1">
      <button
        class="rounded-lg py-2 text-sm font-medium transition-colors"
        :class="tab === 'stopwatch' ? 'bg-cyan-500/15 text-cyan-300' : 'text-muted-foreground hover:text-text-primary'"
        @click="tab = 'stopwatch'"
      >
        秒表
      </button>
      <button
        class="rounded-lg py-2 text-sm font-medium transition-colors"
        :class="tab === 'countdown' ? 'bg-cyan-500/15 text-cyan-300' : 'text-muted-foreground hover:text-text-primary'"
        @click="tab = 'countdown'"
      >
        倒计时
      </button>
    </div>

    <!-- 秒表 -->
    <div v-if="tab === 'stopwatch'" class="flex flex-1 flex-col">
      <div class="flex items-center justify-center py-2">
        <span class="font-mono text-4xl font-semibold tabular-nums text-text-primary sm:text-5xl">
          {{ swDisplay }}
        </span>
      </div>

      <div class="mt-5 flex items-center justify-center gap-2">
        <Button v-if="!swRunning" variant="gradient" size="sm" @click="swStart">
          <Play class="size-4" />
          开始
        </Button>
        <Button v-else variant="secondary" size="sm" @click="swPause">
          <Pause class="size-4" />
          暂停
        </Button>
        <Button variant="outline" size="sm" :disabled="swElapsed === 0" @click="swLap">
          <Flag class="size-4" />
          分段
        </Button>
        <Button variant="ghost" size="sm" :disabled="swElapsed === 0" @click="swReset">
          <RotateCcw class="size-4" />
          归零
        </Button>
      </div>

      <ul v-if="swLaps.length" class="mt-4 space-y-1.5">
        <li
          v-for="(lap, index) in swLaps"
          :key="`${lap}-${index}`"
          class="flex items-center justify-between rounded-lg border border-white/5 bg-card/40 px-3.5 py-2 text-xs"
        >
          <span class="text-muted-foreground">分段 {{ swLaps.length - index }}</span>
          <span class="font-mono tabular-nums text-text-secondary">{{ formatStopwatch(lap) }}</span>
        </li>
      </ul>
    </div>

    <!-- 倒计时 -->
    <div v-else class="flex flex-1 flex-col">
      <div class="flex items-center justify-center py-2">
        <span
          class="font-mono text-4xl font-semibold tabular-nums transition-colors sm:text-5xl"
          :class="cdFinished ? 'animate-pulse text-status-offline' : 'text-text-primary'"
        >
          {{ cdDisplay }}
        </span>
      </div>

      <!-- 进度条 -->
      <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-muted/70">
        <div
          class="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500 transition-all duration-200"
          :style="{ width: `${cdProgress * 100}%` }"
        />
      </div>

      <p v-if="cdFinished" class="mt-3 text-center text-xs font-medium text-status-offline">
        时间到！
      </p>

      <div class="mt-4 flex items-center justify-center gap-2">
        <Input
          :model-value="String(cdMinutes)"
          type="number"
          class="w-20 text-center"
          :disabled="cdRunning"
          @update:model-value="onMinutesInput"
        />
        <span class="text-xs text-muted-foreground">分</span>
        <Input
          :model-value="String(cdSeconds)"
          type="number"
          class="w-20 text-center"
          :disabled="cdRunning"
          @update:model-value="onSecondsInput"
        />
        <span class="text-xs text-muted-foreground">秒</span>
      </div>

      <div class="mt-3 flex flex-wrap items-center justify-center gap-1.5">
        <button
          v-for="preset in presets"
          :key="preset"
          class="rounded-lg border border-white/5 bg-card/40 px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-cyan-400/30 hover:text-cyan-300"
          @click="applyPreset(preset)"
        >
          {{ preset }} 分
        </button>
      </div>

      <div class="mt-5 flex items-center justify-center gap-2">
        <Button v-if="!cdRunning" variant="gradient" size="sm" :disabled="cdRemaining <= 0" @click="cdStart">
          <Play class="size-4" />
          开始
        </Button>
        <Button v-else variant="secondary" size="sm" @click="cdPause">
          <Pause class="size-4" />
          暂停
        </Button>
        <Button variant="ghost" size="sm" @click="cdReset">
          <TimerReset class="size-4" />
          重置
        </Button>
        <Button variant="ghost" size="sm" @click="resetAll">
          <RotateCcw class="size-4" />
          全部归零
        </Button>
      </div>
    </div>
  </div>
</template>
