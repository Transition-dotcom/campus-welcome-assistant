"""
管理后台路由：所有接口需要 ADMIN 角色。
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_admin_user
from app.schemas.course import CourseCreate, CourseResponse
from app.schemas.club import ClubCreate, ClubResponse, ClubEventCreate, ClubEventResponse
from app.schemas.poi import POICreate, POIResponse, POIRouteCreate, POIRouteResponse, POICorrectionResponse
from app.schemas.guide import GuideResponse
from app.services import course_service, club_service, poi_service

router = APIRouter(prefix="/api/admin", tags=["管理后台"])

# ──── 课程管理 ────

@router.post("/courses", response_model=CourseResponse, summary="创建课程")
def admin_create_course(req: CourseCreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return course_service.create_course(db, req)


@router.put("/courses/{course_id}", response_model=CourseResponse, summary="更新课程")
def admin_update_course(course_id: int, req: CourseCreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return course_service.update_course(db, course_id, req)


@router.delete("/courses/{course_id}", summary="删除课程")
def admin_delete_course(course_id: int, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    course_service.delete_course(db, course_id)
    return {"message": "已删除"}


# ──── 社团管理 ────

@router.post("/clubs", response_model=ClubResponse, summary="创建社团")
def admin_create_club(req: ClubCreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return club_service.create_club(db, req)


@router.put("/clubs/{club_id}", response_model=ClubResponse, summary="更新社团")
def admin_update_club(club_id: int, req: ClubCreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return club_service.update_club(db, club_id, req)


@router.delete("/clubs/{club_id}", summary="删除社团")
def admin_delete_club(club_id: int, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    club_service.delete_club(db, club_id)
    return {"message": "已删除"}


@router.post("/clubs/{club_id}/events", response_model=ClubEventResponse, summary="创建社团活动")
def admin_create_event(club_id: int, req: ClubEventCreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return club_service.create_event(db, club_id, req)


# ──── POI 管理 ────

@router.post("/pois", response_model=POIResponse, summary="创建地标")
def admin_create_poi(req: POICreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return poi_service.create_poi(db, req)


@router.put("/pois/{poi_id}", response_model=POIResponse, summary="更新地标")
def admin_update_poi(poi_id: int, req: POICreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return poi_service.update_poi(db, poi_id, req)


@router.delete("/pois/{poi_id}", summary="删除地标")
def admin_delete_poi(poi_id: int, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    poi_service.delete_poi(db, poi_id)
    return {"message": "已删除"}


@router.post("/pois/routes", response_model=POIRouteResponse, summary="创建路径")
def admin_create_route(req: POIRouteCreate, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return poi_service.create_route(db, req)


# ──── 纠错处理 ────

@router.get("/corrections", response_model=list[POICorrectionResponse], summary="纠错列表")
def admin_list_corrections(status: str | None = None, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return poi_service.get_corrections(db, status)


@router.put("/corrections/{correction_id}/resolve", summary="处理纠错")
def admin_resolve_correction(correction_id: int, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    return poi_service.resolve_correction(db, correction_id)


# ──── 用户管理（预留） ────

@router.get("/users", summary="用户列表")
def admin_list_users(_=Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.user import User
    users = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "nickname": u.nickname, "role": u.role, "status": u.status, "created_at": u.created_at} for u in users]
