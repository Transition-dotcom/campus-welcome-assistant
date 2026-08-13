"""
pytest 全局配置：SQLite 内存数据库 + 测试 Fixtures。
"""
import os

# 确保测试环境有 JWT 密钥
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-12345678")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ──── 0. Patch：SQLite 中 BigInteger 主键自增问题 ────
# SQLAlchemy 的 BigInteger 在 SQLite 中映射为 BIGINT，不支持 autoincrement。
# 在导入任何模型之前，将 SQLite 方言的 BIGINT 编译为 INTEGER。
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

_original_visit_BIGINT = SQLiteTypeCompiler.visit_BIGINT

def _visit_BIGINT_as_INTEGER(self, type_, **kw):
    return "INTEGER"

SQLiteTypeCompiler.visit_BIGINT = _visit_BIGINT_as_INTEGER

# ──── 1. 创建 SQLite 内存引擎 ────
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

# ──── 2. 在导入 main 之前替换全局 engine ────
import app.database

app.database.engine = TEST_ENGINE

# ──── 3. 建表 ────
from app.database import Base

Base.metadata.create_all(bind=TEST_ENGINE)

# ──── 4. 导入 app 并替换 get_db 依赖 ────
from app.main import app
from fastapi.testclient import TestClient


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.database import get_db
app.dependency_overrides[get_db] = override_get_db


# ──── Fixtures ────

@pytest.fixture(scope="function")
def db_session():
    """每个测试函数在独立事务中运行，结束后回滚，保持数据库干净。"""
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """提供已注入测试 session 的 TestClient。"""

    def _override():
        try:
            yield db_session
        finally:
            pass

    from app.database import get_db
    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_courses(db_session):
    """插入测试课程数据。"""
    from app.models.course import Course

    courses = [
        Course(name="高等数学", teacher="张教授", college="理学院", category="数学基础", credit=5.0),
        Course(name="线性代数", teacher="李教授", college="理学院", category="数学基础", credit=3.0),
        Course(name="软件工程", teacher="王教授", college="软件学院", category="专业核心", credit=4.0),
        Course(name="计算机组成原理", teacher="赵教授", college="软件学院", category="专业核心", credit=4.0),
    ]
    for c in courses:
        db_session.add(c)
    db_session.commit()
    for c in courses:
        db_session.refresh(c)
    return courses


@pytest.fixture(scope="function")
def seed_clubs(db_session):
    """插入测试社团数据。"""
    from app.models.club import Club

    clubs = [
        Club(name="软件工程协会", category="学术科技", description="编程爱好者的家"),
        Club(name="篮球社", category="体育", description="热爱篮球"),
    ]
    for c in clubs:
        db_session.add(c)
    db_session.commit()
    for c in clubs:
        db_session.refresh(c)
    return clubs


@pytest.fixture(scope="function")
def seed_pois(db_session):
    """插入测试地标数据。"""
    from app.models.poi import POI

    pois = [
        POI(name="图书馆", category="学习", description="学校主图书馆"),
        POI(name="体育馆", category="体育", description="综合体育馆"),
    ]
    for p in pois:
        db_session.add(p)
    db_session.commit()
    for p in pois:
        db_session.refresh(p)
    return pois


@pytest.fixture(scope="function")
def seed_guides(db_session):
    """插入测试攻略数据。"""
    from app.models.guide import Guide

    guides = [
        Guide(title="新生报到流程", category="报到", content=[{"step": 1, "text": "第一步..."}]),
        Guide(title="图书馆借阅指南", category="生活", content=[{"step": 1, "text": "先办卡..."}]),
    ]
    for g in guides:
        db_session.add(g)
    db_session.commit()
    for g in guides:
        db_session.refresh(g)
    return guides


@pytest.fixture(scope="function")
def seed_tasks(db_session):
    """插入测试任务数据。"""
    from app.models.guide import FreshmanTask

    tasks = [
        FreshmanTask(title="参观图书馆", description="去图书馆转一圈", sort_order=1),
        FreshmanTask(title="加入一个社团", description="参加社团活动", sort_order=2),
    ]
    for t in tasks:
        db_session.add(t)
    db_session.commit()
    for t in tasks:
        db_session.refresh(t)
    return tasks


@pytest.fixture(scope="function")
def seed_safety(db_session):
    """插入测试安全提示数据。"""
    from app.models.guide import SafetyTip

    tips = [
        SafetyTip(title="防诈骗提醒", content="不要轻信陌生电话", is_pinned=1, sort_order=1),
        SafetyTip(title="宿舍用电安全", content="禁止使用大功率电器", is_pinned=0, sort_order=2),
    ]
    for t in tips:
        db_session.add(t)
    db_session.commit()
    for t in tips:
        db_session.refresh(t)
    return tips


@pytest.fixture(scope="function")
def seed_all(db_session, seed_courses, seed_clubs, seed_pois, seed_guides, seed_tasks, seed_safety):
    """一键插入所有种子数据。"""
    return {
        "courses": seed_courses,
        "clubs": seed_clubs,
        "pois": seed_pois,
        "guides": seed_guides,
        "tasks": seed_tasks,
        "safety": seed_safety,
    }


@pytest.fixture(scope="function")
def test_user(client):
    """注册一个普通用户并返回用户信息 + token。"""
    resp = client.post("/api/user/register", json={"nickname": "testuser", "password": "testpass123"})
    assert resp.status_code == 200
    data = resp.json()
    return {
        "user_id": data["user"]["id"],
        "nickname": data["user"]["nickname"],
        "role": data["user"]["role"],
        "access_token": data["tokens"]["access_token"],
        "refresh_token": data["tokens"]["refresh_token"],
    }


@pytest.fixture(scope="function")
def admin_user(db_session):
    """直接在数据库插入管理员用户（跳过注册）。"""
    from app.models.user import User
    from app.utils.security import hash_password

    admin = User(
        nickname="admin",
        password_hash=hash_password("admin123"),
        role="ADMIN",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """每个测试前重置限流器状态，防止跨测试污染。"""
    from app.middleware.rate_limit import auth_limiter
    auth_limiter._clients.clear()
    yield
    auth_limiter._clients.clear()
