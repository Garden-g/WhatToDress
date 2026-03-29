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

    # DeepSeek-R1 思维链透传（前端展示用）
    planning_thinking: str          # 规划阶段的思考过程
    summarize_thinking: str         # 总结阶段的思考过程
    tool_calls_info: list[dict[str, Any]]  # 工具调用摘要（name + arguments）

