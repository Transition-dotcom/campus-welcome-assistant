"""
FastAPI 应用入口。启动：uvicorn app.main:app --reload --port 8080
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: 确保所有模型被导入，Base.metadata 包含全部表
from app.routers import user, course, club, poi, guide, admin

# 自动建表（生产环境应使用 Alembic 迁移）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="大学萌新领航站 API",
    description="面向大学新生的综合服务平台后端接口",
    version="2.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"message": "大学萌新领航站 API 运行中", "version": "2.0.0", "docs": "/docs"}
