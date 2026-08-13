<template>
  <div>
    <h4>课程管理</h4>
    <el-button type="primary" @click="openDialog()">添加课程</el-button>

    <el-table :data="courses" border style="margin-top:12px" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="teacher" label="教师" />
      <el-table-column prop="college" label="学院" />
      <el-table-column prop="category" label="类别" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑课程' : '添加课程'" width="min(500px, 90%)">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="教师"><el-input v-model="form.teacher" /></el-form-item>
        <el-form-item label="学院"><el-input v-model="form.college" /></el-form-item>
        <el-form-item label="类别"><el-select v-model="form.category"><el-option v-for="c in cats" :key="c" :label="c" :value="c" /></el-select></el-form-item>
        <el-form-item label="学分"><el-input-number v-model="form.credit" :min="0" :step="0.5" /></el-form-item>
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
import { courseApi, adminApi } from '@/api'

const loading = ref(false)
const courses = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ name: '', teacher: '', college: '', category: '', credit: 0 })
const cats = ['通识必修', '通识选修', '专业必修', '专业选修']

onMounted(() => fetchAll())

async function fetchAll() {
  loading.value = true
  try {
    const data = await courseApi.getList({ page: 1, page_size: 100 })
    courses.value = data.items
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.assign(form, { name: row.name, teacher: row.teacher || '', college: row.college || '', category: row.category || '', credit: row.credit || 0 })
  } else {
    editingId.value = null
    Object.assign(form, { name: '', teacher: '', college: '', category: '', credit: 0 })
  }
  dialogVisible.value = true
}

async function save() {
  try {
    if (editingId.value) {
      await adminApi.updateCourse(editingId.value, form)
    } else {
      await adminApi.createCourse(form)
    }
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
    await adminApi.deleteCourse(id)
    ElMessage.success('已删除')
    await fetchAll()
  } catch { /* 错误已提示 */ }
}
</script>
