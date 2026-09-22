<script setup lang="ts">
import { computed } from 'vue'
import type { ClockFaceProps } from '@/lib/clock'

const props = defineProps<ClockFaceProps>()

interface FlipCell {
  key: string
  kind: 'digit' | 'colon'
  value: string
}

const hourText = computed(() =>
  props.hour12 ? String(props.time.hours12).padStart(2, '0') : props.time.hourText,
)

const cells = computed<FlipCell[]>(() => {
  const list: FlipCell[] = [
    { key: 'h1', kind: 'digit', value: hourText.value[0] ?? '' },
    { key: 'h2', kind: 'digit', value: hourText.value[1] ?? '' },
    { key: 'c1', kind: 'colon', value: ':' },
    { key: 'm1', kind: 'digit', value: props.time.minuteText[0] ?? '' },
    { key: 'm2', kind: 'digit', value: props.time.minuteText[1] ?? '' },
  ]

  if (props.showSeconds) {
    list.push(
      { key: 'c2', kind: 'colon', value: ':' },
      { key: 's1', kind: 'digit', value: props.time.secondText[0] ?? '' },
      { key: 's2', kind: 'digit', value: props.time.secondText[1] ?? '' },
    )
  }

  return list
})

const digitClass = computed(
  () =>
    ({
      sm: 'h-12 w-8 text-2xl rounded-md',
      md: 'h-16 w-11 text-4xl rounded-lg',
      lg: 'h-24 w-16 text-6xl rounded-xl',
    })[props.size],
)

const colonClass = computed(
  () =>
    ({
      sm: 'text-xl',
      md: 'text-2xl',
      lg: 'text-4xl',
    })[props.size],
)
</script>

<template>
  <div class="flex items-center gap-1 sm:gap-1.5">
    <template v-for="cell in cells" :key="cell.key">
      <span
        v-if="cell.kind === 'colon'"
        class="animate-pulse font-bold text-cyan-400/80"
        :class="colonClass"
      >
        {{ cell.value }}
      </span>

      <span
        v-else
        class="flip-card relative inline-flex items-center justify-center border border-white/10 bg-gradient-to-b from-card to-black/50 font-semibold text-text-primary shadow-lg shadow-black/40"
        :class="digitClass"
      >
        <Transition name="flip" mode="out-in">
          <span :key="cell.value" class="flip-digit tabular-nums">{{ cell.value }}</span>
        </Transition>
        <span class="flip-divider" aria-hidden="true" />
      </span>
    </template>
  </div>
</template>

<style scoped>
.flip-card {
  perspective: 320px;
  overflow: hidden;
}

/* 中间的翻页分界线 */
.flip-divider {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: rgba(0, 0, 0, 0.45);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05);
  pointer-events: none;
}

.flip-digit {
  display: block;
  line-height: 1;
}

.flip-enter-active,
.flip-leave-active {
  transition:
    transform 0.32s cubic-bezier(0.22, 0.75, 0.28, 1),
    opacity 0.32s ease;
  transform-origin: center center;
}

.flip-enter-from {
  transform: rotateX(-92deg);
  opacity: 0;
}

.flip-leave-to {
  transform: rotateX(92deg);
  opacity: 0;
}
</style>
