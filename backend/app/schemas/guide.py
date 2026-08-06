"""
攻略与任务模块的 Pydantic 模型。
"""
from datetime import datetime
from pydantic import BaseModel


class GuideResponse(BaseModel):
    id: int
    title: str
    category: str
    content: list | None = None  # JSON 步骤数组
    created_at: datetime

    class Config:
        from_attributes = True


class FreshmanTaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    icon: str | None
    sort_order: int
    badge_level: str | None
    is_checked: bool = False  # 当前用户是否已打卡
    created_at: datetime

    class Config:
        from_attributes = True


class SafetyTipResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: str | None
    sort_order: int
    is_pinned: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """首页仪表盘聚合数据。"""
    task_progress: dict  # {completed: int, total: int}
    hot_reviews: list   # 热门评价
    upcoming_events: list  # 近期社团活动
    pinned_tips: list   # 置顶安全提醒


class SearchResult(BaseModel):
    """全局搜索结果。"""
    type: str   # course / club / poi / guide
    id: int
    title: str
