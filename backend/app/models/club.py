"""
社团相关模型：club, club_event
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Club(Base):
    __tablename__ = "club"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="社团名称")
    category = Column(String(50), nullable=False, comment="学术科技/志愿公益/文体艺术/创新创业/其他")
    logo_url = Column(String(500), nullable=True, comment="Logo URL")
    description = Column(Text, nullable=True, comment="社团简介")
    activity_frequency = Column(String(100), nullable=True, comment="活动频率")
    requirements = Column(Text, nullable=True, comment="招新要求")
    tips = Column(Text, nullable=True, comment="防坑指南")
    contact = Column(String(200), nullable=True, comment="联系方式")
    status = Column(Integer, nullable=False, default=1, comment="1正常 0下架")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_club_category", "category"),
    )

    events = relationship("ClubEvent", back_populates="club", cascade="all, delete-orphan")


class ClubEvent(Base):
    __tablename__ = "club_event"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    club_id = Column(BigInteger, ForeignKey("club.id"), nullable=False)
    title = Column(String(200), nullable=False, comment="活动标题")
    event_type = Column(String(50), nullable=True, comment="宣讲会/面试/开放日/其他")
    event_time = Column(DateTime, nullable=False, comment="活动时间")
    location = Column(String(200), nullable=True, comment="地点")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_event_club_id", "club_id"),
        Index("idx_event_time", "event_time"),
    )

    club = relationship("Club", back_populates="events")
