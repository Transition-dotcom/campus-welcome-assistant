"""
pytest 配置：设置测试环境变量。
"""
import os

# 确保测试环境有 JWT 密钥
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-12345678")
