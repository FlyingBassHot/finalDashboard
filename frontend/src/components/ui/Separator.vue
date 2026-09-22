<script setup lang="ts">
import { Separator } from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    orientation?: 'horizontal' | 'vertical'
    class?: string
  }>(),
  { orientation: 'horizontal', class: '' },
)
</script>

<template>
  <Separator
    :orientation="orientation"
    :class="
      cn(
        'shrink-0 bg-border',
        orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
        props.class,
      )
    "
    v-bind="$attrs"
  />
</template>
