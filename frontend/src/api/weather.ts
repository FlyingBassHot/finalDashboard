import { apiClient } from './client'

/* ============================================
   天气模块 API —— 与后端 /api/weather 对应
   ============================================ */

export interface WeatherLocation {
  home_name: string
  country: string | null
  province: string | null
  city: string | null
  district: string | null
  latitude: number
  longitude: number
  timezone: string
}

export interface CurrentWeather {
  temperature: number
  humidity: number
  apparent_temperature: number | null
  wind_speed: number | null
  weather_code: number
  is_day: boolean
  observed_at: string
}

export interface DailyForecast {
  date: string
  weather_code: number
  temperature_max: number
  temperature_min: number
  precipitation_probability: number | null
  precipitation_sum: number | null
  sunrise: string | null
  sunset: string | null
}

export interface WeatherResponse {
  location: WeatherLocation
  current: CurrentWeather
  daily: DailyForecast[]
}

/** GET /api/weather — 获取当前天气 + 7 天预报 */
export async function fetchWeather(): Promise<WeatherResponse> {
  const { data } = await apiClient.get<WeatherResponse>('/weather')
  return data
}

/** POST /api/weather/refresh — 触发后端立即拉取最新天气 */
export async function refreshWeather(): Promise<void> {
  await apiClient.post('/weather/refresh')
}
