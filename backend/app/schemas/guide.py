"""
攻略与任务模块的 Pydantic 模型。
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class GuideResponse(BaseModel):
    id: int
    title: str
    category: str
    summary: str | None = None
    content: list | None = None  # JSON 步骤数组
    created_at: datetime

    class Config:
        from_attributes = True


class GuideUpsert(BaseModel):
    """管理端：创建/更新攻略。content 为步骤数组，每项含 step/title/description。"""
    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    summary: str | None = Field(None, max_length=500)
    content: list = Field(..., description="步骤数组（JSON）")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: list) -> list:
        """校验 content 是列表，且每项为包含 step/title/description 的字典。"""
        if not isinstance(v, list):
            raise ValueError("content 必须是步骤数组")
        for i, item in enumerate(v):
            if not isinstance(item, dict):
                raise ValueError(f"content[{i}] 必须是对象")
            if "step" not in item or not isinstance(item["step"], (int, str)):
                raise ValueError(f"content[{i}] 缺少 step 字段（数字或字符串）")
            for key in ("title", "description"):
                if key not in item or not isinstance(item[key], str):
                    raise ValueError(f"content[{i}] 缺少 {key} 字段（字符串）")
        return v


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


class FreshmanTaskUpsert(BaseModel):
    """管理端：创建/更新新生任务。"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int | None = Field(None, ge=0)
    badge_level: str | None = Field(None, max_length=20)


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
