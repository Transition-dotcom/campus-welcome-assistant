"""
用户相关模型：user, user_favorite, user_checkin
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nickname = Column(String(50), nullable=False, unique=True, comment="昵称")
    student_id = Column(String(20), nullable=True, unique=True, comment="学号（可选）")
    password_hash = Column(String(255), nullable=False, comment="BCrypt 密码哈希")
    college = Column(String(100), nullable=True, comment="学院")
    major = Column(String(100), nullable=True, comment="专业")
    grade = Column(String(20), nullable=True, comment="入学年份")
    avatar_url = Column(String(500), nullable=True, comment="头像 URL")
    role = Column(String(20), nullable=False, default="USER", comment="角色：USER/ADMIN")
    status = Column(Integer, nullable=False, default=1, comment="1正常 0禁用")
    token_version = Column(Integer, nullable=False, default=0, comment="token 版本号：刷新时 +1，旧 refresh_token 立即失效")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("UserCheckin", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("CourseReview", back_populates="user", cascade="all, delete-orphan")


class UserFavorite(Base):
    __tablename__ = "user_favorite"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    course_review_id = Column(BigInteger, ForeignKey("course_review.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "course_review_id", name="uk_user_review"),
        # 联合唯一键以 (user_id, course_review_id) 为前缀，无法服务按评价查询收藏数的场景
        Index("idx_favorite_review_id", "course_review_id"),
    )

    user = relationship("User", back_populates="favorites")
    review = relationship("CourseReview", back_populates="favorited_by")


class UserCheckin(Base):
    __tablename__ = "user_checkin"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    task_id = Column(BigInteger, ForeignKey("freshman_task.id"), nullable=False)
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uk_user_task"),
        Index("idx_checkin_user_id", "user_id"),
        Index("idx_checkin_task_id", "task_id"),  # 管理端删除任务前检查打卡记录
    )

    user = relationship("User", back_populates="checkins")
    task = relationship("FreshmanTask", back_populates="checkins")
