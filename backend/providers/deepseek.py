"""DeepSeek 适配层。"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.config import Settings


class DeepSeekProvider:
    """封装 DeepSeek OpenAI 兼容接口。"""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用 DeepSeek chat completions 接口。"""

        self.logger.info("Calling DeepSeek model=%s", payload.get("model"))
        response = httpx.post(
            f"{self.settings.deepseek_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def plan_tool_calls(
        self,
        user_message: str,
        chat_history: list[dict[str, str]],
        tool_schemas: list[dict[str, Any]],
        context_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """让 DeepSeek 决定意图和要调用的工具。"""

        system_prompt = (
            "你是衣柜 Agent 的调度器。"
            "你必须只返回 JSON，对用户消息做意图判断，并决定调用哪些工具。"
            "输出字段固定为：intent, action, direct_reply, tool_calls。"
            "action 只能是 query/recommend/clarify/confirm。"
            "tool_calls 必须是数组，每项形如 {\"name\":\"tool_name\",\"arguments\":{...}}。"
            "如果用户是在问衣柜里有什么，就优先调用 wardrobe_query。"
            "如果用户在要穿搭建议，就组合 weather_search、forgotten_recall、wardrobe_query、outfit_recommend。"
            "如果用户语义不足以行动，就 action=clarify。"
            f"可用工具 schema：{json.dumps(tool_schemas, ensure_ascii=False)}。"
            f"当前上下文摘要：{json.dumps(context_snapshot, ensure_ascii=False)}。"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        raw = self._post_chat_completion(
            {
                "model": self.settings.deepseek_chat_model,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }
        )
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)

    def summarize_tool_results(
        self,
        user_message: str,
        plan: dict[str, Any],
        tool_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """根据工具结果生成最终面向前端的回复。"""

        system_prompt = (
            "你是衣柜 Agent 的回复器。"
            "必须只返回 JSON。"
            "输出字段固定为：reply, action, cards。"
            "cards 是数组，元素应尽量直接包含前端展示所需字段。"
            "禁止输出 markdown 代码块。"
        )
        payload = {
            "user_message": user_message,
            "plan": plan,
            "tool_results": tool_results,
        }

        raw = self._post_chat_completion(
            {
                "model": self.settings.deepseek_chat_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                "temperature": 0.4,
                "response_format": {"type": "json_object"},
            }
        )
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)

    def reason_outfits(self, prompt_payload: dict[str, Any]) -> list[dict[str, str]]:
        """让 DeepSeek-R1 为候选穿搭补全更自然的理由。"""

        raw = self._post_chat_completion(
            {
                "model": self.settings.deepseek_reasoner_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是专业穿搭顾问。"
                            "根据输入的候选穿搭返回 JSON。"
                            "顶层必须是对象，结构为 {\"items\": [...]}。"
                            "items 中每个元素必须包含 name、reason、tips 三个字段。"
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            }
        )
        content = json.loads(raw["choices"][0]["message"]["content"])
        if isinstance(content, dict) and "items" in content and isinstance(content["items"], list):
            return content["items"]
        if isinstance(content, list):
            return content
        return []

