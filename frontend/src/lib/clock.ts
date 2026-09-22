/* ============================================
   时钟工具库
   - 按 IANA 时区渲染时间（不依赖客户端时区）
   - 时长 / UTC 偏移 / 城市名称等格式化
   ============================================ */

export type ClockFaceSize = 'sm' | 'md' | 'lg'

/** 时钟面孔统一接收的数据结构（插件化接口） */
export interface ClockFaceProps {
  time: ClockTime
  size: ClockFaceSize
  showSeconds: boolean
  hour12: boolean
}

export interface ClockTime {
  /** 已校准的绝对时间（用于计算） */
  date: Date

  year: number
  /** 1 - 12 */
  month: number
  day: number
  /** 周一 / 周日 */
  weekday: string
  /** 2026年9月13日 */
  dateText: string
  /** 2026年9月13日 周日 */
  dateFullText: string

  /** 0 - 23 */
  hours24: number
  /** 1 - 12 */
  hours12: number
  minutes: number
  seconds: number
  ms: number
  /** 上午 / 下午 */
  period: string

  hourText: string
  minuteText: string
  secondText: string
  /** HH:mm */
  timeText: string
  /** HH:mm:ss */
  timeWithSeconds: string
}

const timeFormatterCache = new Map<string, Intl.DateTimeFormat>()
const offsetFormatterCache = new Map<string, Intl.DateTimeFormat>()

function timeFormatter(timezone: string): Intl.DateTimeFormat {
  const key = timezone || 'local'

  let formatter = timeFormatterCache.get(key)

  if (!formatter) {
    formatter = new Intl.DateTimeFormat('zh-CN', {
      ...(timezone ? { timeZone: timezone } : {}),
      hourCycle: 'h23',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      weekday: 'short',
    })

    timeFormatterCache.set(key, formatter)
  }

  return formatter
}

/** 按指定时区把绝对时间拆解为可渲染的时间部件 */
export function buildClockTime(date: Date, timezone: string): ClockTime {
  const parts = timeFormatter(timezone).formatToParts(date)

  const pick = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((part) => part.type === type)?.value ?? ''

  const year = Number(pick('year'))
  const month = Number(pick('month'))
  const day = Number(pick('day'))
  const hours24 = Number(pick('hour'))
  const minutes = Number(pick('minute'))
  const seconds = Number(pick('second'))
  const weekday = pick('weekday')

  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12

  const hourText = String(hours24).padStart(2, '0')
  const minuteText = String(minutes).padStart(2, '0')
  const secondText = String(seconds).padStart(2, '0')

  const dateText = `${year}年${month}月${day}日`

  return {
    date,
    year,
    month,
    day,
    weekday,
    dateText,
    dateFullText: `${dateText} ${weekday}`,
    hours24,
    hours12,
    minutes,
    seconds,
    ms: date.getMilliseconds(),
    period: hours24 < 12 ? '上午' : '下午',
    hourText,
    minuteText,
    secondText,
    timeText: `${hourText}:${minuteText}`,
    timeWithSeconds: `${hourText}:${minuteText}:${secondText}`,
  }
}

/** UTC 偏移展示：UTC+8 / UTC+5:30 */
export function utcOffsetText(date: Date, timezone: string): string {
  const key = timezone || 'local'

  let formatter = offsetFormatterCache.get(key)

  if (!formatter) {
    formatter = new Intl.DateTimeFormat('en-US', {
      ...(timezone ? { timeZone: timezone } : {}),
      timeZoneName: 'longOffset',
      hour: '2-digit',
    })

    offsetFormatterCache.set(key, formatter)
  }

  const name =
    formatter
      .formatToParts(date)
      .find((part) => part.type === 'timeZoneName')?.value ?? ''

  const matched = name.match(/GMT([+-])(\d{2}):(\d{2})/)

  if (!matched) return name.replace('GMT', 'UTC')

  const [, sign, hour, minute] = matched

  return Number(minute) === 0
    ? `UTC${sign}${Number(hour)}`
    : `UTC${sign}${Number(hour)}:${minute}`
}

/* ============================================
   时长格式化
   ============================================ */

/** 3725 → "1 小时 2 分" / 有效天数时 "3 天 4 小时 12 分" */
export function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))

  const days = Math.floor(seconds / 86_400)
  const hours = Math.floor((seconds % 86_400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days} 天 ${hours} 小时 ${minutes} 分`
  if (hours > 0) return `${hours} 小时 ${minutes} 分`
  if (minutes > 0) return `${minutes} 分 ${seconds % 60} 秒`
  return `${seconds} 秒`
}

/** 紧凑版：3天4小时 / 4小时12分 */
export function formatDurationShort(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))

  const days = Math.floor(seconds / 86_400)
  const hours = Math.floor((seconds % 86_400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days}天${hours}小时`
  if (hours > 0) return `${hours}小时${minutes}分`
  return `${minutes}分${seconds % 60}秒`
}

/** 秒表样式：1:02:03.4 / 02:03.4 */
export function formatStopwatch(ms: number): string {
  const total = Math.max(0, ms)

  const hours = Math.floor(total / 3_600_000)
  const minutes = Math.floor((total % 3_600_000) / 60_000)
  const seconds = Math.floor((total % 60_000) / 1000)
  const tenths = Math.floor((total % 1000) / 100)

  const mm = String(minutes).padStart(2, '0')
  const ss = String(seconds).padStart(2, '0')

  if (hours > 0) return `${hours}:${mm}:${ss}.${tenths}`
  return `${mm}:${ss}.${tenths}`
}

/** 从 "2026-09-09T06:03:00" 提取当天分钟数（当天 00:00 起） */
export function timeOfDayMinutes(iso: string | null): number | null {
  if (!iso) return null

  const matched = iso.match(/T(\d{2}):(\d{2})/)

  if (!matched) return null

  return Number(matched[1]) * 60 + Number(matched[2])
}

/** 当前时间的当天分钟数（含秒的小数部分） */
export function nowMinutesOfDay(time: ClockTime): number {
  return time.hours24 * 60 + time.minutes + time.seconds / 60
}

/* ============================================
   世界时钟城市
   ============================================ */

export interface CityPreset {
  tz: string
  name: string
}

/** 世界时钟可选城市（新增城市只需在此加一行） */
export const CITY_PRESETS: CityPreset[] = [
  { tz: 'Asia/Shanghai', name: '北京' },
  { tz: 'Asia/Hong_Kong', name: '香港' },
  { tz: 'Asia/Tokyo', name: '东京' },
  { tz: 'Asia/Seoul', name: '首尔' },
  { tz: 'Asia/Singapore', name: '新加坡' },
  { tz: 'Asia/Bangkok', name: '曼谷' },
  { tz: 'Asia/Dubai', name: '迪拜' },
  { tz: 'Europe/Moscow', name: '莫斯科' },
  { tz: 'Europe/Berlin', name: '柏林' },
  { tz: 'Europe/Paris', name: '巴黎' },
  { tz: 'Europe/London', name: '伦敦' },
  { tz: 'America/New_York', name: '纽约' },
  { tz: 'America/Chicago', name: '芝加哥' },
  { tz: 'America/Los_Angeles', name: '洛杉矶' },
  { tz: 'America/Sao_Paulo', name: '圣保罗' },
  { tz: 'Australia/Sydney', name: '悉尼' },
  { tz: 'Pacific/Auckland', name: '奥克兰' },
  { tz: 'UTC', name: 'UTC' },
]

export function cityLabel(tz: string): string {
  const preset = CITY_PRESETS.find((city) => city.tz === tz)

  if (preset) return preset.name

  const tail = tz.split('/').pop() ?? tz

  return tail.replace(/_/g, ' ')
}
