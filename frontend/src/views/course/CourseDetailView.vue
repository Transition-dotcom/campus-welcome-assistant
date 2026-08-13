<template>
  <div class="detail-page" v-loading="loading">
    <!-- 课程信息 -->
    <el-card v-if="course">
      <h3>{{ course.name }}</h3>
      <div class="course-meta">
        <span v-if="course.teacher">👨‍🏫 {{ course.teacher }}</span>
        <span v-if="course.college">🏫 {{ course.college }}</span>
        <span v-if="course.credit">📚 {{ course.credit }} 学分</span>
        <span>💬 {{ course.review_count }} 条评价</span>
      </div>
    </el-card>

    <!-- 发表评价 -->
    <el-card v-if="authStore.isLoggedIn" style="margin-top: 12px">
      <template #header><span>发表评价</span></template>
      <el-form :model="reviewForm">
        <el-form-item label="难度评分"><el-rate v-model="reviewForm.difficulty_rating" :max="5" /></el-form-item>
        <el-form-item label="给分评分"><el-rate v-model="reviewForm.score_rating" :max="5" /></el-form-item>
        <el-form-item label="评价内容"><el-input v-model="reviewForm.content" type="textarea" :rows="3" placeholder="至少10个字..." /></el-form-item>
        <el-form-item><el-checkbox v-model="reviewForm.is_anonymous">匿名发表</el-checkbox></el-form-item>
        <el-button type="primary" :loading="submitting" @click="submitReview">提交评价</el-button>
      </el-form>
    </el-card>

    <!-- 评价列表 -->
    <div style="margin-top: 12px">
      <el-radio-group v-model="sort" @change="onSortChange" size="small">
        <el-radio-button value="time">最新</el-radio-button>
        <el-radio-button value="like">最热</el-radio-button>
      </el-radio-group>
    </div>

    <el-card v-for="r in reviews" :key="r.id" class="review-card">
      <div class="review-top">
        <span class="reviewer">{{ r.nickname }}</span>
        <div class="ratings">
          <span>难度 <el-rate :model-value="r.difficulty_rating" disabled size="small" /></span>
          <span>给分 <el-rate :model-value="r.score_rating" disabled size="small" /></span>
        </div>
      </div>
      <p class="review-text">{{ r.content }}</p>
      <div class="review-actions">
        <el-button :type="r.is_liked ? 'primary' : 'default'" size="small" text
          :disabled="!!likePending[r.id]" @click="toggleLike(r)">
          <el-icon><CaretTop /></el-icon> {{ r.like_count }}
        </el-button>
        <el-button size="small" text @click="showComments(r)">
          <el-icon><ChatDotRound /></el-icon> 评论
        </el-button>
        <el-button :type="r.is_favorited ? 'warning' : 'default'" size="small" text
          :disabled="!!favPending[r.id]" @click="toggleFav(r)">
          <el-icon><Star /></el-icon> {{ r.is_favorited ? '已收藏' : '收藏' }}
        </el-button>
        <el-button size="small" text type="danger" @click="reportReview(r)">举报</el-button>
      </div>

      <!-- 评论区 -->
      <div v-if="r.showComments" class="comments-section">
        <div v-for="c in r.comments" :key="c.id" class="comment-item">
          <strong>{{ c.nickname }}</strong>：{{ c.content }}
        </div>
        <el-input v-model="r.commentText" placeholder="写评论..." size="small" style="margin-top:8px"
          @keyup.enter="submitComment(r)">
          <template #append><el-button @click="submitComment(r)">发送</el-button></template>
        </el-input>
      </div>
    </el-card>

    <!-- 加载更多 -->
    <div v-if="reviews.length < reviewsTotal" style="text-align:center;margin-top:16px">
      <el-button :loading="loadingMore" @click="loadMoreReviews">加载更多</el-button>
    </div>

    <el-empty v-if="!loading && reviews.length === 0" description="暂无评价，来写第一条吧" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { courseApi } from '@/api'
import { CaretTop, ChatDotRound, Star } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const submitting = ref(false)
const course = ref(null)
const reviews = ref([])
const sort = ref('time')
const reviewsPage = ref(1)
const reviewsTotal = ref(0)
const loadingMore = ref(false)
// 点赞/收藏请求锁（按 review id），防止双击重复 toggle
const likePending = reactive({})
const favPending = reactive({})
const reviewForm = reactive({ difficulty_rating: 0, score_rating: 0, content: '', is_anonymous: false })

function decorateReviews(items) {
  return items.map(item => ({ ...item, showComments: false, commentText: '', comments: [] }))
}

onMounted(async () => {
  const id = route.params.id
  loading.value = true
  try {
    const c = await courseApi.getDetail(id)
    course.value = c
    await fetchReviews(true)
  } catch { /* 错误已处理 */ }
  finally { loading.value = false }
})

// reset=true 时重新从第 1 页加载；false 时追加下一页
async function fetchReviews(reset = true) {
  if (reset) reviewsPage.value = 1
  const data = await courseApi.getReviews(route.params.id, {
    sort: sort.value,
    page: reviewsPage.value,
    page_size: 10,
  })
  const mapped = decorateReviews(data.items || [])
  reviews.value = reset ? mapped : [...reviews.value, ...mapped]
  reviewsTotal.value = data.total || reviews.value.length
}

function onSortChange() {
  fetchReviews(true)
}

async function loadMoreReviews() {
  if (loadingMore.value) return
  loadingMore.value = true
  try {
    reviewsPage.value += 1
    await fetchReviews(false)
  } catch {
    // 失败时回退页码，用户可重试
    reviewsPage.value -= 1
  } finally {
    loadingMore.value = false
  }
}

async function submitReview() {
  if (!reviewForm.difficulty_rating || !reviewForm.score_rating) { ElMessage.warning('请完成评分'); return }
  if (reviewForm.content.length < 10) { ElMessage.warning('评价内容至少10个字'); return }
  submitting.value = true
  try {
    await courseApi.createReview(route.params.id, {
      difficulty_rating: reviewForm.difficulty_rating,
      score_rating: reviewForm.score_rating,
      content: reviewForm.content,
      is_anonymous: reviewForm.is_anonymous,
    })
    ElMessage.success('评价发表成功')
    reviewForm.content = ''; reviewForm.difficulty_rating = 0; reviewForm.score_rating = 0
    await fetchReviews()
  } catch { /* 错误已处理 */ }
  finally { submitting.value = false }
}

async function toggleLike(r) {
  if (!authStore.isLoggedIn) { ElMessage.warning('请先登录'); return }
  if (likePending[r.id]) return
  likePending[r.id] = true
  try {
    const result = await courseApi.toggleLike(r.id)
    r.is_liked = result.is_liked
    r.like_count = result.like_count
  } catch { /* 错误已提示 */ }
  finally { likePending[r.id] = false }
}

async function toggleFav(r) {
  if (!authStore.isLoggedIn) { ElMessage.warning('请先登录'); return }
  if (favPending[r.id]) return
  favPending[r.id] = true
  try {
    const result = await courseApi.toggleFavorite(r.id)
    r.is_favorited = result.is_favorited
  } catch { /* 错误已提示 */ }
  finally { favPending[r.id] = false }
}

async function showComments(r) {
  r.showComments = !r.showComments
  if (r.showComments && r.comments.length === 0) {
    const data = await courseApi.getComments(r.id)
    r.comments = data.items
  }
}

async function submitComment(r) {
  if (!authStore.isLoggedIn) { ElMessage.warning('请先登录'); return }
  if (!r.commentText.trim()) return
  const result = await courseApi.createComment(r.id, { content: r.commentText })
  r.comments.push(result)
  r.commentText = ''
}

function reportReview(r) {
  if (!authStore.isLoggedIn) { ElMessage.warning('请先登录'); return }
  ElMessageBox.prompt('请输入举报原因（至少5个字）', '举报评价', {
    inputValidator: (val) => (val && val.trim().length >= 5) || '举报原因至少5个字',
  }).then(async ({ value }) => {
    const reason = value.trim()
    if (reason.length < 5) { ElMessage.warning('举报原因至少5个字'); return }
    await courseApi.reportReview(r.id, { reason })
    ElMessage.success('举报已提交')
  }).catch(() => {})
}
</script>

<style scoped>
.detail-page { max-width: 800px; margin: 0 auto; }
.course-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 14px; color: #606266; margin-top: 8px; }
.review-card { margin-top: 12px; }
.review-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.reviewer { font-weight: bold; font-size: 15px; }
.ratings { display: flex; gap: 12px; font-size: 13px; color: #606266; }
.review-text { font-size: 14px; line-height: 1.8; color: #303133; margin-bottom: 8px; }
.review-actions { display: flex; gap: 4px; }
.comments-section { margin-top: 12px; padding-top: 12px; border-top: 1px solid #ebeef5; }
.comment-item { padding: 6px 0; font-size: 14px; color: #606266; }
</style>
