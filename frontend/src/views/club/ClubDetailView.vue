<template>
  <div class="detail-page" v-loading="loading">
    <el-card v-if="club">
      <h3>{{ club.name }}</h3>
      <el-tag v-for="t in club.category.split(',')" :key="t" type="success" style="margin-right:6px">{{ t }}</el-tag>

      <el-descriptions :column="1" border style="margin-top:16px">
        <el-descriptions-item label="简介"><span class="pre-line">{{ club.description || '暂无' }}</span></el-descriptions-item>
        <el-descriptions-item label="活动频率">{{ club.activity_frequency || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="招新要求"><span class="pre-line">{{ club.requirements || '暂无' }}</span></el-descriptions-item>
        <el-descriptions-item label="防坑指南">
          <span style="color:#e6a23c">{{ club.tips || '暂无' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="联系方式">{{ club.contact || '暂无' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 近期活动 -->
      <h4 style="margin-top:20px">近期活动</h4>
      <el-timeline v-if="events.length">
        <el-timeline-item v-for="e in events" :key="e.id" :timestamp="formatTime(e.event_time)" placement="top">
          <strong>{{ e.title }}</strong>
          <el-tag size="small" style="margin-left:8px">{{ e.event_type }}</el-tag>
          <p v-if="e.location">📍 {{ e.location }}</p>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无活动" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { clubApi } from '@/api'

const route = useRoute()
const loading = ref(false)
const club = ref(null)
const events = ref([])

onMounted(async () => {
  loading.value = true
  try {
    const [c, evts] = await Promise.all([
      clubApi.getDetail(route.params.id),
      clubApi.getEvents(route.params.id),
    ])
    club.value = c
    events.value = evts
  } catch { /* ignore */ }
  finally { loading.value = false }
})

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' })
}
</script>

<style scoped>
.detail-page { max-width: 800px; margin: 0 auto; }
.detail-page h3 { margin-bottom: 8px; }
.pre-line { white-space: pre-line; }
</style>
