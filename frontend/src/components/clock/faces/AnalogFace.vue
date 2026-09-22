<script setup lang="ts">
import { computed } from 'vue'
import type { ClockFaceProps } from '@/lib/clock'

const props = defineProps<ClockFaceProps>()

const CENTER = 100

const sizeClass = computed(
  () =>
    ({
      sm: 'h-28 w-28',
      md: 'h-40 w-40',
      lg: 'h-64 w-64',
    })[props.size],
)

/** 60 条刻度（每 5 条为整点长刻度） */
const ticks = computed(() =>
  Array.from({ length: 60 }, (_, i) => {
    const major = i % 5 === 0
    const angle = (i * 6 * Math.PI) / 180
    const outer = 94
    const inner = major ? 82 : 88
    return {
      key: i,
      major,
      x1: CENTER + Math.sin(angle) * inner,
      y1: CENTER - Math.cos(angle) * inner,
      x2: CENTER + Math.sin(angle) * outer,
      y2: CENTER - Math.cos(angle) * outer,
    }
  }),
)

/** 指针角度（秒针带毫秒，实现平滑扫动） */
const hourAngle = computed(() => {
  const { hours24, minutes, seconds } = props.time
  return ((hours24 % 12) + minutes / 60 + seconds / 3600) * 30
})

const minuteAngle = computed(() => {
  const { minutes, seconds } = props.time
  return (minutes + seconds / 60) * 6
})

const secondAngle = computed(() => {
  const { seconds, ms } = props.time
  return (seconds + ms / 1000) * 6
})

const hourMarks = computed(() =>
  Array.from({ length: 12 }, (_, i) => {
    const angle = (i * 30 * Math.PI) / 180
    return {
      key: i,
      label: i === 0 ? 12 : i,
      x: CENTER + Math.sin(angle) * 68,
      y: CENTER - Math.cos(angle) * 68,
    }
  }),
)
</script>

<template>
  <svg :class="sizeClass" viewBox="0 0 200 200" role="img" aria-label="模拟时钟">
    <defs>
      <radialGradient id="dial-surface" cx="50%" cy="35%" r="75%">
        <stop offset="0%" stop-color="rgba(255,255,255,0.07)" />
        <stop offset="70%" stop-color="rgba(255,255,255,0.02)" />
        <stop offset="100%" stop-color="rgba(0,0,0,0.35)" />
      </radialGradient>
    </defs>

    <!-- 表盘 -->
    <circle cx="100" cy="100" r="96" fill="url(#dial-surface)" stroke="rgba(255,255,255,0.10)" stroke-width="1.5" />
    <circle cx="100" cy="100" r="86" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1" />

    <!-- 刻度 -->
    <line
      v-for="tick in ticks"
      :key="tick.key"
      :x1="tick.x1"
      :y1="tick.y1"
      :x2="tick.x2"
      :y2="tick.y2"
      :stroke="tick.major ? 'rgba(226,232,240,0.55)' : 'rgba(148,163,184,0.28)'"
      :stroke-width="tick.major ? 2.4 : 1"
      stroke-linecap="round"
    />

    <!-- 数字刻度 -->
    <text
      v-for="mark in hourMarks"
      :key="`mark-${mark.key}`"
      :x="mark.x"
      :y="mark.y + 4"
      text-anchor="middle"
      font-size="11"
      fill="rgba(148,163,184,0.75)"
    >
      {{ mark.label }}
    </text>

    <!-- 指针 -->
    <line
      :transform="`rotate(${hourAngle} 100 100)`"
      x1="100"
      y1="112"
      x2="100"
      y2="56"
      stroke="#e2e8f0"
      stroke-width="5.5"
      stroke-linecap="round"
    />
    <line
      :transform="`rotate(${minuteAngle} 100 100)`"
      x1="100"
      y1="118"
      x2="100"
      y2="34"
      stroke="#cbd5e1"
      stroke-width="3.6"
      stroke-linecap="round"
    />
    <line
      :transform="`rotate(${secondAngle} 100 100)`"
      x1="100"
      y1="126"
      x2="100"
      y2="26"
      stroke="#22d3ee"
      stroke-width="1.8"
      stroke-linecap="round"
      style="filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.85))"
    />

    <!-- 中心轴 -->
    <circle cx="100" cy="100" r="6.5" fill="#0a0c10" stroke="rgba(255,255,255,0.25)" stroke-width="1.5" />
    <circle cx="100" cy="100" r="2.2" fill="#22d3ee" />
  </svg>
</template>
