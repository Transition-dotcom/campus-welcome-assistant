<template>
  <div>
    <h4>纠错处理</h4>
    <el-radio-group v-model="statusFilter" @change="fetchAll" style="margin-bottom:12px">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="pending">待处理</el-radio-button>
      <el-radio-button value="resolved">已处理</el-radio-button>
    </el-radio-group>

    <el-table :data="corrections" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="poi_id" label="地标ID" width="80" />
      <el-table-column prop="user_id" label="用户ID" width="80" />
      <el-table-column prop="content" label="纠错内容" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }"><el-tag :type="row.status === 'pending' ? 'warning' : 'success'">{{ row.status === 'pending' ? '待处理' : '已处理' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="resolve(row.id)">标记已处理</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && corrections.length === 0" description="暂无纠错" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'

const loading = ref(false)
const corrections = ref([])
const statusFilter = ref('')

onMounted(() => fetchAll())
async function fetchAll() {
  loading.value = true
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : {}
    corrections.value = await adminApi.getCorrections(params)
  } catch { /* ignore */ }
  finally { loading.value = false }
}

async function resolve(id) {
  await adminApi.resolveCorrection(id)
  ElMessage.success('已标记为已处理')
  await fetchAll()
}
</script>
