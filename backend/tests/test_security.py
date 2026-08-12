"""
测试密码哈希与验证。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.security import hash_password, verify_password


class TestPassword:
    """密码哈希与验证测试。"""

    def test_hash_and_verify(self):
        """哈希后可以正确验证。"""
        plain = "my_secure_password"
        hashed = hash_password(plain)

        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails(self):
        """错误密码验证失败。"""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_unique(self):
        """相同密码两次哈希结果不同（随机盐）。"""
        plain = "same_password"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2
        # 但都能正确验证
        assert verify_password(plain, h1) is True
        assert verify_password(plain, h2) is True

    def test_empty_password(self):
        """空密码可以正常哈希和验证。"""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("something", hashed) is False
