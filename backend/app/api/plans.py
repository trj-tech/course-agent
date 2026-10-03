"""学习计划：当前用户计划的查询 / 详情 / 编辑 / 删除。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.plan import StudyPlan
from app.models.user import User

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanUpdate(BaseModel):
    title: str | None = None
    goal: str | None = None
    content: str | None = None
    status: str | None = None  # active / done


def _get_own_plan(db: Session, plan_id: int, user: User) -> StudyPlan:
    plan = db.get(StudyPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    return plan


@router.get("")
def list_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plans = (
        db.query(StudyPlan)
        .filter(StudyPlan.user_id == current_user.id)
        .order_by(StudyPlan.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "title": p.title,
            "goal": p.goal,
            "content": p.content,
            "status": p.status,
            "created_at": str(p.created_at),
        }
        for p in plans
    ]


@router.get("/{plan_id}")
def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = _get_own_plan(db, plan_id, current_user)
    return {
        "id": plan.id,
        "title": plan.title,
        "goal": plan.goal,
        "content": plan.content,
        "status": plan.status,
        "created_at": str(plan.created_at),
    }


@router.put("/{plan_id}")
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = _get_own_plan(db, plan_id, current_user)
    if payload.title is not None:
        plan.title = payload.title.strip() or plan.title
    if payload.goal is not None:
        plan.goal = payload.goal
    if payload.content is not None:
        plan.content = payload.content
    if payload.status is not None:
        if payload.status not in ("active", "done"):
            raise HTTPException(status_code=400, detail="status 仅支持 active / done")
        plan.status = payload.status
    db.commit()
    return {"id": plan.id, "title": plan.title, "status": plan.status}


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = _get_own_plan(db, plan_id, current_user)
    db.delete(plan)
    db.commit()
    return {"ok": True}
