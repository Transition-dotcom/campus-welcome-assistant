"""
审查后修复的新增测试：安全修复、数据正确性、管理端新接口。
基于 SQLite 内存数据库运行。
"""
from datetime import datetime, timedelta

import pytest


def _admin_headers(client, admin_user) -> dict:
    """管理员登录并返回带 token 的请求头。"""
    login_resp = client.post("/api/user/login", json={"nickname": "admin", "password": "admin123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}, login_resp.json()["user"]


def _create_review(client, course_id: int, token: str, content: str = "这是一条足够长的测试评价内容" * 2,
                   is_anonymous: bool = False) -> dict:
    """发表一条评价并返回 JSON。"""
    resp = client.post(
        f"/api/courses/{course_id}/reviews",
        json={
            "difficulty_rating": 3,
            "score_rating": 4,
            "content": content,
            "is_anonymous": is_anonymous,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════
# A. 安全修复
# ═══════════════════════════════════════════════════════════════

class TestAnonymousReviewHidesUserId:
    """匿名评价不应泄漏发布者 user_id。"""

    def test_anonymous_review_user_id_is_null(self, client, seed_courses, test_user):
        course_id = seed_courses[0].id
        review = _create_review(client, course_id, test_user["access_token"], is_anonymous=True)
        assert review["user_id"] is None

        # 列表接口同样置空
        resp = client.get(f"/api/courses/{course_id}/reviews")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["user_id"] is None
        assert item["nickname"] == "匿名用户"

    def test_named_review_keeps_user_id(self, client, seed_courses, test_user):
        course_id = seed_courses[0].id
        review = _create_review(client, course_id, test_user["access_token"], is_anonymous=False)
        assert review["user_id"] == test_user["user_id"]


class TestDisabledUserTokenInvalid:
    """禁用用户后其已签发 token 立即失效（鉴权回查 DB）。"""

    def test_disabled_user_old_token_401_and_reenable_login(self, client, seed_courses, test_user, admin_user):
        headers, admin = _admin_headers(client, admin_user)

        # 禁用用户
        resp = client.put(
            f"/api/admin/users/{test_user['user_id']}/status",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "已禁用"

        # 旧 token 访问受保护接口 → 401
        resp = client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 401

        # 禁用期间无法登录
        resp = client.post("/api/user/login", json={"nickname": "testuser", "password": "testpass123"})
        assert resp.status_code == 403

        # 重新启用后可正常登录
        resp = client.put(
            f"/api/admin/users/{test_user['user_id']}/status",
            json={"status": 1},
            headers=headers,
        )
        assert resp.status_code == 200
        resp = client.post("/api/user/login", json={"nickname": "testuser", "password": "testpass123"})
        assert resp.status_code == 200

    def test_admin_cannot_disable_self(self, client, admin_user):
        headers, admin = _admin_headers(client, admin_user)
        resp = client.put(
            f"/api/admin/users/{admin['id']}/status",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_disable_nonexistent_user_404(self, client, admin_user):
        headers, _ = _admin_headers(client, admin_user)
        resp = client.put("/api/admin/users/99999/status", json={"status": 0}, headers=headers)
        assert resp.status_code == 404


class TestRateLimitSeparation:
    """登录与注册使用独立的限流器。"""

    def test_register_limit_does_not_block_login(self, client):
        # 注册 10 次（配额内）
        for i in range(10):
            resp = client.post("/api/user/register", json={"nickname": f"sepu{i}", "password": "password123"})
            assert resp.status_code == 200
        # 第 11 次注册触发 429
        resp = client.post("/api/user/register", json={"nickname": "sepu10", "password": "password123"})
        assert resp.status_code == 429
        # 登录不受注册限流影响
        resp = client.post("/api/user/login", json={"nickname": "sepu0", "password": "password123"})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# B. 数据正确性
# ═══════════════════════════════════════════════════════════════

class TestReviewTargetExistence:
    """get_reviews / get_comments 校验目标存在。"""

    def test_get_reviews_course_not_found(self, client):
        resp = client.get("/api/courses/99999/reviews")
        assert resp.status_code == 404

    def test_get_reviews_removed_course_404(self, client, seed_courses, admin_user):
        headers, _ = _admin_headers(client, admin_user)
        course_id = seed_courses[0].id
        assert client.delete(f"/api/admin/courses/{course_id}", headers=headers).status_code == 200
        resp = client.get(f"/api/courses/{course_id}/reviews")
        assert resp.status_code == 404

    def test_get_comments_review_not_found(self, client):
        resp = client.get("/api/courses/reviews/99999/comments")
        assert resp.status_code == 404


class TestFavoriteExistence:
    """收藏不存在的评价返回 404。"""

    def test_favorite_nonexistent_review(self, client, test_user):
        resp = client.post(
            "/api/courses/reviews/99999/favorite",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 404

    def test_my_favorites_total_matches_items(self, client, seed_courses, test_user, db_session):
        """total 与 items 一致：已下架评价不计入 total。"""
        from app.models.course import CourseReview

        course_id = seed_courses[0].id
        r1 = _create_review(client, course_id, test_user["access_token"], content="第一条收藏评价内容足够长")
        r2 = _create_review(client, course_id, test_user["access_token"], content="第二条收藏评价内容足够长")

        for rid in (r1["id"], r2["id"]):
            resp = client.post(
                f"/api/courses/reviews/{rid}/favorite",
                headers={"Authorization": f"Bearer {test_user['access_token']}"},
            )
            assert resp.status_code == 200

        # 管理员下架第二条评价（直接改库模拟 remove_review）
        review = db_session.query(CourseReview).filter(CourseReview.id == r2["id"]).first()
        review.status = 0
        db_session.commit()

        resp = client.get(
            "/api/courses/favorites/my",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == r1["id"]


class TestParentIdValidation:
    """parent_id 非法（不存在/跨评价/回复二级评论）→ 400/404。"""

    def test_parent_comment_validations(self, client, seed_courses, test_user):
        course_a = seed_courses[0].id
        course_b = seed_courses[1].id
        ra = _create_review(client, course_a, test_user["access_token"])
        rb = _create_review(client, course_b, test_user["access_token"])

        # 一级评论
        resp = client.post(
            f"/api/courses/reviews/{ra['id']}/comments",
            json={"content": "一级评论"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        comment1_id = resp.json()["id"]

        # 跨评价回复 → 400
        resp = client.post(
            f"/api/courses/reviews/{rb['id']}/comments",
            json={"content": "跨评价回复", "parent_id": comment1_id},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 400

        # 回复一级评论 → 200（二级评论）
        resp = client.post(
            f"/api/courses/reviews/{ra['id']}/comments",
            json={"content": "回复一级评论", "parent_id": comment1_id},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        comment2_id = resp.json()["id"]

        # 回复二级评论 → 400（最多两级）
        resp = client.post(
            f"/api/courses/reviews/{ra['id']}/comments",
            json={"content": "回复二级评论", "parent_id": comment2_id},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 400

        # 父评论不存在 → 404
        resp = client.post(
            f"/api/courses/reviews/{ra['id']}/comments",
            json={"content": "回复不存在的评论", "parent_id": 99999},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 404


class TestToggleLikeCount:
    """点赞重复点击：toggle 两次回到未点赞，计数回 0。"""

    def test_toggle_like_twice(self, client, seed_courses, test_user):
        course_id = seed_courses[0].id
        review = _create_review(client, course_id, test_user["access_token"])

        resp1 = client.post(
            f"/api/courses/reviews/{review['id']}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp1.status_code == 200
        assert resp1.json() == {"is_liked": True, "like_count": 1}

        resp2 = client.post(
            f"/api/courses/reviews/{review['id']}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp2.status_code == 200
        assert resp2.json() == {"is_liked": False, "like_count": 0}

        # 列表接口计数同样为 0
        listing = client.get(f"/api/courses/{course_id}/reviews").json()
        assert listing["items"][0]["like_count"] == 0


class TestDuplicateReport:
    """同一用户对同一评价存在 pending 举报时拒绝重复提交。"""

    def test_duplicate_pending_report(self, client, seed_courses, test_user):
        course_id = seed_courses[0].id
        review = _create_review(client, course_id, test_user["access_token"])

        payload = {"reason": "内容疑似广告，请审核"}
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        resp = client.post(f"/api/courses/reviews/{review['id']}/report", json=payload, headers=headers)
        assert resp.status_code == 200

        resp = client.post(f"/api/courses/reviews/{review['id']}/report", json=payload, headers=headers)
        assert resp.status_code == 400
        assert "已举报" in resp.json()["detail"]


class TestPoiSoftDelete:
    """POI 删除改为软删除：列表/详情不可见，纠错关联信息仍可读。"""

    def test_poi_soft_delete(self, client, seed_pois, test_user, admin_user):
        headers, _ = _admin_headers(client, admin_user)
        poi_id = seed_pois[0].id

        # 删除前可见
        assert client.get(f"/api/pois/{poi_id}").status_code == 200

        # 提交纠错
        resp = client.post(
            "/api/pois/correction",
            json={"poi_id": poi_id, "content": "开放时间已更新"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200

        # 管理员删除（软删除）
        resp = client.delete(f"/api/admin/pois/{poi_id}", headers=headers)
        assert resp.status_code == 200

        # 详情 404，列表不再包含
        assert client.get(f"/api/pois/{poi_id}").status_code == 404
        pois = client.get("/api/pois").json()
        assert all(p["id"] != poi_id for p in pois["items"])

        # 已下架地标不能再提交纠错
        resp = client.post(
            "/api/pois/correction",
            json={"poi_id": poi_id, "content": "第二次纠错"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 404

        # 纠错列表仍可读，且 JOIN 出地标名称
        resp = client.get("/api/admin/corrections", headers=headers)
        assert resp.status_code == 200
        corrections = resp.json()
        assert len(corrections) >= 1
        assert corrections[0]["poi_name"] == "图书馆"


class TestRemovedClubEventsHidden:
    """下架社团的活动不再展示。"""

    def test_removed_club_events_hidden(self, client, seed_clubs, admin_user):
        from app.models.club import ClubEvent

        headers, _ = _admin_headers(client, admin_user)
        club1, club2 = seed_clubs[0], seed_clubs[1]
        future = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        for club, title in ((club1, "活动A"), (club2, "活动B")):
            resp = client.post(
                f"/api/admin/clubs/{club.id}/events",
                json={"title": title, "event_type": "开放日", "event_time": future},
                headers=headers,
            )
            assert resp.status_code == 200

        # 下架社团 1
        assert client.delete(f"/api/admin/clubs/{club1.id}", headers=headers).status_code == 200

        resp = client.get("/api/clubs/events/upcoming")
        assert resp.status_code == 200
        titles = [e["title"] for e in resp.json()]
        assert "活动A" not in titles
        assert "活动B" in titles


# ═══════════════════════════════════════════════════════════════
# D. 管理端新接口
# ═══════════════════════════════════════════════════════════════

class TestAdminReports:
    """举报审核流程：提交举报 → admin 列表可见 → resolve(remove_review) → 评价下架。"""

    def test_report_review_flow(self, client, seed_courses, test_user, admin_user):
        course_id = seed_courses[0].id
        review = _create_review(client, course_id, test_user["access_token"])

        # 1. 用户提交举报
        resp = client.post(
            f"/api/courses/reviews/{review['id']}/report",
            json={"reason": "该评价包含不实内容"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200

        headers, _ = _admin_headers(client, admin_user)

        # 2. 管理员可见 pending 举报，含嵌套 review 与课程名
        resp = client.get("/api/admin/reports", params={"status": "pending"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        item = data["items"][0]
        assert item["review_id"] == review["id"]
        assert item["reporter_nickname"] == "testuser"
        assert item["status"] == "pending"
        assert item["review"]["id"] == review["id"]
        assert item["review"]["course_id"] == course_id
        assert item["review"]["course_name"] == "高等数学"

        # 3. resolve(remove_review) → 评价 status=0
        resp = client.post(
            f"/api/admin/reports/{item['id']}/resolve",
            json={"action": "remove_review"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "已处理"

        # 评价已从列表消失（status=0 被过滤）
        listing = client.get(f"/api/courses/{course_id}/reviews").json()
        assert listing["total"] == 0

        # 已处理的举报再处理 → 400；pending 列表为空
        resp = client.post(
            f"/api/admin/reports/{item['id']}/resolve",
            json={"action": "dismiss"},
            headers=headers,
        )
        assert resp.status_code == 400
        assert client.get("/api/admin/reports", params={"status": "pending"}, headers=headers).json()["total"] == 0
        assert client.get("/api/admin/reports", params={"status": "resolved"}, headers=headers).json()["total"] == 1

        # 不存在的举报 → 404
        resp = client.post("/api/admin/reports/99999/resolve", json={"action": "dismiss"}, headers=headers)
        assert resp.status_code == 404

    def test_report_dismiss_keeps_review(self, client, seed_courses, test_user, admin_user):
        course_id = seed_courses[0].id
        review = _create_review(client, course_id, test_user["access_token"])
        client.post(
            f"/api/courses/reviews/{review['id']}/report",
            json={"reason": "内容疑似不实"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        headers, _ = _admin_headers(client, admin_user)
        report_id = client.get("/api/admin/reports", headers=headers).json()["items"][0]["id"]

        resp = client.post(f"/api/admin/reports/{report_id}/resolve", json={"action": "dismiss"}, headers=headers)
        assert resp.status_code == 200
        # 驳回后评价仍可见
        assert client.get(f"/api/courses/{course_id}/reviews").json()["total"] == 1


class TestAdminGuides:
    """攻略管理 CRUD。"""

    VALID_CONTENT = [{"step": 1, "title": "第一步", "description": "描述一"}]

    def _create(self, client, headers, **overrides):
        payload = {"title": "测试攻略", "category": "办事流程", "content": self.VALID_CONTENT}
        payload.update(overrides)
        return client.post("/api/admin/guides", json=payload, headers=headers)

    def test_guide_crud(self, client, admin_user):
        headers, _ = _admin_headers(client, admin_user)

        # 创建
        resp = self._create(client, headers)
        assert resp.status_code == 200
        guide = resp.json()
        assert guide["title"] == "测试攻略"

        # 分页列表
        resp = client.get("/api/admin/guides", params={"page": 1, "page_size": 20}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data and "total" in data and "total_pages" in data
        assert data["total"] >= 1

        # 更新
        resp = client.put(
            f"/api/admin/guides/{guide['id']}",
            json={"title": "更新后的攻略", "category": "学习攻略", "content": self.VALID_CONTENT},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "更新后的攻略"

        # 删除（硬删除）
        resp = client.delete(f"/api/admin/guides/{guide['id']}", headers=headers)
        assert resp.status_code == 200
        assert client.get(f"/api/guides/{guide['id']}").status_code == 404

    def test_guide_content_validation(self, client, admin_user):
        headers, _ = _admin_headers(client, admin_user)

        # content 不是列表 → 422
        resp = self._create(client, headers, content="not-a-list")
        assert resp.status_code == 422

        # 每项缺少 description → 422
        resp = self._create(client, headers, content=[{"step": 1, "title": "缺描述"}])
        assert resp.status_code == 422

        # 每项缺少 title → 422
        resp = self._create(client, headers, content=[{"step": 1, "description": "缺标题"}])
        assert resp.status_code == 422

        # 非对象元素 → 422
        resp = self._create(client, headers, content=["不是对象"])
        assert resp.status_code == 422


class TestAdminTasks:
    """任务管理 CRUD。"""

    def test_task_crud_and_checkin_guard(self, client, seed_tasks, test_user, admin_user):
        headers, _ = _admin_headers(client, admin_user)

        # 全量列表按 sort_order 升序
        resp = client.get("/api/admin/tasks", headers=headers)
        assert resp.status_code == 200
        tasks = resp.json()
        orders = [t["sort_order"] for t in tasks]
        assert orders == sorted(orders)

        # 创建
        resp = client.post(
            "/api/admin/tasks",
            json={"title": "新任务", "description": "任务说明", "sort_order": 5, "badge_level": "bronze"},
            headers=headers,
        )
        assert resp.status_code == 200
        new_task = resp.json()
        assert new_task["title"] == "新任务"
        assert new_task["sort_order"] == 5

        # 更新
        resp = client.put(
            f"/api/admin/tasks/{new_task['id']}",
            json={"title": "更新任务", "icon": "Star"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "更新任务"
        assert resp.json()["icon"] == "Star"

        # 删除无打卡记录的任务 → 成功
        resp = client.delete(f"/api/admin/tasks/{new_task['id']}", headers=headers)
        assert resp.status_code == 200

        # 有打卡记录的任务删除 → 400
        task_id = seed_tasks[0].id
        resp = client.post(
            f"/api/tasks/{task_id}/checkin",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        resp = client.delete(f"/api/admin/tasks/{task_id}", headers=headers)
        assert resp.status_code == 400
        assert "打卡记录" in resp.json()["detail"]

        # 不存在的任务 → 404
        resp = client.delete("/api/admin/tasks/99999", headers=headers)
        assert resp.status_code == 404
