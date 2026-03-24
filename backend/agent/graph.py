"""LangGraph 图定义。"""

from __future__ import annotations

from typing import Callable

from langgraph.graph import END, START, StateGraph

from backend.agent.state import ClosetAgentState


def build_agent_graph(
    agent_node: Callable[[ClosetAgentState], ClosetAgentState],
    tool_executor_node: Callable[[ClosetAgentState], ClosetAgentState],
):
    """构建最小可用 LangGraph。"""

    graph = StateGraph(ClosetAgentState)
    graph.add_node("agent_node", agent_node)
    graph.add_node("tool_executor_node", tool_executor_node)
    graph.add_edge(START, "agent_node")

    def route_after_agent(state: ClosetAgentState) -> str:
        if state.get("reply"):
            return "end"
        return "tools"

    graph.add_conditional_edges(
        "agent_node",
        route_after_agent,
        {
            "tools": "tool_executor_node",
            "end": END,
        },
    )
    graph.add_edge("tool_executor_node", "agent_node")
    return graph.compile()
