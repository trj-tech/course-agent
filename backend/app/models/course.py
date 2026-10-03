from sqlalchemy import DECIMAL, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    teacher: Mapped[str | None] = mapped_column(String(50))
    credit: Mapped[float | None] = mapped_column(DECIMAL(2, 1))
    semester: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 权限隔离关键字段：课表归属哪个学生
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-7，周一至周日
    start_period: Mapped[int] = mapped_column(Integer, nullable=False)  # 起始节次
    end_period: Mapped[int] = mapped_column(Integer, nullable=False)  # 结束节次
    week_start: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 起始周
    week_end: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 结束周
    location: Mapped[str | None] = mapped_column(String(100))

    course: Mapped[Course] = relationship()
