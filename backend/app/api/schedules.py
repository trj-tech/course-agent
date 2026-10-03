from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.database import get_db
from app.models.course import Schedule
from app.models.user import User

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/me")
def my_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前登录学生的课表（权限隔离：强制按当前用户过滤，无法查他人数据）。"""
    rows = (
        db.query(Schedule)
        .options(joinedload(Schedule.course))
        .filter(Schedule.user_id == current_user.id)
        .all()
    )
    return [
        {
            "id": s.id,
            "weekday": s.weekday,
            "start_period": s.start_period,
            "end_period": s.end_period,
            "week_start": s.week_start,
            "week_end": s.week_end,
            "location": s.location,
            "course_code": s.course.code,
            "course_name": s.course.name,
            "teacher": s.course.teacher,
        }
        for s in rows
    ]
