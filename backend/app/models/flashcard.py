from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Flashcard(Base):
    """AI 复习卡片：基于课程资料由 LLM 生成的问答卡，带间隔重复（SRS）记忆进度。"""

    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("course_documents.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # 记忆周期（Leitner 盒）1-6：认识则升盒、遗忘则回盒1；升到 6 视为已掌握
    box: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # 下次应复习日期（<= 今天即进入「今日待复习」队列）
    due_date: Mapped[date | None] = mapped_column(Date)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 最近一次复习结果：known / fuzzy / unknown
    last_result: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
