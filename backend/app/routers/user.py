"""
用户模块路由：注册、登录、个人信息。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.user import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    UpdateProfileRequest, LoginResponse, TokenResponse, UserProfile,
)
from app.services import user_service

router = APIRouter(prefix="/api/user", tags=["用户中心"])


@router.post("/register", response_model=LoginResponse, summary="用户注册")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户，成功后直接返回 token（注册即登录）。"""
    return user_service.register(db, req)


@router.post("/login", response_model=LoginResponse, summary="用户登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """使用昵称和密码登录，返回 access_token 和 refresh_token。"""
    return user_service.login(db, req)


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """使用 refresh_token 换取新的 token 对。"""
    return user_service.refresh_access_token(db, req.refresh_token)


@router.get("/profile", response_model=UserProfile, summary="获取个人信息")
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前登录用户的个人信息。"""
    return user_service.get_profile(db, current_user["user_id"])


@router.put("/profile", response_model=UserProfile, summary="修改个人信息")
def update_profile(
    req: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前登录用户的个人信息（仅更新提交的字段）。"""
    return user_service.update_profile(db, current_user["user_id"], req)
