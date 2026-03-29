"""DeepSeek 适配层。

全部使用 deepseek-reasoner (R1) 模型。
R1 模型的特殊之处：
  - 不支持 response_format: {"type": "json_object"}，需手动从回复中提取 JSON
  - 不支持自定义 temperature，由模型自行决定
  - 返回 reasoning_content 字段（思维链），可透传给前端展示

同时提供同步和异步流式两套方法：
  - sync: plan_tool_calls / summarize_tool_results / reason_outfits（非流式场景）
  - async: async_stream_plan / async_stream_summarize（SSE 流式场景）
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncGenerator

import httpx

from backend.config import Settings
from backend.models.taxonomy import build_taxonomy_description


class DeepSeekProvider:
    """封装 DeepSeek OpenAI 兼容接口，统一使用 Reasoner (R1) 模型。"""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用 DeepSeek chat completions 接口。

        Returns:
            dict: 原始 API 响应 JSON，包含 choices[0].message.content
                  和 choices[0].message.reasoning_content（仅 R1 模型）。
        """

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

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """从模型回复中提取 JSON 对象。

        DeepSeek-R1 不支持 response_format，模型输出可能包含 markdown 代码块包裹
        或前后有多余文字。这个方法按优先级尝试三种提取策略：
        1. 直接解析整段文本
        2. 提取 ```json ... ``` 代码块
        3. 找到第一个 { 和最后一个 } 之间的内容

        Args:
            text: 模型返回的原始文本。

        Returns:
            dict: 解析出的 JSON 对象。

        Raises:
            ValueError: 三种策略都失败时抛出。
        """

        # 策略 1：直接整段解析
        stripped = text.strip()
        try:
            result = json.loads(stripped)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # 策略 2：提取 ```json ... ``` 代码块
        code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", stripped, re.DOTALL)
        if code_block_match:
            try:
                result = json.loads(code_block_match.group(1).strip())
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        # 策略 3：找第一个 { 到最后一个 } 之间的内容
        first_brace = stripped.find("{")
        last_brace = stripped.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            try:
                result = json.loads(stripped[first_brace : last_brace + 1])
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从模型回复中提取 JSON：{text[:200]}")

    @staticmethod
    def _get_reasoning_content(raw: dict[str, Any]) -> str:
        """从 R1 响应中提取思维链文本。

        Args:
            raw: DeepSeek API 原始响应。

        Returns:
            str: 思维链文本，若不存在则返回空字符串。
        """

        message = raw.get("choices", [{}])[0].get("message", {})
        return message.get("reasoning_content") or ""

    def plan_tool_calls(
        self,
        user_message: str,
        chat_history: list[dict[str, str]],
        tool_schemas: list[dict[str, Any]],
        context_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """让 DeepSeek-R1 决定意图和要调用的工具。

        Returns:
            dict: 包含 intent, action, direct_reply, tool_calls 字段的规划结果，
                  额外附带 _thinking 字段（R1 的思维链文本）。
        """

        system_prompt = (
            "你是衣柜 Agent 的调度器。"
            "你必须只返回 JSON（不要用 markdown 代码块包裹），对用户消息做意图判断，并决定调用哪些工具。"
            "输出字段固定为：intent, action, direct_reply, tool_calls。"
            "action 只能是 query/recommend/clarify/confirm。"
            "tool_calls 必须是数组，每项形如 {\"name\":\"tool_name\",\"arguments\":{...}}。"
            "如果用户是在问衣柜里有什么，就优先调用 wardrobe_query。"
            "如果用户在要穿搭建议，就组合 weather_search、forgotten_recall、wardrobe_query、outfit_recommend。"
            "如果用户语义不足以行动，就 action=clarify。"
            "\n\n【重要】wardrobe_query 的 category 参数必须使用中文分类名。"
            "用户说的口语化描述需要你转换为标准分类名。"
            "例如：用户说'上衣' → category='上衣'，用户说'外套'或'夹克' → category='外套'。"
            "\n" + build_taxonomy_description() + "\n"
            "如果用户询问的分类没有精确对应的衣物，应该查询最接近的大类或返回全部衣物供用户选择，"
            "而不是直接回答没有。\n"
            f"可用工具 schema：{json.dumps(tool_schemas, ensure_ascii=False)}。"
            f"当前上下文摘要：{json.dumps(context_snapshot, ensure_ascii=False)}。"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        # R1 不支持 response_format 和自定义 temperature，直接靠 prompt 约束输出
        raw = self._post_chat_completion(
            {
                "model": self.settings.deepseek_reasoner_model,
                "messages": messages,
            }
        )
        content = raw["choices"][0]["message"]["content"]
        plan = self._extract_json(content)

        # 把 R1 的思维链附加到结果中，方便上层透传给前端
        plan["_thinking"] = self._get_reasoning_content(raw)
        return plan

    def summarize_tool_results(
        self,
        user_message: str,
        plan: dict[str, Any],
        tool_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """根据工具结果生成最终面向前端的回复。

        Returns:
            dict: 包含 reply, action, cards 字段的总结结果，
                  额外附带 _thinking 字段（R1 的思维链文本）。
        """

        system_prompt = (
            "你是衣柜 Agent 的回复器。"
            "必须只返回 JSON（不要用 markdown 代码块包裹）。"
            "输出字段固定为：reply, action, cards。"
            "cards 是数组，元素应尽量直接包含前端展示所需字段。"
            "如果工具返回了衣物数据，即使不完全匹配用户的查询，也要在 reply 中说明情况并展示这些衣物。"
            "不要说'没有找到'，而是说'暂时没有完全匹配的，但这些衣物你可能感兴趣'。"
        )
        # 传给模型时去掉内部 _thinking 字段，避免干扰
        clean_plan = {k: v for k, v in plan.items() if not k.startswith("_")}
        payload = {
            "user_message": user_message,
            "plan": clean_plan,
            "tool_results": tool_results,
        }

        raw = self._post_chat_completion(
            {
                "model": self.settings.deepseek_reasoner_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            }
        )
        content = raw["choices"][0]["message"]["content"]
        summary = self._extract_json(content)

        # 附加思维链
        summary["_thinking"] = self._get_reasoning_content(raw)
        return summary

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
                            "根据输入的候选穿搭只返回 JSON（不要用 markdown 代码块包裹）。"
                            "顶层必须是对象，结构为 {\"items\": [...]}。"
                            "items 中每个元素必须包含 name、reason、tips 三个字段。"
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
                ],
            }
        )
        content_text = raw["choices"][0]["message"]["content"]
        try:
            content = self._extract_json(content_text)
        except ValueError:
            self.logger.warning("reason_outfits JSON extraction failed, returning empty list")
            return []

        if isinstance(content, dict) and "items" in content and isinstance(content["items"], list):
            return content["items"]
        return []

    # ── 异步流式方法（供 SSE 端点使用） ──────────────────────

    async def _async_stream_chat(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[dict[str, str], None]:
        """异步流式调用 DeepSeek R1，逐块 yield reasoning/content 事件。

        DeepSeek streaming SSE 格式（OpenAI 兼容）：
        - data: {"choices":[{"delta":{"reasoning_content":"..."}}]}  → 思维链
        - data: {"choices":[{"delta":{"content":"..."}}]}            → 正文
        - data: [DONE]                                                → 结束

        Yields:
            dict: {type: "reasoning"|"content"|"done", text: str}
            最后一个事件 type="done" 携带完整 reasoning 和 content。
        """
        payload = {
            "model": self.settings.deepseek_reasoner_model,
            "messages": messages,
            "stream": True,
        }

        full_reasoning = ""
        full_content = ""

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{self.settings.deepseek_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})

                    # reasoning_content → 思维链 token
                    rc = delta.get("reasoning_content")
                    if rc:
                        full_reasoning += rc
                        yield {"type": "reasoning", "text": rc}

                    # content → 正文 token
                    ct = delta.get("content")
                    if ct:
                        full_content += ct
                        yield {"type": "content", "text": ct}

        # 最终完整数据
        yield {"type": "done", "text": "", "reasoning": full_reasoning, "content": full_content}

    async def async_stream_plan(
        self,
        user_message: str,
        chat_history: list[dict[str, str]],
        tool_schemas: list[dict[str, Any]],
        context_snapshot: dict[str, Any],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式规划：逐块推送思维链，最终 yield 解析出的 plan。

        Yields:
            - {type: "reasoning", text: "..."}   → 思维链 chunk
            - {type: "plan", plan: {...}}          → 最终规划结果
        """
        system_prompt = (
            "你是衣柜 Agent 的调度器。"
            "你必须只返回 JSON（不要用 markdown 代码块包裹），对用户消息做意图判断，并决定调用哪些工具。"
            "输出字段固定为：intent, action, direct_reply, tool_calls。"
            "action 只能是 query/recommend/clarify/confirm。"
            "tool_calls 必须是数组，每项形如 {\"name\":\"tool_name\",\"arguments\":{...}}。"
            "如果用户是在问衣柜里有什么，就优先调用 wardrobe_query。"
            "如果用户在要穿搭建议，就组合 weather_search、forgotten_recall、wardrobe_query、outfit_recommend。"
            "如果用户语义不足以行动，就 action=clarify。"
            "\n\n【重要】wardrobe_query 的 category 参数必须使用中文分类名。"
            "用户说的口语化描述需要你转换为标准分类名。"
            "例如：用户说'上衣' → category='上衣'，用户说'外套'或'夹克' → category='外套'。"
            "\n" + build_taxonomy_description() + "\n"
            "如果用户询问的分类没有精确对应的衣物，应该查询最接近的大类或返回全部衣物供用户选择，"
            "而不是直接回答没有。\n"
            f"可用工具 schema：{json.dumps(tool_schemas, ensure_ascii=False)}。"
            f"当前上下文摘要：{json.dumps(context_snapshot, ensure_ascii=False)}。"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        full_content = ""
        async for event in self._async_stream_chat(messages):
            if event["type"] == "reasoning":
                yield {"type": "reasoning", "text": event["text"]}
            elif event["type"] == "done":
                full_content = event.get("content", "")

        # 从完整 content 中提取 plan JSON
        try:
            plan = self._extract_json(full_content)
        except ValueError:
            self.logger.warning("async_stream_plan JSON extraction failed, fallback clarify")
            plan = {
                "intent": "clarify",
                "action": "clarify",
                "direct_reply": "抱歉，我没有完全理解你的意思。你可以试试'我有什么蓝色衬衫'或'明天穿什么'。",
                "tool_calls": [],
            }

        yield {"type": "plan", "plan": plan}

    async def async_stream_summarize(
        self,
        user_message: str,
        plan: dict[str, Any],
        tool_results: list[dict[str, Any]],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式总结：逐块推送思维链，最终 yield 解析出的 summary。

        Yields:
            - {type: "reasoning", text: "..."}     → 思维链 chunk
            - {type: "summary", summary: {...}}    → 最终总结结果
        """
        system_prompt = (
            "你是衣柜 Agent 的回复器。"
            "必须只返回 JSON（不要用 markdown 代码块包裹）。"
            "输出字段固定为：reply, action, cards。"
            "cards 是数组，元素应尽量直接包含前端展示所需字段。"
            "如果工具返回了衣物数据，即使不完全匹配用户的查询，也要在 reply 中说明情况并展示这些衣物。"
            "不要说'没有找到'，而是说'暂时没有完全匹配的，但这些衣物你可能感兴趣'。"
        )
        clean_plan = {k: v for k, v in plan.items() if not k.startswith("_")}
        payload = {
            "user_message": user_message,
            "plan": clean_plan,
            "tool_results": tool_results,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

        full_content = ""
        async for event in self._async_stream_chat(messages):
            if event["type"] == "reasoning":
                yield {"type": "reasoning", "text": event["text"]}
            elif event["type"] == "done":
                full_content = event.get("content", "")

        # 从完整 content 中提取 summary JSON
        try:
            summary = self._extract_json(full_content)
        except ValueError:
            self.logger.warning("async_stream_summarize JSON extraction failed, fallback")
            summary = {
                "reply": "数据整理完成了，请看下方结果。",
                "action": "query",
                "cards": [],
            }

        yield {"type": "summary", "summary": summary}

