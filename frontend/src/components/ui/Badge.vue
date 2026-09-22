<script setup lang="ts">
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap border',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary/15 text-cyan-300',
        secondary: 'border-border bg-secondary text-secondary-foreground',
        online: 'border-transparent bg-status-online/15 text-status-online',
        offline: 'border-transparent bg-status-offline/15 text-status-offline',
        warning: 'border-transparent bg-status-warning/15 text-status-warning',
        outline: 'border-border text-muted-foreground',
        preview: 'border-dashed border-cyan-400/30 bg-cyan-400/5 text-cyan-300/80',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

type BadgeVariants = VariantProps<typeof badgeVariants>

const props = withDefaults(
  defineProps<{
    variant?: BadgeVariants['variant']
    class?: string
  }>(),
  { variant: 'default', class: '' },
)

defineOptions({ inheritAttrs: false })
</script>

<template>
  <span :class="cn(badgeVariants({ variant }), props.class)" v-bind="$attrs">
    <slot />
  </span>
</template>
