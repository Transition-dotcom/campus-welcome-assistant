<template>
  <div>
    <h4>攻略管理</h4>
    <el-button type="primary" @click="openDialog()">添加攻略</el-button>

    <el-table :data="guides" border style="margin-top:12px" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
      <el-table-column label="步骤数" width="80">
        <template #default="{ row }">{{ row.content?.length || 0 }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && guides.length === 0" description="暂无攻略" />

    <el-pagination v-if="total > pageSize" :total="total" :page-size="pageSize" :current-page="page"
      layout="prev, pager, next" @current-change="onPageChange" style="margin-top:16px;justify-content:center" />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑攻略' : '添加攻略'" width="min(640px, 90%)">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="form.category" placeholder="如：入学报道、生活服务" /></el-form-item>
        <el-form-item label="摘要"><el-input v-model="form.summary" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="步骤">
          <div class="steps-editor">
            <div v-for="(step, i) in form.content" :key="i" class="step-row">
              <span class="step-no">第 {{ i + 1 }} 步</span>
              <el-input v-model="step.title" placeholder="步骤标题" size="small" />
              <el-input v-model="step.description" placeholder="步骤描述" size="small" />
              <el-input-number v-model="step.location_poi_id" :min="1" placeholder="POI ID" size="small" controls-position="right" class="step-poi" />
              <el-button size="small" type="danger" text @click="removeStep(i)">删除</el-button>
            </div>
            <el-button size="small" @click="addStep">+ 添加步骤</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { adminApi } from '@/api'

const loading = ref(false)
const guides = ref([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ title: '', category: '', summary: '', content: [] })

onMounted(() => fetchAll())

async function fetchAll() {
  loading.value = true
  try {
    const data = await adminApi.getGuides({ page: page.value, page_size: pageSize })
    guides.value = data.items || []
    total.value = data.total || 0
  } catch { /* 错误已提示 */ }
  finally { loading.value = false }
}

function onPageChange(p) {
  page.value = p
  fetchAll()
}

function emptyStep() {
  return { title: '', description: '', location_poi_id: null }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    const content = Array.isArray(row.content)
      ? row.content.map(s => ({ title: s.title || '', description: s.description || '', location_poi_id: s.location_poi_id ?? null }))
      : []
    Object.assign(form, { title: row.title || '', category: row.category || '', summary: row.summary || '', content })
  } else {
    editingId.value = null
    Object.assign(form, { title: '', category: '', summary: '', content: [emptyStep()] })
  }
  dialogVisible.value = true
}

function addStep() {
  form.content.push(emptyStep())
}

function removeStep(i) {
  if (form.content.length > 1) form.content.splice(i, 1)
}

async function save() {
  if (!form.title.trim()) { ElMessage.warning('请填写标题'); return }
  // 过滤全空步骤，step 序号按顺序自动生成
  const steps = form.content
    .filter(s => (s.title || '').trim() || (s.description || '').trim())
    .map((s, i) => ({
      step: i + 1,
      title: (s.title || '').trim(),
      description: (s.description || '').trim(),
      location_poi_id: s.location_poi_id ?? null,
    }))
  const payload = {
    title: form.title.trim(),
    category: form.category.trim(),
    summary: form.summary.trim(),
    content: steps,
  }
  try {
    editingId.value ? await adminApi.updateGuide(editingId.value, payload) : await adminApi.createGuide(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchAll()
  } catch { /* 错误已提示 */ }
}

async function del(id) {
  try {
    await ElMessageBox.confirm('确定删除该攻略？', '提示', { type: 'warning' })
  } catch { return /* 用户取消 */ }
  try {
    await adminApi.deleteGuide(id)
    ElMessage.success('已删除')
    await fetchAll()
  } catch { /* 错误已提示 */ }
}
</script>

<style scoped>
.steps-editor { width: 100%; }
.step-row { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.step-no { flex-shrink: 0; font-size: 12px; color: #909399; width: 48px; }
.step-poi { width: 110px; flex-shrink: 0; }
</style>
