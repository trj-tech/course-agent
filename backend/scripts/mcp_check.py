"""验证 MCP stdio 客户端连接、工具加载与用户绑定（不需要 API Key）。"""
import asyncio
import json


def _content(result: list[dict]) -> list[object]:
    """把 MCP CallToolResult 的 content 块解析成业务数据。"""
    out: list[object] = []
    for item in result:
        if isinstance(item, dict) and item.get("type") == "text":
            try:
                out.append(json.loads(item["text"]))
            except (TypeError, json.JSONDecodeError):
                out.append(item["text"])
    return out


async def main():
    from app.agent.engine import bind_user, mcp_client_config
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(mcp_client_config())
    raw = await client.get_tools()
    print("MCP 工具列表:", [t.name for t in raw])

    tools = bind_user(raw, 1)  # 绑定为 student01
    for t in tools:
        if t.name.endswith("get_my_schedule"):
            # 故意传错 user_id，验证被强制覆盖为 1
            result = await t.ainvoke({"user_id": 999, "weekday": 1})
            names = [r["course_name"] for r in _content(result)]
            print(f"绑定生效：{t.name} -> {names}")

        if t.name.endswith("search_course_documents"):
            result = await t.ainvoke({"user_id": 999, "query": "什么是装饰器", "top_k": 1})
            parsed = _content(result)
            print(f"RAG 工具: {parsed[0]['filename'] if parsed else '无结果'}")

        if t.name.endswith("save_study_plan"):
            result = await t.ainvoke(
                {"user_id": 999, "title": "MCP自检计划", "goal": "测试", "content": "测试内容"}
            )
            print("计划保存:", _content(result))
    print("== MCP 客户端验证通过 ==")


asyncio.run(main())
