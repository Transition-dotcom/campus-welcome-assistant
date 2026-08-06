<template>
  <div class="guide-page">
    <h3>校园攻略</h3>
    <el-tabs v-model="activeCategory" type="card">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="办事流程" name="办事流程" />
      <el-tab-pane label="生活指南" name="生活指南" />
      <el-tab-pane label="学习攻略" name="学习攻略" />
    </el-tabs>

    <div v-loading="loading">
      <el-card v-for="g in filteredGuides" :key="g.id" class="guide-card" @click="$router.push(`/guides/${g.id}`)">
        <h4>{{ g.title }}</h4>
        <el-tag size="small">{{ g.category }}</el-tag>
        <p v-if="g.content?.length">{{ g.content.length }} 个步骤</p>
      </el-card>
      <el-empty v-if="!loading && filteredGuides.length === 0" description="暂无攻略" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { guideApi } from '@/api'

const loading = ref(false)
const guides = ref([])
const activeCategory = ref('')

const filteredGuides = computed(() => {
  if (!activeCategory.value) return guides.value
  return guides.value.filter(g => g.category === activeCategory.value)
})

onMounted(async () => {
  loading.value = true
  try { guides.value = await guideApi.getGuides() } catch { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.guide-page { max-width: 800px; margin: 0 auto; }
.guide-page h3 { margin-bottom: 16px; }
.guide-card { margin-bottom: 10px; cursor: pointer; }
.guide-card:hover { border-color: #909399; }
.guide-card h4 { margin: 0 0 4px; }
</style>
