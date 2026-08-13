"""
FastAPI 应用入口。启动：uvicorn app.main:app --reload --port 8080
"""
import secrets
import warnings
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, Base, get_db
from app.models import *  # noqa: 确保所有模型被导入，Base.metadata 包含全部表
from app.routers import user, course, club, poi, guide, admin

# JWT 密钥安全检查：生产环境必须通过环境变量设置
if not settings.jwt_secret:
    settings.jwt_secret = secrets.token_urlsafe(32)
    warnings.warn(
        "⚠ JWT_SECRET 未设置！已自动生成临时密钥。"
        "生产环境请通过环境变量 JWT_SECRET 设置固定强随机密钥。",
        RuntimeWarning,
    )

# 自动建表（生产环境应使用 Alembic 迁移）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="东北大学软件学院 · 萌新领航站 API",
    description="东北大学软件学院新生综合服务平台 - 基于浑南校区公开信息与软院培养方案",
    version="2.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# 注册路由
app.include_router(user.router)
app.include_router(course.router)
app.include_router(club.router)
app.include_router(poi.router)
app.include_router(guide.router)
app.include_router(admin.router)


@app.get("/", tags=["系统"])
def root():
    """健康检查。"""
    return {"message": "大学萌新领航站 API 运行中", "version": "2.1.0", "docs": "/docs"}


@app.get("/health", tags=["系统"])
def health_check(db: Session = Depends(get_db)):
    """详细健康检查：验证数据库连接。"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "version": "2.1.0"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "detail": str(e)}
