"""
校园导览路由：POI 列表、详情、路径、纠错。
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.poi import POIResponse, POIRouteResponse, POICorrectionCreate, POICorrectionResponse
from app.schemas.common import PageResponse
from app.services import poi_service

router = APIRouter(prefix="/api/pois", tags=["校园导览"])


@router.get("", response_model=PageResponse[POIResponse], summary="地标列表")
def list_pois(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    """分页查询校园地标，支持分类和搜索。"""
    return poi_service.get_pois(db, page, page_size, category, keyword)


@router.get("/{poi_id}", response_model=POIResponse, summary="地标详情")
def get_poi(poi_id: int, db: Session = Depends(get_db)):
    """查询地标详细信息。"""
    return poi_service.get_poi_detail(db, poi_id)


@router.get("/routes/list", response_model=list[POIRouteResponse], summary="路径列表")
def list_routes(poi_id: int | None = None, db: Session = Depends(get_db)):
    """查询路径指引，可按起点 POI 筛选。"""
    return poi_service.get_routes(db, poi_id)


@router.post("/correction", response_model=POICorrectionResponse, summary="提交纠错")
def submit_correction(
    req: POICorrectionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """登录用户提交地标信息纠错。"""
    return poi_service.submit_correction(db, current_user["user_id"], req)
