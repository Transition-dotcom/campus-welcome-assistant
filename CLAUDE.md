# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

东北大学软件学院新生综合服务平台（大学萌新领航站）。基于浑南校区公开信息与软件学院培养方案定制，提供选课评价、GPA 计算、社团导航、校园导览、办事攻略、新生任务打卡、安全防线等功能。

## 常用命令

### 数据库初始化

```bash
mysql -u root -proot --default-character-set=utf8mb4 < backend/init.sql
```

必须加 `--default-character-set=utf8mb4`，含中文的 INSERT 会报编码错误。种子数据包含 25 门课程、8 个社团、14 个地标、攻略、任务、安全提示等。

### 后端（端口 8080）

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate  /  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

- 健康检查: `GET http://localhost:8080/`
- Swagger 文档: `http://localhost:8080/docs`

### 前端（端口 5173）

```bash
cd frontend
npm install
npm run dev          # 开发服务器
npm run build        # 生产构建
npm run preview      # 预览生产构建
```

浏览器访问 `http://localhost:5173`，Vite 已配置 `/api` 代理到后端 8080。

### 默认账号

管理员 `admin` / `admin123`（普通用户可自行注册）。

## 技术栈

- **后端**: Python 3.9+ · FastAPI · SQLAlchemy 2.0 · PyMySQL · MySQL 8 · JWT (python-jose) · bcrypt (passlib)
- **前端**: Vue 3 (Composition API) · Vite 5 · Element Plus · Pinia · Axios · Vue Router 4 (懒加载)

## 架构

### 后端分层 (backend/app/)

```
routers/     ← API 路由层：参数校验、依赖注入，委托 service 处理
services/    ← 业务逻辑层：所有 SQLAlchemy 查询和业务规则
models/      ← SQLAlchemy ORM 模型
schemas/     ← Pydantic 请求/响应模型
middleware/  ← JWT 鉴权依赖（Depends 链）
utils/       ← 密码哈希、JWT 编解码工具
```

**路由注册**在 `main.py` 中：user / course / club / poi / guide / admin 六个模块，统一挂载。应用启动时执行 `Base.metadata.create_all()` 自动建表（生产环境应使用 Alembic）。

**鉴权链**（`middleware/auth.py`）：
- `get_current_user` — 必需 Bearer Token，返回 `{user_id, role}`，失败 → 401
- `get_optional_user` — 可选鉴权，无 token 返回 None，用于"未登录可访问、登录后个性化"接口
- `get_admin_user` — 在 `get_current_user` 基础上检查 `role == "ADMIN"`，非管理员 → 403

**配置** (`config.py`)：使用 pydantic-settings，所有配置项有默认值，可通过 `.env` 文件或环境变量覆盖。关键配置项：`DB_HOST/PORT/USER/PASSWORD/NAME`、`JWT_SECRET`、`CORS_ORIGINS`。

### 前端分层 (frontend/src/)

```
views/       ← 页面组件，按模块分目录：home/course/club/poi/guide/user/admin/search
router/      ← Vue Router 配置，含路由守卫（requiresAuth / requiresAdmin）
stores/      ← Pinia auth store：登录状态、token 管理、localStorage 持久化
api/         ← API 封装，按模块组织（userApi/courseApi/clubApi/poiApi/guideApi/adminApi）
utils/       ← Axios 实例封装：baseURL=/api、Token 自动注入、401 自动刷新、错误提示
```

**路由守卫** (`router/index.js`)：
- `meta.requiresAuth` → 无 token 跳转 `/login`
- `meta.requiresAdmin` → 从 localStorage 读取 user 对象，`role !== 'ADMIN'` 跳转 `/home`

**Axios 拦截器** (`utils/request.js`)：
- 请求拦截器自动从 localStorage 注入 `Authorization: Bearer <token>`
- 响应拦截器遇到 401 自动尝试 refresh_token 刷新，刷新失败跳登录；并发刷新排队处理

### 核心数据模型

**课程评价**：Course → CourseReview → ReviewComment（楼中楼，parent_id）/ ReviewLike（唯一约束 review_id+user_id）/ ReviewReport → 管理员审核

**社团导航**：Club → ClubEvent（近期活动时间线）

**校园导览**：POI（地标）→ POIRoute（路径指引）/ POICorrection（用户纠错 → 管理员审核）

**其他**：User（含 role 字段区分 ADMIN/USER）、Guide（办事攻略）、UserTask + TaskCheckin（新生任务打卡）、SafetyTip（安全防线）

### 前端路由与页面映射

| 路径 | 页面 | 认证要求 |
|------|------|---------|
| `/home` | 首页仪表盘 | 否 |
| `/courses` / `/courses/:id` | 课程列表/详情 | 否 |
| `/clubs` / `/clubs/:id` | 社团列表/详情 | 否 |
| `/pois` / `/pois/:id` | 地标列表/详情 | 否 |
| `/guides` / `/guides/:id` | 攻略列表/详情 | 否 |
| `/gpa` | GPA 计算器 | 否 |
| `/safety` | 安全防线详情 | 否 |
| `/tasks` | 新生任务清单 | 是 |
| `/favorites` | 我的收藏 | 是 |
| `/profile` | 个人中心 | 是 |
| `/login` / `/register` | 登录/注册 | 否 |
| `/search` | 搜索 | 否 |
| `/admin/*` | 管理后台（子路由） | 是 + ADMIN |

### 页面到后端 API 的对应关系

前端首页 (`HomeView.vue`) 同时调用 `guideApi.getDashboard()`、`guideApi.getTasks()`、`clubApi.getUpcomingEvents()`、`guideApi.getSafetyTips()` 组装仪表盘。`getDashboard` 需通过 `get_optional_user` 注入当前用户以返回个性化任务进度。

管理后台中，纠错审核 (`CorrectionsManage.vue`) 调用 `adminApi.getCorrections()` + `resolveCorrection(id)`，纠错由用户在 POI 详情页通过 `poiApi.submitCorrection()` 提交。
