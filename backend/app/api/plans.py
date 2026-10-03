"""学习计划：当前用户计划的查询 / 详情 / 编辑 / 删除 / 条目清单（checklist）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.plan import StudyPlan, StudyPlanItem
from app.models.user import User

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanUpdate(BaseModel):
    title: str | None = None
    goal: str | None = None
    content: str | None = None
    status: str | None = None  # active / done


class ItemCreate(BaseModel):
    title: str
    content: str | None = None


class ItemToggle(BaseModel):
    is_done: bool


def _get_own_plan(db: Session, plan_id: int, user: User) -> StudyPlan:
    plan = db.get(StudyPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    return plan


def _items_of(db: Session, plan_id: int) -> list[StudyPlanItem]:
    return (
        db.query(StudyPlanItem)
        .filter(StudyPlanItem.plan_id == plan_id)
        .order_by(StudyPlanItem.item_order, StudyPlanItem.id)
        .all()
    )


def _item_dict(it: StudyPlanItem) -> dict:
    return {"id": it.id, "title": it.title, "content": it.content, "is_done": it.is_done}


def _progress_of(db: Session, plan_ids: list[int]) -> dict[int, dict]:
    """批量统计各计划的条目完成进度：{plan_id: {done, total}}。"""
    if not plan_ids:
        return {}
    rows = (
        db.query(
            StudyPlanItem.plan_id,
            func.count(StudyPlanItem.id),
            func.sum(func.if_(StudyPlanItem.is_done, 1, 0)),
        )
        .filter(StudyPlanItem.plan_id.in_(plan_ids))
        .group_by(StudyPlanItem.plan_id)
        .all()
    )
    return {pid: {"total": n, "done": int(d or 0)} for pid, n, d in rows}


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
    progress = _progress_of(db, [p.id for p in plans])
    return [
        {
            "id": p.id,
            "title": p.title,
            "goal": p.goal,
            "content": p.content,
            "status": p.status,
            "created_at": str(p.created_at),
            "progress": progress.get(p.id, {"done": 0, "total": 0}),
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
    items = _items_of(db, plan.id)
    return {
        "id": plan.id,
        "title": plan.title,
        "goal": plan.goal,
        "content": plan.content,
        "status": plan.status,
        "created_at": str(plan.created_at),
        "progress": {"done": sum(1 for i in items if i.is_done), "total": len(items)},
        "items": [_item_dict(i) for i in items],
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


@router.post("/{plan_id}/items")
def add_item(
    plan_id: int,
    payload: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = _get_own_plan(db, plan_id, current_user)
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="条目内容不能为空")
    next_order = (
        db.query(func.coalesce(func.max(StudyPlanItem.item_order), -1)).filter(
            StudyPlanItem.plan_id == plan.id
        ).scalar()
        + 1
    )
    it = StudyPlanItem(plan_id=plan.id, item_order=next_order, title=title[:200], content=payload.content)
    db.add(it)
    db.commit()
    db.refresh(it)
    return _item_dict(it)


@router.put("/{plan_id}/items/{item_id}")
def toggle_item(
    plan_id: int,
    item_id: int,
    payload: ItemToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_own_plan(db, plan_id, current_user)  # 归属校验
    it = db.get(StudyPlanItem, item_id)
    if it is None or it.plan_id != plan_id:
        raise HTTPException(status_code=404, detail="条目不存在")
    it.is_done = payload.is_done
    db.commit()
    return _item_dict(it)


@router.delete("/{plan_id}/items/{item_id}")
def delete_item(
    plan_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_own_plan(db, plan_id, current_user)
    it = db.get(StudyPlanItem, item_id)
    if it is None or it.plan_id != plan_id:
        raise HTTPException(status_code=404, detail="条目不存在")
    db.delete(it)
    db.commit()
    return {"ok": True}


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = _get_own_plan(db, plan_id, current_user)
    db.query(StudyPlanItem).filter(StudyPlanItem.plan_id == plan.id).delete()
    db.delete(plan)
    db.commit()
    return {"ok": True}
