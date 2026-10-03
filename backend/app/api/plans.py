"""学习计划：查询当前用户已保存的计划。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.plan import StudyPlan
from app.models.user import User

router = APIRouter(prefix="/plans", tags=["plans"])


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
            "status": p.status,
            "created_at": str(p.created_at),
        }
        for p in plans
    ]
