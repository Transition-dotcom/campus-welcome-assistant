"""
JWT 鉴权依赖。作为 FastAPI 的 Depends 注入到需要认证的路由中。
"""
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.jwt import decode_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    从请求头的 Bearer Token 中解析当前登录用户。
    验证失败 → 401。
    返回 (user_id, role) 元组。
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用 access_token",
        )

    user_id = int(payload.get("sub"))
    role = payload.get("role", "USER")
    return {"user_id": user_id, "role": role}


def get_admin_user(
    current_user: dict = Depends(get_current_user),
):
    """
    管理员权限校验。在 get_current_user 基础上检查角色是否为 ADMIN。
    非管理员 → 403。
    """
    if current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
