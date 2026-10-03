"""聊天接口：Agent 运行过程通过 SSE 实时推送到前端，结束后落库对话历史。"""
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel

from app.agent.engine import bind_user, build_agent, build_llm, mcp_client_config, pretty_tool_name
from app.core.security import get_current_user
from app.database import SessionLocal
from app.models.conversation import AiConversation, AiMessage
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _extract_sources(raw) -> list | None:
    """从 search_course_documents 的工具输出中尽量提取检索来源（文件名/分数/片段）。"""
    if raw is None:
        return None
    text = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, default=str)
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    # MCP 返回 content 块：{"content": [{"type": "text", "text": "..."}]} 或 {"type": "text", "text": "..."}
    if isinstance(data, dict):
        texts = []
        content = data.get("content")
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        elif isinstance(content, str):
            texts = [content]
        elif data.get("type") == "text" and isinstance(data.get("text"), str):
            texts = [data["text"]]
        if texts:
            try:
                data = json.loads(texts[0])
            except (ValueError, TypeError):
                return None
    if isinstance(data, list):
        items = []
        for it in data:
            if isinstance(it, dict) and ("filename" in it or "content" in it):
                items.append(
                    {k: it.get(k) for k in ("filename", "score", "chunk_index", "content") if k in it}
                )
        return items or None
    return None


@router.post("")
async def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    async def gen():
        started_at = time.perf_counter()
        first_token_ms = None  # 第一个字输出时的耗时
        # 提前校验 Key 配置，失败直接返回错误事件
        try:
            build_llm()
        except ValueError as e:
            yield _sse({"type": "error", "message": str(e)})
            return

        db = SessionLocal()
        conversation = None
        collected_text: list[str] = []
        tool_records: list[dict] = []
        retrieval_sources = None
        try:
            # 复用已有会话或新建会话
            if payload.conversation_id:
                conversation = db.get(AiConversation, payload.conversation_id)
                if conversation is None or conversation.user_id != current_user.id:
                    conversation = None
            if conversation is None:
                conversation = AiConversation(
                    user_id=current_user.id,
                    title=payload.message[:20] or "新对话",
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            # 每次会话拉起独立 MCP 服务器子进程（stdio），工具调用后自动清理
            client = MultiServerMCPClient(mcp_client_config())
            raw_tools = await client.get_tools()
            tool_names = {t.name for t in raw_tools}
            tools = bind_user(raw_tools, current_user.id)
            agent = build_agent(current_user, tools)

            # 同一工具在包装层与底层各触发一次事件，只向前端展示第一组
            started: set[str] = set()
            ended: set[str] = set()

            # 多轮记忆：取当前会话最近 20 条历史消息拼进 Agent 输入（含代词/上下文追问）
            history_rows = (
                db.query(AiMessage)
                .filter(AiMessage.conversation_id == conversation.id)
                .order_by(AiMessage.id.desc())
                .limit(20)
                .all()
            )
            history_msgs = [
                AIMessage(content=row.content) if row.role == "assistant" else HumanMessage(content=row.content)
                for row in reversed(history_rows)
            ]
            agent_input = {"messages": history_msgs + [HumanMessage(content=payload.message)]}
            async for event in agent.astream_events(agent_input, version="v2"):
                etype = event.get("event")
                name = event.get("name") or ""
                if etype == "on_tool_start" and name in tool_names and name not in started:
                    started.add(name)
                    inp = {
                        k: v
                        for k, v in (event["data"].get("input") or {}).items()
                        if k != "user_id"  # 对前端隐藏内部用户标识
                    }
                    yield _sse({"type": "tool_start", "name": pretty_tool_name(name), "input": inp})
                elif etype == "on_tool_end" and name in tool_names and name not in ended:
                    ended.add(name)
                    out = event["data"].get("output")
                    yield _sse(
                        {
                            "type": "tool_end",
                            "name": pretty_tool_name(name),
                            "output": json.dumps(out, ensure_ascii=False, default=str)[:500],
                        }
                    )
                    # 落库：记录工具调用痕迹，并尝试提取检索溯源
                    end_inp = {
                        k: v
                        for k, v in (event["data"].get("input") or {}).items()
                        if k != "user_id"
                    }
                    tool_records.append(
                        {
                            "name": pretty_tool_name(name),
                            "input": json.dumps(end_inp, ensure_ascii=False, default=str)[:1000],
                            "output": json.dumps(out, ensure_ascii=False, default=str)[:1000],
                        }
                    )
                    if pretty_tool_name(name) == "search_course_documents":
                        retrieval_sources = _extract_sources(out)
                elif etype == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    content = chunk.content if chunk else None
                    if isinstance(content, str) and content:
                        if first_token_ms is None:
                            first_token_ms = int((time.perf_counter() - started_at) * 1000)
                        collected_text.append(content)
                        yield _sse({"type": "text", "delta": content})

            answer = "".join(collected_text)
            latency = int((time.perf_counter() - started_at) * 1000)
            # 保存对话历史
            db.add(AiMessage(conversation_id=conversation.id, role="user", content=payload.message))
            db.add(
                AiMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=answer,
                    tool_calls=json.dumps(tool_records, ensure_ascii=False) if tool_records else None,
                    retrieval_sources=(
                        json.dumps(retrieval_sources, ensure_ascii=False) if retrieval_sources else None
                    ),
                    latency_ms=latency,
                    first_token_ms=first_token_ms,
                )
            )
            db.commit()
            yield _sse(
                {
                    "type": "done",
                    "conversation_id": conversation.id,
                    "latency_ms": latency,
                    "first_token_ms": first_token_ms,
                }
            )
        except Exception as e:  # noqa: BLE001
            yield _sse({"type": "error", "message": f"服务异常：{e}"})
        finally:
            db.close()

    return StreamingResponse(gen(), media_type="text/event-stream")
