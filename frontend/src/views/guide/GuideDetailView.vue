<template>
  <div class="detail-page" v-loading="loading">
    <el-card v-if="guide">
      <h3>{{ guide.title }}</h3>
      <el-tag>{{ guide.category }}</el-tag>

      <el-steps v-if="guide.content?.length" direction="vertical" style="margin-top:20px">
        <el-step v-for="step in guide.content" :key="step.step"
          :title="`第 ${step.step} 步：${step.title}`"
          :description="step.description" />
      </el-steps>
      <el-empty v-else description="暂无步骤详情" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { guideApi } from '@/api'

const route = useRoute()
const loading = ref(false)
const guide = ref(null)

onMounted(async () => {
  loading.value = true
  try { guide.value = await guideApi.getGuideDetail(route.params.id) } catch { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.detail-page { max-width: 800px; margin: 0 auto; }
.detail-page h3 { margin-bottom: 8px; }
</style>
