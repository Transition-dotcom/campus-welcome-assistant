"""
用户服务：注册、登录、个人信息管理。
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import RegisterRequest, LoginRequest, UpdateProfileRequest, LoginResponse, TokenResponse, UserProfile
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token


def register(db: Session, req: RegisterRequest) -> LoginResponse:
    """用户注册：创建账号并直接返回 token（注册即登录）。"""
    # 检查昵称唯一性
    if db.query(User).filter(User.nickname == req.nickname).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="昵称已被注册")

    # 检查学号唯一性
    if req.student_id and db.query(User).filter(User.student_id == req.student_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="学号已被注册")

    user = User(
        nickname=req.nickname,
        student_id=req.student_id,
        password_hash=hash_password(req.password),
        role="USER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成 token
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    return LoginResponse(
        user=UserProfile.model_validate(user),
        tokens=TokenResponse(access_token=access_token, refresh_token=refresh_token),
    )


def login(db: Session, req: LoginRequest) -> LoginResponse:
    """用户登录：验证凭证，返回 token。"""
    user = db.query(User).filter(User.nickname == req.nickname).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="昵称或密码错误")

    if user.status == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="昵称或密码错误")

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    return LoginResponse(
        user=UserProfile.model_validate(user),
        tokens=TokenResponse(access_token=access_token, refresh_token=refresh_token),
    )


def refresh_access_token(db: Session, refresh_token_str: str) -> TokenResponse:
    """使用 refresh_token 换取新的 access_token。"""
    from app.utils.jwt import decode_token

    payload = decode_token(refresh_token_str)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh_token 无效或已过期")

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status == 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),  # 同时刷新
    )


def get_profile(db: Session, user_id: int) -> UserProfile:
    """获取用户个人信息。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return UserProfile.model_validate(user)


def update_profile(db: Session, user_id: int, req: UpdateProfileRequest) -> UserProfile:
    """更新用户个人信息。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 只更新非 None 的字段
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return UserProfile.model_validate(user)
