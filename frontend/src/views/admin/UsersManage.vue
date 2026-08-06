<template>
  <div>
    <h4>用户管理</h4>
    <el-table :data="users" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="nickname" label="昵称" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }"><el-tag :type="row.role === 'ADMIN' ? 'danger' : 'info'">{{ row.role }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }"><el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'

const loading = ref(false)
const users = ref([])

onMounted(async () => {
  loading.value = true
  try { users.value = await adminApi.getUsers() } catch { /* ignore */ }
  finally { loading.value = false }
})

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}
</script>
