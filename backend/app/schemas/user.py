"""
用户模块的 Pydantic 模型（请求体 & 响应体）。
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


# ──── 请求体 ────

class RegisterRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=50, description="昵称")
    password: str = Field(..., min_length=6, max_length=100, description="密码（最少6位）")
    student_id: str | None = Field(None, max_length=20, description="学号（可选）")


class LoginRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=50, description="昵称")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="refresh_token")


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(None, min_length=2, max_length=50)
    college: str | None = Field(None, max_length=100)
    major: str | None = Field(None, max_length=100)
    grade: str | None = Field(None, max_length=20)
    avatar_url: str | None = Field(None, max_length=500)


# ──── 响应体 ────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: int
    nickname: str
    student_id: str | None
    college: str | None
    major: str | None
    grade: str | None
    avatar_url: str | None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserProfile
    tokens: TokenResponse
