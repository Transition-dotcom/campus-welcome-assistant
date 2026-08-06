"""
JWT Token 生成与验证工具。
"""
from __future__ import annotations
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.config import settings


def create_access_token(user_id: int, role: str) -> str:
    """生成 access_token（短期，2小时）。"""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int, role: str) -> str:
    """生成 refresh_token（长期，7天）。"""
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """解码 token，返回 payload；验证失败返回 None。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> int | None:
    """从 token 中提取 user_id。"""
    payload = decode_token(token)
    if payload is None:
        return None
    return int(payload.get("sub"))


def get_role_from_token(token: str) -> str | None:
    """从 token 中提取角色。"""
    payload = decode_token(token)
    if payload is None:
        return None
    return payload.get("role")
