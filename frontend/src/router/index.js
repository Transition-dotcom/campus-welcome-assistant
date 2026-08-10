import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/home',
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/home/HomeView.vue'),
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/search/SearchView.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/user/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/user/RegisterView.vue'),
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/user/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/guide/TasksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: () => import('@/views/course/FavoritesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('@/views/course/CourseListView.vue'),
  },
  {
    path: '/courses/:id',
    name: 'CourseDetail',
    component: () => import('@/views/course/CourseDetailView.vue'),
  },
  {
    path: '/gpa',
    name: 'GPA',
    component: () => import('@/views/course/GPAView.vue'),
  },
  {
    path: '/clubs',
    name: 'Clubs',
    component: () => import('@/views/club/ClubListView.vue'),
  },
  {
    path: '/clubs/:id',
    name: 'ClubDetail',
    component: () => import('@/views/club/ClubDetailView.vue'),
  },
  {
    path: '/pois',
    name: 'POIs',
    component: () => import('@/views/poi/POIListView.vue'),
  },
  {
    path: '/pois/:id',
    name: 'POIDetail',
    component: () => import('@/views/poi/POIDetailView.vue'),
  },
  {
    path: '/guides',
    name: 'Guides',
    component: () => import('@/views/guide/GuideView.vue'),
  },
  {
    path: '/guides/:id',
    name: 'GuideDetail',
    component: () => import('@/views/guide/GuideDetailView.vue'),
  },
  {
    path: '/safety',
    name: 'Safety',
    component: () => import('@/views/guide/SafetyTipsView.vue'),
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/courses' },
      { path: 'courses', name: 'AdminCourses', component: () => import('@/views/admin/CoursesManage.vue') },
      { path: 'clubs', name: 'AdminClubs', component: () => import('@/views/admin/ClubsManage.vue') },
      { path: 'pois', name: 'AdminPOIs', component: () => import('@/views/admin/POIsManage.vue') },
      { path: 'corrections', name: 'AdminCorrections', component: () => import('@/views/admin/CorrectionsManage.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/UsersManage.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (user.role !== 'ADMIN') {
        next('/home')
        return
      }
    } catch {
      next('/home')
      return
    }
  }

  next()
})

export default router
