<template>
  <div>
    <h4>地标管理</h4>
    <el-button type="primary" @click="openDialog()">添加地标</el-button>

    <el-table :data="pois" border style="margin-top:12px" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="open_hours" label="开放时间" width="150" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑地标' : '添加地标'" width="min(600px, 90%)">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类别"><el-select v-model="form.category"><el-option v-for="c in cats" :key="c" :label="c" :value="c" /></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="开放时间"><el-input v-model="form.open_hours" /></el-form-item>
        <el-form-item label="楼层指引"><el-input v-model="form.floor_info" /></el-form-item>
        <el-form-item label="注意事项"><el-input v-model="form.tips" type="textarea" :rows="2" /></el-form-item>
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
import { poiApi, adminApi } from '@/api'

const loading = ref(false)
const pois = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ name: '', category: '教学楼', description: '', open_hours: '', floor_info: '', tips: '' })
const cats = ['教学楼', '食堂', '宿舍', '快递点', '运动场馆', '行政楼', '其他']

onMounted(() => fetchAll())
async function fetchAll() {
  loading.value = true
  try { pois.value = (await poiApi.getList({ page: 1, page_size: 100 })).items } catch { /* ignore */ }
  finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.assign(form, { name: row.name, category: row.category, description: row.description || '', open_hours: row.open_hours || '', floor_info: row.floor_info || '', tips: row.tips || '' })
  } else {
    editingId.value = null
    Object.assign(form, { name: '', category: '教学楼', description: '', open_hours: '', floor_info: '', tips: '' })
  }
  dialogVisible.value = true
}

async function save() {
  try {
    editingId.value ? await adminApi.updatePoi(editingId.value, form) : await adminApi.createPoi(form)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchAll()
  } catch { /* ignore */ }
}

async function del(id) {
  try {
    await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  } catch { return /* 用户取消 */ }
  try {
    await adminApi.deletePoi(id)
    ElMessage.success('已删除')
    await fetchAll()
  } catch { /* 错误已提示 */ }
}
</script>
