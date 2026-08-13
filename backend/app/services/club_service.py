"""
社团服务：社团 CRUD、活动管理。
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.club import Club, ClubEvent
from app.schemas.club import ClubCreate, ClubResponse, ClubEventCreate, ClubEventResponse
from app.schemas.common import PageResponse


def get_clubs(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    category: str | None = None,
    keyword: str | None = None,
) -> PageResponse:
    """分页查询社团列表，支持分类筛选和关键词搜索。"""
    q = db.query(Club).filter(Club.status == 1)

    if category:
        # 支持逗号分隔的多分类（如「学生组织,志愿公益」），任一分类命中即返回
        q = q.filter(Club.category.like(f"%{category}%"))
    if keyword:
        q = q.filter(Club.name.contains(keyword))

    total = q.count()
    clubs = q.order_by(desc(Club.id)).offset((page - 1) * page_size).limit(page_size).all()

    items = [ClubResponse.model_validate(c) for c in clubs]
    total_pages = (total + page_size - 1) // page_size
    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


def get_club_detail(db: Session, club_id: int) -> ClubResponse:
    """查询社团详情。"""
    club = db.query(Club).filter(Club.id == club_id, Club.status == 1).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="社团不存在")
    return ClubResponse.model_validate(club)


def create_club(db: Session, req: ClubCreate) -> ClubResponse:
    """管理员创建社团。"""
    club = Club(**req.model_dump())
    db.add(club)
    db.commit()
    db.refresh(club)
    return ClubResponse.model_validate(club)


def update_club(db: Session, club_id: int, req: ClubCreate) -> ClubResponse:
    """管理员更新社团。"""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="社团不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(club, key, value)
    db.commit()
    db.refresh(club)
    return ClubResponse.model_validate(club)


def delete_club(db: Session, club_id: int):
    """管理员删除社团（软删除）。"""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="社团不存在")
    club.status = 0
    db.commit()


# ──── 社团活动 ────

def get_events(db: Session, club_id: int | None = None, upcoming_only: bool = True) -> list[ClubEventResponse]:
    """查询社团活动：可按社团筛选，默认只返回未过期的。下架社团（status=0）的活动不再展示。"""
    from datetime import datetime
    q = db.query(ClubEvent).join(Club, Club.id == ClubEvent.club_id).filter(Club.status == 1)
    if club_id:
        q = q.filter(ClubEvent.club_id == club_id)
    if upcoming_only:
        q = q.filter(ClubEvent.event_time >= datetime.utcnow())

    events = q.order_by(ClubEvent.event_time).all()
    return [ClubEventResponse.model_validate(e) for e in events]


def create_event(db: Session, club_id: int, req: ClubEventCreate) -> ClubEventResponse:
    """管理员创建社团活动。"""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="社团不存在")

    event = ClubEvent(club_id=club_id, **req.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return ClubEventResponse.model_validate(event)
