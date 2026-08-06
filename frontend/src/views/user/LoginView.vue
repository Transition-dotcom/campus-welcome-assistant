<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2>登录</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" @keyup.enter="doLogin" />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="doLogin" style="width:100%">登录</el-button>
      </el-form>
      <p class="auth-link">还没有账号？<router-link to="/register">立即注册</router-link></p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ nickname: '', password: '' })
const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
}

async function doLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const data = await userApi.login({ nickname: form.nickname, password: form.password })
    authStore.setAuth(data)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch { /* 错误已在拦截器处理 */ }
  finally { loading.value = false }
}
</script>

<style scoped>
.auth-page { display: flex; justify-content: center; align-items: center; min-height: 70vh; }
.auth-card { width: 100%; max-width: 400px; }
.auth-card h2 { text-align: center; margin-bottom: 20px; color: #2c3e50; }
.auth-link { text-align: center; margin-top: 16px; font-size: 14px; color: #909399; }
</style>
