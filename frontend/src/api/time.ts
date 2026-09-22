import { apiClient } from './client'

/* ============================================
   时间模块 API —— 与后端 /api/time 对应
   ============================================ */

export interface ServerTime {
  /** Unix 毫秒时间戳（服务器当前时间） */
  timestamp_ms: number
  /** 服务器 UTC 时间的 ISO 字符串 */
  iso_utc: string
  /** 后端进程启动时刻（UTC ISO） */
  started_at: string
  /** 家庭配置的时区（IANA 名称，如 Asia/Shanghai） */
  timezone: string
  /** 后端进程已运行秒数 */
  uptime_seconds: number
}

/** GET /api/time — 服务器时间与运行时长（只读） */
export async function fetchServerTime(): Promise<ServerTime> {
  const { data } = await apiClient.get<ServerTime>('/time')
  return data
}
