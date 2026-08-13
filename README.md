# 🏫 大学萌新领航站（东北大学软件学院版）

东北大学软件学院新生综合服务平台。基于浑南校区公开信息与软件学院培养方案定制，为新生提供**选课评价、GPA 计算、社团导航、校园导览、办事攻略、新生任务打卡、安全防线**一站式服务。

## ✨ 功能模块

| 模块 | 说明 |
|------|------|
| 选课评价 | 课程浏览、老生经验评价、点赞/收藏/举报 |
| GPA 计算器 | 按学分计算 GPA |
| 社团导航 | 学院及全校社团介绍、近期活动时间线 |
| 校园导览 | 浑南校区地标详情、路径指引、纠错提交 |
| 办事攻略 | 报到流程、图书馆借阅、选课操作等图文步骤 |
| 新生任务 | 12 项成长任务清单 + 打卡 + 奖牌徽章 |
| 安全防线 | 防诈骗提醒、宿舍安全、紧急电话等 |
| 管理后台 | 课程/社团/地标管理、纠错审核、用户管理 |

## 🛠 技术栈

- **后端**：Python 3.9+ · FastAPI · SQLAlchemy · MySQL 8 · JWT 鉴权
- **前端**：Vue 3 · Vite 5 · Element Plus · Pinia · Axios

## 🚀 本地运行

### 1. 准备 MySQL

项目后端使用 MySQL，默认连接配置（见 `backend/app/config.py`）：

```
host=localhost  port=3306  user=root  password=root  database=campus_nav
```

可用环境变量或 `backend/.env` 覆盖，例如 `DB_PASSWORD=你的密码`。

**初始化数据库**（库、表、种子数据）：

```bash
mysql -u root -proot --default-character-set=utf8mb4 < backend/init.sql
```

> ⚠️ 必须加 `--default-character-set=utf8mb4`，否则含中文的 INSERT 会报编码错误。
> 种子数据包含：25 门课程（依据软件学院培养方案）、8 个社团、14 个地标、攻略、任务、安全提示等。

### 2. 启动后端（端口 8080）

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   /  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

- 健康检查：http://localhost:8080/
- API 文档（Swagger）：http://localhost:8080/docs

### 3. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 **http://localhost:5173**（Vite 已配置 `/api` 代理到后端 8080）。

### 4. 运行测试

```bash
# 单元 + 集成测试（无需 MySQL，SQLite 内存库，92 个用例）
cd backend && python3 -m pytest tests/

# 全流程 E2E 冒烟测试（需 MySQL 已初始化 + 后端已启动，52 项断言）
bash scripts/e2e_smoke.sh
```

### 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | `admin` | `admin123` |

普通用户可自行注册。

## 📝 变更记录

### 2026-08-13 安全加固 & 功能补齐 & 全流程测试

- **fix**: 匿名评价不再泄漏 `user_id`；鉴权每请求回查数据库（禁用用户/降权管理员立即失效）
- **feat**: refresh token 轮换撤销（`token_version` 版本号），旧 refresh token 一经使用即作废
- **feat**: 管理后台补齐举报审核、攻略管理、任务管理、用户禁用（前后端契约一致）
- **fix**: 种子社团活动改用相对时间（`DATE_ADD(NOW(), INTERVAL n DAY)`），招新日历永久不过期
- **fix**: `init.sql` 可重复执行（导入前自动重建数据库，重置为干净演示数据）
- **perf**: element-plus 按需引入，最大 chunk 1073KB → 344KB（gzip 106KB）
- **docs**: 补齐数据库设计 / API 接口 / 部署说明 / 用户使用手册（`docs/`）
- **test**: 新增 `tests/test_fixes.py`、`test_refresh_rotation.py`（92 用例全绿）；`scripts/e2e_smoke.sh` 真实环境全流程冒烟测试 52 项全通过

### 2026-08 环境准备 & 修复

- **fix**: `init.sql` 中 admin 账号替换为有效 bcrypt 哈希，修复开箱后 `admin/admin123` 登录失败
- **feat**: 移动端底部导航新增「登录/我的」入口，修复窄窗口（<768px）下无登录入口的问题
- **feat**: 首页「新生任务进度」卡片可点击，跳转到任务清单页
- **feat**: 新增「安全防线」详情页（`/safety`），首页安全防线卡可点击查看全部提示与完整内容
- **fix**: 首页任务进度按当前登录用户实时统计（原 `/dashboard` 未注入用户信息，进度恒为 0）
- **fix**: 首页 GPA 入口图标改用可用的 `Operation` 计算器图标（`Calculator` 图标在 element-plus 中不存在）

### 历史版本

- **v2.0**：完整项目框架与功能实现
- **定制化**：东北大学软件学院（浑南校区）公开信息与培养方案数据

## 📁 目录结构

```
campus-welcome-assistant/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # 路由（用户/课程/社团/地标/攻略/管理后台）
│   │   ├── services/        # 业务逻辑
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── middleware/      # JWT 鉴权
│   │   └── utils/           # 密码哈希 / JWT 工具
│   ├── init.sql             # 建库建表 + 种子数据
│   └── requirements.txt
└── frontend/                # Vue 3 前端
    └── src/
        ├── views/           # 页面（home/course/club/poi/guide/user/admin）
        ├── router/          # 路由配置
        ├── stores/          # Pinia 状态
        └── api/             # API 封装
```
