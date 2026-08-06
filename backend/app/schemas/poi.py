"""
校园导览模块的 Pydantic 模型。
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class POIBase(BaseModel):
    name: str
    category: str
    description: str | None = None
    photo_url: str | None = None
    open_hours: str | None = None
    floor_info: str | None = None
    tips: str | None = None
    lat: float | None = None
    lng: float | None = None


class POICreate(POIBase):
    pass


class POIResponse(POIBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class POIRouteBase(BaseModel):
    from_poi_id: int
    to_poi_id: int
    description: str
    estimated_minutes: int | None = None


class POIRouteCreate(POIRouteBase):
    pass


class POIRouteResponse(POIRouteBase):
    id: int
    from_poi_name: str | None = None  # 查询时填充
    to_poi_name: str | None = None

    class Config:
        from_attributes = True


class POICorrectionCreate(BaseModel):
    poi_id: int
    content: str


class POICorrectionResponse(BaseModel):
    id: int
    poi_id: int
    user_id: int
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
