<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Construction, Sparkles } from 'lucide-vue-next'
import { MODULES } from '@/config/modules'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'

const route = useRoute()
const router = useRouter()

const moduleInfo = computed(() => {
  const key = (route.meta.module as string | undefined) ?? ''
  return MODULES[key] ?? MODULES.settings
})

const featureIcons = [Sparkles, Sparkles, Sparkles]
</script>

<template>
  <div class="flex min-h-[70vh] items-center justify-center">
    <div class="w-full max-w-xl">
      <div class="glass-card glow-border relative overflow-hidden p-8 text-center sm:p-12">
        <!-- 装饰光斑 -->
        <div class="pointer-events-none absolute -right-16 -top-16 size-48 rounded-full bg-cyan-500/10 blur-3xl" />
        <div class="pointer-events-none absolute -bottom-16 -left-16 size-48 rounded-full bg-violet-500/10 blur-3xl" />

        <div class="relative">
          <div class="mb-2 flex justify-center">
            <Badge variant="preview">
              <Construction class="size-3" />
              模块建设中
            </Badge>
          </div>

          <!-- 模块图标 -->
          <div
            class="mx-auto mt-5 flex size-20 items-center justify-center rounded-3xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 ring-1 ring-inset ring-white/10"
          >
            <component :is="moduleInfo.icon" class="size-9 text-cyan-300" />
          </div>

          <h2 class="mt-5 text-2xl font-bold tracking-tight text-text-primary">
            {{ moduleInfo.title }}
          </h2>
          <p class="mt-0.5 font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground/60">
            {{ moduleInfo.subtitle }}
          </p>
          <p class="mx-auto mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">
            {{ moduleInfo.description }}
          </p>

          <!-- 规划中的能力 -->
          <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
            <span
              v-for="(feature, i) in moduleInfo.features"
              :key="feature"
              class="inline-flex items-center gap-1.5 rounded-full border border-white/8 bg-card/70 px-3 py-1.5 text-xs text-text-secondary"
            >
              <component :is="featureIcons[i] ?? Sparkles" class="size-3.5 text-cyan-400/80" />
              {{ feature }}
            </span>
          </div>

          <div class="mt-8 flex items-center justify-center gap-3">
            <Button variant="secondary" @click="router.push('/dashboard')">
              <ArrowLeft class="size-4" />
              返回 Dashboard
            </Button>
          </div>

          <p class="mt-6 text-xs text-muted-foreground/60">
            后端接口开发完成后，此页面将自动替换为功能界面
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
