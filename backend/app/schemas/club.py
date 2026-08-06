"""
社团模块的 Pydantic 模型。
"""
from datetime import datetime
from pydantic import BaseModel


class ClubBase(BaseModel):
    name: str
    category: str
    logo_url: str | None = None
    description: str | None = None
    activity_frequency: str | None = None
    requirements: str | None = None
    tips: str | None = None
    contact: str | None = None


class ClubCreate(ClubBase):
    pass


class ClubResponse(ClubBase):
    id: int
    status: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClubEventBase(BaseModel):
    title: str
    event_type: str | None = None
    event_time: datetime
    location: str | None = None
    description: str | None = None


class ClubEventCreate(ClubEventBase):
    pass


class ClubEventResponse(ClubEventBase):
    id: int
    club_id: int
    created_at: datetime

    class Config:
        from_attributes = True
