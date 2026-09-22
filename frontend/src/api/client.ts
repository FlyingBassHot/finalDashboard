import axios from 'axios'

/**
 * 全局 API 客户端。
 * 开发环境由 Vite 代理将 /api 转发到后端 (127.0.0.1:8000)，
 * 生产环境请将构建产物交由后端托管或配置同源反向代理。
 */
export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

export class ApiError extends Error {
  status: number | null

  constructor(message: string, status: number | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status ?? null
    const detail = error?.response?.data?.detail
    const message =
      detail ??
      (status === null
        ? '无法连接后端服务，请确认服务已启动'
        : `请求失败（HTTP ${status}）`)
    return Promise.reject(new ApiError(message, status))
  },
)
