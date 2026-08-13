# API 接口文档

> 项目：大学萌新领航站（东北大学软件学院 · 校园新生服务平台）
> API 版本：2.1.0　后端：FastAPI（Python 3.9+，端口 8080）
> 文档来源：由 `backend/app/main.py` 实际导出 `app.openapi()` 生成，并结合 `routers/`、`schemas/`、`services/` 源码核对认证要求与错误信息，**与代码一致**。

---

## 1. 全局说明

### 1.1 基本信息

| 项目 | 说明 |
|------|------|
| Swagger 文档 | <http://localhost:8080/docs>（启动后端后可直接在线调试） |
| API 前缀 | `/api`（仅健康检查 `GET /`、`GET /health` 不带前缀） |
| 数据格式 | JSON；时间字段为 ISO 8601（`string（date-time）`，UTC） |
| 接口总数 | 58 个，按 tag 分为 7 组：用户中心 / 课程评价 / 社团导航 / 校园导览 / 攻略 & 首页 / 管理后台 / 系统 |

### 1.2 统一响应格式

**分页响应** `PageResponse`（所有分页接口统一）：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 当前页数据 |
| total | integer | 符合条件的总条数 |
| page | integer | 当前页码（从 1 开始） |
| page_size | integer | 每页条数 |
| total_pages | integer | 总页数 |

**消息响应**（写操作常用）：`{"message": "..."}`，如「已删除」「已处理」「举报已提交，管理员将尽快处理」。

**错误响应**：所有错误统一为 `{"detail": "错误说明"}`：

```json
{ "detail": "课程不存在" }
```

### 1.3 鉴权说明

- 请求头：`Authorization: Bearer <access_token>`；
- **access_token**：有效期 2 小时（`access_token_expire_minutes=120`），payload 含 `sub`（用户 ID）、`role`、`type=access`、`ver`、`exp`；
- **refresh_token**：有效期 7 天（`refresh_token_expire_days=7`），仅用于 `POST /api/user/refresh` 换新；
- **token 轮换撤销**：每次刷新成功后 `user.token_version +1` 并签发新 token 对，旧 refresh_token 立即失效；收到版本不匹配的 token（疑似复用/被盗）返回 401「refresh_token 已失效，请重新登录」；
- 鉴权依赖每请求**回查数据库**：用户被禁用或删除后，其已签发的 token 立即失效；角色以数据库为准；
- 角色：`USER`（普通用户）/ `ADMIN`（管理员）。管理后台接口要求 ADMIN，否则 403「需要管理员权限」；
- 可选鉴权：`GET /api/dashboard` 未登录可访问，携带有效 token 时任务进度按当前用户统计。

### 1.4 限流说明

| 接口 | 限额 | 超限响应 |
|------|------|---------|
| POST /api/user/login | 10 次/分钟/IP | 429「请求过于频繁，请稍后再试」 |
| POST /api/user/register | 10 次/分钟/IP（与登录独立计数） | 同上 |

限流基于内存滑动窗口（`middleware/rate_limit.py`），仅适用于单机部署。

### 1.5 通用错误码

| 状态码 | 含义 | 来源 |
|--------|------|------|
| 400 | 业务规则冲突 / 数据冲突或重复 | 服务层校验；全局 IntegrityError/DataError 处理器 |
| 401 | 未登录 / Token 无效或已过期 / 凭证错误 | `get_current_user`、login、refresh |
| 403 | 账号被禁用 / 需要管理员权限 | login、`get_admin_user` |
| 404 | 资源不存在（含已软删除资源） | 各服务层 |
| 422 | 请求参数校验失败（字段缺失/越界/格式错误） | FastAPI/Pydantic 自动校验 |
| 429 | 触发限流 | `rate_limit.py` |
| 500 | 服务器内部错误（细节只记日志） | 全局 SQLAlchemy 异常处理器 |

### 1.6 默认账号

| 角色 | 昵称 | 密码 | 说明 |
|------|------|------|------|
| 管理员 | `admin` | `admin123` | 可访问全部管理后台接口 |

普通用户通过 `POST /api/user/register` 自行注册（注册即登录，直接返回 token）。

---

## 2. 接口分组

- 用户中心（5 个）：注册 / 登录 / 刷新 Token / 个人信息
- 课程评价（10 个）：课程 / 评价 / 点赞 / 评论 / 收藏 / 举报
- 社团导航（4 个）：社团列表 / 详情 / 活动
- 校园导览（4 个）：地标 / 路径 / 纠错
- 攻略 & 首页（8 个）：攻略 / 任务打卡 / 安全防线 / 仪表盘 / 全局搜索
- 管理后台（25 个）：课程 / 社团 / 地标 / 纠错 / 用户 / 举报 / 攻略 / 任务管理
- 系统（2 个）：健康检查

---

## 3. 用户中心

### 1. POST `/api/user/register` 用户注册

**功能**：注册新用户，成功后直接返回 token（注册即登录）。

**认证**：公开（限流：10 次/分钟/IP）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `nickname` | string | 是 | 昵称；2-50 字符 |
| `password` | string | 是 | 密码（6-72位）；6-72 字符 |
| `student_id` | string（可空） | 否 | 学号（可选） |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `user.id` | integer |  |
| `user.nickname` | string |  |
| `user.student_id` | string（可空） |  |
| `user.college` | string（可空） |  |
| `user.major` | string（可空） |  |
| `user.grade` | string（可空） |  |
| `user.avatar_url` | string（可空） |  |
| `user.role` | string |  |
| `user.created_at` | string（date-time） |  |
| `tokens.access_token` | string |  |
| `tokens.refresh_token` | string |  |
| `tokens.token_type` | string |  |

**主要错误**：400 昵称已被注册 / 学号已被注册；422 参数校验失败（昵称 2-50 字符、密码 6-72 位）；429 触发限流

---

### 2. POST `/api/user/login` 用户登录

**功能**：使用昵称和密码登录，返回 access_token 和 refresh_token。

**认证**：公开（限流：10 次/分钟/IP）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `nickname` | string | 是 | 昵称；2-50 字符 |
| `password` | string | 是 | 密码；6-72 字符 |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `user.id` | integer |  |
| `user.nickname` | string |  |
| `user.student_id` | string（可空） |  |
| `user.college` | string（可空） |  |
| `user.major` | string（可空） |  |
| `user.grade` | string（可空） |  |
| `user.avatar_url` | string（可空） |  |
| `user.role` | string |  |
| `user.created_at` | string（date-time） |  |
| `tokens.access_token` | string |  |
| `tokens.refresh_token` | string |  |
| `tokens.token_type` | string |  |

**主要错误**：401 昵称或密码错误；403 账号已被禁用；429 触发限流

---

### 3. POST `/api/user/refresh` 刷新 Token

**功能**：使用 refresh_token 换取新的 token 对。

**认证**：公开（需携带 refresh_token，无需 access_token）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `refresh_token` | string | 是 | refresh_token |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | string |  |
| `refresh_token` | string |  |
| `token_type` | string |  |

**主要错误**：401 refresh_token 无效或已过期 / refresh_token 已失效，请重新登录（版本不匹配，疑似复用）/ 用户不存在或已禁用

---

### 4. GET `/api/user/profile` 获取个人信息

**功能**：获取当前登录用户的个人信息。

**认证**：登录（Bearer access_token）

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `nickname` | string |  |
| `student_id` | string（可空） |  |
| `college` | string（可空） |  |
| `major` | string（可空） |  |
| `grade` | string（可空） |  |
| `avatar_url` | string（可空） |  |
| `role` | string |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 Token 无效或已过期 / 用户不存在或已被禁用；404 用户不存在

---

### 5. PUT `/api/user/profile` 修改个人信息

**功能**：修改当前登录用户的个人信息（仅更新提交的字段）。

**认证**：登录（Bearer access_token）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `nickname` | string（可空） | 否 |  |
| `college` | string（可空） | 否 |  |
| `major` | string（可空） | 否 |  |
| `grade` | string（可空） | 否 |  |
| `avatar_url` | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `nickname` | string |  |
| `student_id` | string（可空） |  |
| `college` | string（可空） |  |
| `major` | string（可空） |  |
| `grade` | string（可空） |  |
| `avatar_url` | string（可空） |  |
| `role` | string |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 Token 无效或已过期 / 用户不存在或已被禁用；404 用户不存在

---


## 4. 课程评价

### 1. GET `/api/courses` 课程列表

**功能**：分页查询课程，支持按学院和类别筛选。

**认证**：公开

**请求参数（4 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~50；默认 10 |
| `college` | query | string（可空） | 否 |  |
| `category` | query | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].name` | string |  |
| `items[元素].teacher` | string（可空） |  |
| `items[元素].college` | string（可空） |  |
| `items[元素].category` | string（可空） |  |
| `items[元素].credit` | number（可空） |  |
| `items[元素].id` | integer |  |
| `items[元素].status` | integer |  |
| `items[元素].review_count` | integer |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：422 参数越界（page ≥ 1、page_size 1-50）

---

### 2. GET `/api/courses/{course_id}` 课程详情

**功能**：查询课程详情（含评价数）。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `course_id` | path | integer | 是 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `teacher` | string（可空） |  |
| `college` | string（可空） |  |
| `category` | string（可空） |  |
| `credit` | number（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `review_count` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：404 课程不存在

---

### 3. GET `/api/courses/{course_id}/reviews` 评价列表

**功能**：分页查询课程评价，支持按时间/点赞排序。

**认证**：公开

**请求参数（4 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `course_id` | path | integer | 是 |  |
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~50；默认 10 |
| `sort` | query | string | 否 | 匹配: `^(time/like)$`；默认 time |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].id` | integer |  |
| `items[元素].course_id` | integer |  |
| `items[元素].user_id` | integer（可空） |  |
| `items[元素].nickname` | string |  |
| `items[元素].is_anonymous` | boolean |  |
| `items[元素].difficulty_rating` | integer |  |
| `items[元素].score_rating` | integer |  |
| `items[元素].content` | string |  |
| `items[元素].like_count` | integer |  |
| `items[元素].is_liked` | boolean |  |
| `items[元素].is_favorited` | boolean |  |
| `items[元素].status` | integer |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：404 课程不存在；422 sort 仅支持 time/like

---

### 4. POST `/api/courses/{course_id}/reviews` 发表评价

**功能**：对课程发表评价（需登录）。

**认证**：登录（Bearer access_token）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `course_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `difficulty_rating` | integer | 是 | 难度评分 1-5；范围 1.0~5.0 |
| `score_rating` | integer | 是 | 给分评分 1-5；范围 1.0~5.0 |
| `content` | string | 是 | 评价正文；10-5000 字符 |
| `is_anonymous` | boolean | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `course_id` | integer |  |
| `user_id` | integer（可空） |  |
| `nickname` | string |  |
| `is_anonymous` | boolean |  |
| `difficulty_rating` | integer |  |
| `score_rating` | integer |  |
| `content` | string |  |
| `like_count` | integer |  |
| `is_liked` | boolean |  |
| `is_favorited` | boolean |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；404 课程不存在；422 评分须 1-5、正文 10-5000 字

---

### 5. POST `/api/courses/reviews/{review_id}/like` 点赞/取消点赞

**功能**：对评价点赞，再次调用则取消点赞（幂等）。

**认证**：登录（Bearer access_token）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `review_id` | path | integer | 是 |  |

**成功响应 200**：

`{"is_liked": true/false, "like_count": 12}` — 返回点赞/取消点赞后的最新状态与计数。

**主要错误**：401 未登录或 Token 无效；404 评价不存在；400 请勿重复点赞

---

### 6. GET `/api/courses/reviews/{review_id}/comments` 评论列表

**功能**：获取评价的评论列表（含楼中楼）。

**认证**：公开

**请求参数（3 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `review_id` | path | integer | 是 |  |
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~50；默认 20 |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].id` | integer |  |
| `items[元素].review_id` | integer |  |
| `items[元素].user_id` | integer |  |
| `items[元素].nickname` | string |  |
| `items[元素].parent_id` | integer（可空） |  |
| `items[元素].content` | string |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：404 评价不存在

---

### 7. POST `/api/courses/reviews/{review_id}/comments` 发表评论

**功能**：对评价发表评论（需登录），支持回复某条评论（parent_id）。

**认证**：登录（Bearer access_token）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `review_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | 是 | 1-2000 字符 |
| `parent_id` | integer（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `review_id` | integer |  |
| `user_id` | integer |  |
| `nickname` | string |  |
| `parent_id` | integer（可空） |  |
| `content` | string |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；404 评价不存在 / 回复的评论不存在；400 不能跨评价回复评论 / 最多支持两级评论，不能回复二级评论

---

### 8. POST `/api/courses/reviews/{review_id}/favorite` 收藏/取消收藏

**功能**：收藏评价，再次调用则取消收藏（幂等）。

**认证**：登录（Bearer access_token）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `review_id` | path | integer | 是 |  |

**成功响应 200**：

`{"is_favorited": true/false}` — 返回收藏/取消收藏后的状态。

**主要错误**：401 未登录或 Token 无效；404 评价不存在；400 请勿重复收藏

---

### 9. GET `/api/courses/favorites/my` 我的收藏

**功能**：获取当前用户的收藏列表。

**认证**：登录（Bearer access_token）

**请求参数（2 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~50；默认 10 |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].id` | integer |  |
| `items[元素].course_id` | integer |  |
| `items[元素].user_id` | integer（可空） |  |
| `items[元素].nickname` | string |  |
| `items[元素].is_anonymous` | boolean |  |
| `items[元素].difficulty_rating` | integer |  |
| `items[元素].score_rating` | integer |  |
| `items[元素].content` | string |  |
| `items[元素].like_count` | integer |  |
| `items[元素].is_liked` | boolean |  |
| `items[元素].is_favorited` | boolean |  |
| `items[元素].status` | integer |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：401 未登录或 Token 无效

---

### 10. POST `/api/courses/reviews/{review_id}/report` 举报评价

**功能**：举报不当评价（需登录）。

**认证**：登录（Bearer access_token）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `review_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 是 | 5-500 字符 |

**成功响应 200**：

`{"message": "举报已提交，管理员将尽快处理"}`。

**主要错误**：401 未登录或 Token 无效；404 评价不存在；400 已举报，请等待处理

---


## 5. 社团导航

### 1. GET `/api/clubs` 社团列表

**功能**：分页查询社团，支持分类筛选和名称搜索。

**认证**：公开

**请求参数（4 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~50；默认 10 |
| `category` | query | string（可空） | 否 |  |
| `keyword` | query | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].name` | string |  |
| `items[元素].category` | string |  |
| `items[元素].logo_url` | string（可空） |  |
| `items[元素].description` | string（可空） |  |
| `items[元素].activity_frequency` | string（可空） |  |
| `items[元素].requirements` | string（可空） |  |
| `items[元素].tips` | string（可空） |  |
| `items[元素].contact` | string（可空） |  |
| `items[元素].id` | integer |  |
| `items[元素].status` | integer |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：422 参数越界（page_size 1-50）

---

### 2. GET `/api/clubs/{club_id}` 社团详情

**功能**：查询社团详细信息。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `club_id` | path | integer | 是 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `category` | string |  |
| `logo_url` | string（可空） |  |
| `description` | string（可空） |  |
| `activity_frequency` | string（可空） |  |
| `requirements` | string（可空） |  |
| `tips` | string（可空） |  |
| `contact` | string（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：404 社团不存在

---

### 3. GET `/api/clubs/{club_id}/events` 社团活动

**功能**：查询社团的近期活动。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `club_id` | path | integer | 是 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].title` | string |  |
| `[元素].event_type` | string（可空） |  |
| `[元素].event_time` | string（date-time） |  |
| `[元素].location` | string（可空） |  |
| `[元素].description` | string（可空） |  |
| `[元素].id` | integer |  |
| `[元素].club_id` | integer |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：只返回未过期活动；社团已下架时活动不展示

---

### 4. GET `/api/clubs/events/upcoming` 近期活动

**功能**：查询全校近期社团活动（未过期）。

**认证**：公开

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].title` | string |  |
| `[元素].event_type` | string（可空） |  |
| `[元素].event_time` | string（date-time） |  |
| `[元素].location` | string（可空） |  |
| `[元素].description` | string（可空） |  |
| `[元素].id` | integer |  |
| `[元素].club_id` | integer |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：无

---


## 6. 校园导览

### 1. GET `/api/pois` 地标列表

**功能**：分页查询校园地标，支持分类和搜索。

**认证**：公开

**请求参数（4 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~50；默认 20 |
| `category` | query | string（可空） | 否 |  |
| `keyword` | query | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].name` | string |  |
| `items[元素].category` | string |  |
| `items[元素].description` | string（可空） |  |
| `items[元素].photo_url` | string（可空） |  |
| `items[元素].open_hours` | string（可空） |  |
| `items[元素].floor_info` | string（可空） |  |
| `items[元素].tips` | string（可空） |  |
| `items[元素].lat` | number（可空） |  |
| `items[元素].lng` | number（可空） |  |
| `items[元素].id` | integer |  |
| `items[元素].status` | integer |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：422 参数越界（page_size 1-50）

---

### 2. GET `/api/pois/{poi_id}` 地标详情

**功能**：查询地标详细信息。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `poi_id` | path | integer | 是 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `category` | string |  |
| `description` | string（可空） |  |
| `photo_url` | string（可空） |  |
| `open_hours` | string（可空） |  |
| `floor_info` | string（可空） |  |
| `tips` | string（可空） |  |
| `lat` | number（可空） |  |
| `lng` | number（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：404 地标不存在（已下架同样 404）

---

### 3. GET `/api/pois/routes/list` 路径列表

**功能**：查询路径指引，可按起点 POI 筛选。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `poi_id` | query | integer（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].from_poi_id` | integer |  |
| `[元素].to_poi_id` | integer |  |
| `[元素].description` | string |  |
| `[元素].estimated_minutes` | integer（可空） |  |
| `[元素].id` | integer |  |
| `[元素].from_poi_name` | string（可空） |  |
| `[元素].to_poi_name` | string（可空） |  |

**主要错误**：无

---

### 4. POST `/api/pois/correction` 提交纠错

**功能**：登录用户提交地标信息纠错。

**认证**：登录（Bearer access_token）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `poi_id` | integer | 是 |  |
| `content` | string | 是 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `poi_id` | integer |  |
| `user_id` | integer |  |
| `content` | string |  |
| `status` | string |  |
| `created_at` | string（date-time） |  |
| `poi_name` | string（可空） |  |

**主要错误**：401 未登录或 Token 无效；404 地标不存在

---


## 7. 攻略 & 首页

### 1. GET `/api/guides` 攻略列表

**功能**：查询办事流程/生活指南/学习攻略。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `category` | query | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].id` | integer |  |
| `[元素].title` | string |  |
| `[元素].category` | string |  |
| `[元素].summary` | string（可空） |  |
| `[元素].content` | array（可空） |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：无

---

### 2. GET `/api/guides/{guide_id}` 攻略详情

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `guide_id` | path | integer | 是 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `title` | string |  |
| `category` | string |  |
| `summary` | string（可空） |  |
| `content` | array（可空） |  |
| `created_at` | string（date-time） |  |

**主要错误**：404 攻略不存在

---

### 3. GET `/api/tasks` 新生任务列表

**功能**：获取所有新生任务（不含打卡状态）。

**认证**：公开（不含打卡状态）

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].id` | integer |  |
| `[元素].title` | string |  |
| `[元素].description` | string（可空） |  |
| `[元素].icon` | string（可空） |  |
| `[元素].sort_order` | integer |  |
| `[元素].badge_level` | string（可空） |  |
| `[元素].is_checked` | boolean |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：无

---

### 4. GET `/api/tasks/my` 我的任务列表

**功能**：获取新生任务列表（含当前用户打卡状态）。

**认证**：登录（Bearer access_token，含当前用户打卡状态）

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].id` | integer |  |
| `[元素].title` | string |  |
| `[元素].description` | string（可空） |  |
| `[元素].icon` | string（可空） |  |
| `[元素].sort_order` | integer |  |
| `[元素].badge_level` | string（可空） |  |
| `[元素].is_checked` | boolean |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效

---

### 5. POST `/api/tasks/{task_id}/checkin` 打卡任务

**功能**：对指定任务打卡（需登录）。

**认证**：登录（Bearer access_token）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `task_id` | path | integer | 是 |  |

**成功响应 200**：

`{"completed": 3, "total": 12, "badge": "bronze"|"silver"|"gold"|"diamond"|null}` — 打卡后的完成进度与当前勋章等级（3 铜 / 5 银 / 10 金 / 全部钻石）。

**主要错误**：401 未登录或 Token 无效；404 任务不存在；400 已完成打卡

---

### 6. GET `/api/safety-tips` 安全防线

**功能**：查询安全提醒，pinned_only=true 只返回置顶内容。

**认证**：公开

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `pinned_only` | query | boolean | 否 | 默认 False |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].id` | integer |  |
| `[元素].title` | string |  |
| `[元素].content` | string |  |
| `[元素].image_url` | string（可空） |  |
| `[元素].sort_order` | integer |  |
| `[元素].is_pinned` | boolean |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：无

---

### 7. GET `/api/dashboard` 首页聚合

**功能**：首页仪表盘：聚合任务进度、热门评价、近期活动、安全提醒。登录时任务进度按当前用户统计。

**认证**：公开（可选登录：携带有效 Token 时任务进度按当前用户统计）

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_progress` | object |  |
| `hot_reviews` | array |  |
| `upcoming_events` | array |  |
| `pinned_tips` | array |  |

**补充说明**：`task_progress` = `{"completed": n, "total": n}`（未登录时 completed 恒为 0）；`hot_reviews[]` 元素 = `{id, course_id, nickname, difficulty_rating, score_rating, content（截断 150 字）, like_count, created_at}`（点赞数最多的 3 条）；`upcoming_events[]` 元素 = `{id, club_id, title, event_type, event_time, location}`（未来最近的 3 条，只含未下架社团）；`pinned_tips[]` 元素同 SafetyTipResponse（`id/title/content/image_url/sort_order/is_pinned/created_at`）。

**主要错误**：无

---

### 8. GET `/api/search` 全局搜索

**功能**：跨模块搜索课程、社团、地标、攻略。

**认证**：公开

**请求参数（3 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `keyword` | query | string | 是 | 2-100 字符 |
| `page` | query | integer | 否 | 页码；最小 1；默认 1 |
| `page_size` | query | integer | 否 | 每页条数；范围 1~100；默认 20 |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items` | array |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**补充说明**：`items[]` 元素 = `{type: "course"|"club"|"poi"|"guide", id, title}`；支持课程缩写扩展（如「高数」→「高等数学」）。

**主要错误**：422 keyword 长度 2-100 字符

---


## 8. 管理后台

### 1. POST `/api/admin/courses` 创建课程

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 |  |
| `teacher` | string（可空） | 否 |  |
| `college` | string（可空） | 否 |  |
| `category` | string（可空） | 否 |  |
| `credit` | number（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `teacher` | string（可空） |  |
| `college` | string（可空） |  |
| `category` | string（可空） |  |
| `credit` | number（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `review_count` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 2. PUT `/api/admin/courses/{course_id}` 更新课程

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `course_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 |  |
| `teacher` | string（可空） | 否 |  |
| `college` | string（可空） | 否 |  |
| `category` | string（可空） | 否 |  |
| `credit` | number（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `teacher` | string（可空） |  |
| `college` | string（可空） |  |
| `category` | string（可空） |  |
| `credit` | number（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `review_count` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 课程不存在

---

### 3. DELETE `/api/admin/courses/{course_id}` 删除课程

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `course_id` | path | integer | 是 |  |

**成功响应 200**：

`{"message": "已删除"}`（软删除，status 置 0）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 课程不存在（软删除，status 置 0）

---

### 4. POST `/api/admin/clubs` 创建社团

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 |  |
| `category` | string | 是 |  |
| `logo_url` | string（可空） | 否 |  |
| `description` | string（可空） | 否 |  |
| `activity_frequency` | string（可空） | 否 |  |
| `requirements` | string（可空） | 否 |  |
| `tips` | string（可空） | 否 |  |
| `contact` | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `category` | string |  |
| `logo_url` | string（可空） |  |
| `description` | string（可空） |  |
| `activity_frequency` | string（可空） |  |
| `requirements` | string（可空） |  |
| `tips` | string（可空） |  |
| `contact` | string（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 5. PUT `/api/admin/clubs/{club_id}` 更新社团

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `club_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 |  |
| `category` | string | 是 |  |
| `logo_url` | string（可空） | 否 |  |
| `description` | string（可空） | 否 |  |
| `activity_frequency` | string（可空） | 否 |  |
| `requirements` | string（可空） | 否 |  |
| `tips` | string（可空） | 否 |  |
| `contact` | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `category` | string |  |
| `logo_url` | string（可空） |  |
| `description` | string（可空） |  |
| `activity_frequency` | string（可空） |  |
| `requirements` | string（可空） |  |
| `tips` | string（可空） |  |
| `contact` | string（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 社团不存在

---

### 6. DELETE `/api/admin/clubs/{club_id}` 删除社团

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `club_id` | path | integer | 是 |  |

**成功响应 200**：

`{"message": "已删除"}`（软删除，status 置 0）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 社团不存在（软删除，status 置 0）

---

### 7. POST `/api/admin/clubs/{club_id}/events` 创建社团活动

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `club_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 |  |
| `event_type` | string（可空） | 否 |  |
| `event_time` | string（date-time） | 是 |  |
| `location` | string（可空） | 否 |  |
| `description` | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string |  |
| `event_type` | string（可空） |  |
| `event_time` | string（date-time） |  |
| `location` | string（可空） |  |
| `description` | string（可空） |  |
| `id` | integer |  |
| `club_id` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 社团不存在

---

### 8. POST `/api/admin/pois` 创建地标

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 |  |
| `category` | string | 是 |  |
| `description` | string（可空） | 否 |  |
| `photo_url` | string（可空） | 否 |  |
| `open_hours` | string（可空） | 否 |  |
| `floor_info` | string（可空） | 否 |  |
| `tips` | string（可空） | 否 |  |
| `lat` | number（可空） | 否 |  |
| `lng` | number（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `category` | string |  |
| `description` | string（可空） |  |
| `photo_url` | string（可空） |  |
| `open_hours` | string（可空） |  |
| `floor_info` | string（可空） |  |
| `tips` | string（可空） |  |
| `lat` | number（可空） |  |
| `lng` | number（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 9. PUT `/api/admin/pois/{poi_id}` 更新地标

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `poi_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 |  |
| `category` | string | 是 |  |
| `description` | string（可空） | 否 |  |
| `photo_url` | string（可空） | 否 |  |
| `open_hours` | string（可空） | 否 |  |
| `floor_info` | string（可空） | 否 |  |
| `tips` | string（可空） | 否 |  |
| `lat` | number（可空） | 否 |  |
| `lng` | number（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string |  |
| `category` | string |  |
| `description` | string（可空） |  |
| `photo_url` | string（可空） |  |
| `open_hours` | string（可空） |  |
| `floor_info` | string（可空） |  |
| `tips` | string（可空） |  |
| `lat` | number（可空） |  |
| `lng` | number（可空） |  |
| `id` | integer |  |
| `status` | integer |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 地标不存在

---

### 10. DELETE `/api/admin/pois/{poi_id}` 删除地标

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `poi_id` | path | integer | 是 |  |

**成功响应 200**：

`{"message": "已删除"}`（软删除，status 置 0，关联纠错/路径仍可读）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 地标不存在（软删除，status 置 0）

---

### 11. POST `/api/admin/pois/routes` 创建路径

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `from_poi_id` | integer | 是 |  |
| `to_poi_id` | integer | 是 |  |
| `description` | string | 是 |  |
| `estimated_minutes` | integer（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `from_poi_id` | integer |  |
| `to_poi_id` | integer |  |
| `description` | string |  |
| `estimated_minutes` | integer（可空） |  |
| `id` | integer |  |
| `from_poi_name` | string（可空） |  |
| `to_poi_name` | string（可空） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 12. GET `/api/admin/corrections` 纠错列表

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `status` | query | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].id` | integer |  |
| `[元素].poi_id` | integer |  |
| `[元素].user_id` | integer |  |
| `[元素].content` | string |  |
| `[元素].status` | string |  |
| `[元素].created_at` | string（date-time） |  |
| `[元素].poi_name` | string（可空） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 13. PUT `/api/admin/corrections/{correction_id}/resolve` 处理纠错

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `correction_id` | path | integer | 是 |  |

**成功响应 200**：

`{"message": "已标记为已处理"}`。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 纠错记录不存在

---

### 14. GET `/api/admin/users` 用户列表

**认证**：管理员（Bearer access_token + ADMIN 角色）

**成功响应 200**：

`[{"id":1,"nickname":"admin","role":"ADMIN","status":1,"created_at":"..."}]` — 全部用户（按 id 升序，不分页）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 15. PUT `/api/admin/users/{user_id}/status` 启用/禁用用户

**功能**：启用/禁用用户。禁用后该用户已签发的 token 立即失效（鉴权回查 DB）。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `user_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | integer | 是 | 1启用 0禁用；范围 0.0~1.0 |

**成功响应 200**：

`{"message": "已禁用"|"已启用"}`。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；400 不能对自己执行禁用操作；404 用户不存在（禁用后该用户已签发 token 立即失效）

---

### 16. GET `/api/admin/reports` 举报列表

**功能**：分页查询举报记录（pending 待处理 / resolved 已处理）。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（3 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `status` | query | string | 否 | 举报状态；匹配: `^(pending/resolved)$`；默认 pending |
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~100；默认 20 |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items` | array |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

items 元素为 AdminReportItem：`{id, review_id, user_id, reporter_nickname, reason, status, created_at, review: {id, course_id, course_name, content, nickname, is_anonymous, like_count, status, created_at}}`（review 为被举报评价摘要，含课程名与评价作者昵称）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 17. POST `/api/admin/reports/{report_id}/resolve` 处理举报

**功能**：处理举报：dismiss 驳回 / remove_review 下架对应评价。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `report_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | dismiss 或 remove_review；匹配: `^(dismiss/remove_review)$` |

**成功响应 200**：

`{"message": "已处理"}`（action=remove_review 时被举报评价 status 置 0 下架）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 举报记录不存在；400 该举报已处理

---

### 18. GET `/api/admin/guides` 攻略列表（分页）

**功能**：分页查询攻略。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（2 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `page` | query | integer | 否 | 最小 1；默认 1 |
| `page_size` | query | integer | 否 | 范围 1~100；默认 20 |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[元素].id` | integer |  |
| `items[元素].title` | string |  |
| `items[元素].category` | string |  |
| `items[元素].summary` | string（可空） |  |
| `items[元素].content` | array（可空） |  |
| `items[元素].created_at` | string（date-time） |  |
| `total` | integer |  |
| `page` | integer |  |
| `page_size` | integer |  |
| `total_pages` | integer |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 19. POST `/api/admin/guides` 创建攻略

**功能**：创建攻略。content 为步骤数组，每项含 step/title/description。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 1-200 字符 |
| `category` | string | 是 | 1-50 字符 |
| `summary` | string（可空） | 否 |  |
| `content` | array | 是 | 步骤数组（JSON） |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `title` | string |  |
| `category` | string |  |
| `summary` | string（可空） |  |
| `content` | array（可空） |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 20. PUT `/api/admin/guides/{guide_id}` 更新攻略

**功能**：更新攻略。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `guide_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 1-200 字符 |
| `category` | string | 是 | 1-50 字符 |
| `summary` | string（可空） | 否 |  |
| `content` | array | 是 | 步骤数组（JSON） |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `title` | string |  |
| `category` | string |  |
| `summary` | string（可空） |  |
| `content` | array（可空） |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 攻略不存在

---

### 21. DELETE `/api/admin/guides/{guide_id}` 删除攻略

**功能**：删除攻略（硬删除）。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `guide_id` | path | integer | 是 |  |

**成功响应 200**：

`{"message": "已删除"}`（Guide 无子表，硬删除）。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 攻略不存在（硬删除）

---

### 22. GET `/api/admin/tasks` 任务列表

**功能**：获取全部新生任务（按 sort_order 升序，不分页）。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `[元素].id` | integer |  |
| `[元素].title` | string |  |
| `[元素].description` | string（可空） |  |
| `[元素].icon` | string（可空） |  |
| `[元素].sort_order` | integer |  |
| `[元素].badge_level` | string（可空） |  |
| `[元素].is_checked` | boolean |  |
| `[元素].created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 23. POST `/api/admin/tasks` 创建任务

**功能**：创建新生任务。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 1-200 字符 |
| `description` | string（可空） | 否 |  |
| `icon` | string（可空） | 否 |  |
| `sort_order` | integer（可空） | 否 |  |
| `badge_level` | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `title` | string |  |
| `description` | string（可空） |  |
| `icon` | string（可空） |  |
| `sort_order` | integer |  |
| `badge_level` | string（可空） |  |
| `is_checked` | boolean |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限

---

### 24. PUT `/api/admin/tasks/{task_id}` 更新任务

**功能**：更新新生任务。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `task_id` | path | integer | 是 |  |

**请求体**（必填，JSON）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 1-200 字符 |
| `description` | string（可空） | 否 |  |
| `icon` | string（可空） | 否 |  |
| `sort_order` | integer（可空） | 否 |  |
| `badge_level` | string（可空） | 否 |  |

**成功响应 200**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer |  |
| `title` | string |  |
| `description` | string（可空） |  |
| `icon` | string（可空） |  |
| `sort_order` | integer |  |
| `badge_level` | string（可空） |  |
| `is_checked` | boolean |  |
| `created_at` | string（date-time） |  |

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 任务不存在

---

### 25. DELETE `/api/admin/tasks/{task_id}` 删除任务

**功能**：删除新生任务。存在关联打卡记录时拒绝（400）。

**认证**：管理员（Bearer access_token + ADMIN 角色）

**请求参数（1 个）**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `task_id` | path | integer | 是 |  |

**成功响应 200**：

`{"message": "已删除"}`。

**主要错误**：401 未登录或 Token 无效；403 需要管理员权限；404 任务不存在；400 该任务存在 N 条打卡记录，请先清理打卡记录

---


## 9. 系统

### 1. GET `/` Root

**功能**：健康检查。

**认证**：公开

**成功响应 200**：

`{"message": "大学萌新领航站 API 运行中", "version": "2.1.0", "docs": "/docs"}`。

**主要错误**：无

---

### 2. GET `/health` Health Check

**功能**：详细健康检查：验证数据库连接。异常细节只记日志，不外泄。

**认证**：公开

**成功响应 200**：

`{"status": "ok"|"error", "database": "connected"|"disconnected", "version": "2.1.0"}`（数据库异常时返回 status=error，不抛 500，细节仅记日志）。

**主要错误**：数据库不可用时返回 200 status=error（不抛异常，细节仅记日志）

---

