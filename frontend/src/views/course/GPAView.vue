<template>
  <div class="gpa-page">
    <h3>GPA 计算器</h3>

    <el-radio-group v-model="algorithm" style="margin-bottom:16px">
      <el-radio-button value="4.0">4.0 算法</el-radio-button>
      <el-radio-button value="5.0">5.0 算法</el-radio-button>
    </el-radio-group>

    <el-table :data="courses" border>
      <el-table-column prop="name" label="课程名称"><template #default="{row}"><el-input v-model="row.name" size="small" placeholder="课程名" /></template></el-table-column>
      <el-table-column prop="credit" label="学分" width="90"><template #default="{row}"><el-input-number v-model="row.credit" :min="0" :max="10" :step="0.5" size="small" controls-position="right" /></template></el-table-column>
      <el-table-column prop="score" label="成绩" width="100"><template #default="{row}"><el-input-number v-model="row.score" :min="0" :max="100" size="small" controls-position="right" /></template></el-table-column>
      <el-table-column label="绩点" width="70"><template #default="{row}">{{ toGpa(row.score).toFixed(1) }}</template></el-table-column>
      <el-table-column label="操作" width="60"><template #default="{ $index }"><el-button type="danger" size="small" text @click="removeRow($index)">删除</el-button></template></el-table-column>
    </el-table>

    <el-button type="primary" @click="addRow" style="margin-top:12px">+ 添加课程</el-button>

    <el-card class="result-card">
      <div class="result-row">
        <span>加权平均分</span>
        <strong class="big-number">{{ weightedAvg }}</strong>
      </div>
      <div class="result-row">
        <span>GPA</span>
        <strong class="big-number accent">{{ gpa }}</strong>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const algorithm = ref('4.0')
const courses = ref([{ name: '', credit: 0, score: 0 }])

// 成绩 → 绩点映射
const gpa4 = (s) => s>=90?4.0:s>=85?3.7:s>=82?3.3:s>=78?3.0:s>=75?2.7:s>=72?2.3:s>=68?2.0:s>=64?1.5:s>=60?1.0:0
const gpa5 = (s) => s>=90?5.0:s>=85?4.5:s>=82?4.0:s>=78?3.5:s>=75?3.0:s>=72?2.5:s>=68?2.0:s>=64?1.5:s>=60?1.0:0

function toGpa(s) { return algorithm.value === '4.0' ? gpa4(s) : gpa5(s) }

const validCourses = computed(() => courses.value.filter(c => c.credit > 0 && c.score >= 0))

const weightedAvg = computed(() => {
  const v = validCourses.value
  if (!v.length) return '0.00'
  const totalW = v.reduce((s, c) => s + c.score * c.credit, 0)
  const totalC = v.reduce((s, c) => s + c.credit, 0)
  return totalC ? (totalW / totalC).toFixed(2) : '0.00'
})

const gpa = computed(() => {
  const v = validCourses.value
  if (!v.length) return '0.00'
  const totalG = v.reduce((s, c) => s + toGpa(c.score) * c.credit, 0)
  const totalC = v.reduce((s, c) => s + c.credit, 0)
  return totalC ? (totalG / totalC).toFixed(2) : '0.00'
})

function addRow() { courses.value.push({ name: '', credit: 0, score: 0 }) }
function removeRow(i) { if (courses.value.length > 1) courses.value.splice(i, 1) }

// 本地存储
onMounted(() => {
  try {
    const saved = localStorage.getItem('gpa_courses')
    if (saved) courses.value = JSON.parse(saved)
  } catch {}
})
watch(courses, (val) => localStorage.setItem('gpa_courses', JSON.stringify(val)), { deep: true })
</script>

<style scoped>
.gpa-page { max-width: 800px; margin: 0 auto; }
.gpa-page h3 { margin-bottom: 16px; }
.result-card { margin-top: 20px; text-align: center; }
.result-row { display: flex; justify-content: space-between; padding: 12px 20px; font-size: 16px; }
.big-number { font-size: 32px; color: #409eff; }
.accent { color: #67c23a; }
</style>
