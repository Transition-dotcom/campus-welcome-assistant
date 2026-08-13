<template>
  <div class="not-found-page">
    <el-empty description="页面不存在或已被移除">
      <template #image>
        <el-icon :size="96" color="#c0c4cc"><Compass /></el-icon>
      </template>
      <el-button type="primary" @click="$router.push('/home')">返回首页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { Compass } from '@element-plus/icons-vue'
</script>

<style scoped>
.not-found-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}
</style>
