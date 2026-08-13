<template>
  <div id="app-container">
    <!-- 顶部导航 -->
    <el-header v-if="!isMobile || !showBottomNav" class="main-header">
      <div class="header-left" @click="$router.push('/')">
        <el-icon :size="24"><School /></el-icon>
        <span class="app-title">NEU软院 · 萌新领航站</span>
      </div>
      <div class="header-right" v-if="!isMobile">
        <el-menu mode="horizontal" :default-active="activeMenu" :ellipsis="false" router>
          <el-menu-item index="/home">首页</el-menu-item>
          <el-menu-item index="/courses">选课评价</el-menu-item>
          <el-menu-item index="/gpa">GPA计算器</el-menu-item>
          <el-menu-item index="/clubs">社团导航</el-menu-item>
          <el-menu-item index="/pois">校园导览</el-menu-item>
          <el-menu-item index="/guides">校园攻略</el-menu-item>
        </el-menu>
        <div class="user-area">
          <template v-if="authStore.isLoggedIn">
            <el-dropdown @command="handleUserCommand">
              <span class="user-name">{{ authStore.user?.nickname || '用户' }}</span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                  <el-dropdown-item command="tasks">我的任务</el-dropdown-item>
                  <el-dropdown-item command="favorites">我的收藏</el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" command="admin" divided>管理后台</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" size="small" @click="$router.push('/login')">登录</el-button>
          </template>
        </div>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <el-main class="main-content">
      <router-view />
    </el-main>

    <!-- 移动端底部导航 -->
    <div v-if="isMobile && showBottomNav" class="bottom-nav">
      <div class="nav-item" :class="{ active: $route.path === '/home' }" @click="$router.push('/home')">
        <el-icon><HomeFilled /></el-icon><span>首页</span>
      </div>
      <div class="nav-item" :class="{ active: $route.path.startsWith('/courses') }" @click="$router.push('/courses')">
        <el-icon><Notebook /></el-icon><span>选课</span>
      </div>
      <div class="nav-item" :class="{ active: $route.path.startsWith('/clubs') }" @click="$router.push('/clubs')">
        <el-icon><Flag /></el-icon><span>社团</span>
      </div>
      <div class="nav-item" :class="{ active: $route.path.startsWith('/pois') }" @click="$router.push('/pois')">
        <el-icon><LocationFilled /></el-icon><span>导览</span>
      </div>
      <div class="nav-item" :class="{ active: $route.path === '/guides' }" @click="$router.push('/guides')">
        <el-icon><Document /></el-icon><span>攻略</span>
      </div>
      <div class="nav-item" :class="{ active: $route.path === '/profile' || $route.path === '/login' }" @click="handleMobileUserClick">
        <el-icon><User /></el-icon><span>{{ authStore.isLoggedIn ? '我的' : '登录' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { School, HomeFilled, Notebook, Flag, LocationFilled, Document, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 响应式移动端判断：监听窗口尺寸变化，避免 computed 无依赖不更新
const isMobile = ref(window.innerWidth < 768)
function updateIsMobile() {
  isMobile.value = window.innerWidth < 768
}
onMounted(() => window.addEventListener('resize', updateIsMobile))
onBeforeUnmount(() => window.removeEventListener('resize', updateIsMobile))
const activeMenu = computed(() => route.path)
const showBottomNav = computed(() => {
  const hiddenPaths = ['/login', '/register']
  return !hiddenPaths.includes(route.path) && !route.path.startsWith('/admin')
})

function handleMobileUserClick() {
  if (authStore.isLoggedIn) {
    router.push('/profile')
  } else {
    router.push('/login')
  }
}

function handleUserCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/home')
  } else {
    router.push(`/${command}`)
  }
}

// 应用启动时从 localStorage 恢复登录状态
authStore.restoreFromStorage()
</script>

<style>
#app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.main-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #2c3e50;
  font-weight: bold;
  font-size: 18px;
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-area {
  display: flex;
  align-items: center;
}

.user-name {
  color: #409eff;
  cursor: pointer;
  font-size: 14px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
  min-height: calc(100vh - 56px - 60px);
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  color: #909399;
  cursor: pointer;
}

.nav-item.active {
  color: #409eff;
}

.nav-item .el-icon {
  font-size: 20px;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-header {
    padding: 0 12px;
  }
  .main-content {
    padding: 12px;
    padding-bottom: 70px;
  }
  .header-right .el-menu {
    display: none;
  }
}
</style>
