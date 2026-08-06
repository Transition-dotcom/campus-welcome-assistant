/**
 * Axios 封装：统一 baseURL、Token 注入、错误处理、Token 刷新。
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器：自动携带 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 是否正在刷新 Token（避免并发刷新）
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken))
  refreshSubscribers = []
}

// 响应拦截器
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { config, response } = error

    // 401 且非刷新接口 → 尝试刷新 Token
    if (response?.status === 401 && !config.url.includes('/user/refresh')) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // 没有 refresh_token，直接跳登录
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (!isRefreshing) {
        isRefreshing = true

        try {
          const res = await axios.post('/api/user/refresh', { refresh_token: refreshToken })
          const { access_token, refresh_token } = res.data
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          isRefreshing = false
          onTokenRefreshed(access_token)

          // 重试原请求
          config.headers.Authorization = `Bearer ${access_token}`
          return request(config)
        } catch (refreshError) {
          isRefreshing = false
          refreshSubscribers = []
          localStorage.clear()
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // 正在刷新中，排队等待
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            config.headers.Authorization = `Bearer ${newToken}`
            resolve(request(config))
          })
        })
      }
    }

    // 其他错误
    const message = response?.data?.detail || '请求失败，请稍后重试'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
