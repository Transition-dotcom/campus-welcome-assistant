"""
测试 JWT 工具函数：生成、解码、验证。
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
    get_role_from_token,
)
from app.config import settings


class TestJWT:
    """JWT Token 生成与验证测试。"""

    def test_create_and_decode_access_token(self):
        """生成 access token 并成功解码。"""
        token = create_access_token(user_id=1, role="USER")
        assert isinstance(token, str)
        assert len(token) > 20

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["role"] == "USER"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        """生成 refresh token 并成功解码。"""
        token = create_refresh_token(user_id=2, role="ADMIN")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "2"
        assert payload["role"] == "ADMIN"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """解码无效 token 返回 None。"""
        assert decode_token("not.a.valid.token") is None
        assert decode_token("") is None

    def test_get_user_id_from_token(self):
        """从 token 中提取 user_id。"""
        token = create_access_token(user_id=42, role="USER")
        assert get_user_id_from_token(token) == 42

    def test_get_role_from_token(self):
        """从 token 中提取角色。"""
        token = create_access_token(user_id=1, role="ADMIN")
        assert get_role_from_token(token) == "ADMIN"

    def test_token_type_distinction(self):
        """access token 和 refresh token 的 type 字段不同。"""
        access = create_access_token(user_id=1, role="USER")
        refresh = create_refresh_token(user_id=1, role="USER")

        access_payload = decode_token(access)
        refresh_payload = decode_token(refresh)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"

    def test_token_contains_expiration(self):
        """Token 包含过期时间字段。"""
        token = create_access_token(user_id=1, role="USER")
        payload = decode_token(token)
        assert "exp" in payload
        assert "iat" in payload
