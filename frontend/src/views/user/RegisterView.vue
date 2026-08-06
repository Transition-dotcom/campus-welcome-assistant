<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2>注册</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="2-50个字符" />
        </el-form-item>
        <el-form-item label="学号（可选）" prop="studentId">
          <el-input v-model="form.studentId" placeholder="选填" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPwd">
          <el-input v-model="form.confirmPwd" type="password" show-password placeholder="再次输入密码" />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="doRegister" style="width:100%">注册</el-button>
      </el-form>
      <p class="auth-link">已有账号？<router-link to="/login">立即登录</router-link></p>
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
const form = reactive({ nickname: '', studentId: '', password: '', confirmPwd: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  nickname: [{ required: true, min: 2, max: 50, message: '昵称2-50个字符', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirmPwd: [{ required: true, validator: validateConfirm, trigger: 'blur' }],
}

async function doRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const data = await userApi.register({
      nickname: form.nickname,
      password: form.password,
      student_id: form.studentId || null,
    })
    authStore.setAuth(data)
    ElMessage.success('注册成功')
    router.push('/home')
  } catch { /* 拦截器处理 */ }
  finally { loading.value = false }
}
</script>

<style scoped>
.auth-page { display: flex; justify-content: center; align-items: center; min-height: 70vh; }
.auth-card { width: 100%; max-width: 400px; }
.auth-card h2 { text-align: center; margin-bottom: 20px; color: #2c3e50; }
.auth-link { text-align: center; margin-top: 16px; font-size: 14px; color: #909399; }
</style>
