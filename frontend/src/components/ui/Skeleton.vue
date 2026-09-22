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
  <div
    :class="cn('animate-pulse rounded-lg bg-muted/60', props.class)"
    v-bind="$attrs"
  />
</template>
