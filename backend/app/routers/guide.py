"""
攻略与任务路由：攻略、任务打卡、安全防线、首页、全局搜索。
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.schemas.guide import GuideResponse, FreshmanTaskResponse, SafetyTipResponse, DashboardResponse, SearchResult
from app.schemas.common import PageResponse
from app.services import guide_service

router = APIRouter(prefix="/api", tags=["攻略 & 首页"])

# ──── 攻略 ────

@router.get("/guides", response_model=list[GuideResponse], summary="攻略列表")
def list_guides(category: str | None = None, db: Session = Depends(get_db)):
    """查询办事流程/生活指南/学习攻略。"""
    return guide_service.get_guides(db, category)


@router.get("/guides/{guide_id}", response_model=GuideResponse, summary="攻略详情")
def get_guide(guide_id: int, db: Session = Depends(get_db)):
    return guide_service.get_guide_detail(db, guide_id)


# ──── 新生任务 & 打卡 ────

@router.get("/tasks", response_model=list[FreshmanTaskResponse], summary="新生任务列表")
def list_tasks(db: Session = Depends(get_db)):
    """获取所有新生任务（不含打卡状态）。"""
    return guide_service.get_tasks(db)


@router.get("/tasks/my", response_model=list[FreshmanTaskResponse], summary="我的任务列表")
def my_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取新生任务列表（含当前用户打卡状态）。"""
    return guide_service.get_tasks(db, current_user["user_id"])


@router.post("/tasks/{task_id}/checkin", summary="打卡任务")
def checkin_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对指定任务打卡（需登录）。"""
    return guide_service.checkin_task(db, current_user["user_id"], task_id)


# ──── 安全防线 ────

@router.get("/safety-tips", response_model=list[SafetyTipResponse], summary="安全防线")
def list_safety_tips(pinned_only: bool = False, db: Session = Depends(get_db)):
    """查询安全提醒，pinned_only=true 只返回置顶内容。"""
    return guide_service.get_safety_tips(db, pinned_only)


# ──── 首页仪表盘 ────

@router.get("/dashboard", response_model=DashboardResponse, summary="首页聚合")
def dashboard(
    current_user: dict | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """首页仪表盘：聚合任务进度、热门评价、近期活动、安全提醒。登录时任务进度按当前用户统计。"""
    user_id = current_user["user_id"] if current_user else None
    return guide_service.get_dashboard(db, user_id)


# ──── 全局搜索 ────

@router.get("/search", response_model=PageResponse, summary="全局搜索")
def search(
    keyword: str = Query(..., min_length=2, max_length=100),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
):
    """跨模块搜索课程、社团、地标、攻略。"""
    return guide_service.search_all(db, keyword, page, page_size)
