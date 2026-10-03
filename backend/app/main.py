from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  # 导入模型以注册到 Base.metadata
from app.api import auth, health, schedules
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发阶段：启动时自动建表（正式项目改用迁移工具 Alembic）
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="course-agent", version="0.1.0", lifespan=lifespan)

# 开发环境：允许本地 Vite 前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
