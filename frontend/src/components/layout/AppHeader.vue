<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  CheckCircle2,
  ChevronRight,
  LogOut,
  Menu,
  Search,
  Settings,
  User,
  Wifi,
  Zap,
} from 'lucide-vue-next'
import {
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'radix-vue'
import { ALL_NAV_ITEMS } from '@/config/nav'
import { useUi } from '@/composables/useUi'
import { useWeather } from '@/composables/useWeather'
import { weatherIcon, weatherInfo, formatTemperature } from '@/lib/weather'
import Input from '@/components/ui/Input.vue'
import Avatar from '@/components/ui/Avatar.vue'
import DropdownMenu from '@/components/ui/DropdownMenu.vue'
import HeaderClock from './HeaderClock.vue'

const route = useRoute()
const router = useRouter()
const ui = useUi()
const weather = useWeather()

const breadcrumb = computed(() => (route.meta.breadcrumb as string | undefined) ?? '总览')
const pageTitle = computed(() => (route.meta.title as string | undefined) ?? 'Home Hub')

/** 顶栏天气快捷卡片 */
const weatherChip = computed(() => {
  const data = weather.state.data
  if (!data) return null
  const info = weatherInfo(data.current.weather_code)
  return {
    icon: weatherIcon(data.current.weather_code, data.current.is_day),
    glow: info.glow,
    temp: formatTemperature(data.current.temperature),
    label: `${data.location.home_name} · ${info.label}`,
  }
})

/** 搜索回车 → 跳转第一个命中模块 */
function onSearchEnter() {
  const q = ui.state.searchQuery.trim().toLowerCase()
  if (!q) return
  const hit = ALL_NAV_ITEMS.find(
    (item) =>
      item.label.toLowerCase().includes(q) ||
      item.keywords.some((k) => k.toLowerCase().includes(q)),
  )
  if (hit) {
    ui.setSearchQuery('')
    ui.closeSidebar()
    router.push(hit.to)
  }
}

const NOTIFICATIONS = [
  {
    id: 1,
    icon: Zap,
    tint: 'bg-status-warning/15 text-status-warning',
    title: '设备能耗提醒',
    desc: '空调今日用电较昨日上升 12%',
    time: '10 分钟前',
  },
  {
    id: 2,
    icon: Wifi,
    tint: 'bg-cyan-500/15 text-cyan-400',
    title: '网络波动',
    desc: '路由器检测到 5GHz 频段信号波动',
    time: '1 小时前',
  },
  {
    id: 3,
    icon: CheckCircle2,
    tint: 'bg-status-online/15 text-status-online',
    title: '系统更新完成',
    desc: 'Home Hub 后端已更新至最新版本',
    time: '昨天',
  },
]

const itemClass =
  'flex cursor-pointer select-none items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-foreground/90 outline-none transition-colors hover:bg-accent data-[highlighted]:bg-accent [&_svg]:size-4 [&_svg]:shrink-0 [&_svg]:text-muted-foreground'
</script>

<template>
  <header
    class="sticky top-0 z-30 border-b border-white/5 bg-hub-bg-deep/75 backdrop-blur-xl"
  >
    <div
      class="mx-auto flex h-16 w-full max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8"
    >
      <!-- 移动端菜单按钮 -->
      <button
        class="rounded-lg p-2 text-text-secondary transition-colors hover:bg-accent hover:text-text-primary lg:hidden"
        @click="ui.openSidebar()"
        aria-label="打开菜单"
      >
        <Menu class="size-5" />
      </button>

      <!-- 标题 + 面包屑 -->
      <div class="min-w-0 leading-tight">
        <div class="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span class="hidden sm:inline">Home Hub</span>
          <ChevronRight class="hidden size-3 sm:inline" />
          <span class="truncate">{{ breadcrumb }}</span>
        </div>
        <h1 class="truncate text-[17px] font-bold tracking-tight text-text-primary">
          {{ pageTitle }}
        </h1>
      </div>

      <div class="ml-auto flex items-center gap-2 sm:gap-3">
        <!-- 时钟（迷你） -->
        <HeaderClock />

        <!-- 搜索 -->
        <div class="relative hidden md:block">
          <Search
            class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/60"
          />
          <Input
            :model-value="ui.state.searchQuery"
            class="w-52 pl-9 lg:w-64"
            placeholder="搜索功能模块…"
            @update:model-value="ui.setSearchQuery"
            @keydown.enter="onSearchEnter"
          />
        </div>

        <!-- 天气快捷卡片 -->
        <button
          v-if="weatherChip"
          class="hidden items-center gap-2 rounded-full border border-white/8 bg-card/60 py-1.5 pl-2.5 pr-3.5 transition-colors hover:border-cyan-400/30 hover:bg-card sm:flex"
          @click="router.push('/weather')"
          :title="`天气 · ${weatherChip.label}`"
        >
          <component :is="weatherChip.icon" class="size-4" :class="weatherChip.glow" />
          <span class="text-sm font-semibold tabular-nums text-text-primary">
            {{ weatherChip.temp }}
          </span>
        </button>

        <!-- 通知 -->
        <DropdownMenu>
          <template #trigger>
            <DropdownMenuTrigger
              class="relative rounded-lg p-2 text-text-secondary outline-none transition-colors hover:bg-accent hover:text-text-primary data-[state=open]:bg-accent"
              aria-label="通知"
            >
              <Bell class="size-5" />
              <span
                class="absolute right-1.5 top-1.5 size-2 rounded-full bg-status-offline ring-2 ring-hub-bg-deep"
              />
            </DropdownMenuTrigger>
          </template>

          <DropdownMenuLabel class="px-2.5 py-2 text-xs font-semibold text-muted-foreground">
            通知中心
          </DropdownMenuLabel>
          <DropdownMenuSeparator class="my-1 h-px bg-border" />
          <div class="max-h-72 space-y-0.5 overflow-y-auto">
            <DropdownMenuItem
              v-for="n in NOTIFICATIONS"
              :key="n.id"
              as="div"
              class="flex cursor-default items-start gap-3 rounded-lg px-2.5 py-2.5"
            >
              <span
                class="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg"
                :class="n.tint"
              >
                <component :is="n.icon" class="size-4" />
              </span>
              <span class="min-w-0">
                <span class="block text-sm font-medium text-text-primary">{{ n.title }}</span>
                <span class="block truncate text-xs text-muted-foreground">{{ n.desc }}</span>
                <span class="block text-[11px] text-muted-foreground/60">{{ n.time }}</span>
              </span>
            </DropdownMenuItem>
          </div>
          <DropdownMenuSeparator class="my-1 h-px bg-border" />
          <DropdownMenuItem as="button" class="justify-center text-xs text-muted-foreground">
            查看全部通知 · 开发中
          </DropdownMenuItem>
        </DropdownMenu>

        <!-- 用户菜单 -->
        <DropdownMenu>
          <template #trigger>
            <DropdownMenuTrigger
              class="outline-none transition-transform hover:scale-105 data-[state=open]:scale-105"
              aria-label="用户菜单"
            >
              <Avatar fallback="家" class="size-9 cursor-pointer" />
            </DropdownMenuTrigger>
          </template>

          <DropdownMenuLabel class="px-2.5 py-2">
            <span class="block text-sm font-semibold text-text-primary">家庭管理员</span>
            <span class="block text-xs text-muted-foreground">本地用户 · 管理员</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator class="my-1 h-px bg-border" />
          <DropdownMenuItem as="button" :class="itemClass" @select="router.push('/profile')">
            <User />
            个人中心
          </DropdownMenuItem>
          <DropdownMenuItem as="button" :class="itemClass" @select="router.push('/settings')">
            <Settings />
            设置
          </DropdownMenuItem>
          <DropdownMenuSeparator class="my-1 h-px bg-border" />
          <DropdownMenuItem as="button" :class="itemClass" class="text-status-offline">
            <LogOut class="!text-status-offline" />
            退出登录
          </DropdownMenuItem>
        </DropdownMenu>
      </div>
    </div>
  </header>
</template>
