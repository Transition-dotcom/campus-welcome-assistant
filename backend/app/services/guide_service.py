"""
攻略与任务服务：攻略查询、任务管理、打卡、安全防线、首页聚合、全局搜索。
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.guide import Guide, FreshmanTask, SafetyTip
from app.models.user import UserCheckin
from app.models.course import CourseReview
from app.models.club import Club, ClubEvent
from app.schemas.guide import (
    GuideResponse, GuideUpsert, FreshmanTaskResponse, FreshmanTaskUpsert,
    SafetyTipResponse, DashboardResponse, SearchResult,
)
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
    from sqlalchemy.orm import joinedload

    # 任务进度
    total_tasks = db.query(FreshmanTask).count()
    completed_tasks = 0
    if user_id:
        completed_tasks = db.query(UserCheckin).filter(UserCheckin.user_id == user_id).count()

    # 热门评价（点赞最多，取 3 条）— 预加载 user 避免 N+1
    hot = (
        db.query(CourseReview)
        .filter(CourseReview.status == 1)
        .options(joinedload(CourseReview.user))
        .order_by(desc(CourseReview.like_count), desc(CourseReview.id))
        .limit(3)
        .all()
    )

    # 近期社团活动（未来 3 条，只展示未下架社团的活动）
    upcoming = (
        db.query(ClubEvent)
        .join(Club, Club.id == ClubEvent.club_id)
        .filter(ClubEvent.event_time >= datetime.utcnow(), Club.status == 1)
        .order_by(ClubEvent.event_time)
        .limit(3)
        .all()
    )

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

# 常见课程缩写 → 全称，用于搜索扩展（如「高数」→「高等数学」）
COURSE_ALIASES = {
    "高数": "高等数学",
    "线代": "线性代数",
    "计组": "计算机组成原理",
    "软工": "软件工程",
    "概率统计": "概率论与数理统计",
}


def _expand_keywords(keyword: str) -> list[str]:
    """把关键词扩展成一组检索词：原词 + 常见缩写对应的全称。"""
    terms = [keyword]
    full = COURSE_ALIASES.get(keyword) or COURSE_ALIASES.get(keyword.strip())
    if full:
        terms.append(full)
    return terms


def search_all(db: Session, keyword: str, page: int = 1, page_size: int = 20) -> PageResponse:
    """跨模块搜索。支持常见课程缩写（如「高数」）扩展匹配全称。返回分页结果。

    避免全表加载：每张表只取 limit(page_size * page) 条数据，
    total 用 COUNT 单独统计，保证分页信息准确。
    """
    from sqlalchemy import or_

    from app.models.course import Course
    from app.models.poi import POI

    if not keyword or len(keyword) < 2:
        return PageResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)

    terms = _expand_keywords(keyword)
    fetch_limit = page_size * page

    total = 0
    results: list[SearchResult] = []

    def _search_model(model, title_col: str, type_name: str, extra_filters=None) -> None:
        """对单张表执行搜索：COUNT 统计 total + LIMIT 取当前页需要的数据。"""
        nonlocal total
        col = getattr(model, title_col)
        like_filters = or_(*[col.like(f"%{t}%") for t in terms])
        q = db.query(model)
        if extra_filters is not None:
            q = q.filter(*extra_filters)
        q = q.filter(like_filters)
        total += q.count()
        rows = q.order_by(model.id).limit(fetch_limit).all()
        for row in rows:
            results.append(SearchResult(type=type_name, id=row.id, title=getattr(row, title_col)))

    # 搜课程（只展示上架课程）
    _search_model(Course, "name", "course", extra_filters=(Course.status == 1,))
    # 搜社团（只展示上架社团）
    _search_model(Club, "name", "club", extra_filters=(Club.status == 1,))
    # 搜 POI（只展示未下架地标）
    _search_model(POI, "name", "poi", extra_filters=(POI.status == 1,))
    # 搜攻略
    _search_model(Guide, "title", "guide")

    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    page_items = results[start:end]

    return PageResponse(items=page_items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ──── 管理端：攻略 CRUD ────

def get_guides_page(db: Session, page: int = 1, page_size: int = 20) -> PageResponse:
    """管理员分页查询攻略列表。"""
    q = db.query(Guide)
    total = q.count()
    guides = q.order_by(Guide.id).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size
    return PageResponse(
        items=[GuideResponse.model_validate(g) for g in guides],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


def create_guide(db: Session, req: GuideUpsert) -> GuideResponse:
    """管理员创建攻略。"""
    guide = Guide(title=req.title, category=req.category, summary=req.summary, content=req.content)
    db.add(guide)
    db.commit()
    db.refresh(guide)
    return GuideResponse.model_validate(guide)


def update_guide(db: Session, guide_id: int, req: GuideUpsert) -> GuideResponse:
    """管理员更新攻略。"""
    from fastapi import HTTPException, status

    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="攻略不存在")
    guide.title = req.title
    guide.category = req.category
    guide.summary = req.summary
    guide.content = req.content
    db.commit()
    db.refresh(guide)
    return GuideResponse.model_validate(guide)


def delete_guide(db: Session, guide_id: int) -> dict:
    """管理员删除攻略（Guide 无子表，硬删除）。"""
    from fastapi import HTTPException, status

    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="攻略不存在")
    db.delete(guide)
    db.commit()
    return {"message": "已删除"}


# ──── 管理端：任务 CRUD ────

def create_task(db: Session, req: FreshmanTaskUpsert) -> FreshmanTaskResponse:
    """管理员创建新生任务。"""
    task = FreshmanTask(
        title=req.title,
        description=req.description,
        icon=req.icon,
        sort_order=req.sort_order if req.sort_order is not None else 0,
        badge_level=req.badge_level,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return FreshmanTaskResponse.model_validate(task)


def update_task(db: Session, task_id: int, req: FreshmanTaskUpsert) -> FreshmanTaskResponse:
    """管理员更新新生任务（仅更新提交的字段）。"""
    from fastapi import HTTPException, status

    task = db.query(FreshmanTask).filter(FreshmanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return FreshmanTaskResponse.model_validate(task)


def delete_task(db: Session, task_id: int) -> dict:
    """管理员删除新生任务。存在打卡记录时拒绝删除。"""
    from fastapi import HTTPException, status

    task = db.query(FreshmanTask).filter(FreshmanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    checkin_count = db.query(UserCheckin).filter(UserCheckin.task_id == task_id).count()
    if checkin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该任务存在 {checkin_count} 条打卡记录，请先清理打卡记录",
        )

    db.delete(task)
    db.commit()
    return {"message": "已删除"}
