<template>
  <div>
    <h4>社团管理</h4>
    <el-button type="primary" @click="openDialog()">添加社团</el-button>

    <el-table :data="clubs" border style="margin-top:12px" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="contact" label="联系方式" width="150" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑社团' : '添加社团'" width="min(600px, 90%)">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类别"><el-select v-model="form.category" multiple placeholder="可多选"><el-option v-for="c in cats" :key="c" :label="c" :value="c" /></el-select></el-form-item>
        <el-form-item label="简介"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="活动频率"><el-input v-model="form.activity_frequency" /></el-form-item>
        <el-form-item label="招新要求"><el-input v-model="form.requirements" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="防坑指南"><el-input v-model="form.tips" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="联系方式"><el-input v-model="form.contact" /></el-form-item>
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
import { clubApi, adminApi } from '@/api'

const loading = ref(false)
const clubs = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ name: '', category: [], description: '', activity_frequency: '', requirements: '', tips: '', contact: '' })
const cats = ['学生组织', '学术科技', '志愿公益', '文体艺术', '创新创业', '其他']

onMounted(() => fetchAll())
async function fetchAll() {
  loading.value = true
  try { clubs.value = (await clubApi.getList({ page: 1, page_size: 100 })).items } catch { /* ignore */ }
  finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.assign(form, { name: row.name, category: row.category ? row.category.split(',') : [], description: row.description || '', activity_frequency: row.activity_frequency || '', requirements: row.requirements || '', tips: row.tips || '', contact: row.contact || '' })
  } else {
    editingId.value = null
    Object.assign(form, { name: '', category: [], description: '', activity_frequency: '', requirements: '', tips: '', contact: '' })
  }
  dialogVisible.value = true
}

async function save() {
  try {
    const payload = { ...form, category: form.category.join(',') }
    editingId.value ? await adminApi.updateClub(editingId.value, payload) : await adminApi.createClub(payload)
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
    await adminApi.deleteClub(id)
    ElMessage.success('已删除')
    await fetchAll()
  } catch { /* 错误已提示 */ }
}
</script>
