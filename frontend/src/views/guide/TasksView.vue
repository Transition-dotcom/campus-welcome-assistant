<template>
  <div class="tasks-page">
    <h3>新生任务清单</h3>

    <!-- 进度 + 勋章 -->
    <el-card class="progress-card">
      <div class="progress-header">
        <el-icon :size="28" color="#409eff"><Trophy /></el-icon>
        <div>
          <el-progress :percentage="taskPercent" :stroke-width="16" :color="progressColor" />
          <p style="margin-top:8px;text-align:center;color:#606266">
            已完成 {{ completedCount }} / {{ tasks.length }} 项
            <el-tag v-if="badge" :type="badgeType" style="margin-left:8px">{{ badgeLabel }}</el-tag>
          </p>
        </div>
      </div>
    </el-card>

    <!-- 任务列表 -->
    <div v-loading="loading">
      <el-card v-for="t in tasks" :key="t.id" class="task-card" :class="{ done: t.is_checked }">
        <div class="task-row">
          <div class="task-left">
            <el-icon v-if="t.icon" :size="24"><component :is="t.icon" /></el-icon>
            <div>
              <h4 :style="t.is_checked ? 'text-decoration:line-through;color:#67c23a' : ''">{{ t.title }}</h4>
              <p>{{ t.description }}</p>
            </div>
          </div>
          <el-button v-if="!t.is_checked" type="success" size="small" :loading="!!checkinPending[t.id]" @click="doCheckin(t)">打卡</el-button>
          <el-tag v-else type="success" size="small">已完成</el-tag>
        </div>
      </el-card>
      <el-empty v-if="!loading && tasks.length === 0" description="暂无任务" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { guideApi } from '@/api'
import { Trophy } from '@element-plus/icons-vue'

const loading = ref(false)
const tasks = ref([])
const badge = ref(null)
// 每任务的打卡请求锁，防止双击重复提交
const checkinPending = reactive({})

const completedCount = computed(() => tasks.value.filter(t => t.is_checked).length)
const taskPercent = computed(() => tasks.value.length ? Math.round((completedCount.value / tasks.value.length) * 100) : 0)
const progressColor = computed(() => taskPercent.value >= 100 ? '#67c23a' : taskPercent.value >= 50 ? '#409eff' : '#e6a23c')
const badgeType = computed(() => {
  const map = { bronze: 'warning', silver: 'info', gold: 'warning', diamond: 'danger' }
  return map[badge.value] || 'info'
})
const badgeLabel = computed(() => {
  const map = { bronze: '🥉 铜牌', silver: '🥈 银牌', gold: '🥇 金牌', diamond: '💎 钻石' }
  return map[badge.value] || badge.value
})

onMounted(async () => {
  loading.value = true
  try { tasks.value = await guideApi.getTasks() } catch { /* ignore */ }
  finally { loading.value = false }
})

async function doCheckin(t) {
  if (checkinPending[t.id]) return
  checkinPending[t.id] = true
  try {
    const result = await guideApi.checkinTask(t.id)
    t.is_checked = true
    badge.value = result.badge
    ElMessage.success('打卡成功！')
  } catch { /* ignore */ }
  finally { checkinPending[t.id] = false }
}
</script>

<style scoped>
.tasks-page { max-width: 800px; margin: 0 auto; }
.tasks-page h3 { margin-bottom: 16px; }
.progress-card { margin-bottom: 16px; }
.progress-header { display: flex; align-items: center; gap: 16px; }
.task-card { margin-bottom: 8px; }
.task-card.done { opacity: 0.7; background: #f0f9eb; }
.task-row { display: flex; align-items: center; justify-content: space-between; }
.task-left { display: flex; align-items: center; gap: 12px; }
.task-left h4 { margin: 0; font-size: 15px; }
.task-left p { margin: 4px 0 0; font-size: 13px; color: #909399; }
</style>
