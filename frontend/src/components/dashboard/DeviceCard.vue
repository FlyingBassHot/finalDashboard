<script setup lang="ts">
import type { Component } from 'vue'
import {
  AirVent,
  Database,
  Lightbulb,
  Monitor,
  Server,
  Wifi,
} from 'lucide-vue-next'
import type { Device } from '@/data/devices'

defineProps<{
  device: Device
}>()

/** 图标组件映射（数据文件存字符串 key，便于后续直接替换为真实接口数据） */
const iconMap: Record<string, Component> = {
  Database,
  Wifi,
  Server,
  Monitor,
  Lightbulb,
  AirVent,
}
</script>

<template>
  <div class="glass-card group relative overflow-hidden p-5">
    <!-- 顶部氛围线 -->
    <div
      class="pointer-events-none absolute inset-x-0 top-0 h-px opacity-60 transition-opacity group-hover:opacity-100"
      :class="device.status === 'online' ? 'bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent' : 'bg-gradient-to-r from-transparent via-white/15 to-transparent'"
    />
    <div class="flex items-start gap-4">
      <div
        class="flex size-12 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
        :class="device.tint"
      >
        <component :is="iconMap[device.icon] ?? Database" class="size-6" />
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <h3 class="truncate text-[15px] font-semibold text-text-primary">
            {{ device.name }}
          </h3>
          <span
            class="flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium"
            :class="
              device.status === 'online'
                ? 'bg-status-online/12 text-status-online'
                : 'bg-status-offline/12 text-status-offline'
            "
          >
            <span
              class="size-1.5 rounded-full"
              :class="
                device.status === 'online'
                  ? 'bg-status-online animate-pulse-ring'
                  : 'bg-status-offline'
              "
            />
            {{ device.status === 'online' ? '在线' : '离线' }}
          </span>
        </div>
        <div class="mt-0.5 truncate text-xs text-muted-foreground">{{ device.model }}</div>
        <div class="mt-2.5 truncate text-[13px] text-text-secondary/90">
          {{ device.metric }}
        </div>
      </div>
    </div>
  </div>
</template>
