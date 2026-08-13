<template>
  <div class="detail-page" v-loading="loading">
    <el-card v-if="poi">
      <h3>{{ poi.name }}</h3>
      <el-tag :type="tagType(poi.category)">{{ poi.category }}</el-tag>

      <el-descriptions :column="1" border style="margin-top:16px">
        <el-descriptions-item label="描述">{{ poi.description || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="开放时间">{{ poi.open_hours || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="楼层指引">{{ poi.floor_info || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="注意事项">{{ poi.tips || '暂无' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 路径指引 -->
      <h4 style="margin-top:20px">🚶 路径指引</h4>
      <div v-if="routes.length">
        <el-card v-for="r in routes" :key="r.id" class="route-card">
          <strong>{{ r.from_poi_name }}</strong> → <strong>{{ r.to_poi_name }}</strong>
          <span v-if="r.estimated_minutes" style="color:#909399">（约 {{ r.estimated_minutes }} 分钟）</span>
          <p style="margin-top:4px;color:#606266">{{ r.description }}</p>
        </el-card>
      </div>
      <el-empty v-else description="暂无路径指引" />

      <!-- 纠错入口 -->
      <div style="margin-top:20px;text-align:center">
        <el-button type="warning" @click="showCorrection = true">📝 信息纠错</el-button>
      </div>

      <el-dialog v-model="showCorrection" title="提交纠错" width="90%" :close-on-click-modal="false">
        <el-input v-model="correctionText" type="textarea" :rows="3" placeholder="请描述需要更正的信息..." />
        <template #footer>
          <el-button @click="showCorrection = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitCorrection">提交</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { poiApi } from '@/api'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const submitting = ref(false)
const poi = ref(null)
const routes = ref([])
const showCorrection = ref(false)
const correctionText = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const [p, rts] = await Promise.all([
      poiApi.getDetail(route.params.id),
      poiApi.getRoutes({ poi_id: route.params.id }),
    ])
    poi.value = p
    routes.value = rts
  } catch { /* ignore */ }
  finally { loading.value = false }
})

async function submitCorrection() {
  if (!authStore.isLoggedIn) { ElMessage.warning('请先登录'); return }
  if (!correctionText.value.trim()) { ElMessage.warning('请输入纠错内容'); return }
  submitting.value = true
  try {
    await poiApi.submitCorrection({ poi_id: poi.value.id, content: correctionText.value })
    ElMessage.success('纠错已提交，感谢反馈！')
    showCorrection.value = false
    correctionText.value = ''
  } catch { /* ignore */ }
  finally { submitting.value = false }
}

function tagType(cat) {
  const map = { '教学楼':'', '食堂':'warning', '宿舍':'success', '快递点':'info', '运动场馆':'danger' }
  return map[cat] || 'info'
}
</script>

<style scoped>
.detail-page { max-width: 800px; margin: 0 auto; }
.route-card { margin-bottom: 8px; }
</style>
