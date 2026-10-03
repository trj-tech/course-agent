"""聊天接口：Agent 运行过程通过 SSE 实时推送到前端。"""
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel

from app.agent.engine import bind_user, build_agent, build_llm, mcp_client_config, pretty_tool_name
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


@router.post("")
async def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    async def gen():
        # 提前校验 Key 配置，失败直接返回错误事件
        try:
            build_llm()
        except ValueError as e:
            yield _sse({"type": "error", "message": str(e)})
            return

        try:
            # 每次会话拉起独立 MCP 服务器子进程（stdio），工具调用后自动清理
            client = MultiServerMCPClient(mcp_client_config())
            raw_tools = await client.get_tools()
            tool_names = {t.name for t in raw_tools}
            tools = bind_user(raw_tools, current_user.id)
            agent = build_agent(current_user, tools)

            # 同一工具在包装层与底层各触发一次事件，只向前端展示第一组
            started: set[str] = set()
            ended: set[str] = set()

            agent_input = {"messages": [HumanMessage(content=payload.message)]}
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
                elif etype == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    content = chunk.content if chunk else None
                    if isinstance(content, str) and content:
                        yield _sse({"type": "text", "delta": content})
            yield _sse({"type": "done"})
        except Exception as e:  # noqa: BLE001
            yield _sse({"type": "error", "message": f"服务异常：{e}"})

    return StreamingResponse(gen(), media_type="text/event-stream")
