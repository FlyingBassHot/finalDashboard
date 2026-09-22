import type { Component } from 'vue'
import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudMoon,
  CloudRain,
  CloudSnow,
  CloudSun,
  Moon,
  Sun,
} from 'lucide-vue-next'

export interface WeatherCodeInfo {
  /** 中文天气描述 */
  label: string
  /** 对应的 lucide 图标组件（白天） */
  icon: Component
  /** 对应的 lucide 图标组件（夜间） */
  nightIcon?: Component
  /** Hero 背景渐变（Tailwind 渐变类） */
  gradient: string
  /** 图标光晕颜色 */
  glow: string
  /** 强调色（文字/小图标） */
  accent: string
}

/**
 * WMO Weather Interpretation Codes → 中文描述 + 图标 + 主题色
 * 参考: https://open-meteo.com/en/docs
 */
export const WEATHER_CODES: Record<number, WeatherCodeInfo> = {
  0: {
    label: '晴朗',
    icon: Sun,
    nightIcon: Moon,
    gradient: 'from-amber-500/60 via-orange-500/30 to-transparent',
    glow: 'text-amber-300',
    accent: 'text-amber-300',
  },
  1: {
    label: '基本晴朗',
    icon: CloudSun,
    nightIcon: CloudMoon,
    gradient: 'from-sky-500/50 via-cyan-500/25 to-transparent',
    glow: 'text-sky-300',
    accent: 'text-sky-300',
  },
  2: {
    label: '局部多云',
    icon: CloudSun,
    nightIcon: CloudMoon,
    gradient: 'from-slate-500/50 via-sky-500/20 to-transparent',
    glow: 'text-slate-300',
    accent: 'text-slate-300',
  },
  3: {
    label: '阴天',
    icon: Cloud,
    gradient: 'from-slate-600/60 via-slate-500/25 to-transparent',
    glow: 'text-slate-400',
    accent: 'text-slate-300',
  },
  45: {
    label: '雾',
    icon: CloudFog,
    gradient: 'from-slate-500/50 via-slate-400/20 to-transparent',
    glow: 'text-slate-400',
    accent: 'text-slate-300',
  },
  48: {
    label: '雾凇',
    icon: CloudFog,
    gradient: 'from-slate-500/50 via-slate-400/20 to-transparent',
    glow: 'text-slate-400',
    accent: 'text-slate-300',
  },
  51: {
    label: '小毛毛雨',
    icon: CloudDrizzle,
    gradient: 'from-blue-600/60 via-blue-500/25 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  53: {
    label: '毛毛雨',
    icon: CloudDrizzle,
    gradient: 'from-blue-600/60 via-blue-500/25 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  55: {
    label: '大毛毛雨',
    icon: CloudDrizzle,
    gradient: 'from-blue-700/60 via-blue-500/25 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  56: {
    label: '冻毛毛雨',
    icon: CloudDrizzle,
    gradient: 'from-cyan-700/60 via-cyan-500/25 to-transparent',
    glow: 'text-cyan-300',
    accent: 'text-cyan-300',
  },
  57: {
    label: '强冻毛毛雨',
    icon: CloudDrizzle,
    gradient: 'from-cyan-700/60 via-cyan-500/25 to-transparent',
    glow: 'text-cyan-300',
    accent: 'text-cyan-300',
  },
  61: {
    label: '小雨',
    icon: CloudRain,
    gradient: 'from-blue-700/70 via-blue-600/30 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  63: {
    label: '中雨',
    icon: CloudRain,
    gradient: 'from-blue-800/70 via-blue-600/30 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  65: {
    label: '大雨',
    icon: CloudRain,
    gradient: 'from-indigo-800/70 via-blue-700/30 to-transparent',
    glow: 'text-indigo-300',
    accent: 'text-indigo-300',
  },
  66: {
    label: '冻雨',
    icon: CloudRain,
    gradient: 'from-cyan-800/70 via-cyan-600/30 to-transparent',
    glow: 'text-cyan-300',
    accent: 'text-cyan-300',
  },
  67: {
    label: '强冻雨',
    icon: CloudRain,
    gradient: 'from-cyan-800/70 via-cyan-600/30 to-transparent',
    glow: 'text-cyan-300',
    accent: 'text-cyan-300',
  },
  71: {
    label: '小雪',
    icon: CloudSnow,
    gradient: 'from-cyan-700/60 via-slate-600/30 to-transparent',
    glow: 'text-cyan-200',
    accent: 'text-cyan-200',
  },
  73: {
    label: '中雪',
    icon: CloudSnow,
    gradient: 'from-cyan-800/60 via-slate-700/30 to-transparent',
    glow: 'text-cyan-200',
    accent: 'text-cyan-200',
  },
  75: {
    label: '大雪',
    icon: CloudSnow,
    gradient: 'from-slate-800/70 via-cyan-800/30 to-transparent',
    glow: 'text-slate-200',
    accent: 'text-slate-200',
  },
  77: {
    label: '雪粒',
    icon: CloudSnow,
    gradient: 'from-slate-700/60 via-cyan-700/25 to-transparent',
    glow: 'text-slate-200',
    accent: 'text-slate-200',
  },
  80: {
    label: '小阵雨',
    icon: CloudRain,
    gradient: 'from-blue-700/70 via-blue-600/30 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  81: {
    label: '阵雨',
    icon: CloudRain,
    gradient: 'from-blue-800/70 via-blue-600/30 to-transparent',
    glow: 'text-blue-300',
    accent: 'text-blue-300',
  },
  82: {
    label: '强阵雨',
    icon: CloudRain,
    gradient: 'from-indigo-800/70 via-blue-700/30 to-transparent',
    glow: 'text-indigo-300',
    accent: 'text-indigo-300',
  },
  85: {
    label: '小阵雪',
    icon: CloudSnow,
    gradient: 'from-cyan-700/60 via-slate-600/30 to-transparent',
    glow: 'text-cyan-200',
    accent: 'text-cyan-200',
  },
  86: {
    label: '强阵雪',
    icon: CloudSnow,
    gradient: 'from-slate-800/70 via-cyan-800/30 to-transparent',
    glow: 'text-slate-200',
    accent: 'text-slate-200',
  },
  95: {
    label: '雷暴',
    icon: CloudLightning,
    gradient: 'from-violet-800/70 via-purple-700/30 to-transparent',
    glow: 'text-violet-300',
    accent: 'text-violet-300',
  },
  96: {
    label: '雷暴伴小冰雹',
    icon: CloudLightning,
    gradient: 'from-violet-900/70 via-purple-800/30 to-transparent',
    glow: 'text-violet-300',
    accent: 'text-violet-300',
  },
  99: {
    label: '雷暴伴大冰雹',
    icon: CloudLightning,
    gradient: 'from-violet-900/70 via-purple-800/30 to-transparent',
    glow: 'text-violet-300',
    accent: 'text-violet-300',
  },
}

/** 未知天气代码兜底 */
export const UNKNOWN_WEATHER: WeatherCodeInfo = {
  label: '未知天气',
  icon: Cloud,
  gradient: 'from-slate-600/50 to-transparent',
  glow: 'text-slate-300',
  accent: 'text-slate-300',
}

export function weatherInfo(code: number): WeatherCodeInfo {
  return WEATHER_CODES[code] ?? UNKNOWN_WEATHER
}

/** 根据天气代码 + 昼夜获取图标组件（夜间晴天显示月亮等） */
export function weatherIcon(code: number, isDay = true): Component {
  const info = weatherInfo(code)
  if (!isDay && info.nightIcon) {
    return info.nightIcon
  }
  return info.icon
}

/** 温度格式化：26.4 → "26°" */
export function formatTemperature(value: number): string {
  return `${Math.round(value)}°`
}

/** 观测时间格式化：今天/昨天 + HH:mm */
export function formatObservedAt(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '--'

  const now = new Date()
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const diffDays = Math.round((startOfDay(now) - startOfDay(date)) / 86_400_000)

  const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  if (diffDays === 0) return `今天 ${time}`
  if (diffDays === 1) return `昨天 ${time}`
  return `${date.getMonth() + 1}月${date.getDate()}日 ${time}`
}

/** 日出/日落时间格式化：ISO → "06:02" */
export function formatSunTime(iso: string | null): string {
  if (!iso) return '--'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '--'
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

/** 日期标签：预报首日显示「今天」，其余显示「周三」样式 */
export function forecastDayLabel(dateStr: string, index: number): string {
  if (index === 0) return '今天'
  const date = new Date(`${dateStr}T00:00:00`)
  if (Number.isNaN(date.getTime())) return dateStr
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[date.getDay()] ?? dateStr
}
