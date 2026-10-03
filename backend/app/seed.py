r"""初始化数据库并写入模拟数据。

用法（在 backend 目录下）：
    .\.venv\Scripts\python -m app.seed
"""
from pathlib import Path

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Course, CourseDocument, Schedule, StudyPlan, User

SAMPLE_DOC_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "sample_docs" / "程序设计基础讲义.md"
)

COURSES = [
    {"code": "CS101", "name": "程序设计基础", "teacher": "李老师", "credit": 3, "semester": "2026-2027-1",
     "description": "Python 语言基础与编程思维入门"},
    {"code": "CS201", "name": "数据结构", "teacher": "王老师", "credit": 3.5, "semester": "2026-2027-1",
     "description": "线性表、树、图等核心数据结构"},
    {"code": "MATH101", "name": "高等数学", "teacher": "赵老师", "credit": 5, "semester": "2026-2027-1",
     "description": "微积分、极限与导数"},
    {"code": "ENG101", "name": "大学英语", "teacher": "孙老师", "credit": 2, "semester": "2026-2027-1",
     "description": "大学英语综合读写"},
    {"code": "AI101", "name": "人工智能导论", "teacher": "周老师", "credit": 2, "semester": "2026-2027-1",
     "description": "机器学习、大模型与 Agent 基础概念"},
]

# (user_key, course_code, weekday, start_period, end_period, week_start, week_end, location)
SCHEDULES = {
    "student01": [
        ("CS101", 1, 1, 2, 1, 16, "教学楼A301"),
        ("MATH101", 1, 3, 4, 1, 16, "教学楼A201"),
        ("ENG101", 2, 5, 6, 1, 16, "外语楼B102"),
        ("CS201", 3, 3, 4, 1, 16, "实验楼C305"),
        ("MATH101", 4, 1, 2, 1, 16, "教学楼A201"),
        ("AI101", 5, 7, 8, 1, 16, "教学楼A105"),
    ],
    "student02": [
        ("MATH101", 1, 5, 6, 1, 16, "教学楼A201"),
        ("CS101", 2, 1, 2, 1, 16, "教学楼A301"),
        ("CS201", 3, 5, 6, 1, 16, "实验楼C305"),
        ("ENG101", 4, 3, 4, 1, 16, "外语楼B102"),
        ("AI101", 5, 1, 2, 1, 16, "教学楼A105"),
    ],
}


def seed():
    # 先建表（seed 脚本独立运行，不经过 FastAPI 启动流程）
    Base.metadata.create_all(bind=engine)

    print("== 清空旧数据 ==")
    db = SessionLocal()
    try:
        db.query(StudyPlan).delete()
        db.query(Schedule).delete()
        db.query(CourseDocument).delete()
        db.query(Course).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()

    print("== 写入用户 ==")
    users = {
        "student01": User(username="student01", name="张三", role="student",
                          student_no="2023001", password_hash=hash_password("student01")),
        "student02": User(username="student02", name="李四", role="student",
                          student_no="2023002", password_hash=hash_password("student02")),
        "admin01": User(username="admin01", name="王老师", role="admin",
                        student_no=None, password_hash=hash_password("admin01")),
    }

    print("== 写入课程 ==")
    course_map = {}
    db = SessionLocal()
    try:
        for c in COURSES:
            course = Course(**c)
            db.add(course)
            db.flush()
            course_map[course.code] = course

        db.add_all(users.values())
        db.flush()

        print("== 写入课表 ==")
        for username, items in SCHEDULES.items():
            user = users[username]
            for code, weekday, start, end, ws, we, location in items:
                db.add(Schedule(
                    user_id=user.id,
                    course_id=course_map[code].id,
                    weekday=weekday,
                    start_period=start,
                    end_period=end,
                    week_start=ws,
                    week_end=we,
                    location=location,
                ))

        print("== 写入样例课程资料 ==")
        if SAMPLE_DOC_PATH.exists():
            db.add(CourseDocument(
                user_id=users["student01"].id,
                course_id=course_map["CS101"].id,
                filename=SAMPLE_DOC_PATH.name,
                file_path=str(SAMPLE_DOC_PATH),
                file_type="md",
                status="ready",
            ))

        db.commit()
        print("== 模拟数据写入完成 ==")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
