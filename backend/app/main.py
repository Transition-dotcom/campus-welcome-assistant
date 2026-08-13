"""
FastAPI 应用入口。启动：uvicorn app.main:app --reload --port 8080
"""
import logging
import secrets
import warnings
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, Base, get_db
from app.models import *  # noqa: 确保所有模型被导入，Base.metadata 包含全部表
from app.routers import user, course, club, poi, guide, admin

logger = logging.getLogger(__name__)

# JWT 密钥安全检查：生产环境必须通过环境变量设置
if not settings.jwt_secret:
    generated_secret = secrets.token_urlsafe(32)
    settings.jwt_secret = generated_secret
    # 持久化到 backend/.env，保证下次启动复用同一密钥（否则重启后所有 token 失效）
    env_path = Path(__file__).resolve().parent.parent / ".env"
    try:
        content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        if "JWT_SECRET" not in content:
            if content and not content.endswith("\n"):
                content += "\n"
            env_path.write_text(content + f"JWT_SECRET={generated_secret}\n", encoding="utf-8")
            warnings.warn(
                "⚠ JWT_SECRET 未设置！已自动生成随机密钥并写入 backend/.env，"
                "下次启动将复用同一密钥。生产环境请通过环境变量 JWT_SECRET 设置固定强随机密钥。",
                RuntimeWarning,
            )
    except OSError:
        warnings.warn(
            "⚠ JWT_SECRET 未设置！已自动生成临时密钥（写入 .env 失败，重启后旧 token 将失效）。"
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


# ──── SQLAlchemy 异常兜底处理 ────

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """唯一键/外键冲突等完整性错误 → 400，避免裸 500。"""
    logger.warning("数据库完整性冲突: %s", exc.orig)
    return JSONResponse(status_code=400, content={"detail": "数据冲突或重复"})


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    """数据格式错误（字段超长、非法值等）→ 400。"""
    logger.warning("数据库数据格式错误: %s", exc.orig)
    return JSONResponse(status_code=400, content={"detail": "请求数据格式不正确"})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """其他 SQLAlchemy 错误 → 500 通用提示，细节只记日志。"""
    logger.exception("数据库操作异常: %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误，请稍后重试"})


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
    """详细健康检查：验证数据库连接。异常细节只记日志，不外泄。"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "version": "2.1.0"}
    except Exception:
        logger.exception("健康检查失败：数据库连接异常")
        return {"status": "error", "database": "disconnected"}
