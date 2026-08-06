<template>
  <div class="poi-page">
    <h3>校园导览</h3>
    <el-tabs v-model="activeCategory" @tab-change="fetchPOIs" type="card">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane v-for="c in categories" :key="c" :label="c" :name="c" />
    </el-tabs>
    <el-input v-model="keyword" placeholder="搜索地标..." clearable @clear="fetchPOIs" @keyup.enter="fetchPOIs" style="margin-bottom:12px" />

    <div v-loading="loading" class="poi-grid">
      <el-card v-for="p in pois" :key="p.id" class="poi-card" @click="$router.push(`/pois/${p.id}`)">
        <h4>{{ p.name }}</h4>
        <el-tag size="small" :type="tagType(p.category)">{{ p.category }}</el-tag>
        <p class="poi-desc">{{ p.description?.slice(0, 80) }}{{ p.description?.length > 80 ? '...' : '' }}</p>
        <div class="poi-meta" v-if="p.open_hours">🕐 {{ p.open_hours }}</div>
      </el-card>
      <el-empty v-if="!loading && pois.length === 0" description="暂无地标" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { poiApi } from '@/api'

const loading = ref(false)
const pois = ref([])
const activeCategory = ref('')
const keyword = ref('')
const categories = ['教学楼', '食堂', '宿舍', '快递点', '运动场馆', '行政楼', '其他']

onMounted(() => fetchPOIs())

async function fetchPOIs() {
  loading.value = true
  try {
    const params = { page: 1, page_size: 50 }
    if (activeCategory.value) params.category = activeCategory.value
    if (keyword.value) params.keyword = keyword.value
    const data = await poiApi.getList(params)
    pois.value = data.items
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function tagType(cat) {
  const map = { '教学楼':'', '食堂':'warning', '宿舍':'success', '快递点':'info', '运动场馆':'danger', '行政楼':'' }
  return map[cat] || 'info'
}
</script>

<style scoped>
.poi-page { max-width: 800px; margin: 0 auto; }
.poi-page h3 { margin-bottom: 16px; }
.poi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.poi-card { cursor: pointer; }
.poi-card:hover { border-color: #e6a23c; }
.poi-card h4 { margin: 8px 0 4px; }
.poi-desc { font-size: 13px; color: #606266; margin-top: 6px; }
.poi-meta { font-size: 12px; color: #909399; margin-top: 4px; }
@media (max-width: 768px) {
  .poi-grid { grid-template-columns: 1fr; }
}
</style>
