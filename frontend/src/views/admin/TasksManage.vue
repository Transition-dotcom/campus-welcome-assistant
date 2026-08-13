<template>
  <div>
    <h4>任务管理</h4>
    <el-button type="primary" @click="openDialog()">添加任务</el-button>

    <el-table :data="tasks" border style="margin-top:12px" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="icon" label="图标名" width="140">
        <template #default="{ row }">
          <span v-if="row.icon">
            <el-icon style="vertical-align:-2px"><component :is="row.icon" /></el-icon>
            {{ row.icon }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="70" />
      <el-table-column prop="badge_level" label="勋章等级" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.badge_level" :type="badgeTagType(row.badge_level)">{{ badgeLabel(row.badge_level) }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && tasks.length === 0" description="暂无任务" />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑任务' : '添加任务'" width="min(500px, 90%)">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="图标名"><el-input v-model="form.icon" placeholder="如：Trophy、Notebook（Element Plus 图标名）" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
        <el-form-item label="勋章等级">
          <el-select v-model="form.badge_level" placeholder="选择勋章等级">
            <el-option label="无" :value="null" />
            <el-option label="bronze（铜牌）" value="bronze" />
            <el-option label="silver（银牌）" value="silver" />
            <el-option label="gold（金牌）" value="gold" />
            <el-option label="diamond（钻石）" value="diamond" />
          </el-select>
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
const tasks = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ title: '', description: '', icon: '', sort_order: 0, badge_level: null })

onMounted(() => fetchAll())

async function fetchAll() {
  loading.value = true
  try {
    tasks.value = await adminApi.getTasks()
  } catch { /* 错误已提示 */ }
  finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.assign(form, {
      title: row.title || '',
      description: row.description || '',
      icon: row.icon || '',
      sort_order: row.sort_order ?? 0,
      badge_level: row.badge_level || null,
    })
  } else {
    editingId.value = null
    Object.assign(form, { title: '', description: '', icon: '', sort_order: 0, badge_level: null })
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.title.trim()) { ElMessage.warning('请填写标题'); return }
  const payload = {
    title: form.title.trim(),
    description: (form.description || '').trim(),
    icon: (form.icon || '').trim(),
    sort_order: form.sort_order ?? 0,
    badge_level: form.badge_level,
  }
  try {
    editingId.value ? await adminApi.updateTask(editingId.value, payload) : await adminApi.createTask(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchAll()
  } catch { /* 错误已提示 */ }
}

async function del(id) {
  try {
    await ElMessageBox.confirm('确定删除该任务？', '提示', { type: 'warning' })
  } catch { return /* 用户取消 */ }
  try {
    await adminApi.deleteTask(id)
    ElMessage.success('已删除')
    await fetchAll()
  } catch { /* 错误已提示（如已有打卡记录时后端返回 400） */ }
}

function badgeTagType(level) {
  return { bronze: 'warning', silver: 'info', gold: 'warning', diamond: 'danger' }[level] || 'info'
}
function badgeLabel(level) {
  return { bronze: '🥉 铜牌', silver: '🥈 银牌', gold: '🥇 金牌', diamond: '💎 钻石' }[level] || level
}
</script>
