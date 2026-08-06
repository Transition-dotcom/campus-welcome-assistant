"""
攻略与任务服务：攻略查询、任务管理、打卡、安全防线、首页聚合、全局搜索。
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.guide import Guide, FreshmanTask, SafetyTip
from app.models.user import UserCheckin
from app.models.course import CourseReview
from app.models.club import ClubEvent
from app.schemas.guide import GuideResponse, FreshmanTaskResponse, SafetyTipResponse, DashboardResponse, SearchResult
from app.schemas.common import PageResponse
from datetime import datetime


# ──── 攻略 ────

def get_guides(db: Session, category: str | None = None) -> list[GuideResponse]:
    """查询攻略列表。"""
    q = db.query(Guide)
    if category:
        q = q.filter(Guide.category == category)
    guides = q.order_by(Guide.id).all()
    return [GuideResponse.model_validate(g) for g in guides]


def get_guide_detail(db: Session, guide_id: int) -> GuideResponse:
    """查询攻略详情。"""
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="攻略不存在")
    return GuideResponse.model_validate(guide)


# ──── 任务 & 打卡 ────

def get_tasks(db: Session, user_id: int | None = None) -> list[FreshmanTaskResponse]:
    """获取新生任务列表，如果已登录则附带打卡状态。"""
    tasks = db.query(FreshmanTask).order_by(FreshmanTask.sort_order).all()

    checked_task_ids = set()
    if user_id:
        checkins = db.query(UserCheckin).filter(UserCheckin.user_id == user_id).all()
        checked_task_ids = {c.task_id for c in checkins}

    result = []
    for t in tasks:
        resp = FreshmanTaskResponse.model_validate(t)
        resp.is_checked = t.id in checked_task_ids
        result.append(resp)
    return result


def checkin_task(db: Session, user_id: int, task_id: int) -> dict:
    """打卡任务。"""
    from fastapi import HTTPException, status

    task = db.query(FreshmanTask).filter(FreshmanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    existing = db.query(UserCheckin).filter(
        UserCheckin.user_id == user_id, UserCheckin.task_id == task_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已完成打卡")

    checkin = UserCheckin(user_id=user_id, task_id=task_id)
    db.add(checkin)
    db.commit()

    # 计算进度
    total = db.query(FreshmanTask).count()
    completed = db.query(UserCheckin).filter(UserCheckin.user_id == user_id).count()
    badge = _get_badge_level(completed, total)
    return {"completed": completed, "total": total, "badge": badge}


def _get_badge_level(completed: int, total: int) -> str | None:
    """根据完成数返回勋章等级。"""
    if completed >= total and total > 0:
        return "diamond"
    elif completed >= 10:
        return "gold"
    elif completed >= 5:
        return "silver"
    elif completed >= 3:
        return "bronze"
    return None


# ──── 安全防线 ────

def get_safety_tips(db: Session, pinned_only: bool = False) -> list[SafetyTipResponse]:
    """查询安全防线。"""
    q = db.query(SafetyTip)
    if pinned_only:
        q = q.filter(SafetyTip.is_pinned == 1)
    tips = q.order_by(desc(SafetyTip.is_pinned), SafetyTip.sort_order).all()
    return [SafetyTipResponse.model_validate(t) for t in tips]


# ──── 首页仪表盘 ────

def get_dashboard(db: Session, user_id: int | None = None) -> DashboardResponse:
    """聚合首页数据。"""
    # 任务进度
    total_tasks = db.query(FreshmanTask).count()
    completed_tasks = 0
    if user_id:
        completed_tasks = db.query(UserCheckin).filter(UserCheckin.user_id == user_id).count()

    # 热门评价（点赞最多，取 3 条）
    hot = db.query(CourseReview).filter(CourseReview.status == 1).order_by(
        desc(CourseReview.like_count), desc(CourseReview.id)
    ).limit(3).all()

    # 近期社团活动（未来 3 条）
    upcoming = db.query(ClubEvent).filter(ClubEvent.event_time >= datetime.utcnow()).order_by(
        ClubEvent.event_time
    ).limit(3).all()

    # 置顶安全提醒
    pinned = db.query(SafetyTip).filter(SafetyTip.is_pinned == 1).order_by(SafetyTip.sort_order).all()

    return DashboardResponse(
        task_progress={"completed": completed_tasks, "total": total_tasks},
        hot_reviews=_serialize_reviews(hot),
        upcoming_events=_serialize_events(upcoming),
        pinned_tips=[SafetyTipResponse.model_validate(t) for t in pinned],
    )


def _serialize_reviews(reviews):
    """序列化评价列表（不含敏感信息）。"""
    from app.models.user import User
    result = []
    for r in reviews:
        user = r.user  # relationship
        result.append({
            "id": r.id,
            "course_id": r.course_id,
            "nickname": "匿名用户" if r.is_anonymous else (user.nickname if user else "未知"),
            "difficulty_rating": r.difficulty_rating,
            "score_rating": r.score_rating,
            "content": r.content[:150] + ("..." if len(r.content) > 150 else ""),
            "like_count": r.like_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


def _serialize_events(events):
    """序列化活动列表。"""
    result = []
    for e in events:
        result.append({
            "id": e.id,
            "club_id": e.club_id,
            "title": e.title,
            "event_type": e.event_type,
            "event_time": e.event_time.isoformat() if e.event_time else None,
            "location": e.location,
        })
    return result


# ──── 全局搜索 ────

def search_all(db: Session, keyword: str, limit: int = 20) -> list[SearchResult]:
    """跨模块搜索。"""
    from app.models.course import Course
    from app.models.club import Club
    from app.models.poi import POI
    from app.models.guide import Guide

    if not keyword or len(keyword) < 2:
        return []

    results = []
    kw = f"%{keyword}%"

    # 搜课程
    courses = db.query(Course).filter(Course.name.like(kw), Course.status == 1).limit(limit).all()
    for c in courses:
        results.append(SearchResult(type="course", id=c.id, title=c.name))

    # 搜社团
    clubs = db.query(Club).filter(Club.name.like(kw), Club.status == 1).limit(limit).all()
    for c in clubs:
        results.append(SearchResult(type="club", id=c.id, title=c.name))

    # 搜 POI
    pois = db.query(POI).filter(POI.name.like(kw)).limit(limit).all()
    for p in pois:
        results.append(SearchResult(type="poi", id=p.id, title=p.name))

    # 搜攻略
    guides = db.query(Guide).filter(Guide.title.like(kw)).limit(limit).all()
    for g in guides:
        results.append(SearchResult(type="guide", id=g.id, title=g.title))

    return results[:limit]
