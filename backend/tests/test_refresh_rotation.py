"""
测试 refresh token 轮换撤销机制（token_version）。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.jwt import decode_token


class TestRefreshRotation:
    """refresh_token 轮换：每次刷新版本 +1，旧 token 立即失效。"""

    def test_token_contains_ver_claim(self):
        """access/refresh token 均携带 ver 版本号。"""
        from app.utils.jwt import create_access_token, create_refresh_token

        access = decode_token(create_access_token(1, "USER", ver=3))
        refresh = decode_token(create_refresh_token(1, "USER", ver=3))
        assert access["ver"] == 3
        assert refresh["ver"] == 3

    def test_refresh_rotation_flow(self, client, test_user):
        """刷新成功 → 新 token 可用、旧 refresh_token 复用被拒 401。"""
        old_refresh = test_user["refresh_token"]

        # 第一次刷新成功
        resp = client.post("/api/user/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 200, resp.text
        tokens1 = resp.json()
        assert tokens1["refresh_token"] != old_refresh

        # 旧 refresh_token 已被轮换作废 → 401
        resp = client.post("/api/user/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 401

        # 新 refresh_token 继续可用（再次轮换）
        resp = client.post("/api/user/refresh", json={"refresh_token": tokens1["refresh_token"]})
        assert resp.status_code == 200
        assert resp.json()["refresh_token"] != tokens1["refresh_token"]

        # 新 access_token 仍能访问受保护接口
        resp = client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {tokens1['access_token']}"},
        )
        assert resp.status_code == 200

    def test_token_version_increments_in_db(self, client, test_user, db_session):
        """每次刷新后数据库中 token_version +1。"""
        from app.models.user import User

        user = db_session.query(User).filter(User.id == test_user["user_id"]).first()
        v0 = user.token_version

        resp = client.post("/api/user/refresh", json={"refresh_token": test_user["refresh_token"]})
        assert resp.status_code == 200

        db_session.refresh(user)
        assert user.token_version == v0 + 1

    def test_admin_disabled_refresh_rejected(self, client, admin_user, db_session):
        """禁用用户的 refresh_token 被拒（与轮换机制配合）。"""
        from app.utils.jwt import create_refresh_token

        refresh = create_refresh_token(admin_user.id, admin_user.role, admin_user.token_version)
        admin_user.status = 0
        db_session.commit()

        resp = client.post("/api/user/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 401
