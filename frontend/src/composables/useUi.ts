import { computed, reactive, readonly } from 'vue'
import { ALL_NAV_ITEMS } from '@/config/nav'

/**
 * 全局 UI 状态：侧边栏（移动端抽屉）开关、顶栏搜索关键词。
 */
const state = reactive({
  sidebarOpen: false,
  searchQuery: '',
})

function openSidebar() {
  state.sidebarOpen = true
}

function closeSidebar() {
  state.sidebarOpen = false
}

function setSearchQuery(value: string) {
  state.searchQuery = value
}

/** 搜索是否有命中（供顶栏提示使用） */
const hasSearchMatch = computed(() => {
  const q = state.searchQuery.trim().toLowerCase()
  if (!q) return true
  return ALL_NAV_ITEMS.some(
    (item) =>
      item.label.toLowerCase().includes(q) ||
      item.keywords.some((k) => k.toLowerCase().includes(q)),
  )
})

export function useUi() {
  return {
    state: readonly(state),
    hasSearchMatch,
    openSidebar,
    closeSidebar,
    setSearchQuery,
  }
}
