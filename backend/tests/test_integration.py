"""
全流程集成测试：覆盖用户、课程、社团、POI、攻略、任务、搜索、管理后台等核心链路。
基于 SQLite 内存数据库运行，无需外部 MySQL。
"""
import pytest


# ═══════════════════════════════════════════════════════════════
# 一、系统端点
# ═══════════════════════════════════════════════════════════════

class TestSystemEndpoints:
    """系统级端点测试。"""

    def test_root_endpoint(self, client):
        """GET / 返回服务状态。"""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "大学萌新领航站 API 运行中"
        assert data["version"] == "2.1.0"
        assert "/docs" in data["docs"]

    def test_health_check(self, client):
        """GET /health 返回数据库连接状态。"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"


# ═══════════════════════════════════════════════════════════════
# 二、用户模块
# ═══════════════════════════════════════════════════════════════

class TestUserFlow:
    """用户注册、登录、个人信息全流程。"""

    def test_register_success(self, client):
        """正常注册。"""
        resp = client.post("/api/user/register", json={"nickname": "newuser", "password": "password123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["nickname"] == "newuser"
        assert data["user"]["role"] == "USER"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_register_duplicate_nickname(self, client):
        """重复昵称注册应失败。"""
        client.post("/api/user/register", json={"nickname": "dupuser", "password": "password123"})
        resp = client.post("/api/user/register", json={"nickname": "dupuser", "password": "password123"})
        assert resp.status_code == 400

    def test_register_nickname_too_short(self, client):
        """昵称过短应被校验拦截。"""
        resp = client.post("/api/user/register", json={"nickname": "a", "password": "password123"})
        assert resp.status_code == 422

    def test_register_password_too_short(self, client):
        """密码过短应被校验拦截。"""
        resp = client.post("/api/user/register", json={"nickname": "user2", "password": "123"})
        assert resp.status_code == 422

    def test_login_success(self, client, test_user):
        """正常登录。"""
        resp = client.post("/api/user/login", json={"nickname": "testuser", "password": "testpass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["nickname"] == "testuser"
        assert "access_token" in data["tokens"]

    def test_login_wrong_password(self, client, test_user):
        """密码错误应失败。"""
        resp = client.post("/api/user/login", json={"nickname": "testuser", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        """不存在的用户登录应失败。"""
        resp = client.post("/api/user/login", json={"nickname": "nobody", "password": "password123"})
        assert resp.status_code == 401

    def test_get_profile_unauthorized(self, client):
        """未登录访问个人信息应 403（HTTPBearer 默认行为）。"""
        resp = client.get("/api/user/profile")
        assert resp.status_code == 403

    def test_get_profile_success(self, client, test_user):
        """登录后获取个人信息。"""
        resp = client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nickname"] == "testuser"
        assert data["role"] == "USER"

    def test_update_profile(self, client, test_user):
        """修改个人信息。"""
        resp = client.put(
            "/api/user/profile",
            json={"college": "软件学院", "major": "软件工程"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["college"] == "软件学院"
        assert data["major"] == "软件工程"

    def test_refresh_token(self, client, test_user):
        """使用 refresh_token 换取新 token。"""
        resp = client.post("/api/user/refresh", json={"refresh_token": test_user["refresh_token"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data


# ═══════════════════════════════════════════════════════════════
# 三、课程模块
# ═══════════════════════════════════════════════════════════════

class TestCourseFlow:
    """课程浏览、评价、点赞、收藏、评论、举报全流程。"""

    def test_list_courses(self, client, seed_courses):
        """课程列表接口。"""
        resp = client.get("/api/courses")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

    def test_list_courses_with_filter(self, client, seed_courses):
        """按学院筛选课程。"""
        resp = client.get("/api/courses", params={"college": "软件学院"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        names = [c["name"] for c in data["items"]]
        assert "软件工程" in names
        assert "计算机组成原理" in names

    def test_course_detail(self, client, seed_courses):
        """课程详情。"""
        course_id = seed_courses[0].id
        resp = client.get(f"/api/courses/{course_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "高等数学"

    def test_course_detail_not_found(self, client):
        """不存在的课程应 404。"""
        resp = client.get("/api/courses/99999")
        assert resp.status_code == 404

    def test_create_review(self, client, seed_courses, test_user):
        """发表课程评价。"""
        course_id = seed_courses[0].id
        resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={
                "difficulty_rating": 4,
                "score_rating": 5,
                "content": "这门课非常有用，老师讲得也很好！",
                "is_anonymous": False,
            },
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "这门课非常有用，老师讲得也很好！"
        assert data["difficulty_rating"] == 4

    def test_create_review_content_too_short(self, client, seed_courses, test_user):
        """评价内容过短应 422。"""
        course_id = seed_courses[0].id
        resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 4, "score_rating": 5, "content": "短"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 422

    def test_list_reviews(self, client, seed_courses, test_user):
        """评价列表。"""
        course_id = seed_courses[0].id
        client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 3, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        resp = client.get(f"/api/courses/{course_id}/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_toggle_like(self, client, seed_courses, test_user):
        """点赞后再取消点赞。"""
        course_id = seed_courses[0].id
        review_resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 3, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        review_id = review_resp.json()["id"]

        # 点赞
        resp1 = client.post(
            f"/api/courses/reviews/{review_id}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["is_liked"] is True
        assert resp1.json()["like_count"] == 1

        # 取消点赞
        resp2 = client.post(
            f"/api/courses/reviews/{review_id}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["is_liked"] is False
        assert resp2.json()["like_count"] == 0

    def test_toggle_favorite(self, client, seed_courses, test_user):
        """收藏后再取消收藏。"""
        course_id = seed_courses[0].id
        review_resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 3, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        review_id = review_resp.json()["id"]

        # 收藏
        resp1 = client.post(
            f"/api/courses/reviews/{review_id}/favorite",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["is_favorited"] is True

        # 取消收藏
        resp2 = client.post(
            f"/api/courses/reviews/{review_id}/favorite",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["is_favorited"] is False

    def test_create_comment(self, client, seed_courses, test_user):
        """发表评论评论。"""
        course_id = seed_courses[0].id
        review_resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 3, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        review_id = review_resp.json()["id"]

        resp = client.post(
            f"/api/courses/reviews/{review_id}/comments",
            json={"content": "我也觉得这门课不错！"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "我也觉得这门课不错！"

    def test_report_review(self, client, seed_courses, test_user):
        """举报评价。"""
        course_id = seed_courses[0].id
        review_resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 3, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        review_id = review_resp.json()["id"]

        resp = client.post(
            f"/api/courses/reviews/{review_id}/report",
            json={"reason": "内容不适当"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        assert "举报已提交" in resp.json()["message"]


# ═══════════════════════════════════════════════════════════════
# 四、社团 / POI / 攻略
# ═══════════════════════════════════════════════════════════════

class TestClubPoiGuideFlow:
    """社团、地标、攻略浏览链路。"""

    def test_list_clubs(self, client, seed_clubs):
        resp = client.get("/api/clubs")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_club_detail(self, client, seed_clubs):
        club_id = seed_clubs[0].id
        resp = client.get(f"/api/clubs/{club_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "软件工程协会"

    def test_list_pois(self, client, seed_pois):
        resp = client.get("/api/pois")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_poi_detail(self, client, seed_pois):
        poi_id = seed_pois[0].id
        resp = client.get(f"/api/pois/{poi_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "图书馆"

    def test_list_guides(self, client, seed_guides):
        resp = client.get("/api/guides")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_guide_detail(self, client, seed_guides):
        guide_id = seed_guides[0].id
        resp = client.get(f"/api/guides/{guide_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "新生报到流程"

    def test_list_guides_with_category(self, client, seed_guides):
        resp = client.get("/api/guides", params={"category": "报到"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ═══════════════════════════════════════════════════════════════
# 五、任务 / 打卡 / 安全 / 首页
# ═══════════════════════════════════════════════════════════════

class TestTasksSafetyDashboard:
    """新生任务、安全防线、首页仪表盘。"""

    def test_list_tasks(self, client, seed_tasks):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 2

    def test_my_tasks(self, client, seed_tasks, test_user):
        """登录后查看我的任务（含打卡状态）。"""
        resp = client.get(
            "/api/tasks/my",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 2
        assert tasks[0]["is_checked"] is False

    def test_checkin_task(self, client, seed_tasks, test_user):
        """任务打卡。"""
        task_id = seed_tasks[0].id
        resp = client.post(
            f"/api/tasks/{task_id}/checkin",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed"] == 1
        # 2 个任务完成 1 个，不满 3 个，badge 为 None
        assert data["badge"] is None

    def test_checkin_same_task_twice(self, client, seed_tasks, test_user):
        """重复打卡应失败。"""
        task_id = seed_tasks[0].id
        client.post(
            f"/api/tasks/{task_id}/checkin",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        resp = client.post(
            f"/api/tasks/{task_id}/checkin",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 400
        assert "已完成打卡" in resp.json()["detail"]

    def test_safety_tips(self, client, seed_safety):
        resp = client.get("/api/safety-tips")
        assert resp.status_code == 200
        tips = resp.json()
        assert len(tips) == 2
        assert tips[0]["is_pinned"] is True

    def test_safety_tips_pinned_only(self, client, seed_safety):
        resp = client.get("/api/safety-tips", params={"pinned_only": "true"})
        assert resp.status_code == 200
        tips = resp.json()
        assert len(tips) == 1
        assert tips[0]["title"] == "防诈骗提醒"

    def test_dashboard(self, client, seed_all):
        """未登录访问首页仪表盘。"""
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_progress" in data
        assert "hot_reviews" in data
        assert "upcoming_events" in data
        assert "pinned_tips" in data

    def test_dashboard_with_user(self, client, seed_all, test_user):
        """登录后访问首页仪表盘。"""
        resp = client.get(
            "/api/dashboard",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_progress"]["completed"] == 0


# ═══════════════════════════════════════════════════════════════
# 六、全局搜索（含分页）
# ═══════════════════════════════════════════════════════════════

class TestSearch:
    """全局搜索及分页。"""

    def test_search_keyword_too_short(self, client):
        """关键词过短应 422。"""
        resp = client.get("/api/search", params={"keyword": "a"})
        assert resp.status_code == 422

    def test_search_no_results(self, client):
        """无匹配结果。"""
        resp = client.get("/api/search", params={"keyword": "不存在的词"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_search_course(self, client, seed_courses):
        resp = client.get("/api/search", params={"keyword": "数学"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        types = [item["type"] for item in data["items"]]
        assert "course" in types

    def test_search_club(self, client, seed_clubs):
        resp = client.get("/api/search", params={"keyword": "篮球"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        types = [item["type"] for item in data["items"]]
        assert "club" in types

    def test_search_poi(self, client, seed_pois):
        resp = client.get("/api/search", params={"keyword": "图书"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        types = [item["type"] for item in data["items"]]
        assert "poi" in types

    def test_search_guide(self, client, seed_guides):
        resp = client.get("/api/search", params={"keyword": "报到"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        types = [item["type"] for item in data["items"]]
        assert "guide" in types

    def test_search_pagination(self, client, seed_courses, seed_clubs, seed_pois, seed_guides):
        """搜索分页参数生效。"""
        # 用至少 2 个字符的关键词
        resp_all = client.get("/api/search", params={"keyword": "数学"})
        total = resp_all.json()["total"]
        if total <= 1:
            pytest.skip("数据量不足以测试分页")

        page_size = 1
        resp_page1 = client.get("/api/search", params={"keyword": "学", "page": 1, "page_size": page_size})
        data1 = resp_page1.json()
        assert data1["page_size"] == page_size
        assert len(data1["items"]) == 1
        assert data1["total_pages"] == total

        resp_page2 = client.get("/api/search", params={"keyword": "学", "page": 2, "page_size": page_size})
        data2 = resp_page2.json()
        assert len(data2["items"]) == 1
        assert data1["items"][0]["id"] != data2["items"][0]["id"]

    def test_search_alias(self, client, seed_courses):
        """搜索缩写扩展（如「高数」→「高等数学」）。"""
        resp = client.get("/api/search", params={"keyword": "高数"})
        assert resp.status_code == 200
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert "高等数学" in titles


# ═══════════════════════════════════════════════════════════════
# 七、管理后台
# ═══════════════════════════════════════════════════════════════

class TestAdmin:
    """管理员接口权限与功能。"""

    def test_admin_users_list(self, client, admin_user):
        """管理员获取用户列表。"""
        login_resp = client.post("/api/user/login", json={"nickname": "admin", "password": "admin123"})
        assert login_resp.status_code == 200
        token = login_resp.json()["tokens"]["access_token"]

        resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_admin_create_course(self, client, admin_user):
        """管理员创建课程。"""
        login_resp = client.post("/api/user/login", json={"nickname": "admin", "password": "admin123"})
        assert login_resp.status_code == 200
        token = login_resp.json()["tokens"]["access_token"]

        resp = client.post(
            "/api/admin/courses",
            json={"name": "测试课程", "teacher": "测试老师", "college": "测试学院", "category": "测试", "credit": 2.0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "测试课程"

    def test_admin_access_denied_for_normal_user(self, client, test_user):
        """普通用户访问管理后台应 403。"""
        resp = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 403

    def test_admin_access_denied_for_guest(self, client):
        """未登录访问管理后台应 403（HTTPBearer 默认行为）。"""
        resp = client.get("/api/admin/users")
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════
# 八、限流
# ═══════════════════════════════════════════════════════════════

class TestRateLimit:
    """登录/注册接口限流。"""

    def test_register_rate_limit(self, client):
        """快速多次注册应触发 429。"""
        responses = []
        for i in range(12):
            resp = client.post(
                "/api/user/register",
                json={"nickname": f"ratelimit{i}", "password": "password123"},
            )
            responses.append(resp.status_code)

        assert 429 in responses, f"期望出现 429，但得到的状态码: {responses}"


# ═══════════════════════════════════════════════════════════════
# 九、输入校验边界
# ═══════════════════════════════════════════════════════════════

class TestInputValidation:
    """各类输入校验边界测试。"""

    def test_login_nickname_too_short(self, client):
        resp = client.post("/api/user/login", json={"nickname": "a", "password": "password123"})
        assert resp.status_code == 422

    def test_search_keyword_max_length(self, client):
        """搜索关键词超过 100 字符应 422。"""
        long_kw = "a" * 101
        resp = client.get("/api/search", params={"keyword": long_kw})
        assert resp.status_code == 422

    def test_review_rating_out_of_range(self, client, seed_courses, test_user):
        """评分超出 1-5 范围应 422。"""
        course_id = seed_courses[0].id
        resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 10, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 422

    def test_report_reason_too_short(self, client, seed_courses, test_user):
        """举报原因过短应 422。"""
        course_id = seed_courses[0].id
        review_resp = client.post(
            f"/api/courses/{course_id}/reviews",
            json={"difficulty_rating": 3, "score_rating": 4, "content": "评价内容足够长" * 3},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        review_id = review_resp.json()["id"]

        resp = client.post(
            f"/api/courses/reviews/{review_id}/report",
            json={"reason": "短"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
        )
        assert resp.status_code == 422
