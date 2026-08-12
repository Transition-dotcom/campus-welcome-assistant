<template>
  <div class="search-page">
    <!-- 搜索栏 -->
    <div class="search-box">
      <el-input
        v-model="keyword"
        placeholder="搜索课程、社团、地标、攻略..."
        size="large"
        clearable
        @keyup.enter="handleSearch"
        @clear="clearResults"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
        <template #append>
          <el-button :disabled="!keyword.trim()" @click="handleSearch">搜索</el-button>
        </template>
      </el-input>
      <p v-if="keyword.trim() && keyword.trim().length < 2" class="hint">请输入至少 2 个字符</p>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="result-loading">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 结果列表（按类型分组） -->
    <template v-else-if="results.length">
      <div class="result-summary">
        共找到 <b>{{ results.length }}</b> 条与「{{ keyword.trim() }}」相关的结果
      </div>
      <el-card v-for="group in grouped" :key="group.type" class="group-card" shadow="never">
        <template #header>
          <div class="group-header">
            <el-icon :size="18" :color="group.color"><component :is="group.icon" /></el-icon>
            <span class="group-title">{{ group.label }}</span>
            <span class="group-count">{{ group.items.length }} 条</span>
          </div>
        </template>
        <div v-for="item in group.items" :key="item.id" class="result-item" @click="goTo(item)">
          <el-tag size="small" :type="group.tag">{{ group.label }}</el-tag>
          <span class="result-title">{{ item.title }}</span>
          <el-icon class="result-arrow"><ArrowRight /></el-icon>
        </div>
      </el-card>
    </template>

    <!-- 无结果 / 未搜索 -->
    <el-empty v-else-if="searched" description="未找到相关结果，换个关键词试试" />
    <el-empty v-else description="输入关键词开始搜索" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { guideApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Search, ArrowRight } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const keyword = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)

const typeMeta = {
  course: { label: '课程', tag: '', icon: 'Notebook', color: '#409eff', path: '/courses' },
  club: { label: '社团', tag: 'success', icon: 'Flag', color: '#67c23a', path: '/clubs' },
  poi: { label: '地标', tag: 'warning', icon: 'LocationFilled', color: '#e6a23c', path: '/pois' },
  guide: { label: '攻略', tag: 'info', icon: 'Document', color: '#909399', path: '/guides' },
}

const grouped = computed(() => {
  const groups = []
  for (const [type, meta] of Object.entries(typeMeta)) {
    const items = results.value.filter(r => r.type === type)
    if (items.length) groups.push({ type, ...meta, items })
  }
  return groups
})

// 输入框变化 → 防抖搜索
let searchTimer = null
watch(keyword, (val) => {
  clearTimeout(searchTimer)
  const kw = val.trim()
  if (kw.length < 2) {
    results.value = []
    searched.value = false
    return
  }
  searchTimer = setTimeout(() => {
    runSearch(kw)
    syncUrl(kw)
  }, 400)
})

// URL 中的 keyword 变化（外部跳转进入 / 刷新）时同步到输入框并触发搜索
watch(
  () => route.query.keyword,
  (kw) => {
    const val = kw || ''
    if (keyword.value !== val) keyword.value = val
  },
  { immediate: true }
)

async function runSearch(kw = keyword.value.trim()) {
  if (kw.length < 2) return
  loading.value = true
  try {
    results.value = await guideApi.search(kw)
    searched.value = true
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  clearTimeout(searchTimer)
  const kw = keyword.value.trim()
  if (kw.length < 2) {
    ElMessage.warning('请输入至少 2 个字符')
    return
  }
  runSearch(kw)
  syncUrl(kw)
}

function syncUrl(kw) {
  if (route.query.keyword !== kw) {
    router.replace({ path: '/search', query: { keyword: kw } })
  }
}

function clearResults() {
  clearTimeout(searchTimer)
  results.value = []
  searched.value = false
}

function goTo(item) {
  const meta = typeMeta[item.type]
  if (meta) router.push(`${meta.path}/${item.id}`)
}
</script>

<style scoped>
.search-page { max-width: 800px; margin: 0 auto; }
.search-box { margin-bottom: 16px; }
.hint { font-size: 12px; color: #e6a23c; margin-top: 4px; }
.result-loading { padding: 8px 0; }
.result-summary { color: #606266; font-size: 14px; margin-bottom: 12px; }
.result-summary b { color: #409eff; }
.group-card { margin-bottom: 12px; }
.group-header { display: flex; align-items: center; gap: 8px; }
.group-title { font-weight: bold; color: #303133; }
.group-count { margin-left: auto; font-size: 12px; color: #909399; font-weight: normal; }
.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 4px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}
.result-item:last-child { border-bottom: none; }
.result-item:hover .result-title { color: #409eff; }
.result-title { font-size: 14px; color: #303133; flex: 1; }
.result-arrow { color: #c0c4cc; }
</style>
