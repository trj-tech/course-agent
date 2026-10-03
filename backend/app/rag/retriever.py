"""语义检索：按 user_id 过滤后做余弦相似度，避免越权读取他人资料。"""
import json
import math

from sqlalchemy.orm import Session

from app.models.document import CourseDocument, DocumentChunk
from app.rag.embedder import embed_query


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(db: Session, user_id: int, query: str, top_k: int = 3) -> list[dict]:
    """检索当前用户已 ready 的文档切片，返回 top-k。"""
    qv = embed_query(query)
    rows = (
        db.query(DocumentChunk, CourseDocument.filename)
        .join(CourseDocument, DocumentChunk.document_id == CourseDocument.id)
        .filter(CourseDocument.user_id == user_id, CourseDocument.status == "ready")
        .all()
    )
    scored = []
    for chunk, filename in rows:
        vec = json.loads(chunk.embedding or "[]")
        if not vec:
            continue
        scored.append((cosine(qv, vec), chunk, filename))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "score": round(s, 4),
            "filename": fn,
            "chunk_index": c.chunk_index,
            "content": c.content[:500],
        }
        for s, c, fn in scored[:top_k]
    ]
