<script setup lang="ts">
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 cursor-pointer',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground shadow-lg shadow-cyan-500/20 hover:bg-cyan-400 active:scale-[0.98]',
        secondary:
          'bg-secondary text-secondary-foreground border border-border hover:bg-accent active:scale-[0.98]',
        outline:
          'border border-border bg-transparent text-foreground hover:bg-accent/60 active:scale-[0.98]',
        ghost: 'text-foreground hover:bg-accent/60',
        gradient:
          'bg-gradient-to-r from-cyan-400 to-violet-500 text-white shadow-lg shadow-cyan-500/25 hover:brightness-110 active:scale-[0.98]',
        destructive:
          'bg-status-offline/90 text-white hover:bg-status-offline active:scale-[0.98]',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-11 rounded-xl px-6 text-base',
        icon: 'size-10',
        'icon-sm': 'size-8 rounded-md',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

type ButtonVariants = VariantProps<typeof buttonVariants>

const props = withDefaults(
  defineProps<{
    variant?: ButtonVariants['variant']
    size?: ButtonVariants['size']
    loading?: boolean
  }>(),
  {
    variant: 'default',
    size: 'default',
    loading: false,
  },
)

defineOptions({ inheritAttrs: false })
</script>

<template>
  <button
    :class="cn(buttonVariants({ variant, size }), $attrs.class ?? '')"
    v-bind="{
      type: 'button',
      ...$attrs,
    }"
    :disabled="loading || $attrs.disabled === true"
  >
    <svg
      v-if="loading"
      class="size-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"
      />
    </svg>
    <slot />
  </button>
</template>
