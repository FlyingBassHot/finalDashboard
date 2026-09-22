import { computed, reactive, readonly } from 'vue'
import { fetchWeather, refreshWeather, type WeatherResponse } from '@/api/weather'
import { ApiError } from '@/api/client'

/**
 * 天气全局状态（模块级单例，无需 pinia）。
 * 侧边栏/顶栏/多页面共享同一份数据，避免重复请求。
 */

const state = reactive({
  data: null as WeatherResponse | null,
  loading: false,
  refreshing: false,
  /**
   * '' 无错误
   * 'unconfigured' 家庭位置未设置（HTTP 409）
   * 'empty' 位置已配置但暂无天气数据（HTTP 404）
   * 'error:xxx' 其他错误（xxx 为错误信息）
   */
  error: '' as string,
})

function classifyError(err: unknown, fallback: string): string {
  if (err instanceof ApiError) {
    if (err.status === 409) return 'unconfigured'
    if (err.status === 404) return 'empty'
    return `error:${err.message}`
  }
  return `error:${err instanceof Error && err.message ? err.message : fallback}`
}

/** 初始加载（仅在尚未加载过时执行） */
async function load(): Promise<void> {
  if (state.loading || state.data || state.error) return
  await reload()
}

/** 强制重新加载 */
async function reload(): Promise<void> {
  state.loading = true
  state.error = ''
  try {
    state.data = await fetchWeather()
  } catch (err) {
    state.error = classifyError(err, '加载失败')
  } finally {
    state.loading = false
  }
}

/** 触发后端刷新（拉取 Open-Meteo 最新数据）并重新加载 */
async function refresh(): Promise<void> {
  if (state.refreshing) return
  state.refreshing = true
  state.error = ''
  try {
    await refreshWeather()
    state.data = await fetchWeather()
  } catch (err) {
    state.error = classifyError(err, '刷新失败')
  } finally {
    state.refreshing = false
  }
}

/** 清空状态（设置保存成功后调用，强制下次重新拉取） */
function invalidate(): void {
  state.data = null
  state.error = ''
}

const temperature = computed(() => state.data?.current.temperature ?? null)

export function useWeather() {
  return {
    state: readonly(state),
    temperature,
    load,
    reload,
    refresh,
    invalidate,
  }
}
