/**
 * Axios 封装：统一 baseURL、Token 注入、错误处理、Token 刷新。
 */
import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

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

// 仅清除认证相关 key，避免误删其他业务数据（如 GPA 缓存 gpa_courses）
function clearAuthStorage() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

// 提取后端错误消息（FastAPI 422 的 detail 为数组，避免 [object Object]）
function extractErrorMessage(detail) {
  if (Array.isArray(detail)) {
    const first = detail[0]
    return (first && (first.msg || first.message)) || '请求参数有误'
  }
  if (typeof detail === 'string' && detail) return detail
  return '请求失败，请稍后重试'
}

// 跳转登录页（携带 redirect，登录后回跳原页面）
function redirectToLogin() {
  const current = router.currentRoute.value.fullPath
  if (current && current !== '/login') {
    router.push({ path: '/login', query: { redirect: current } })
  } else {
    router.push('/login')
  }
}

// 响应拦截器
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { config, response } = error

    // 401 且非刷新/登录接口 → 尝试刷新 Token
    const url = (config && config.url) || ''
    if (response?.status === 401 && !url.includes('/user/refresh') && !url.includes('/user/login')) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // 没有 refresh_token，直接跳登录
        clearAuthStorage()
        redirectToLogin()
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

          // 同步 Pinia 内存状态，保证 store 与 localStorage 一致
          try {
            useAuthStore().setTokens({ access_token, refresh_token })
          } catch { /* pinia 未初始化时忽略 */ }

          // 重试原请求
          config.headers.Authorization = `Bearer ${access_token}`
          return request(config)
        } catch (refreshError) {
          isRefreshing = false
          // 逐个回调 null，唤醒所有排队请求并让其失败，避免 Promise 永不 settle
          onTokenRefreshed(null)
          clearAuthStorage()
          ElMessage.error('登录已过期，请重新登录')
          redirectToLogin()
          return Promise.reject(refreshError)
        }
      } else {
        // 正在刷新中，排队等待
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken) => {
            if (newToken) {
              config.headers.Authorization = `Bearer ${newToken}`
              resolve(request(config))
            } else {
              // 刷新失败，让排队请求直接失败
              reject(new Error('登录已过期，请重新登录'))
            }
          })
        })
      }
    }

    // 其他错误
    const detail = response?.data?.detail
    const message = detail ? extractErrorMessage(detail) : '请求失败，请稍后重试'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
