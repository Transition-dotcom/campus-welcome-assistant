<template>
  <div class="home-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索课程、社团、地标、攻略..."
        size="large"
        clearable
        @keyup.enter="doSearch"
        @clear="searchResults = []"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <div v-if="searchResults.length" class="search-dropdown">
        <div v-for="item in searchResults" :key="item.type + item.id" class="search-item"
             @click="goTo(item)">
          <el-tag size="small" :type="tagType(item.type)">{{ typeLabel(item.type) }}</el-tag>
          <span>{{ item.title }}</span>
        </div>
      </div>
    </div>

    <!-- 任务进度卡 -->
    <el-card v-if="authStore.isLoggedIn" class="progress-card" @click="$router.push('/tasks')">
      <div class="progress-header">
        <el-icon :size="20" color="#409eff"><Trophy /></el-icon>
        <span>新生任务进度</span>
        <span class="view-more">查看详情 ›</span>
      </div>
      <el-progress :percentage="taskPercent" :stroke-width="14" :color="progressColor" />
      <p class="progress-text">已完成 {{ dashboard.task_progress?.completed || 0 }} / {{ dashboard.task_progress?.total || 0 }} 项</p>
    </el-card>

    <!-- 快捷入口 -->
    <div class="quick-entries">
      <div class="entry-item" @click="$router.push('/courses')">
        <el-icon :size="28" color="#409eff"><Notebook /></el-icon>
        <span>选课评价</span>
      </div>
      <div class="entry-item" @click="$router.push('/gpa')">
        <el-icon :size="28" color="#67c23a"><Operation /></el-icon>
        <span>GPA计算</span>
      </div>
      <div class="entry-item" @click="$router.push('/pois')">
        <el-icon :size="28" color="#e6a23c"><LocationFilled /></el-icon>
        <span>校园导览</span>
      </div>
      <div class="entry-item" @click="$router.push('/clubs')">
        <el-icon :size="28" color="#f56c6c"><Flag /></el-icon>
        <span>社团导航</span>
      </div>
      <div class="entry-item" @click="$router.push('/guides')">
        <el-icon :size="28" color="#909399"><Document /></el-icon>
        <span>办事攻略</span>
      </div>
    </div>

    <!-- 热门评价 -->
    <el-card class="section-card">
      <template #header><span>🔥 热门课程评价</span></template>
      <div v-if="dashboard.hot_reviews?.length" class="review-list">
        <div v-for="r in dashboard.hot_reviews" :key="r.id" class="review-item"
             @click="$router.push(`/courses/${r.course_id}`)">
          <div class="review-meta">
            <span class="reviewer">{{ r.nickname }}</span>
            <el-rate :model-value="r.score_rating" disabled size="small" />
            <span class="likes">{{ r.like_count }} 赞</span>
          </div>
          <p class="review-content">{{ r.content }}</p>
        </div>
      </div>
      <el-empty v-else description="暂无评价" />
    </el-card>

    <!-- 近期活动 -->
    <el-card class="section-card">
      <template #header><span>📅 近期社团活动</span></template>
      <el-timeline v-if="dashboard.upcoming_events?.length">
        <el-timeline-item v-for="e in dashboard.upcoming_events" :key="e.id"
          :timestamp="formatTime(e.event_time)" placement="top">
          <strong>{{ e.title }}</strong>
          <p v-if="e.location">📍 {{ e.location }}</p>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无近期活动" />
    </el-card>

    <!-- 安全提醒 -->
    <el-card v-if="dashboard.pinned_tips?.length" class="safety-card" @click="$router.push('/safety')">
      <template #header>
        <div class="safety-header">
          <span style="color:#f56c6c">🛡️ 安全防线</span>
          <span class="view-more">查看详情 ›</span>
        </div>
      </template>
      <el-alert v-for="tip in dashboard.pinned_tips" :key="tip.id"
        :title="tip.title" type="warning" :closable="false" show-icon
        style="margin-bottom:8px" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { guideApi } from '@/api'
import { Search, Trophy, Notebook, Operation, LocationFilled, Flag, Document } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const keyword = ref('')
const searchResults = ref([])
const dashboard = ref({ task_progress: {}, hot_reviews: [], upcoming_events: [], pinned_tips: [] })

const taskPercent = computed(() => {
  const { completed, total } = dashboard.value.task_progress
  return total ? Math.round((completed / total) * 100) : 0
})

const progressColor = computed(() => {
  if (taskPercent.value >= 100) return [{ color: '#67c23a', percentage: 100 }]
  if (taskPercent.value >= 50) return [{ color: '#409eff', percentage: 100 }]
  return [{ color: '#e6a23c', percentage: 100 }]
})

onMounted(async () => {
  try {
    dashboard.value = await guideApi.getDashboard()
  } catch { /* 无数据时静默 */ }
})

let searchTimer = null
let abortController = null
watch(keyword, (val) => {
  clearTimeout(searchTimer)
  if (val.length < 2) { searchResults.value = []; return }

  // 取消前一个未完成的请求，避免"先发后到"结果错乱
  if (abortController) abortController.abort()
  abortController = new AbortController()

  searchTimer = setTimeout(async () => {
    try {
      searchResults.value = await guideApi.search(val, abortController.signal)
    } catch (err) {
      if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
        searchResults.value = []
      }
    }
  }, 300)
})

function doSearch() {
  const kw = keyword.value.trim()
  if (kw.length >= 2) {
    router.push({ path: '/search', query: { keyword: kw } })
  }
}

function goTo(item) {
  searchResults.value = []
  keyword.value = ''
  const paths = { course: '/courses', club: '/clubs', poi: '/pois', guide: '/guides' }
  const path = paths[item.type] || '/'
  router.push(`${path}/${item.id}`)
}

function tagType(type) {
  return { course: '', club: 'success', poi: 'warning', guide: 'info' }[type] || ''
}
function typeLabel(type) {
  return { course: '课程', club: '社团', poi: '地标', guide: '攻略' }[type] || type
}
function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.home-page { max-width: 800px; margin: 0 auto; }
.search-bar { position: relative; margin-bottom: 16px; }
.search-dropdown { position: absolute; top: 42px; left: 0; right: 0; background: #fff; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); z-index: 200; max-height: 300px; overflow-y: auto; }
.search-item { padding: 10px 16px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #f0f0f0; }
.search-item:hover { background: #f5f7fa; }
.progress-card { margin-bottom: 16px; cursor: pointer; transition: box-shadow 0.2s; }
.progress-card:hover { box-shadow: 0 4px 12px rgba(64,158,255,0.15); }
.progress-header { display: flex; align-items: center; gap: 8px; font-weight: bold; margin-bottom: 12px; }
.view-more { margin-left: auto; font-size: 13px; font-weight: normal; color: #409eff; }
.progress-text { text-align: center; color: #909399; margin-top: 8px; font-size: 14px; }
.quick-entries { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.entry-item { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 16px 8px; background: #fff; border-radius: 12px; cursor: pointer; transition: transform 0.2s; font-size: 13px; color: #606266; }
.entry-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.section-card { margin-bottom: 16px; }
.safety-card { cursor: pointer; transition: box-shadow 0.2s; }
.safety-card:hover { box-shadow: 0 4px 12px rgba(245,108,108,0.15); }
.safety-header { display: flex; align-items: center; }
.review-list { display: flex; flex-direction: column; gap: 12px; }
.review-item { padding: 12px; background: #fafafa; border-radius: 8px; cursor: pointer; }
.review-item:hover { background: #f0f2f5; }
.review-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.reviewer { font-weight: bold; font-size: 14px; }
.likes { font-size: 12px; color: #909399; }
.review-content { font-size: 14px; color: #606266; line-height: 1.6; }
@media (max-width: 768px) {
  .quick-entries { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .entry-item { padding: 12px 4px; font-size: 12px; }
}
</style>
