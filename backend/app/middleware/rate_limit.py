"""
简单的内存限流中间件：按 IP 限制请求频率，适用于单机部署。
"""
from __future__ import annotations
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    """基于滑动窗口的简单限流器。"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self):
        """清理超过 5 分钟未活动的客户端记录，防止内存无限增长。"""
        now = time.time()
        stale = [ip for ip, times in self._clients.items() if not times or now - times[-1] > 300]
        for ip in stale:
            del self._clients[ip]

    def is_allowed(self, client_ip: str) -> bool:
        """检查客户端是否在限流窗口内超过请求上限。"""
        now = time.time()
        window_start = now - self.window_seconds

        # 移除窗口外的记录
        self._clients[client_ip] = [t for t in self._clients[client_ip] if t > window_start]

        if len(self._clients[client_ip]) >= self.max_requests:
            return False

        self._clients[client_ip].append(now)

        # 定期清理（概率触发）
        if len(self._clients) > 1000 and hash(client_ip) % 100 == 0:
            self._cleanup()
        return True


def _check(client_ip: str, limiter: RateLimiter):
    """通用检查逻辑：超限返回 429。"""
    if not limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )


# 登录与注册各自独立的限流器实例（各自配额，互不挤占）
login_limiter = RateLimiter(max_requests=10, window_seconds=60)
register_limiter = RateLimiter(max_requests=10, window_seconds=60)

# 兼容旧引用（登录限流器）
auth_limiter = login_limiter


async def rate_limit_auth(request: Request):
    """FastAPI 依赖：对登录接口限流。超限返回 429。"""
    client_ip = request.client.host if request.client else "unknown"
    _check(client_ip, login_limiter)


async def rate_limit_register(request: Request):
    """FastAPI 依赖：对注册接口限流。超限返回 429。"""
    client_ip = request.client.host if request.client else "unknown"
    _check(client_ip, register_limiter)
