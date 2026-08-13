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
        <template #default="{ row }"><el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <el-button v-if="row.role !== 'ADMIN'" size="small" :type="row.status === 1 ? 'danger' : 'success'" @click="toggleStatus(row)">
            {{ row.status === 1 ? '禁用' : '启用' }}
          </el-button>
          <span v-else style="color:#909399">-</span>
        </template>
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

async function toggleStatus(row) {
  const targetStatus = row.status === 1 ? 0 : 1
  const actionText = targetStatus === 0 ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${actionText}用户「${row.nickname}」？`, '提示', { type: 'warning' })
  } catch { return /* 用户取消 */ }
  try {
    await adminApi.updateUserStatus(row.id, targetStatus)
    row.status = targetStatus
    ElMessage.success(`${actionText}成功`)
  } catch { /* 错误已提示 */ }
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}
</script>
