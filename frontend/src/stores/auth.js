/**
 * 用户认证状态管理（Pinia）。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref('')
  const refreshTokenVal = ref('')

  const isLoggedIn = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  function setAuth(authData) {
    user.value = authData.user
    accessToken.value = authData.tokens.access_token
    refreshTokenVal.value = authData.tokens.refresh_token

    localStorage.setItem('access_token', accessToken.value)
    localStorage.setItem('refresh_token', refreshTokenVal.value)
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  function setTokens(tokens) {
    accessToken.value = tokens.access_token
    refreshTokenVal.value = tokens.refresh_token
    localStorage.setItem('access_token', accessToken.value)
    localStorage.setItem('refresh_token', refreshTokenVal.value)
  }

  function setUser(userData) {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function restoreFromStorage() {
    const token = localStorage.getItem('access_token')
    const refresh = localStorage.getItem('refresh_token')
    const userStr = localStorage.getItem('user')

    if (token) {
      accessToken.value = token
      refreshTokenVal.value = refresh || ''
      try {
        user.value = userStr ? JSON.parse(userStr) : null
      } catch {
        user.value = null
      }
    }
  }

  function logout() {
    user.value = null
    accessToken.value = ''
    refreshTokenVal.value = ''
    // 只清除认证相关 key，避免误删其他业务数据（如 GPA 缓存 gpa_courses）
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  return {
    user, accessToken, refreshTokenVal,
    isLoggedIn, isAdmin,
    setAuth, setTokens, setUser,
    restoreFromStorage, logout,
  }
})
