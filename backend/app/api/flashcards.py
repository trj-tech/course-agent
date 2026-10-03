"""AI 复习卡片：基于用户课程资料（RAG 切片）由 LLM 生成问答卡，带间隔重复复习。"""
import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.document import CourseDocument, DocumentChunk
from app.models.flashcard import Flashcard
from app.models.user import User
from app.agent.engine import build_llm

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

# 各记忆周期的复习间隔（天）：认识一次升一盒，遗忘回到盒 1
INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15, 6: 30}
MASTER_BOX = 6  # 升到该盒视为「已掌握」

GEN_PROMPT = """你是课程复习助手。请严格基于下面的课程资料片段，生成 {count} 张复习卡片。

要求：
- 只使用资料中出现过的知识点，不要编造
- 问题应简短明确，答案精炼（2-3 句话以内）
- 使用简体中文

课程资料片段：
{context}

严格按以下 JSON 数组格式输出，不要输出任何其他内容：
[{{"question": "问题", "answer": "答案"}}]"""


class GenerateIn(BaseModel):
    document_id: int | None = None  # 不传则用全部资料
    count: int = 5


class ReviewIn(BaseModel):
    result: str  # known / fuzzy / unknown


def _card_dict(f: Flashcard, filename: str | None) -> dict:
    today = date.today()
    return {
        "id": f.id,
        "question": f.question,
        "answer": f.answer,
        "filename": filename,
        "created_at": str(f.created_at),
        "box": f.box,
        "mastered": f.box >= MASTER_BOX,
        "review_count": f.review_count,
        "last_result": f.last_result,
        "due_date": str(f.due_date) if f.due_date else None,
        "is_due": bool(f.due_date and f.due_date <= today),
        "can_undo": f.prev_box is not None,
    }


def _extract_json(text: str) -> list[dict]:
    """从模型输出中提取 JSON 数组（容忍代码围栏与前后缀文本）。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("模型输出中未找到 JSON 数组")
    cards = json.loads(text[start : end + 1])
    return [
        {"question": str(c.get("question", "")).strip(), "answer": str(c.get("answer", "")).strip()}
        for c in cards
        if isinstance(c, dict) and c.get("question") and c.get("answer")
    ]


@router.post("/generate")
def generate_flashcards(
    payload: GenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (1 <= payload.count <= 15):
        raise HTTPException(status_code=400, detail="count 需在 1-15 之间")

    # 取当前用户已入库资料切片作为生成素材
    q = (
        db.query(DocumentChunk, CourseDocument.filename)
        .join(CourseDocument, DocumentChunk.document_id == CourseDocument.id)
        .filter(CourseDocument.user_id == current_user.id, CourseDocument.status == "ready")
    )
    doc = None
    if payload.document_id:
        doc = db.get(CourseDocument, payload.document_id)
        if doc is None or doc.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="文档不存在")
        q = q.filter(CourseDocument.id == payload.document_id)
    rows = q.all()
    if not rows:
        raise HTTPException(status_code=400, detail="没有已入库的课程资料，请先上传资料")

    # 均匀取切片作为上下文，避免超长
    step = max(1, len(rows) // max(payload.count * 2, 4))
    chunks = [rows[i] for i in range(0, len(rows), step)][: payload.count * 2]
    context = "\n\n".join(f"【{fn}】{c.content}" for c, fn in chunks)

    llm = build_llm()
    output = llm.invoke(GEN_PROMPT.format(count=payload.count, context=context)).content
    try:
        cards = _extract_json(output)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"生成失败：{e}")
    if not cards:
        raise HTTPException(status_code=502, detail="生成失败：模型未返回有效卡片")

    saved = []
    for c in cards:
        f = Flashcard(
            user_id=current_user.id,
            document_id=doc.id if doc else None,
            question=c["question"],
            answer=c["answer"],
            box=1,
            due_date=date.today(),  # 新卡当天即进入复习队列
        )
        db.add(f)
        saved.append(f)
    db.commit()
    return [_card_dict(f, None) for f in saved]


@router.get("")
def list_flashcards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Flashcard, CourseDocument.filename)
        .join(CourseDocument, Flashcard.document_id == CourseDocument.id, isouter=True)
        .filter(Flashcard.user_id == current_user.id)
        .order_by(Flashcard.id.desc())
        .all()
    )
    return [_card_dict(f, fn) for f, fn in rows]


@router.post("/{fid}/review")
def review_flashcard(
    fid: int,
    payload: ReviewIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """复习打卡：known 升盒拉长间隔，fuzzy 保持明天再见，unknown 回盒 1 当天再见。"""
    f = db.get(Flashcard, fid)
    if f is None or f.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="卡片不存在")
    if payload.result not in ("known", "fuzzy", "unknown"):
        raise HTTPException(status_code=400, detail="result 仅支持 known / fuzzy / unknown")

    today = date.today()
    # 存快照供撤销
    f.prev_box = f.box
    f.prev_due = f.due_date
    f.prev_reviews = f.review_count
    f.prev_result = f.last_result
    if payload.result == "known":
        f.box = min(f.box + 1, MASTER_BOX)
        f.due_date = today + timedelta(days=INTERVALS[f.box])
    elif payload.result == "fuzzy":
        f.due_date = today + timedelta(days=1)
    else:
        f.box = 1
        f.due_date = today
    f.review_count += 1
    f.last_result = payload.result
    db.commit()
    return _card_dict(f, None)


@router.post("/{fid}/undo")
def undo_review(
    fid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """撤销最近一次复习打卡：恢复到打卡前的周期 / 日期 / 次数。"""
    f = db.get(Flashcard, fid)
    if f is None or f.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="卡片不存在")
    if f.prev_box is None:
        raise HTTPException(status_code=400, detail="该卡片没有可撤销的复习记录")
    f.box = f.prev_box
    f.due_date = f.prev_due
    f.review_count = f.prev_reviews or 0
    f.last_result = f.prev_result
    f.prev_box = f.prev_due = f.prev_reviews = f.prev_result = None
    db.commit()
    return _card_dict(f, None)


@router.delete("/{fid}")
def delete_flashcard(
    fid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = db.get(Flashcard, fid)
    if f is None or f.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="卡片不存在")
    db.delete(f)
    db.commit()
    return {"ok": True}
