"""管理后台 API：仅 admin 角色可访问。

课程管理、课表管理（筛选/分页/节次冲突检测）、用户管理、
文档管理（全量列表/删除/重新入库/预览）与系统统计。
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.documents import extract_text
from app.core.security import get_current_admin, hash_password
from app.database import get_db
from app.models.conversation import AiConversation, AiMessage
from app.models.course import Course, Schedule
from app.models.document import CourseDocument, DocumentChunk
from app.models.plan import StudyPlan
from app.models.user import User
from app.rag.indexer import index_document

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


# ---------- 系统统计 ----------

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    def count(model):
        return db.query(func.count(model.id)).scalar() or 0

    return {
        "users": count(User),
        "students": db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0,
        "courses": count(Course),
        "schedules": count(Schedule),
        "documents": count(CourseDocument),
        "plans": count(StudyPlan),
        "conversations": count(AiConversation),
        "messages": count(AiMessage),
    }


# ---------- 课程管理 ----------

class CourseIn(BaseModel):
    code: str
    name: str
    teacher: str | None = None
    credit: float | None = None
    semester: str | None = None
    description: str | None = None


@router.get("/courses")
def list_courses(keyword: str = "", db: Session = Depends(get_db)):
    q = db.query(Course)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(Course.name.like(like) | Course.code.like(like) | Course.teacher.like(like))
    return [
        {
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "teacher": c.teacher,
            "credit": float(c.credit) if c.credit is not None else None,
            "semester": c.semester,
            "description": c.description,
        }
        for c in q.order_by(Course.code).all()
    ]


@router.post("/courses")
def create_course(payload: CourseIn, db: Session = Depends(get_db)):
    if db.query(Course).filter(Course.code == payload.code).first():
        raise HTTPException(status_code=409, detail=f"课程代码 {payload.code} 已存在")
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"id": course.id}


@router.put("/courses/{cid}")
def update_course(cid: int, payload: CourseIn, db: Session = Depends(get_db)):
    course = db.get(Course, cid)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    dup = db.query(Course).filter(Course.code == payload.code, Course.id != cid).first()
    if dup:
        raise HTTPException(status_code=409, detail=f"课程代码 {payload.code} 已被其他课程使用")
    for k, v in payload.model_dump().items():
        setattr(course, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/courses/{cid}")
def delete_course(cid: int, db: Session = Depends(get_db)):
    course = db.get(Course, cid)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if db.query(Schedule).filter(Schedule.course_id == cid).first():
        raise HTTPException(status_code=409, detail="该课程已被课表引用，请先删除相关课表记录")
    db.delete(course)
    db.commit()
    return {"ok": True}


# ---------- 课表管理 ----------

class ScheduleIn(BaseModel):
    user_id: int
    course_id: int
    weekday: int  # 1-7
    start_period: int
    end_period: int
    week_start: int = 1
    week_end: int = 16
    location: str | None = None


def _conflict(db: Session, user_id: int, weekday: int, start: int, end: int, exclude_id: int | None = None) -> Schedule | None:
    """同一天节次区间重叠即视为冲突（允许首尾相接：如 1-2 与 3-4 不冲突）。"""
    rows = db.query(Schedule).filter(Schedule.user_id == user_id, Schedule.weekday == weekday).all()
    for r in rows:
        if exclude_id is not None and r.id == exclude_id:
            continue
        if start <= r.end_period and end >= r.start_period:
            return r
    return None


def _schedule_out(s: Schedule) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "course_id": s.course_id,
        "weekday": s.weekday,
        "start_period": s.start_period,
        "end_period": s.end_period,
        "week_start": s.week_start,
        "week_end": s.week_end,
        "location": s.location,
    }


@router.get("/schedules")
def list_schedules(
    username: str = "",
    weekday: int | None = None,
    page: int = 1,
    page_size: int = 15,
    db: Session = Depends(get_db),
):
    q = (
        db.query(Schedule, User.username, Course.code, Course.name)
        .join(User, Schedule.user_id == User.id)
        .join(Course, Schedule.course_id == Course.id)
    )
    if username:
        q = q.filter(User.username.like(f"%{username}%"))
    if weekday is not None:
        q = q.filter(Schedule.weekday == weekday)
    total = q.count()
    rows = q.order_by(Schedule.user_id, Schedule.weekday, Schedule.start_period).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                **_schedule_out(s),
                "username": uname,
                "course_code": ccode,
                "course_name": cname,
            }
            for s, uname, ccode, cname in rows
        ],
    }


@router.post("/schedules")
def create_schedule(payload: ScheduleIn, db: Session = Depends(get_db)):
    if payload.weekday < 1 or payload.weekday > 7:
        raise HTTPException(status_code=400, detail="weekday 需在 1-7 之间")
    if payload.end_period < payload.start_period:
        raise HTTPException(status_code=400, detail="结束节次不能早于开始节次")
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if db.get(Course, payload.course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    hit = _conflict(db, payload.user_id, payload.weekday, payload.start_period, payload.end_period)
    if hit:
        raise HTTPException(status_code=409, detail="与该用户当天已有课程节次冲突")
    s = Schedule(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _schedule_out(s)


@router.put("/schedules/{sid}")
def update_schedule(sid: int, payload: ScheduleIn, db: Session = Depends(get_db)):
    s = db.get(Schedule, sid)
    if s is None:
        raise HTTPException(status_code=404, detail="课表记录不存在")
    if payload.end_period < payload.start_period:
        raise HTTPException(status_code=400, detail="结束节次不能早于开始节次")
    hit = _conflict(db, payload.user_id, payload.weekday, payload.start_period, payload.end_period, exclude_id=sid)
    if hit:
        raise HTTPException(status_code=409, detail="与该用户当天已有课程节次冲突")
    for k, v in payload.model_dump().items():
        setattr(s, k, v)
    db.commit()
    return _schedule_out(s)


@router.delete("/schedules/{sid}")
def delete_schedule(sid: int, db: Session = Depends(get_db)):
    s = db.get(Schedule, sid)
    if s is None:
        raise HTTPException(status_code=404, detail="课表记录不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ---------- 用户管理 ----------

class UserIn(BaseModel):
    username: str
    password: str | None = None
    name: str | None = None
    role: str = "student"
    student_no: str | None = None


@router.get("/users")
def list_users(
    keyword: str = "",
    role: str = "",
    page: int = 1,
    page_size: int = 15,
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(User.username.like(like) | User.name.like(like) | User.student_no.like(like))
    if role:
        q = q.filter(User.role == role)
    total = q.count()
    rows = q.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "name": u.name,
                "role": u.role,
                "student_no": u.student_no,
                "created_at": str(u.created_at),
            }
            for u in rows
        ],
    }


@router.post("/users")
def create_user(payload: UserIn, db: Session = Depends(get_db)):
    if not payload.password:
        raise HTTPException(status_code=400, detail="新用户必须设置密码")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="用户名已被占用")
    u = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name or payload.username,
        role=payload.role,
        student_no=payload.student_no,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "username": u.username}


@router.put("/users/{uid}")
def update_user(uid: int, payload: UserIn, db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    dup = db.query(User).filter(User.username == payload.username, User.id != uid).first()
    if dup:
        raise HTTPException(status_code=409, detail="用户名已被占用")
    u.username = payload.username
    if payload.name is not None:
        u.name = payload.name
    if payload.role:
        u.role = payload.role
    if payload.student_no is not None:
        u.student_no = payload.student_no
    if payload.password:
        u.password_hash = hash_password(payload.password)
    db.commit()
    return {"ok": True}


@router.delete("/users/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if db.query(Schedule).filter(Schedule.user_id == uid).first():
        raise HTTPException(status_code=409, detail="该用户还有课表记录，请先删除其课表")
    if db.query(CourseDocument).filter(CourseDocument.user_id == uid).first():
        raise HTTPException(status_code=409, detail="该用户还有课程资料，请先删除其资料")
    db.delete(u)
    db.commit()
    return {"ok": True}


# ---------- 文档管理（全量） ----------

@router.get("/documents")
def list_admin_documents(
    status: str = "",
    page: int = 1,
    page_size: int = 15,
    db: Session = Depends(get_db),
):
    q = db.query(CourseDocument, User.username).join(User, CourseDocument.user_id == User.id)
    if status:
        q = q.filter(CourseDocument.status == status)
    total = q.count()
    rows = q.order_by(CourseDocument.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for d, uname in rows:
        size = 0
        try:
            size = Path(d.file_path).stat().st_size
        except OSError:
            pass
        items.append(
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "status": d.status,
                "size": size,
                "username": uname,
                "created_at": str(d.created_at),
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.delete("/documents/{did}")
def delete_document(did: int, db: Session = Depends(get_db)):
    d = db.get(CourseDocument, did)
    if d is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == did).delete()
    try:
        Path(d.file_path).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(d)
    db.commit()
    return {"ok": True}


@router.post("/documents/{did}/reindex")
def reindex_document(did: int, db: Session = Depends(get_db)):
    """重新解析原文件并重新入库（先清除旧切片）。"""
    d = db.get(CourseDocument, did)
    if d is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    path = Path(d.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="原文件已丢失")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == did).delete()
    try:
        text = extract_text(path, d.file_type)
        index_document(db, d, text)
    except Exception as e:  # noqa: BLE001
        d.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"重新入库失败：{e}")
    return {"id": d.id, "status": d.status}


@router.get("/documents/{did}/preview")
def preview_document(did: int, db: Session = Depends(get_db)):
    d = db.get(CourseDocument, did)
    if d is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    path = Path(d.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="原文件已丢失")
    try:
        text = extract_text(path, d.file_type)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"解析失败：{e}")
    return {"id": d.id, "filename": d.filename, "content": text[:2000]}
