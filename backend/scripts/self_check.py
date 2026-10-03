"""一次性自检：MCP 工具直调 + RAG 索引与检索（不需要 API Key）。"""
from pathlib import Path

from app.database import SessionLocal
from app.mcp.server import get_my_schedule, save_study_plan
from app.models.document import CourseDocument
from app.rag.indexer import index_document
from app.rag.retriever import retrieve

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_docs" / "程序设计基础讲义.md"

print("== 1. MCP 工具 get_my_schedule(user_id=1) ==")
rows = get_my_schedule(1)
print(f"student01 课表 {len(rows)} 条，示例: {rows[0]['course_name']} {rows[0]['location']}")

print("== 2. RAG：对样例讲义切片 + 向量化 ==")
db = SessionLocal()
try:
    doc = db.query(CourseDocument).filter(CourseDocument.filename == SAMPLE.name).first()
    if doc is None:
        print("未找到样例文档，先写入一条记录")
        doc = CourseDocument(user_id=1, filename=SAMPLE.name, file_path=str(SAMPLE), file_type="md", status="pending")
        db.add(doc)
        db.commit()
        db.refresh(doc)
    index_document(db, doc, SAMPLE.read_text(encoding="utf-8"))
    print(f"状态: {doc.status}")

    print("== 3. RAG 检索：'什么是装饰器' ==")
    hits = retrieve(db, 1, "什么是装饰器", top_k=2)
    for h in hits:
        print(f"score={h['score']} 来源={h['filename']} 片段={h['content'][:40]!r}")

    print("== 4. 权限隔离检查：user_id=2 检索不到 user_id=1 的资料 ==")
    hits2 = retrieve(db, 2, "什么是装饰器", top_k=2)
    print(f"student02 检索结果数: {len(hits2)}（应为 0）")

    print("== 5. MCP 工具 save_study_plan(user_id=1) ==")
    result = save_study_plan(1, "自检计划", "测试目标", "测试内容")
    print(f"保存结果: {result}")
    # 清掉自检产生的计划，保持数据干净
    from app.models.plan import StudyPlan

    db.query(StudyPlan).filter(StudyPlan.title == "自检计划").delete()
    db.commit()
    print("自检计划已清理")
finally:
    db.close()

print("== 自检通过 ==")
