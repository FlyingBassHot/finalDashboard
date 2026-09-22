<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    class?: string
  }>(),
  { class: '' },
)
</script>

<template>
  <div :class="cn('glass-card p-6', props.class)" v-bind="$attrs">
    <slot />
  </div>
</template>
