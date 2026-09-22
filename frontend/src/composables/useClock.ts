import { computed, reactive, readonly, ref } from 'vue'
import { fetchServerTime } from '@/api/time'
import { buildClockTime, type ClockTime } from '@/lib/clock'

/* ============================================
   全局时钟（模块级单例）
   - 启动时向 /api/time 校准一次，得到本机与服务器的偏差
   - 之后用 Date.now() + offset 本地走时（断网也能走）
   - 所有时间按「家庭时区」渲染，不受客户端时区设置影响
   ============================================ */

const TICK_MS = 100

/** 自动重新校准间隔（10 分钟） */
const RESYNC_MS = 10 * 60 * 1000

const FALLBACK_TIMEZONE = 'Asia/Shanghai'

type SyncState = 'idle' | 'syncing' | 'synced' | 'local'

const state = reactive({
  /** 本机时钟 → 服务器时钟 的偏差（毫秒） */
  offsetMs: 0,
  /** 用于渲染的时区（来自后端家庭配置） */
  timezone: '',
  /** 后端进程启动时刻（毫秒时间戳，0 表示未知） */
  startedAtMs: 0,
  /** 是否成功与服务器校时 */
  serverReachable: false,
  syncState: 'idle' as SyncState,
  syncing: false,
  lastSyncMs: 0,
})

const nowMs = ref(Date.now() + state.offsetMs)

let tickTimer: number | null = null
let resyncTimer: number | null = null
let started = false

function localTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || FALLBACK_TIMEZONE
  } catch {
    return FALLBACK_TIMEZONE
  }
}

/** 立即刷新当前时间（校准后调用，避免等待下一个 tick） */
function refreshNow() {
  nowMs.value = Date.now() + state.offsetMs
}

/** 与后端校时（网络失败时退回本机时间，不阻塞走时） */
async function sync(): Promise<void> {
  if (state.syncing) return

  state.syncing = true
  if (!state.serverReachable) state.syncState = 'syncing'

  try {
    const sentAt = Date.now()
    const server = await fetchServerTime()
    const receivedAt = Date.now()

    // 补偿一半网络往返延迟，减少偏差
    const rtt = receivedAt - sentAt
    state.offsetMs = server.timestamp_ms + Math.round(rtt / 2) - receivedAt

    if (server.timezone) state.timezone = server.timezone
    state.startedAtMs = Date.parse(server.started_at) || 0

    state.serverReachable = true
    state.syncState = 'synced'
    state.lastSyncMs = receivedAt

    refreshNow()
  } catch {
    state.serverReachable = false
    state.syncState = 'local'

    if (!state.timezone) state.timezone = localTimezone()
  } finally {
    state.syncing = false
  }
}

function onVisibilityChange() {
  if (document.visibilityState !== 'visible') return

  // 回到前台时若已超过校准间隔，重新校时
  if (Date.now() - state.lastSyncMs > RESYNC_MS) {
    void sync()
  } else {
    refreshNow()
  }
}

function start() {
  if (started) return
  started = true

  state.timezone = localTimezone()

  tickTimer = window.setInterval(refreshNow, TICK_MS)
  resyncTimer = window.setInterval(() => void sync(), RESYNC_MS)

  document.addEventListener('visibilitychange', onVisibilityChange)

  void sync()
}

/* ---------- 派生数据 ---------- */

const time = computed<ClockTime>(() => buildClockTime(new Date(nowMs.value), state.timezone))

/** 服务运行时长（秒，实时增长） */
const uptimeSeconds = computed(() => {
  if (!state.serverReachable || !state.startedAtMs) return 0
  return Math.max(0, (nowMs.value - state.startedAtMs) / 1000)
})

/** 校时偏差的显示文本 */
const offsetText = computed(() => {
  const offset = state.offsetMs
  if (Math.abs(offset) < 50) return '±0.0s'
  return `${offset > 0 ? '+' : '-'}${(Math.abs(offset) / 1000).toFixed(1)}s`
})

/* ---------- 对外接口 ---------- */

export function useClock() {
  start()

  return {
    state: readonly(state),
    /** 供面孔组件使用的响应式时间对象 */
    nowMs,
    time,
    uptimeSeconds,
    offsetText,
    sync,
    /** 供停止计时器（一般不需要） */
    stop() {
      if (tickTimer !== null) window.clearInterval(tickTimer)
      if (resyncTimer !== null) window.clearInterval(resyncTimer)
      document.removeEventListener('visibilitychange', onVisibilityChange)
      tickTimer = null
      resyncTimer = null
      started = false
    },
  }
}
