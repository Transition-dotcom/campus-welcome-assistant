<template>
  <div class="safety-page">
    <h3>🛡️ 安全防线</h3>

    <div v-loading="loading">
      <el-card v-for="tip in tips" :key="tip.id" class="safety-card" :class="{ pinned: tip.is_pinned }">
        <div class="tip-header">
          <span class="tip-title">{{ tip.title }}</span>
          <el-tag v-if="tip.is_pinned" type="danger" size="small" style="margin-left:8px">置顶</el-tag>
        </div>
        <img v-if="tip.image_url" :src="tip.image_url" class="tip-image" alt="安全提示配图" />
        <p class="tip-content">{{ tip.content }}</p>
      </el-card>
      <el-empty v-if="!loading && tips.length === 0" description="暂无安全提示" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { guideApi } from '@/api'

const loading = ref(false)
const tips = ref([])

onMounted(async () => {
  loading.value = true
  try {
    tips.value = await guideApi.getSafetyTips()
  } catch { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.safety-page { max-width: 800px; margin: 0 auto; }
.safety-page h3 { margin-bottom: 16px; }
.safety-card { margin-bottom: 12px; }
.safety-card.pinned { border-left: 3px solid #f56c6c; }
.tip-header { display: flex; align-items: center; margin-bottom: 8px; }
.tip-title { font-weight: bold; font-size: 15px; }
.tip-content { margin: 0; font-size: 14px; color: #606266; line-height: 1.7; white-space: pre-line; }
.tip-image { max-width: 100%; border-radius: 8px; margin-bottom: 8px; }
</style>
