import { reactive, readonly } from 'vue'

/* ============================================
   时钟偏好（localStorage 存储）
   - 存储层通过适配器抽象，未来可无痛替换为后端存储
   - 默认值：数字钟 / 24 小时制 / 显示秒 / 显示运行时长
   ============================================ */

export const CLOCK_FACE_IDS = ['digital', 'flip', 'analog'] as const

export type ClockFaceId = (typeof CLOCK_FACE_IDS)[number]

export interface ClockPrefs {
  /** 选中的时钟面孔 */
  face: ClockFaceId
  /** 12 小时制 */
  hour12: boolean
  /** 显示秒 */
  showSeconds: boolean
  /** 首页时钟卡显示服务运行时长 */
  showUptime: boolean
  /** 世界时钟城市（IANA 时区名） */
  cities: string[]
  /** 详情页显示的世界时钟城市数量上限（0 = 全部） */
  maxWorldClocks: number
}

export const DEFAULT_CLOCK_PREFS: ClockPrefs = {
  face: 'digital',
  hour12: false,
  showSeconds: true,
  showUptime: true,
  cities: ['Asia/Shanghai', 'Asia/Tokyo', 'Europe/London', 'America/New_York'],
  maxWorldClocks: 0,
}

const STORAGE_KEY = 'homehub:clock-prefs'

/** 存储适配器接口（替换后端存储时只需实现这两个方法） */
export interface ClockPrefsStorage {
  load(): Partial<ClockPrefs> | null
  save(prefs: ClockPrefs): void
}

const localStorageAdapter: ClockPrefsStorage = {
  load() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY)
      return raw ? (JSON.parse(raw) as Partial<ClockPrefs>) : null
    } catch {
      return null
    }
  },
  save(prefs) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
    } catch {
      /* 存储不可用时静默降级为内存态 */
    }
  },
}

let storage: ClockPrefsStorage = localStorageAdapter

/** 替换存储实现（升级到后端存储时调用） */
export function setClockPrefsStorage(adapter: ClockPrefsStorage) {
  storage = adapter
}

function sanitize(input: Partial<ClockPrefs> | null): ClockPrefs {
  if (!input) return { ...DEFAULT_CLOCK_PREFS }

  const face = CLOCK_FACE_IDS.includes(input.face as ClockFaceId)
    ? (input.face as ClockFaceId)
    : DEFAULT_CLOCK_PREFS.face

  const cities = Array.isArray(input.cities)
    ? input.cities.filter((city): city is string => typeof city === 'string' && city.length > 0)
    : DEFAULT_CLOCK_PREFS.cities

  return {
    face,
    hour12: typeof input.hour12 === 'boolean' ? input.hour12 : DEFAULT_CLOCK_PREFS.hour12,
    showSeconds:
      typeof input.showSeconds === 'boolean'
        ? input.showSeconds
        : DEFAULT_CLOCK_PREFS.showSeconds,
    showUptime:
      typeof input.showUptime === 'boolean'
        ? input.showUptime
        : DEFAULT_CLOCK_PREFS.showUptime,
    cities: cities.length ? cities : DEFAULT_CLOCK_PREFS.cities,
    maxWorldClocks:
      typeof input.maxWorldClocks === 'number' && input.maxWorldClocks >= 0
        ? input.maxWorldClocks
        : DEFAULT_CLOCK_PREFS.maxWorldClocks,
  }
}

const state = reactive<ClockPrefs>(sanitize(storage.load()))

function persist() {
  storage.save({ ...state })
}

function update<K extends keyof ClockPrefs>(key: K, value: ClockPrefs[K]) {
  state[key] = value
  persist()
}

function setFace(face: ClockFaceId) {
  update('face', face)
}

function addCity(timezone: string) {
  if (!timezone || state.cities.includes(timezone)) return
  update('cities', [...state.cities, timezone])
}

function removeCity(timezone: string) {
  if (state.cities.length <= 1) return
  update(
    'cities',
    state.cities.filter((city) => city !== timezone),
  )
}

function moveCity(timezone: string, delta: number) {
  const index = state.cities.indexOf(timezone)
  const next = index + delta
  if (index < 0 || next < 0 || next >= state.cities.length) return

  const cities = [...state.cities]
  const [moved] = cities.splice(index, 1)

  if (moved) cities.splice(next, 0, moved)

  update('cities', cities)
}

function reset() {
  Object.assign(state, DEFAULT_CLOCK_PREFS)
  persist()
}

export function useClockPrefs() {
  return {
    prefs: readonly(state),
    update,
    setFace,
    addCity,
    removeCity,
    moveCity,
    reset,
  }
}
