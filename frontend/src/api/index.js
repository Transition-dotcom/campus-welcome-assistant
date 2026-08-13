/**
 * API 接口封装。按模块组织。
 */
import request from '@/utils/request'

// ──── 用户 ────
export const userApi = {
  register: (data) => request.post('/user/register', data),
  login: (data) => request.post('/user/login', data),
  refreshToken: (data) => request.post('/user/refresh', data),
  getProfile: () => request.get('/user/profile'),
  updateProfile: (data) => request.put('/user/profile', data),
}

// ──── 课程 ────
export const courseApi = {
  getList: (params) => request.get('/courses', { params }),
  getDetail: (id) => request.get(`/courses/${id}`),
  getReviews: (courseId, params) => request.get(`/courses/${courseId}/reviews`, { params }),
  createReview: (courseId, data) => request.post(`/courses/${courseId}/reviews`, data),
  toggleLike: (reviewId) => request.post(`/courses/reviews/${reviewId}/like`),
  getComments: (reviewId, params) => request.get(`/courses/reviews/${reviewId}/comments`, { params }),
  createComment: (reviewId, data) => request.post(`/courses/reviews/${reviewId}/comments`, data),
  toggleFavorite: (reviewId) => request.post(`/courses/reviews/${reviewId}/favorite`),
  getMyFavorites: (params) => request.get('/courses/favorites/my', { params }),
  reportReview: (reviewId, data) => request.post(`/courses/reviews/${reviewId}/report`, data),
}

// ──── 社团 ────
export const clubApi = {
  getList: (params) => request.get('/clubs', { params }),
  getDetail: (id) => request.get(`/clubs/${id}`),
  getEvents: (clubId) => request.get(`/clubs/${clubId}/events`),
  getUpcomingEvents: () => request.get('/clubs/events/upcoming'),
}

// ──── 校园导览 ────
export const poiApi = {
  getList: (params) => request.get('/pois', { params }),
  getDetail: (id) => request.get(`/pois/${id}`),
  getRoutes: (params) => request.get('/pois/routes/list', { params }),
  submitCorrection: (data) => request.post('/pois/correction', data),
}

// ──── 攻略 & 首页 ────
export const guideApi = {
  getGuides: (params) => request.get('/guides', { params }),
  getGuideDetail: (id) => request.get(`/guides/${id}`),
  getTasks: () => request.get('/tasks/my'),
  checkinTask: (taskId) => request.post(`/tasks/${taskId}/checkin`),
  getSafetyTips: (params) => request.get('/safety-tips', { params }),
  getDashboard: () => request.get('/dashboard'),
  search: (keyword, page = 1, pageSize = 20, signal) => request.get('/search', { params: { keyword, page, page_size: pageSize }, signal }),
}

// ──── 管理后台 ────
export const adminApi = {
  // 课程
  createCourse: (data) => request.post('/admin/courses', data),
  updateCourse: (id, data) => request.put(`/admin/courses/${id}`, data),
  deleteCourse: (id) => request.delete(`/admin/courses/${id}`),
  // 社团
  createClub: (data) => request.post('/admin/clubs', data),
  updateClub: (id, data) => request.put(`/admin/clubs/${id}`, data),
  deleteClub: (id) => request.delete(`/admin/clubs/${id}`),
  createEvent: (clubId, data) => request.post(`/admin/clubs/${clubId}/events`, data),
  // POI
  createPoi: (data) => request.post('/admin/pois', data),
  updatePoi: (id, data) => request.put(`/admin/pois/${id}`, data),
  deletePoi: (id) => request.delete(`/admin/pois/${id}`),
  createRoute: (data) => request.post('/admin/pois/routes', data),
  // 纠错
  getCorrections: (params) => request.get('/admin/corrections', { params }),
  resolveCorrection: (id) => request.put(`/admin/corrections/${id}/resolve`),
  // 举报审核
  getReports: (params) => request.get('/admin/reports', { params }),
  resolveReport: (id, action) => request.post(`/admin/reports/${id}/resolve`, { action }),
  // 攻略
  getGuides: (params) => request.get('/admin/guides', { params }),
  createGuide: (data) => request.post('/admin/guides', data),
  updateGuide: (id, data) => request.put(`/admin/guides/${id}`, data),
  deleteGuide: (id) => request.delete(`/admin/guides/${id}`),
  // 任务
  getTasks: () => request.get('/admin/tasks'),
  createTask: (data) => request.post('/admin/tasks', data),
  updateTask: (id, data) => request.put(`/admin/tasks/${id}`, data),
  deleteTask: (id) => request.delete(`/admin/tasks/${id}`),
  // 用户
  getUsers: () => request.get('/admin/users'),
  updateUserStatus: (id, status) => request.put(`/admin/users/${id}/status`, { status }),
}
