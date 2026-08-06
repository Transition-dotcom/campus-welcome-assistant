"""
校园导览相关模型：poi, poi_route, poi_correction
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import relationship
from app.database import Base


class POI(Base):
    __tablename__ = "poi"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="地标名称")
    category = Column(String(50), nullable=False, comment="教学楼/食堂/宿舍/快递点/运动场馆/行政楼/其他")
    description = Column(Text, nullable=True, comment="图文描述")
    photo_url = Column(String(500), nullable=True)
    open_hours = Column(String(200), nullable=True, comment="开放时间")
    floor_info = Column(String(500), nullable=True, comment="楼层指引")
    tips = Column(Text, nullable=True, comment="注意事项")
    lat = Column(DECIMAL(10, 7), nullable=True, comment="纬度（预留）")
    lng = Column(DECIMAL(10, 7), nullable=True, comment="经度（预留）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_poi_category", "category"),
    )

    corrections = relationship("POICorrection", back_populates="poi", cascade="all, delete-orphan")


class POIRoute(Base):
    __tablename__ = "poi_route"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_poi_id = Column(BigInteger, ForeignKey("poi.id"), nullable=False)
    to_poi_id = Column(BigInteger, ForeignKey("poi.id"), nullable=False)
    description = Column(Text, nullable=False, comment="路径文字描述")
    estimated_minutes = Column(Integer, nullable=True, comment="预估步行分钟数")

    __table_args__ = (
        Index("idx_route_from_to", "from_poi_id", "to_poi_id"),
    )

    from_poi = relationship("POI", foreign_keys=[from_poi_id])
    to_poi = relationship("POI", foreign_keys=[to_poi_id])


class POICorrection(Base):
    __tablename__ = "poi_correction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    poi_id = Column(BigInteger, ForeignKey("poi.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    content = Column(Text, nullable=False, comment="纠错内容")
    status = Column(String(20), nullable=False, default="pending", comment="pending/resolved")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    poi = relationship("POI", back_populates="corrections")
