<template>
  <div>
    <h4>评价审核（举报处理）</h4>
    <el-tabs v-model="activeStatus" @tab-change="onTabChange">
      <el-tab-pane label="待处理" name="pending" />
      <el-tab-pane label="已处理" name="resolved" />
    </el-tabs>

    <el-table :data="reports" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="reporter_nickname" label="举报人" width="120" />
      <el-table-column prop="reason" label="举报原因" min-width="140" show-overflow-tooltip />
      <el-table-column label="被举报评价" min-width="180">
        <template #default="{ row }">
          <div class="review-cell">
            <p class="review-content">{{ row.review?.content || '-' }}</p>
            <p class="review-meta">
              {{ row.review?.is_anonymous ? '匿名' : (row.review?.nickname || '未知') }}
              · 课程：{{ row.review?.course_name || row.review?.course_id || '-' }}
            </p>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="举报时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'pending' ? 'warning' : 'success'">{{ row.status === 'pending' ? '待处理' : '已处理' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button size="small" @click="resolve(row, 'dismiss')">忽略</el-button>
            <el-button size="small" type="danger" @click="resolve(row, 'remove_review')">下架评价</el-button>
          </template>
          <span v-else style="color:#909399">-</span>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && reports.length === 0" description="暂无举报" />

    <el-pagination v-if="total > pageSize" :total="total" :page-size="pageSize" :current-page="page"
      layout="prev, pager, next" @current-change="onPageChange" style="margin-top:16px;justify-content:center" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'

const loading = ref(false)
const reports = ref([])
const activeStatus = ref('pending')
const page = ref(1)
const pageSize = 10
const total = ref(0)

onMounted(() => fetchAll())

async function fetchAll() {
  loading.value = true
  try {
    const data = await adminApi.getReports({ status: activeStatus.value, page: page.value, page_size: pageSize })
    reports.value = data.items || []
    total.value = data.total || 0
  } catch { /* 错误已提示 */ }
  finally { loading.value = false }
}

function onTabChange() {
  page.value = 1
  fetchAll()
}

function onPageChange(p) {
  page.value = p
  fetchAll()
}

async function resolve(row, action) {
  const isDismiss = action === 'dismiss'
  const tip = isDismiss ? '确定忽略该举报？' : '确定下架该评价？下架后用户将不可见。'
  try {
    await ElMessageBox.confirm(tip, '提示', { type: 'warning', confirmButtonText: isDismiss ? '忽略' : '下架' })
  } catch { return /* 用户取消 */ }
  try {
    await adminApi.resolveReport(row.id, action)
    ElMessage.success(isDismiss ? '已忽略该举报' : '评价已下架')
    await fetchAll()
  } catch { /* 错误已提示 */ }
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}
</script>

<style scoped>
.review-cell p { margin: 0; }
.review-content { font-size: 13px; color: #303133; }
.review-meta { font-size: 12px; color: #909399; margin-top: 2px; }
</style>
