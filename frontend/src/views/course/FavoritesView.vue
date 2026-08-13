<template>
  <div class="fav-page">
    <h3>我的收藏</h3>
    <div v-loading="loading">
      <el-card v-for="r in favorites" :key="r.id" class="fav-card">
        <div class="fav-main" @click="$router.push(`/courses/${r.course_id}`)">
          <div class="fav-top">
            <span class="reviewer">{{ r.nickname }}</span>
            <el-rate :model-value="r.score_rating" disabled size="small" />
          </div>
          <p>{{ r.content }}</p>
        </div>
        <div class="fav-actions">
          <el-button size="small" type="danger" text :loading="!!removing[r.id]" @click="removeFav(r)">取消收藏</el-button>
        </div>
      </el-card>
      <el-empty v-if="!loading && favorites.length === 0" description="还没有收藏任何评价" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { courseApi } from '@/api'

const loading = ref(false)
const favorites = ref([])
const removing = reactive({})

onMounted(loadFavorites)

async function loadFavorites() {
  loading.value = true
  try {
    const data = await courseApi.getMyFavorites({ page: 1, page_size: 50 })
    favorites.value = data.items
  } catch { /* 错误已处理 */ }
  finally { loading.value = false }
}

async function removeFav(r) {
  if (removing[r.id]) return
  removing[r.id] = true
  try {
    // toggle favorite 接口：已收藏时再次调用即取消收藏
    await courseApi.toggleFavorite(r.id)
    favorites.value = favorites.value.filter(f => f.id !== r.id)
    ElMessage.success('已取消收藏')
  } catch { /* 错误已提示 */ }
  finally { removing[r.id] = false }
}
</script>

<style scoped>
.fav-page { max-width: 800px; margin: 0 auto; }
.fav-page h3 { margin-bottom: 16px; }
.fav-card { margin-bottom: 10px; }
.fav-main { cursor: pointer; }
.fav-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.reviewer { font-weight: bold; }
.fav-actions { display: flex; justify-content: flex-end; border-top: 1px solid #f0f0f0; margin-top: 8px; padding-top: 4px; }
</style>
