"""
社团模块路由：社团列表、详情、活动。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.club import ClubResponse, ClubEventResponse
from app.schemas.common import PageResponse
from app.services import club_service

router = APIRouter(prefix="/api/clubs", tags=["社团导航"])


@router.get("", response_model=PageResponse[ClubResponse], summary="社团列表")
def list_clubs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    """分页查询社团，支持分类筛选和名称搜索。"""
    return club_service.get_clubs(db, page, page_size, category, keyword)


@router.get("/{club_id}", response_model=ClubResponse, summary="社团详情")
def get_club(club_id: int, db: Session = Depends(get_db)):
    """查询社团详细信息。"""
    return club_service.get_club_detail(db, club_id)


@router.get("/{club_id}/events", response_model=list[ClubEventResponse], summary="社团活动")
def get_events(club_id: int, db: Session = Depends(get_db)):
    """查询社团的近期活动。"""
    return club_service.get_events(db, club_id=club_id)


@router.get("/events/upcoming", response_model=list[ClubEventResponse], summary="近期活动")
def upcoming_events(db: Session = Depends(get_db)):
    """查询全校近期社团活动（未过期）。"""
    return club_service.get_events(db)
