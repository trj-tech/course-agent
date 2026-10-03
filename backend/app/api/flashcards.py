"""AI 复习卡片：基于用户课程资料（RAG 切片）由 LLM 生成问答卡。"""
import json

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
        )
        db.add(f)
        saved.append(f)
    db.commit()
    return [
        {"id": f.id, "question": f.question, "answer": f.answer, "document_id": f.document_id}
        for f in saved
    ]


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
    return [
        {
            "id": f.id,
            "question": f.question,
            "answer": f.answer,
            "filename": fn,
            "created_at": str(f.created_at),
        }
        for f, fn in rows
    ]


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
