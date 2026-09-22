<script setup lang="ts">
import { computed } from 'vue'
import { useClock } from '@/composables/useClock'
import { useClockPrefs } from '@/composables/useClockPrefs'
import { getFace } from './registry'
import type { ClockFaceSize } from '@/lib/clock'

const props = withDefaults(
  defineProps<{
    size?: ClockFaceSize
    /** 指定面孔（不传则使用用户偏好） */
    face?: string
    /** 指定面孔是否忽略小尺寸限制（顶栏/首页卡片用） */
    ignoreCompact?: boolean
  }>(),
  { size: 'md', face: '', ignoreCompact: false },
)

const { time } = useClock()
const { prefs } = useClockPrefs()

const activeFace = computed(() => {
  const preferred = props.face || prefs.face

  // 小尺寸下若面孔不支持紧凑展示，自动回退到数字钟
  if (!props.ignoreCompact && props.size === 'sm' && !getFace(preferred).compact) {
    return getFace('digital')
  }

  return getFace(preferred)
})
</script>

<template>
  <div class="flex items-center justify-center">
    <component
      :is="activeFace.component"
      :time="time"
      :size="size"
      :show-seconds="prefs.showSeconds"
      :hour12="prefs.hour12"
    />
  </div>
</template>
