<template>
  <div class="profile-page">
    <el-card>
      <template #header><span>个人信息</span></template>
      <el-form :model="form" label-width="80px" v-if="!editing">
        <el-form-item label="昵称"><span>{{ form.nickname }}</span></el-form-item>
        <el-form-item label="学号"><span>{{ form.studentId || '未填写' }}</span></el-form-item>
        <el-form-item label="学院"><span>{{ form.college || '未填写' }}</span></el-form-item>
        <el-form-item label="专业"><span>{{ form.major || '未填写' }}</span></el-form-item>
        <el-form-item label="年级"><span>{{ form.grade || '未填写' }}</span></el-form-item>
        <el-button type="primary" @click="editing = true">编辑资料</el-button>
      </el-form>

      <el-form :model="editForm" label-width="80px" v-else>
        <el-form-item label="昵称"><el-input v-model="editForm.nickname" /></el-form-item>
        <el-form-item label="学院"><el-input v-model="editForm.college" placeholder="如：计算机学院" /></el-form-item>
        <el-form-item label="专业"><el-input v-model="editForm.major" placeholder="如：软件工程" /></el-form-item>
        <el-form-item label="年级"><el-input v-model="editForm.grade" placeholder="如：2024" /></el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        <el-button @click="editing = false">取消</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { userApi } from '@/api'

const authStore = useAuthStore()
const editing = ref(false)
const saving = ref(false)
const form = reactive({ nickname: '', studentId: '', college: '', major: '', grade: '' })
const editForm = reactive({ nickname: '', college: '', major: '', grade: '' })

onMounted(async () => {
  try {
    const data = await userApi.getProfile()
    Object.assign(form, { nickname: data.nickname, studentId: data.student_id, college: data.college, major: data.major, grade: data.grade })
    Object.assign(editForm, { nickname: data.nickname, college: data.college, major: data.major, grade: data.grade })
  } catch { /* 错误已处理 */ }
})

async function save() {
  saving.value = true
  try {
    const data = await userApi.updateProfile(editForm)
    Object.assign(form, { nickname: data.nickname, studentId: data.student_id, college: data.college, major: data.major, grade: data.grade })
    authStore.setUser(data)
    ElMessage.success('保存成功')
    editing.value = false
  } catch { /* 错误已处理 */ }
  finally { saving.value = false }
}
</script>

<style scoped>
.profile-page { max-width: 500px; margin: 0 auto; }
</style>
