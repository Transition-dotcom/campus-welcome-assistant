"""
课程评价模块的 Pydantic 模型。
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ──── 课程 ────

class CourseBase(BaseModel):
    name: str
    teacher: str | None = None
    college: str | None = None
    category: str | None = None
    credit: float | None = None


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    status: int
    review_count: int = 0  # 评价数（查询时填充）
    created_at: datetime

    class Config:
        from_attributes = True


# ──── 评价 ────

class ReviewCreate(BaseModel):
    difficulty_rating: int = Field(..., ge=1, le=5, description="难度评分 1-5")
    score_rating: int = Field(..., ge=1, le=5, description="给分评分 1-5")
    content: str = Field(..., min_length=10, max_length=5000, description="评价正文")
    is_anonymous: bool = False


class ReviewResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    nickname: str = "匿名用户"  # 服务层填充
    is_anonymous: bool
    difficulty_rating: int
    score_rating: int
    content: str
    like_count: int
    is_liked: bool = False  # 当前用户是否已点赞
    is_favorited: bool = False  # 当前用户是否已收藏
    status: int
    created_at: datetime

    class Config:
        from_attributes = True


# ──── 评论 ────

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: int | None = None  # 回复某条评论


class CommentResponse(BaseModel):
    id: int
    review_id: int
    user_id: int
    nickname: str = "匿名用户"
    parent_id: int | None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ──── 举报 ────

class ReportCreate(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
