<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    /** 头像文字（图片加载失败或无图片时显示） */
    fallback?: string
    class?: string
  }>(),
  { fallback: '', class: '' },
)
</script>

<template>
  <span
    :class="
      cn(
        'relative inline-flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-cyan-500/80 to-violet-500/80 text-sm font-semibold text-white ring-1 ring-white/15',
        props.class,
      )
    "
    v-bind="$attrs"
  >
    <slot />
    <span v-if="!$slots.default" class="select-none">{{ fallback }}</span>
  </span>
</template>
