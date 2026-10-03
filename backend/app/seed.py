r"""初始化数据库并写入模拟数据。

用法（在 backend 目录下）：
    .\.venv\Scripts\python -m app.seed
"""
from pathlib import Path

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Assignment, Course, CourseDocument, Schedule, Score, StudyPlan, User

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


# (user_key, course_code, title, description, 偏移天数, 时点, status)
ASSIGNMENTS = [
    ("student01", "CS201", "数据结构实验三：二叉树遍历", "实现二叉树的前序/中序/后序遍历并提交实验报告", 2, "23:59", "pending"),
    ("student01", "MATH101", "高等数学第4章作业", "完成教材 P128 习题 4.3 第 1-10 题", 5, "23:59", "pending"),
    ("student01", "CS101", "程序设计基础课程设计", "提交图书管理系统源码与设计文档", -1, "23:59", "pending"),
    ("student02", "AI101", "人工智能导论文献综述", "阅读 3 篇大模型相关论文并撰写综述", 7, "23:59", "pending"),
]

# (user_key, course_code, score)
SCORES = [
    ("student01", "CS101", 92),
    ("student01", "CS201", 85),
    ("student01", "MATH101", 76),
    ("student01", "ENG101", 88),
    ("student02", "MATH101", 81),
    ("student02", "CS101", 95),
]


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

        print("== 写入作业 ==")
        from datetime import datetime, timedelta

        for user_key, code, title, desc, offset_days, time_of_day, status in ASSIGNMENTS:
            due = (datetime.now() + timedelta(days=offset_days)).replace(
                hour=int(time_of_day[:2]), minute=0, second=0, microsecond=0
            )
            db.add(Assignment(
                user_id=users[user_key].id,
                course_id=course_map[code].id,
                title=title,
                description=desc,
                due_at=due,
                status=status,
            ))

        print("== 写入成绩 ==")
        for user_key, code, score in SCORES:
            db.add(Score(user_id=users[user_key].id, course_id=course_map[code].id, score=score))

        db.commit()
        print("== 模拟数据写入完成 ==")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
