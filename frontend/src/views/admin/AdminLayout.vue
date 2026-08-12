<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="200px" class="admin-sidebar">
        <h4 style="padding:16px;color:#fff;text-align:center">管理后台</h4>
        <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
          <el-menu-item index="/admin/courses"><el-icon><Notebook /></el-icon>课程管理</el-menu-item>
          <el-menu-item index="/admin/clubs"><el-icon><Flag /></el-icon>社团管理</el-menu-item>
          <el-menu-item index="/admin/pois"><el-icon><LocationFilled /></el-icon>地标管理</el-menu-item>
          <el-menu-item index="/admin/corrections"><el-icon><Warning /></el-icon>纠错处理</el-menu-item>
          <el-menu-item index="/admin/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
          <el-menu-item index="/home"><el-icon><HomeFilled /></el-icon>返回前台</el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Notebook, Flag, LocationFilled, Warning, User, HomeFilled } from '@element-plus/icons-vue'
const route = useRoute()
</script>

<style scoped>
.admin-layout { min-height: calc(100vh - 56px); }
.admin-sidebar { background: #304156; min-height: calc(100vh - 56px); }
.admin-main { padding: 20px; background: #f5f7fa; }
@media (max-width: 768px) {
  .admin-sidebar { width: 120px !important; }
  .admin-sidebar h4 { font-size: 13px; }
}
</style>
