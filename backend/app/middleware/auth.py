"""
JWT 鉴权依赖。作为 FastAPI 的 Depends 注入到需要认证的路由中。
"""
from __future__ import annotations
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
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

    安全说明：每次请求都会回查数据库，确认用户仍存在且未被禁用，
    角色也以数据库为准（不信任 token 中可被伪造的 role）。
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
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return {"user_id": user.id, "role": user.role}


def get_optional_user(request: Request, db: Session = Depends(get_db)):
    """
    可选鉴权：请求头带有效 Bearer Token 时返回用户信息，否则返回 None。
    用于"未登录可访问、登录后个性化"的接口（如首页仪表盘的任务进度）。
    token 有效但用户不存在/被禁用时同样按未登录处理（返回 None）。
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    payload = decode_token(auth.split(" ", 1)[1])
    if payload is None or payload.get("type") != "access":
        return None

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != 1:
        return None
    return {"user_id": user.id, "role": user.role}


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
