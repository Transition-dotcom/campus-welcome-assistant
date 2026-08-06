"""
课程评价路由：课程列表、评价 CRUD、点赞、评论、收藏、举报。
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.course import (
    CourseResponse, ReviewCreate, ReviewResponse,
    CommentCreate, CommentResponse, ReportCreate,
)
from app.schemas.common import PageResponse
from app.services import course_service

router = APIRouter(prefix="/api/courses", tags=["课程评价"])

# ──── 课程 ────

@router.get("", response_model=PageResponse[CourseResponse], summary="课程列表")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    college: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    """分页查询课程，支持按学院和类别筛选。"""
    return course_service.get_courses(db, page, page_size, college, category)


@router.get("/{course_id}", response_model=CourseResponse, summary="课程详情")
def get_course(course_id: int, db: Session = Depends(get_db)):
    """查询课程详情（含评价数）。"""
    return course_service.get_course_detail(db, course_id)


# ──── 评价 ────

@router.get("/{course_id}/reviews", response_model=PageResponse[ReviewResponse], summary="评价列表")
def list_reviews(
    course_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    sort: str = Query("time", pattern="^(time|like)$"),
    db: Session = Depends(get_db),
):
    """分页查询课程评价，支持按时间/点赞排序。"""
    return course_service.get_reviews(db, course_id, page, page_size, sort)


@router.post("/{course_id}/reviews", response_model=ReviewResponse, summary="发表评价")
def create_review(
    course_id: int,
    req: ReviewCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对课程发表评价（需登录）。"""
    return course_service.create_review(db, course_id, current_user["user_id"], req)


# ──── 点赞 ────

@router.post("/reviews/{review_id}/like", summary="点赞/取消点赞")
def toggle_like(
    review_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对评价点赞，再次调用则取消点赞（幂等）。"""
    return course_service.toggle_like(db, review_id, current_user["user_id"])


# ──── 评论 ────

@router.get("/reviews/{review_id}/comments", response_model=PageResponse[CommentResponse], summary="评论列表")
def list_comments(
    review_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """获取评价的评论列表（含楼中楼）。"""
    return course_service.get_comments(db, review_id, page, page_size)


@router.post("/reviews/{review_id}/comments", response_model=CommentResponse, summary="发表评论")
def create_comment(
    review_id: int,
    req: CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对评价发表评论（需登录），支持回复某条评论（parent_id）。"""
    return course_service.create_comment(db, review_id, current_user["user_id"], req)


# ──── 收藏 ────

@router.post("/reviews/{review_id}/favorite", summary="收藏/取消收藏")
def toggle_favorite(
    review_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """收藏评价，再次调用则取消收藏（幂等）。"""
    return course_service.toggle_favorite(db, review_id, current_user["user_id"])


@router.get("/favorites/my", response_model=PageResponse[ReviewResponse], summary="我的收藏")
def my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的收藏列表。"""
    return course_service.get_my_favorites(db, current_user["user_id"], page, page_size)


# ──── 举报 ────

@router.post("/reviews/{review_id}/report", summary="举报评价")
def report_review(
    review_id: int,
    req: ReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """举报不当评价（需登录）。"""
    return course_service.report_review(db, review_id, current_user["user_id"], req)
