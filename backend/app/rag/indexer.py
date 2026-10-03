"""文档切片 + 向量化 + 写入 document_chunks。"""
import json

from sqlalchemy.orm import Session

from app.models.document import CourseDocument, DocumentChunk
from app.rag.embedder import embed_texts

CHUNK_SIZE = 500  # 每块约 500 字


def split_text(text: str) -> list[str]:
    """按换行段落切分，接近 CHUNK_SIZE 时收束为一块。"""
    chunks: list[str] = []
    current = ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(current) + len(line) > CHUNK_SIZE and current:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current)
    return chunks


def index_document(db: Session, doc: CourseDocument, text: str) -> None:
    """切片、向量化并落库；成功后把文档状态置为 ready。"""
    chunks = split_text(text)
    if not chunks:
        doc.status = "failed"
        db.commit()
        return

    vectors = embed_texts(chunks)
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        db.add(
            DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk,
                embedding=json.dumps(vec),
            )
        )
    doc.status = "ready"
    db.commit()
