<template>
  <div class="club-page">
    <h3>社团导航</h3>
    <el-tabs v-model="activeCategory" @tab-change="fetchClubs" type="card">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane v-for="c in categories" :key="c" :label="c" :name="c" />
    </el-tabs>
    <el-input v-model="keyword" placeholder="搜索社团..." clearable @clear="fetchClubs" @keyup.enter="fetchClubs" style="margin-bottom:12px" />

    <div v-loading="loading">
      <el-card v-for="c in clubs" :key="c.id" class="club-card" @click="$router.push(`/clubs/${c.id}`)">
        <div class="club-header">
          <h4>{{ c.name }}</h4>
          <el-tag size="small">{{ c.category }}</el-tag>
        </div>
        <p class="club-desc">{{ c.description?.slice(0, 100) }}{{ c.description?.length > 100 ? '...' : '' }}</p>
        <div class="club-meta">
          <span v-if="c.activity_frequency">📅 {{ c.activity_frequency }}</span>
          <span v-if="c.contact">📞 {{ c.contact }}</span>
        </div>
      </el-card>
      <el-empty v-if="!loading && clubs.length === 0" description="暂无社团" />
    </div>

    <el-pagination v-if="total > pageSize" :total="total" :page-size="pageSize" :current-page="page"
      layout="prev, pager, next" @current-change="p => { page = p; fetchClubs() }" style="margin-top:16px;justify-content:center" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { clubApi } from '@/api'

const loading = ref(false)
const clubs = ref([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const activeCategory = ref('')
const keyword = ref('')
const categories = ['学术科技', '志愿公益', '文体艺术', '创新创业', '其他']

onMounted(() => fetchClubs())

async function fetchClubs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (activeCategory.value) params.category = activeCategory.value
    if (keyword.value) params.keyword = keyword.value
    const data = await clubApi.getList(params)
    clubs.value = data.items
    total.value = data.total
  } catch { /* ignore */ }
  finally { loading.value = false }
}
</script>

<style scoped>
.club-page { max-width: 800px; margin: 0 auto; }
.club-page h3 { margin-bottom: 16px; }
.club-card { margin-bottom: 10px; cursor: pointer; }
.club-card:hover { border-color: #67c23a; }
.club-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.club-header h4 { margin: 0; }
.club-desc { font-size: 14px; color: #606266; }
.club-meta { display: flex; gap: 16px; font-size: 13px; color: #909399; margin-top: 6px; }
</style>
