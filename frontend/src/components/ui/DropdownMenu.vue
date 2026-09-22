<script setup lang="ts">
import {
  DropdownMenuContent,
  DropdownMenuPortal,
  DropdownMenuRoot,
} from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    align?: 'start' | 'center' | 'end'
    sideOffset?: number
    contentClass?: string
  }>(),
  { align: 'end', sideOffset: 8, contentClass: '' },
)
</script>

<template>
  <DropdownMenuRoot v-bind="$attrs">
    <slot name="trigger" />
    <DropdownMenuPortal>
      <DropdownMenuContent
        :align="align"
        :side-offset="sideOffset"
        :class="
          cn(
            'z-50 min-w-48 overflow-hidden rounded-xl border border-border bg-popover/95 p-1.5 text-popover-foreground shadow-2xl shadow-black/50 backdrop-blur-xl',
            props.contentClass,
          )
        "
      >
        <slot />
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
