<script setup lang="ts">
import type { Component } from 'vue'

defineOptions({ inheritAttrs: false })

withDefaults(
  defineProps<{
    icon: Component
    tint: string
    label: string
    value: string
    sub: string
    /** 可选：底部迷你进度条（0-100） */
    progress?: number
  }>(),
  { progress: undefined },
)
</script>

<template>
  <div
    class="glass-card group relative overflow-hidden p-5"
    v-bind="$attrs"
  >
    <!-- 悬浮光效 -->
    <div
      class="pointer-events-none absolute -right-8 -top-8 size-24 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100"
      :class="tint"
    />
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <div class="text-xs text-muted-foreground">{{ label }}</div>
        <div class="mt-1.5 text-2xl font-bold tabular-nums tracking-tight text-text-primary">
          {{ value }}
        </div>
        <div class="mt-1 truncate text-xs text-muted-foreground/80">{{ sub }}</div>
      </div>
      <div
        class="flex size-11 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
        :class="tint"
      >
        <component :is="icon" class="size-5" />
      </div>
    </div>
    <div
      v-if="progress !== undefined"
      class="mt-3 h-1 overflow-hidden rounded-full bg-muted/70"
    >
      <div
        class="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500 transition-all duration-700"
        :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }"
      />
    </div>
  </div>
</template>
