r"""MCP 服务器：把业务能力封装成标准工具，供 Agent 调用。

以 stdio 子进程方式被 Agent 拉起：
    python -m app.mcp.server

所有工具都要求 user_id 参数——该值由 Agent 侧强制绑定为登录用户，工具内不再重复鉴权。
"""
from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.course import Course, Schedule
from app.models.document import CourseDocument
from app.models.plan import StudyPlan
from app.rag.retriever import retrieve

mcp = FastMCP("course-agent")


@mcp.tool()
def get_my_schedule(user_id: int) -> list[dict]:
    """查询指定学生的完整课表（星期、节次、课程、教师、周次、教室）。"""
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(Schedule, Course.name, Course.code, Course.teacher)
            .join(Course, Schedule.course_id == Course.id)
            .filter(Schedule.user_id == user_id)
            .all()
        )
        return [
            {
                "weekday": s.weekday,
                "start_period": s.start_period,
                "end_period": s.end_period,
                "week_start": s.week_start,
                "week_end": s.week_end,
                "location": s.location,
                "course_name": name,
                "course_code": code,
                "teacher": teacher,
            }
            for s, name, code, teacher in rows
        ]
    finally:
        db.close()


@mcp.tool()
def search_course_documents(user_id: int, query: str, top_k: int = 3) -> list[dict]:
    """在指定学生的课程资料中做语义检索（RAG），返回最相关的片段及来源文件名。"""
    db: Session = SessionLocal()
    try:
        return retrieve(db, user_id, query, top_k)
    finally:
        db.close()


@mcp.tool()
def list_my_documents(user_id: int) -> list[dict]:
    """列出指定学生已上传的课程资料。"""
    db: Session = SessionLocal()
    try:
        docs = db.query(CourseDocument).filter(CourseDocument.user_id == user_id).all()
        return [
            {"id": d.id, "filename": d.filename, "file_type": d.file_type, "status": d.status}
            for d in docs
        ]
    finally:
        db.close()


@mcp.tool()
def save_study_plan(user_id: int, title: str, goal: str, content: str) -> dict:
    """为指定学生保存一份学习计划并落库，返回计划 id。"""
    db: Session = SessionLocal()
    try:
        plan = StudyPlan(user_id=user_id, title=title, goal=goal, content=content, status="active")
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return {"id": plan.id, "title": plan.title, "status": plan.status}
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
