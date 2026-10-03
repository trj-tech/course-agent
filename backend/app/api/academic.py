"""学生端：我的作业、我的成绩、个人学习统计。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.assignment import Assignment
from app.models.conversation import AiConversation, AiMessage
from app.models.course import Course, Schedule
from app.models.document import CourseDocument
from app.models.plan import StudyPlan
from app.models.score import Score, score_to_gpapoint
from app.models.user import User

router = APIRouter(tags=["academic"])


# ---------- 我的作业 ----------

@router.get("/assignments")
def my_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Assignment, Course.name, Course.code)
        .join(Course, Assignment.course_id == Course.id, isouter=True)
        .filter(Assignment.user_id == current_user.id)
        .order_by(Assignment.status.desc(), Assignment.due_at)  # pending 在前（"pending"<"done"）
        .all()
    )
    now = datetime.now()
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "due_at": a.due_at.strftime("%Y-%m-%d %H:%M"),
            "days_left": round((a.due_at - now).total_seconds() / 86400, 1),
            "overdue": a.status == "pending" and a.due_at < now,
            "status": a.status,
            "course_name": cname,
            "course_code": ccode,
        }
        for a, cname, ccode in rows
    ]


class AssignmentStatusIn(BaseModel):
    status: str  # pending / done


@router.put("/assignments/{aid}/status")
def toggle_assignment(
    aid: int,
    payload: AssignmentStatusIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.get(Assignment, aid)
    if a is None or a.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="作业不存在")
    if payload.status not in ("pending", "done"):
        raise HTTPException(status_code=400, detail="status 仅支持 pending / done")
    a.status = payload.status
    db.commit()
    return {"id": a.id, "status": a.status}


# ---------- 我的成绩 ----------

def _score_summary(db: Session, user_id: int) -> dict:
    rows = (
        db.query(Score, Course.name, Course.code, Course.credit)
        .join(Course, Score.course_id == Course.id)
        .filter(Score.user_id == user_id)
        .all()
    )
    items = [
        {
            "course_name": name,
            "course_code": code,
            "credit": float(credit),
            "score": s.score,
            "gpapoint": score_to_gpapoint(s.score),
        }
        for s, name, code, credit in rows
    ]
    if not items:
        return {"gpa": None, "average": None, "weakest": None, "courses": []}
    total_credit = sum(i["credit"] for i in items)
    weakest = min(items, key=lambda i: i["score"])
    return {
        "gpa": round(sum(i["gpapoint"] * i["credit"] for i in items) / total_credit, 2),
        "average": round(sum(i["score"] * i["credit"] for i in items) / total_credit, 1),
        "weakest": {"course_name": weakest["course_name"], "score": weakest["score"]},
        "courses": items,
    }


@router.get("/scores/me")
def my_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _score_summary(db, current_user.id)


# ---------- 个人学习统计 ----------

@router.get("/stats/me")
def my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv_ids = [
        cid
        for (cid,) in db.query(AiConversation.id)
        .filter(AiConversation.user_id == current_user.id)
        .all()
    ]
    q_msg = db.query(AiMessage)
    if conv_ids:
        q_msg = q_msg.filter(AiMessage.conversation_id.in_(conv_ids))
    messages = q_msg.count()
    assistant_msgs = []
    if conv_ids:
        assistant_msgs = (
            q_msg.filter(AiMessage.role == "assistant").all()
        )

    # 工具调用总数与分布（从工具痕迹 JSON 统计）
    tool_total = 0
    tool_dist: dict[str, int] = {}
    latencies = [m.latency_ms for m in assistant_msgs if m.latency_ms]
    first_tokens = [m.first_token_ms for m in assistant_msgs if m.first_token_ms]
    for m in assistant_msgs:
        if not m.tool_calls:
            continue
        try:
            import json

            records = json.loads(m.tool_calls)
        except (ValueError, TypeError):
            continue
        for rec in records if isinstance(records, list) else []:
            name = rec.get("name") if isinstance(rec, dict) else None
            if name:
                tool_total += 1
                tool_dist[name] = tool_dist.get(name, 0) + 1

    pending_q = db.query(Assignment).filter(
        Assignment.user_id == current_user.id, Assignment.status == "pending"
    )
    pending_assignments = pending_q.count()
    next_due = pending_q.order_by(Assignment.due_at).first()

    return {
        "conversations": len(conv_ids),
        "messages": messages,
        "tool_calls": tool_total,
        "tool_distribution": tool_dist,
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else None,
        "avg_first_token_ms": round(sum(first_tokens) / len(first_tokens)) if first_tokens else None,
        "documents": db.query(func.count(CourseDocument.id))
        .filter(CourseDocument.user_id == current_user.id)
        .scalar()
        or 0,
        "plans": db.query(func.count(StudyPlan.id))
        .filter(StudyPlan.user_id == current_user.id)
        .scalar()
        or 0,
        "schedules": db.query(func.count(Schedule.id))
        .filter(Schedule.user_id == current_user.id)
        .scalar()
        or 0,
        "pending_assignments": pending_assignments,
        "next_due_at": next_due.due_at.strftime("%Y-%m-%d %H:%M") if next_due else None,
        "score_summary": _score_summary(db, current_user.id),
    }
