"""
攻略与任务相关模型：guide, freshman_task, safety_tip
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Guide(Base):
    __tablename__ = "guide"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, comment="办事流程/生活指南/学习攻略")
    content = Column(JSON, nullable=True, comment="步骤内容（JSON数组）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_guide_category", "category"),
        Index("idx_guide_title", "title"),  # 搜索
    )


class FreshmanTask(Base):
    __tablename__ = "freshman_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, nullable=True, comment="任务说明")
    icon = Column(String(50), nullable=True, comment="Element Plus 图标名")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    badge_level = Column(String(20), nullable=True, comment="关联勋章等级")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_task_sort", "sort_order"),
    )

    checkins = relationship("UserCheckin", back_populates="task", cascade="all, delete-orphan")


class SafetyTip(Base):
    __tablename__ = "safety_tip"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_pinned = Column(Integer, nullable=False, default=0, comment="是否置顶")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_safety_pinned_sort", "is_pinned", "sort_order"),
    )
