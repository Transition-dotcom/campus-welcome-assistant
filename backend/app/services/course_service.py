"""
课程评价服务：课程 CRUD、评价 CRUD、点赞、评论、收藏、举报。
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.course import Course, CourseReview, ReviewComment, ReviewLike, ReviewReport
from app.models.user import User, UserFavorite
from app.schemas.course import (
    CourseCreate, CourseResponse, ReviewCreate, ReviewResponse,
    CommentCreate, CommentResponse, ReportCreate,
)
from app.schemas.common import PageResponse


# ──── 课程 ────

def get_courses(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    college: str | None = None,
    category: str | None = None,
) -> PageResponse:
    """分页查询课程列表，支持按学院和类别筛选。"""
    q = db.query(Course).filter(Course.status == 1)

    if college:
        q = q.filter(Course.college == college)
    if category:
        q = q.filter(Course.category == category)

    total = q.count()
    courses = q.order_by(desc(Course.id)).offset((page - 1) * page_size).limit(page_size).all()

    # 填充每个课程的评价数
    items = []
    for c in courses:
        review_count = db.query(CourseReview).filter(
            CourseReview.course_id == c.id, CourseReview.status == 1
        ).count()
        resp = CourseResponse.model_validate(c)
        resp.review_count = review_count
        items.append(resp)

    total_pages = (total + page_size - 1) // page_size
    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


def get_course_detail(db: Session, course_id: int) -> CourseResponse:
    """查询单个课程详情。"""
    course = db.query(Course).filter(Course.id == course_id, Course.status == 1).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

    review_count = db.query(CourseReview).filter(
        CourseReview.course_id == course_id, CourseReview.status == 1
    ).count()
    resp = CourseResponse.model_validate(course)
    resp.review_count = review_count
    return resp


def create_course(db: Session, req: CourseCreate) -> CourseResponse:
    """管理员创建课程。"""
    course = Course(**req.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    resp = CourseResponse.model_validate(course)
    resp.review_count = 0
    return resp


def update_course(db: Session, course_id: int, req: CourseCreate) -> CourseResponse:
    """管理员更新课程。"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return CourseResponse.model_validate(course)


def delete_course(db: Session, course_id: int):
    """管理员删除课程（软删除）。"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    course.status = 0
    db.commit()


# ──── 评价 ────

def get_reviews(
    db: Session,
    course_id: int,
    page: int = 1,
    page_size: int = 10,
    sort: str = "time",
    current_user_id: int | None = None,
) -> PageResponse:
    """分页查询课程评价，支持按时间/点赞排序。"""
    q = db.query(CourseReview).filter(
        CourseReview.course_id == course_id, CourseReview.status == 1
    )

    if sort == "like":
        q = q.order_by(desc(CourseReview.like_count), desc(CourseReview.id))
    else:
        q = q.order_by(desc(CourseReview.id))

    total = q.count()
    reviews = q.offset((page - 1) * page_size).limit(page_size).all()

    items = [_build_review_response(db, r, current_user_id) for r in reviews]
    total_pages = (total + page_size - 1) // page_size
    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


def create_review(db: Session, course_id: int, user_id: int, req: ReviewCreate) -> ReviewResponse:
    """发表课程评价。"""
    course = db.query(Course).filter(Course.id == course_id, Course.status == 1).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

    review = CourseReview(
        course_id=course_id,
        user_id=user_id,
        is_anonymous=1 if req.is_anonymous else 0,
        difficulty_rating=req.difficulty_rating,
        score_rating=req.score_rating,
        content=req.content,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _build_review_response(db, review, user_id)


def _build_review_response(db: Session, review: CourseReview, current_user_id: int | None) -> ReviewResponse:
    """构建评价响应（填充昵称、是否已点赞、是否已收藏）。"""
    resp = ReviewResponse.model_validate(review)

    # 匿名处理
    if review.is_anonymous:
        resp.nickname = "匿名用户"
    else:
        user = db.query(User).filter(User.id == review.user_id).first()
        resp.nickname = user.nickname if user else "未知用户"

    # 当前用户是否已点赞
    if current_user_id:
        liked = db.query(ReviewLike).filter(
            ReviewLike.review_id == review.id, ReviewLike.user_id == current_user_id
        ).first()
        resp.is_liked = liked is not None

        favorited = db.query(UserFavorite).filter(
            UserFavorite.course_review_id == review.id, UserFavorite.user_id == current_user_id
        ).first()
        resp.is_favorited = favorited is not None

    return resp


# ──── 点赞（幂等：点赞 ↔ 取消点赞） ────

def toggle_like(db: Session, review_id: int, user_id: int) -> dict:
    """点赞或取消点赞，返回最新状态。"""
    review = db.query(CourseReview).filter(CourseReview.id == review_id, CourseReview.status == 1).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价不存在")

    existing = db.query(ReviewLike).filter(
        ReviewLike.review_id == review_id, ReviewLike.user_id == user_id
    ).first()

    if existing:
        # 取消点赞
        db.delete(existing)
        review.like_count = max(0, review.like_count - 1)
        db.commit()
        return {"is_liked": False, "like_count": review.like_count}
    else:
        # 点赞
        like = ReviewLike(review_id=review_id, user_id=user_id)
        db.add(like)
        review.like_count += 1
        db.commit()
        return {"is_liked": True, "like_count": review.like_count}


# ──── 评论 ────

def get_comments(db: Session, review_id: int, page: int = 1, page_size: int = 20) -> PageResponse:
    """获取评价的评论列表。"""
    q = db.query(ReviewComment).filter(ReviewComment.review_id == review_id)
    total = q.count()
    comments = q.order_by(ReviewComment.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in comments:
        resp = CommentResponse.model_validate(c)
        user = db.query(User).filter(User.id == c.user_id).first()
        resp.nickname = user.nickname if user else "未知用户"
        items.append(resp)

    total_pages = (total + page_size - 1) // page_size
    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


def create_comment(db: Session, review_id: int, user_id: int, req: CommentCreate) -> CommentResponse:
    """发表评论。"""
    review = db.query(CourseReview).filter(CourseReview.id == review_id, CourseReview.status == 1).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价不存在")

    comment = ReviewComment(
        review_id=review_id,
        user_id=user_id,
        parent_id=req.parent_id,
        content=req.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    resp = CommentResponse.model_validate(comment)
    user = db.query(User).filter(User.id == user_id).first()
    resp.nickname = user.nickname if user else "未知用户"
    return resp


# ──── 收藏 ────

def toggle_favorite(db: Session, review_id: int, user_id: int) -> dict:
    """收藏或取消收藏评价。"""
    existing = db.query(UserFavorite).filter(
        UserFavorite.course_review_id == review_id, UserFavorite.user_id == user_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorited": False}
    else:
        fav = UserFavorite(course_review_id=review_id, user_id=user_id)
        db.add(fav)
        db.commit()
        return {"is_favorited": True}


def get_my_favorites(db: Session, user_id: int, page: int = 1, page_size: int = 10) -> PageResponse:
    """获取我的收藏列表。"""
    q = db.query(UserFavorite).filter(UserFavorite.user_id == user_id).order_by(desc(UserFavorite.id))
    total = q.count()
    favs = q.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for fav in favs:
        review = db.query(CourseReview).filter(CourseReview.id == fav.course_review_id).first()
        if review and review.status == 1:
            items.append(_build_review_response(db, review, user_id))

    total_pages = (total + page_size - 1) // page_size
    return PageResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ──── 举报 ────

def report_review(db: Session, review_id: int, user_id: int, req: ReportCreate) -> dict:
    """举报评价。"""
    review = db.query(CourseReview).filter(CourseReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价不存在")

    report = ReviewReport(review_id=review_id, user_id=user_id, reason=req.reason)
    db.add(report)
    db.commit()
    return {"message": "举报已提交，管理员将尽快处理"}
