import { apiClient } from './client'

/* ============================================
   设置模块 API —— 与后端 /api/settings 对应
   ============================================ */

export interface LocationOption {
  adcode: string
  name: string
  level: string
  citycode: string | null
  center: string | null
  /** 高德原始坐标（GCJ-02） */
  gcj02_longitude: number | null
  gcj02_latitude: number | null
  /** WGS84 坐标（Open-Meteo 等使用） */
  longitude: number | null
  latitude: number | null
  timezone: string
  /** 下级行政区（subdistrict=1 时返回） */
  children: LocationOption[]
}

export interface HomeSettings {
  id: number
  home_name: string
  country: string | null
  province: string | null
  city: string | null
  district: string | null
  adcode: string | null
  gcj02_latitude: number | null
  gcj02_longitude: number | null
  latitude: number | null
  longitude: number | null
  timezone: string | null
  location_source: string
  is_configured: boolean
  created_at: string
  updated_at: string
}

export interface HomeSettingsUpdate {
  home_name: string
  country: string
  province: string
  city: string
  district: string | null
  adcode: string
  gcj02_latitude: number
  gcj02_longitude: number
  latitude: number
  longitude: number
  timezone: string
  location_source?: string
}

/** GET /api/settings/home — 获取家庭设置（不存在时后端自动创建默认行） */
export async function getHomeSettings(): Promise<HomeSettings> {
  const { data } = await apiClient.get<HomeSettings>('/settings/home')
  return data
}

/** GET /api/settings/locations — 行政区搜索（keywords 支持名称或 adcode） */
export async function searchLocations(
  keywords: string,
  subdistrict = 0,
): Promise<LocationOption[]> {
  const { data } = await apiClient.get<LocationOption[]>('/settings/locations', {
    params: { keywords, subdistrict },
  })
  return data
}

/** PUT /api/settings/home — 更新家庭设置（后端保存成功后会立即刷新天气） */
export async function updateHomeSettings(
  payload: HomeSettingsUpdate,
): Promise<HomeSettings> {
  const { data } = await apiClient.put<HomeSettings>('/settings/home', payload)
  return data
}
