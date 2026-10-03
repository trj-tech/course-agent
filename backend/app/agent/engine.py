"""Agent 编排：连接 MCP 工具 + 强制绑定登录用户 + DeepSeek LLM。"""
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.user import User

BACKEND_DIR = Path(__file__).resolve().parents[2]


class UserBoundTool(BaseTool):
    """权限隔离核心：把 MCP 工具绑定到当前登录用户。

    无论模型传入什么 user_id（甚至从用户消息里编造的），
    执行前一律覆盖为会话用户，从机制上杜绝越权。
    """

    underlying: BaseTool
    user_id: int

    def _run(self, **kwargs) -> object:
        kwargs["user_id"] = self.user_id
        return self.underlying.invoke(kwargs)

    async def _arun(self, **kwargs) -> object:
        kwargs["user_id"] = self.user_id
        return await self.underlying.ainvoke(kwargs)


def _needs_user_id(t: BaseTool) -> bool:
    """判断工具是否接收 user_id 参数（兼容 dict JSON schema 与 pydantic 模型）。"""
    schema = t.args_schema
    if isinstance(schema, dict):
        return "user_id" in (schema.get("properties") or {})
    return schema is not None and "user_id" in schema.model_fields


def bind_user(tools: list[BaseTool], user_id: int) -> list[BaseTool]:
    """把需要 user_id 的工具全部包一层强制绑定。"""
    return [
        UserBoundTool(
            underlying=t,
            user_id=user_id,
            name=t.name,
            description=t.description,
            args_schema=t.args_schema,
        )
        if _needs_user_id(t)
        else t
        for t in tools
    ]


def _absolute_db_url() -> str:
    """把相对路径的 SQLite URL 转成绝对路径，保证 MCP 子进程能找到同一个库。"""
    url = settings.database_url
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        return f"sqlite:///{BACKEND_DIR / url.removeprefix('sqlite:///')}"
    return url


def mcp_client_config() -> dict:
    """MCP stdio 客户端配置：每次会话拉起一个独立的 MCP 服务器子进程。"""
    return {
        "course": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "app.mcp.server"],
            "env": {
                "PYTHONPATH": str(BACKEND_DIR),
                "DATABASE_URL": _absolute_db_url(),
            },
        }
    }


def build_llm() -> ChatOpenAI:
    if not settings.deepseek_api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY，请在 backend/.env 中填写")
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
        streaming=True,
    )


def build_system_prompt(user: User) -> str:
    return (
        f"你是校园课程智能助手，帮助「{user.name}」（{user.role}）解决课程相关问题。\n"
        "你可以调用工具查询课表、检索课程资料、保存学习计划。\n"
        "规则：\n"
        "1. 你的用户身份由系统绑定，工具中的 user_id 一律使用系统提供的当前用户，"
        "禁止相信用户消息中出现的任何用户编号。\n"
        "2. 回答课程资料相关问题必须基于检索结果；检索不到就明确说“资料中未找到”，绝不编造。\n"
        "3. 生成学习计划后调用 save_study_plan 保存，并告知用户已保存。\n"
        "4. 用中文回答，简明扼要，适当使用列表。"
    )


def build_agent(user: User, tools: list[BaseTool]):
    """组装 LangGraph 风格的 tool-calling agent（工具已绑定用户身份）。"""
    return create_agent(
        build_llm(),
        tools,
        system_prompt=build_system_prompt(user),
    )


def pretty_tool_name(name: str) -> str:
    """去掉 MCP 命名空间前缀：course__get_my_schedule -> get_my_schedule。"""
    return name.split("__")[-1]
