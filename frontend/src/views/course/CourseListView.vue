<template>
  <div class="course-page">
    <h3>课程评价</h3>
    <!-- 筛选 -->
    <el-row :gutter="12" class="filters">
      <el-col :xs="12" :sm="6"><el-select v-model="filters.college" placeholder="学院" clearable><el-option v-for="c in colleges" :key="c" :label="c" :value="c" /></el-select></el-col>
      <el-col :xs="12" :sm="6"><el-select v-model="filters.category" placeholder="类别" clearable><el-option v-for="c in categories" :key="c" :label="c" :value="c" /></el-select></el-col>
      <el-col :xs="24" :sm="12" style="margin-top:8px"><el-button type="primary" @click="fetchCourses">筛选</el-button></el-col>
    </el-row>

    <!-- 列表 -->
    <div v-loading="loading">
      <el-card v-for="c in courses" :key="c.id" class="course-card" @click="$router.push(`/courses/${c.id}`)">
        <div class="course-header">
          <h4>{{ c.name }}</h4>
          <el-tag size="small">{{ c.category }}</el-tag>
        </div>
        <div class="course-info">
          <span v-if="c.teacher">👨‍🏫 {{ c.teacher }}</span>
          <span v-if="c.college">🏫 {{ c.college }}</span>
          <span v-if="c.credit">📚 {{ c.credit }} 学分</span>
          <span>💬 {{ c.review_count }} 条评价</span>
        </div>
      </el-card>
      <el-empty v-if="!loading && courses.length === 0" description="暂无课程" />
    </div>

    <el-pagination v-if="total > pageSize" :total="total" :page-size="pageSize" :current-page="page"
      layout="prev, pager, next" @current-change="onPageChange" style="margin-top:16px;justify-content:center" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { courseApi } from '@/api'

const loading = ref(false)
const courses = ref([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const filters = ref({ college: '', category: '' })
const colleges = ['计算机学院', '数学学院', '经济管理学院', '外国语学院', '物理学院', '马克思主义学院']
const categories = ['通识必修', '通识选修', '专业必修', '专业选修']

onMounted(() => fetchCourses())

async function fetchCourses() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (filters.value.college) params.college = filters.value.college
    if (filters.value.category) params.category = filters.value.category
    const data = await courseApi.getList(params)
    courses.value = data.items
    total.value = data.total
  } catch { /* 错误已处理 */ }
  finally { loading.value = false }
}

function onPageChange(p) { page.value = p; fetchCourses() }
</script>

<style scoped>
.course-page { max-width: 800px; margin: 0 auto; }
.course-page h3 { margin-bottom: 16px; color: #2c3e50; }
.filters { margin-bottom: 16px; }
.filters .el-select { width: 100%; }
.course-card { margin-bottom: 12px; cursor: pointer; }
.course-card:hover { border-color: #409eff; }
.course-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.course-header h4 { margin: 0; color: #303133; }
.course-info { display: flex; flex-wrap: wrap; gap: 12px; font-size: 13px; color: #909399; }
</style>
