"""
校园导览服务：POI CRUD、路径管理、纠错。
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.poi import POI, POIRoute, POICorrection
from app.schemas.poi import (
    POICreate, POIResponse, POIRouteCreate, POIRouteResponse,
    POICorrectionCreate, POICorrectionResponse,
)
from app.schemas.common import PageResponse


def get_pois(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    keyword: str | None = None,
) -> PageResponse:
    """分页查询 POI，支持分类和搜索。"""
    q = db.query(POI)
    if category:
        q = q.filter(POI.category == category)
    if keyword:
        q = q.filter(POI.name.contains(keyword))

    total = q.count()
    pois = q.order_by(POI.id).offset((page - 1) * page_size).limit(page_size).all()

    items = [POIResponse.model_validate(p) for p in pois]
    total_pages = (total + page_size - 1) // page_size
    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


def get_poi_detail(db: Session, poi_id: int) -> POIResponse:
    """查询 POI 详情。"""
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地标不存在")
    return POIResponse.model_validate(poi)


def create_poi(db: Session, req: POICreate) -> POIResponse:
    """管理员创建 POI。"""
    poi = POI(**req.model_dump())
    db.add(poi)
    db.commit()
    db.refresh(poi)
    return POIResponse.model_validate(poi)


def update_poi(db: Session, poi_id: int, req: POICreate) -> POIResponse:
    """管理员更新 POI。"""
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地标不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(poi, key, value)
    db.commit()
    db.refresh(poi)
    return POIResponse.model_validate(poi)


def delete_poi(db: Session, poi_id: int):
    """管理员删除 POI。"""
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地标不存在")
    db.delete(poi)
    db.commit()


# ──── 路径 ────

def get_routes(db: Session, poi_id: int | None = None) -> list[POIRouteResponse]:
    """查询路径：可按起点 POI 筛选。"""
    q = db.query(POIRoute)
    if poi_id:
        q = q.filter(POIRoute.from_poi_id == poi_id)

    routes = q.all()

    # 批量查询所有涉及的 POI 名称
    poi_ids = set()
    for r in routes:
        poi_ids.add(r.from_poi_id)
        poi_ids.add(r.to_poi_id)
    pois_map: dict[int, POI] = {}
    if poi_ids:
        pois_map = {p.id: p for p in db.query(POI).filter(POI.id.in_(poi_ids)).all()}

    result = []
    for r in routes:
        resp = POIRouteResponse.model_validate(r)
        from_poi = pois_map.get(r.from_poi_id)
        to_poi = pois_map.get(r.to_poi_id)
        resp.from_poi_name = from_poi.name if from_poi else None
        resp.to_poi_name = to_poi.name if to_poi else None
        result.append(resp)
    return result


def create_route(db: Session, req: POIRouteCreate) -> POIRouteResponse:
    """管理员创建路径。"""
    route = POIRoute(**req.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    return POIRouteResponse.model_validate(route)


# ──── 纠错 ────

def submit_correction(db: Session, user_id: int, req: POICorrectionCreate) -> POICorrectionResponse:
    """用户提交 POI 纠错。"""
    poi = db.query(POI).filter(POI.id == req.poi_id).first()
    if not poi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地标不存在")

    correction = POICorrection(poi_id=req.poi_id, user_id=user_id, content=req.content)
    db.add(correction)
    db.commit()
    db.refresh(correction)
    return POICorrectionResponse.model_validate(correction)


def get_corrections(db: Session, status_filter: str | None = None) -> list[POICorrectionResponse]:
    """管理员查询纠错列表。"""
    q = db.query(POICorrection)
    if status_filter:
        q = q.filter(POICorrection.status == status_filter)
    corrections = q.order_by(desc(POICorrection.id)).all()
    return [POICorrectionResponse.model_validate(c) for c in corrections]


def resolve_correction(db: Session, correction_id: int) -> dict:
    """管理员标记纠错为已处理。"""
    correction = db.query(POICorrection).filter(POICorrection.id == correction_id).first()
    if not correction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="纠错记录不存在")
    correction.status = "resolved"
    db.commit()
    return {"message": "已标记为已处理"}
