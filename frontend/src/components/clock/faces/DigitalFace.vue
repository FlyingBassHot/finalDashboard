<script setup lang="ts">
import { computed } from 'vue'
import type { ClockFaceProps } from '@/lib/clock'

const props = defineProps<ClockFaceProps>()

const hourText = computed(() =>
  props.hour12 ? String(props.time.hours12).padStart(2, '0') : props.time.hourText,
)

const mainSizeClass = computed(
  () =>
    ({
      sm: 'text-5xl',
      md: 'text-6xl',
      lg: 'text-8xl',
    })[props.size],
)

const secondSizeClass = computed(
  () =>
    ({
      sm: 'text-xl',
      md: 'text-3xl',
      lg: 'text-5xl',
    })[props.size],
)
</script>

<template>
  <div class="flex items-end gap-2 sm:gap-3">
    <div class="flex items-baseline font-semibold tabular-nums tracking-tight">
      <span class="text-text-primary" :class="mainSizeClass">{{ hourText }}</span>
      <span class="text-text-primary/70" :class="mainSizeClass">:</span>
      <span class="text-text-primary" :class="mainSizeClass">{{ time.minuteText }}</span>
    </div>

    <div v-if="showSeconds" class="flex items-baseline gap-1.5 pb-1.5">
      <span
        class="text-cyan-400 drop-shadow-[0_0_12px_rgba(34,211,238,0.55)] tabular-nums"
        :class="secondSizeClass"
      >
        {{ time.secondText }}
      </span>
      <span v-if="hour12" class="text-xs font-medium text-muted-foreground">
        {{ time.period }}
      </span>
    </div>

    <span
      v-else-if="hour12"
      class="pb-2 text-xs font-medium text-muted-foreground"
    >
      {{ time.period }}
    </span>
  </div>
</template>
