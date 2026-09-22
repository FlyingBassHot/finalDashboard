<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="relative min-h-screen">
    <!-- 环境光背景 -->
    <div
      class="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden="true"
    >
      <div
        class="absolute -top-40 left-1/4 size-[500px] rounded-full bg-cyan-500/8 blur-[140px]"
      />
      <div
        class="absolute -right-40 top-1/3 size-[420px] rounded-full bg-violet-500/8 blur-[140px]"
      />
      <div
        class="absolute -bottom-40 left-10 size-[380px] rounded-full bg-sky-500/6 blur-[120px]"
      />
    </div>

    <AppSidebar />

    <div class="flex min-h-screen flex-col lg:pl-64">
      <AppHeader />
      <main class="mx-auto w-full max-w-7xl flex-1 px-4 pb-12 pt-6 sm:px-6 lg:px-8">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
      <footer
        class="mx-auto w-full max-w-7xl px-4 pb-6 text-center text-xs text-muted-foreground/60 sm:px-6 lg:px-8"
      >
        Home Hub · 家庭设备仪表盘 — 数据由本地服务提供，部分模块为预览数据
      </footer>
    </div>
  </div>
</template>
