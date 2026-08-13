<template>
  <div class="gpa-page">
    <h3>GPA 计算器 <span style="font-size:14px;color:#909399">（东北大学算法）</span></h3>

    <el-alert type="info" :closable="false" style="margin-bottom:12px">
      <template #title>
        东北大学绩点公式：<strong>课程绩点 = (百分制成绩 - 50) / 10</strong>（60分以下为0）
      </template>
    </el-alert>

    <el-radio-group v-model="scoreType" style="margin-bottom:16px">
      <el-radio-button value="percent">百分制</el-radio-button>
      <el-radio-button value="five">五级制</el-radio-button>
    </el-radio-group>

    <el-table :data="courses" border>
      <el-table-column prop="name" label="课程名称">
        <template #default="{row}"><el-input v-model="row.name" size="small" placeholder="课程名" /></template>
      </el-table-column>
      <el-table-column prop="credit" label="学分" width="90">
        <template #default="{row}"><el-input-number v-model="row.credit" :min="0" :max="10" :step="0.5" size="small" controls-position="right" /></template>
      </el-table-column>
      <el-table-column label="成绩" width="120">
        <template #default="{row}">
          <el-input-number v-if="scoreType==='percent'" v-model="row.score" :min="0" :max="100" size="small" controls-position="right" />
          <el-select v-else v-model="row.fiveLevel" size="small" placeholder="等级">
            <el-option label="优秀(95)" value="优秀" />
            <el-option label="良好(85)" value="良好" />
            <el-option label="中等(75)" value="中等" />
            <el-option label="及格(65)" value="及格" />
            <el-option label="不及格(0)" value="不及格" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="绩点" width="70">
        <template #default="{row}">{{ toGpa(row).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="60">
        <template #default="{ $index }"><el-button type="danger" size="small" text @click="removeRow($index)">删除</el-button></template>
      </el-table-column>
    </el-table>

    <el-button type="primary" @click="addRow" style="margin-top:12px">+ 添加课程</el-button>

    <el-card class="result-card">
      <div class="result-row">
        <span>加权平均分</span>
        <strong class="big-number">{{ weightedAvg }}</strong>
      </div>
      <div class="result-row">
        <span>GPA（总平均学分绩点）</span>
        <strong class="big-number accent">{{ gpa }}</strong>
      </div>
      <div class="result-row" style="font-size:13px;color:#909399">
        <span>总学分</span>
        <span>{{ totalCredits }}</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

/**
 * 东北大学绩点算法（官方公式）
 * 依据：《东北大学本科生学分绩点实施细则》（东大教字〔2018〕106 号）
 * 课程绩点 Y = X/10 - 5（60≤X≤100），即 (百分制成绩 - 50) / 10
 * 60分以下绩点为0
 * 五级制：优秀=95(4.5), 良好=85(3.5), 中等=75(2.5), 及格=65(1.5), 不及格=0(0)
 * GPA = Σ(课程学分 × 单科绩点) / Σ(课程学分)
 * 注：官方公式对补考/重修按考核次数加权，本工具按首次考核简化计算
 */
const scoreType = ref('percent')
const courses = ref([{ name: '', credit: 0, score: 0, fiveLevel: '' }])

const FIVE_TO_SCORE = { '优秀': 95, '良好': 85, '中等': 75, '及格': 65, '不及格': 0 }

function getScore(row) {
  if (scoreType.value === 'percent') return row.score
  return FIVE_TO_SCORE[row.fiveLevel] || 0
}

function toGpa(row) {
  const score = getScore(row)
  if (score < 60) return 0
  return (score - 50) / 10
}

// 仅统计有效行：学分 > 0，且成绩已填写（百分制 score > 0；五级制已选择等级）
const validCourses = computed(() =>
  courses.value.filter(c => {
    if (c.credit <= 0) return false
    if (scoreType.value === 'percent') return c.score > 0
    return !!c.fiveLevel
  })
)

const totalCredits = computed(() =>
  validCourses.value.reduce((s, c) => s + c.credit, 0)
)

const weightedAvg = computed(() => {
  const v = validCourses.value
  if (!v.length) return '0.00'
  const totalW = v.reduce((s, c) => s + getScore(c) * c.credit, 0)
  return totalCredits.value ? (totalW / totalCredits.value).toFixed(2) : '0.00'
})

const gpa = computed(() => {
  const v = validCourses.value
  if (!v.length) return '0.00'
  const totalG = v.reduce((s, c) => s + toGpa(c) * c.credit, 0)
  return totalCredits.value ? (totalG / totalCredits.value).toFixed(4) : '0.0000'  // NEU保留4位
})

function addRow() { courses.value.push({ name: '', credit: 0, score: 0, fiveLevel: '' }) }
function removeRow(i) { if (courses.value.length > 1) courses.value.splice(i, 1) }

// 本地存储：恢复时归一化补默认字段，防止脏数据/旧版本数据导致渲染异常
function normalizeRow(item) {
  const credit = Number(item?.credit)
  const score = Number(item?.score)
  return {
    name: typeof item?.name === 'string' ? item.name : '',
    credit: Number.isFinite(credit) && credit > 0 ? credit : 0,
    score: Number.isFinite(score) && score > 0 && score <= 100 ? score : 0,
    fiveLevel: typeof item?.fiveLevel === 'string' ? item.fiveLevel : '',
  }
}

onMounted(() => {
  try {
    const saved = localStorage.getItem('gpa_courses')
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed)) {
        const normalized = parsed.map(normalizeRow)
        if (normalized.length) courses.value = normalized
      }
    }
  } catch { /* 数据损坏时忽略，保留默认空行 */ }
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
