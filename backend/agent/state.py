"""Agent 状态定义。"""

from __future__ import annotations

from typing import Any, TypedDict


class ClosetAgentState(TypedDict, total=False):
    """LangGraph 中流转的状态对象。"""

    user_message: str
    chat_history: list[dict[str, str]]
    plan: dict[str, Any]
    tool_results: list[dict[str, Any]]
    reply: str
    cards: list[dict[str, Any]]
    action: str

