"""LangGraph 节点实现。"""

from __future__ import annotations

import logging
from typing import Any, Callable

from backend.agent.state import ClosetAgentState
from backend.providers.deepseek import DeepSeekProvider


ToolCallable = Callable[..., Any]


def build_agent_node(
    provider: DeepSeekProvider,
    tool_schemas: list[dict[str, Any]],
    context_builder: Callable[[], dict[str, Any]],
    logger: logging.Logger,
) -> Callable[[ClosetAgentState], ClosetAgentState]:
    """创建 agent_node。"""

    def agent_node(state: ClosetAgentState) -> ClosetAgentState:
        if not state.get("tool_results"):
            logger.info("agent_node planning")
            try:
                plan = provider.plan_tool_calls(
                    user_message=state["user_message"],
                    chat_history=state.get("chat_history", []),
                    tool_schemas=tool_schemas,
                    context_snapshot=context_builder(),
                )
            except Exception as error:
                logger.warning("DeepSeek planning failed, fallback clarify: %s", error)
                return {
                    **state,
                    "plan": {
                        "intent": "clarify",
                        "action": "clarify",
                        "direct_reply": "我先没完全听明白。你可以直接说“我有什么蓝色衬衫”或“明天 18 度通勤穿什么”。",
                        "tool_calls": [],
                    },
                    "reply": "我先没完全听明白。你可以直接说“我有什么蓝色衬衫”或“明天 18 度通勤穿什么”。",
                    "cards": [],
                    "action": "clarify",
                    "planning_thinking": "",
                    "summarize_thinking": "",
                    "tool_calls_info": [],
                }

            # 提取 R1 思维链和工具调用摘要
            planning_thinking = plan.pop("_thinking", "")
            tool_calls = plan.get("tool_calls") or []
            tool_calls_info = [
                {"name": tc.get("name", ""), "arguments": tc.get("arguments", {})}
                for tc in tool_calls
            ]

            if not tool_calls:
                return {
                    **state,
                    "plan": plan,
                    "reply": plan.get("direct_reply") or "我这边先需要你补充一点信息。",
                    "cards": [],
                    "action": plan.get("action") or "clarify",
                    "planning_thinking": planning_thinking,
                    "summarize_thinking": "",
                    "tool_calls_info": tool_calls_info,
                }
            return {
                **state,
                "plan": plan,
                "planning_thinking": planning_thinking,
                "tool_calls_info": tool_calls_info,
            }

        logger.info("agent_node summarizing")
        try:
            summary = provider.summarize_tool_results(
                user_message=state["user_message"],
                plan=state.get("plan", {}),
                tool_results=state.get("tool_results", []),
            )
            return {
                **state,
                "reply": summary.get("reply", "我已经帮你整理好了结果。"),
                "cards": summary.get("cards", []),
                "action": summary.get("action", state.get("plan", {}).get("action", "query")),
                "summarize_thinking": summary.get("_thinking", ""),
            }
        except Exception as error:
            logger.warning("DeepSeek summarize failed, fallback local summary: %s", error)
            cards: list[dict[str, Any]] = []
            for result in state.get("tool_results", []):
                if isinstance(result.get("cards"), list):
                    cards.extend(result["cards"])
                elif isinstance(result.get("result"), dict) and isinstance(result["result"].get("cards"), list):
                    cards.extend(result["result"]["cards"])
            return {
                **state,
                "reply": "我已经根据当前数据整理好了，你可以先看下面的卡片结果。",
                "cards": cards,
                "action": state.get("plan", {}).get("action", "query"),
                "summarize_thinking": "",
            }

    return agent_node


def build_tool_executor_node(
    tool_registry: dict[str, ToolCallable],
    logger: logging.Logger,
) -> Callable[[ClosetAgentState], ClosetAgentState]:
    """创建 tool_executor_node。"""

    def tool_executor_node(state: ClosetAgentState) -> ClosetAgentState:
        plan = state.get("plan", {})
        tool_results: list[dict[str, Any]] = []

        for tool_call in plan.get("tool_calls", []):
            name = tool_call.get("name")
            arguments = tool_call.get("arguments") or {}
            tool = tool_registry.get(name)
            if not tool:
                logger.warning("Tool not found: %s", name)
                tool_results.append({"tool": name, "error": "tool not found"})
                continue

            logger.info("tool_executor running tool=%s", name)
            result = tool(**arguments)
            tool_results.append({"tool": name, "result": result})

        return {**state, "tool_results": tool_results}

    return tool_executor_node

