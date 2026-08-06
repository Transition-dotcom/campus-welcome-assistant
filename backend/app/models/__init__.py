"""
统一导出所有模型，方便 Base.metadata.create_all 一次性建表。
"""
from app.models.user import User, UserFavorite, UserCheckin
from app.models.course import Course, CourseReview, ReviewComment, ReviewLike, ReviewReport
from app.models.club import Club, ClubEvent
from app.models.poi import POI, POIRoute, POICorrection
from app.models.guide import Guide, FreshmanTask, SafetyTip

# 延迟导入避免循环引用
UserFavorite.review = None  # 在 user.py 和 course.py 中已定义，此处占位
