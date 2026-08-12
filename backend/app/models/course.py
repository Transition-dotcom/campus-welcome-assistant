"""
课程评价相关模型：course, course_review, review_comment, review_like, review_report
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey, DECIMAL, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Course(Base):
    __tablename__ = "course"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="课程名称")
    teacher = Column(String(100), nullable=True, comment="授课教师")
    college = Column(String(100), nullable=True, comment="开课学院")
    category = Column(String(50), nullable=True, comment="课程类别")
    credit = Column(DECIMAL(4, 2), nullable=True, comment="学分")
    status = Column(Integer, nullable=False, default=1, comment="1正常 0下架")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_course_college", "college"),
        Index("idx_course_category", "category"),
    )

    reviews = relationship("CourseReview", back_populates="course", cascade="all, delete-orphan")


class CourseReview(Base):
    __tablename__ = "course_review"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, ForeignKey("course.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    is_anonymous = Column(Integer, nullable=False, default=0, comment="0实名 1匿名")
    difficulty_rating = Column(Integer, nullable=False, comment="难度 1-5")
    score_rating = Column(Integer, nullable=False, comment="给分 1-5")
    content = Column(Text, nullable=False, comment="评价正文")
    like_count = Column(Integer, nullable=False, default=0, comment="点赞数（冗余）")
    status = Column(Integer, nullable=False, default=1, comment="1正常 0被下架")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_review_course_id", "course_id"),
        Index("idx_review_user_id", "user_id"),
        Index("idx_review_created_at", "created_at"),
        Index("idx_review_hot", "status", "like_count", "id"),  # 热门评价排序
    )

    course = relationship("Course", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    comments = relationship("ReviewComment", back_populates="review", cascade="all, delete-orphan")
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    favorited_by = relationship("UserFavorite", back_populates="review", cascade="all, delete-orphan")
    reports = relationship("ReviewReport", back_populates="review", cascade="all, delete-orphan")


class ReviewComment(Base):
    __tablename__ = "review_comment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_id = Column(BigInteger, ForeignKey("course_review.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False, comment="评论者")
    parent_id = Column(BigInteger, nullable=True, comment="回复的评论ID，NULL为一级评论")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_comment_review_id", "review_id"),
    )

    review = relationship("CourseReview", back_populates="comments")


class ReviewLike(Base):
    __tablename__ = "review_like"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_id = Column(BigInteger, ForeignKey("course_review.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uk_review_user"),
        Index("idx_like_user_id", "user_id"),
    )

    review = relationship("CourseReview", back_populates="likes")


class ReviewReport(Base):
    __tablename__ = "review_report"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_id = Column(BigInteger, ForeignKey("course_review.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False, comment="举报人")
    reason = Column(String(500), nullable=False, comment="举报原因")
    status = Column(String(20), nullable=False, default="pending", comment="pending/resolved/dismissed")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_report_status", "status"),
    )

    review = relationship("CourseReview", back_populates="reports")
