<template>
  <div class="fav-page">
    <h3>我的收藏</h3>
    <div v-loading="loading">
      <el-card v-for="r in favorites" :key="r.id" class="fav-card" @click="$router.push(`/courses/${r.course_id}`)">
        <div class="fav-top">
          <span class="reviewer">{{ r.nickname }}</span>
          <el-rate :model-value="r.score_rating" disabled size="small" />
        </div>
        <p>{{ r.content }}</p>
      </el-card>
      <el-empty v-if="!loading && favorites.length === 0" description="还没有收藏任何评价" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { courseApi } from '@/api'

const loading = ref(false)
const favorites = ref([])

onMounted(async () => {
  loading.value = true
  try {
    const data = await courseApi.getMyFavorites({ page: 1, page_size: 50 })
    favorites.value = data.items
  } catch { /* 错误已处理 */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.fav-page { max-width: 800px; margin: 0 auto; }
.fav-page h3 { margin-bottom: 16px; }
.fav-card { margin-bottom: 10px; cursor: pointer; }
.fav-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.reviewer { font-weight: bold; }
</style>
