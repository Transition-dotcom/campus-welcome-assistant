"""
管理后台路由：所有接口需要 ADMIN 角色。
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_admin_user
from app.schemas.course import CourseCreate, CourseResponse, ReportResolveRequest
from app.schemas.club import ClubCreate, ClubResponse, ClubEventCreate, ClubEventResponse
from app.schemas.poi import POICreate, POIResponse, POIRouteCreate, POIRouteResponse, POICorrectionResponse
from app.schemas.guide import GuideResponse, GuideUpsert, FreshmanTaskResponse, FreshmanTaskUpsert
from app.schemas.user import UserStatusUpdate
from app.schemas.common import PageResponse
from app.services import course_service, club_service, poi_service, guide_service

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


# ──── 用户管理 ────

@router.get("/users", summary="用户列表")
def admin_list_users(_=Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.user import User
    users = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "nickname": u.nickname, "role": u.role, "status": u.status, "created_at": u.created_at} for u in users]


@router.put("/users/{user_id}/status", summary="启用/禁用用户")
def admin_update_user_status(
    user_id: int,
    req: UserStatusUpdate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """启用/禁用用户。禁用后该用户已签发的 token 立即失效（鉴权回查 DB）。"""
    from fastapi import HTTPException, status
    from app.models.user import User

    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能对自己执行禁用操作")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.status = req.status
    db.commit()
    return {"message": "已禁用" if req.status == 0 else "已启用"}


# ──── 举报审核 ────

@router.get("/reports", response_model=PageResponse, summary="举报列表")
def admin_list_reports(
    status: str = Query("pending", pattern="^(pending|resolved)$", description="举报状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """分页查询举报记录（pending 待处理 / resolved 已处理）。"""
    return course_service.get_reports(db, status, page, page_size)


@router.post("/reports/{report_id}/resolve", summary="处理举报")
def admin_resolve_report(
    report_id: int,
    req: ReportResolveRequest,
    _=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """处理举报：dismiss 驳回 / remove_review 下架对应评价。"""
    return course_service.resolve_report(db, report_id, req)


# ──── 攻略管理 ────

@router.get("/guides", response_model=PageResponse[GuideResponse], summary="攻略列表（分页）")
def admin_list_guides(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """分页查询攻略。"""
    return guide_service.get_guides_page(db, page, page_size)


@router.post("/guides", response_model=GuideResponse, summary="创建攻略")
def admin_create_guide(req: GuideUpsert, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    """创建攻略。content 为步骤数组，每项含 step/title/description。"""
    return guide_service.create_guide(db, req)


@router.put("/guides/{guide_id}", response_model=GuideResponse, summary="更新攻略")
def admin_update_guide(guide_id: int, req: GuideUpsert, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    """更新攻略。"""
    return guide_service.update_guide(db, guide_id, req)


@router.delete("/guides/{guide_id}", summary="删除攻略")
def admin_delete_guide(guide_id: int, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    """删除攻略（硬删除）。"""
    return guide_service.delete_guide(db, guide_id)


# ──── 任务管理 ────

@router.get("/tasks", response_model=list[FreshmanTaskResponse], summary="任务列表")
def admin_list_tasks(_=Depends(get_admin_user), db: Session = Depends(get_db)):
    """获取全部新生任务（按 sort_order 升序，不分页）。"""
    return guide_service.get_tasks(db)


@router.post("/tasks", response_model=FreshmanTaskResponse, summary="创建任务")
def admin_create_task(req: FreshmanTaskUpsert, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    """创建新生任务。"""
    return guide_service.create_task(db, req)


@router.put("/tasks/{task_id}", response_model=FreshmanTaskResponse, summary="更新任务")
def admin_update_task(task_id: int, req: FreshmanTaskUpsert, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    """更新新生任务。"""
    return guide_service.update_task(db, task_id, req)


@router.delete("/tasks/{task_id}", summary="删除任务")
def admin_delete_task(task_id: int, _=Depends(get_admin_user), db: Session = Depends(get_db)):
    """删除新生任务。存在关联打卡记录时拒绝（400）。"""
    return guide_service.delete_task(db, task_id)
