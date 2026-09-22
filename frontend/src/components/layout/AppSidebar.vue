<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRight, Home, Search, UserCircle, X } from 'lucide-vue-next'
import { NAV_GROUPS, type NavItem } from '@/config/nav'
import { useUi } from '@/composables/useUi'
import { cn } from '@/lib/utils'
import Avatar from '@/components/ui/Avatar.vue'

const route = useRoute()
const router = useRouter()
const ui = useUi()

const PROFILE_ITEM: NavItem = {
  label: '个人中心',
  to: '/profile',
  icon: UserCircle,
  keywords: ['profile', '用户', '账号'],
}

const query = computed(() => ui.state.searchQuery.trim().toLowerCase())

const filteredGroups = computed(() => {
  if (!query.value) return NAV_GROUPS
  return NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter(
      (item) =>
        item.label.toLowerCase().includes(query.value) ||
        item.keywords.some((k) => k.toLowerCase().includes(query.value)),
    ),
  })).filter((group) => group.items.length > 0)
})

const hasMatch = computed(() => filteredGroups.value.length > 0)

function isActive(to: string) {
  return route.path === to
}

function go(item: NavItem) {
  ui.closeSidebar()
  ui.setSearchQuery('')
  router.push(item.to)
}
</script>

<template>
  <Teleport to="body">
    <!-- 移动端遮罩 -->
    <Transition
      enter-active-class="transition-opacity duration-300"
      leave-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="ui.state.sidebarOpen"
        class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        @click="ui.closeSidebar()"
      />
    </Transition>

    <aside
      :class="
        cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/5 bg-hub-bg-elevated/90 backdrop-blur-2xl transition-transform duration-300 ease-out lg:translate-x-0',
          ui.state.sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )
      "
    >
      <!-- Logo -->
      <div class="flex items-center gap-3 px-5 pb-5 pt-6">
        <div
          class="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-violet-500 shadow-lg shadow-cyan-500/30"
        >
          <Home class="size-5 text-white" />
        </div>
        <div class="leading-tight">
          <div class="text-[15px] font-bold tracking-wide text-text-primary">
            Home<span class="text-gradient">Hub</span>
          </div>
          <div class="text-[11px] text-muted-foreground">家庭设备控制中心</div>
        </div>
        <button
          class="ml-auto rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground lg:hidden"
          @click="ui.closeSidebar()"
          aria-label="关闭菜单"
        >
          <X class="size-4" />
        </button>
      </div>

      <!-- 用户卡片 -->
      <button
        class="group mx-3 mb-4 flex items-center gap-3 rounded-xl border border-white/5 bg-card/60 p-3 text-left transition-colors hover:border-cyan-400/30 hover:bg-card"
        @click="go(PROFILE_ITEM)"
      >
        <Avatar fallback="家" class="size-9" />
        <div class="min-w-0 flex-1 leading-tight">
          <div class="truncate text-sm font-semibold text-text-primary">家庭管理员</div>
          <div class="truncate text-[11px] text-muted-foreground">本地用户 · 管理员</div>
        </div>
        <ChevronRight class="size-3.5 text-muted-foreground/60 transition-transform group-hover:translate-x-0.5" />
      </button>

      <!-- 导航 -->
      <nav class="flex-1 space-y-5 overflow-y-auto px-3 pb-4">
        <div
          v-for="group in filteredGroups"
          :key="group.label"
          class="space-y-1"
        >
          <div class="px-2.5 pb-1 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
            {{ group.label }}
          </div>
          <button
            v-for="item in group.items"
            :key="item.to"
            class="group flex w-full items-center gap-3 rounded-xl px-2.5 py-2.5 text-sm transition-all duration-200"
            :class="
              isActive(item.to)
                ? 'bg-gradient-to-r from-cyan-500/15 to-violet-500/10 text-cyan-300 shadow-inner ring-1 ring-inset ring-cyan-400/20'
                : 'text-text-secondary hover:bg-hub-bg-hover hover:text-text-primary'
            "
            @click="go(item)"
          >
            <component
              :is="item.icon"
              class="size-[18px] shrink-0 transition-transform duration-200 group-hover:scale-110"
              :class="isActive(item.to) ? 'text-cyan-300' : 'text-muted-foreground'"
            />
            <span class="font-medium">{{ item.label }}</span>
            <span
              v-if="isActive(item.to)"
              class="ml-auto size-1.5 rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(34,211,238,0.9)]"
            />
          </button>
        </div>

        <!-- 搜索无结果 -->
        <div
          v-if="!hasMatch"
          class="flex flex-col items-center gap-2 rounded-xl border border-dashed border-white/10 px-4 py-8 text-center"
        >
          <Search class="size-5 text-muted-foreground/50" />
          <p class="text-sm text-muted-foreground">未找到相关模块</p>
          <button
            class="text-xs text-cyan-400 hover:underline"
            @click="ui.setSearchQuery('')"
          >
            清除搜索
          </button>
        </div>
      </nav>

      <!-- 底部状态 -->
      <div class="border-t border-white/5 px-5 py-4">
        <div class="flex items-center gap-2 text-xs text-muted-foreground">
          <span class="size-2 rounded-full bg-status-online animate-pulse-ring" />
          <span>系统运行正常</span>
          <span class="ml-auto font-mono">v0.1.0</span>
        </div>
      </div>
    </aside>
  </Teleport>
</template>
