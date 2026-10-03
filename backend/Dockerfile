# 后端镜像：FastAPI + MCP 工具进程
FROM python:3.11-slim

WORKDIR /app

# 先装依赖以利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY app ./app
COPY data ./data

EXPOSE 8000

# lifespan 启动时自动建表（Base.metadata.create_all）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
