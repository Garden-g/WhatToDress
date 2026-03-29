"""GLM-4.6V 视觉识图适配层。"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from backend.config import Settings


class GlmProvider:
    """封装智谱 GLM-4.6V 识图能力。

    这里走 OpenAI 兼容 chat/completions，而不是把智谱的返回直接暴露给业务层。
    这样做的目的，是让上层始终只消费统一的识图结果结构。
    """

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def _build_data_url(self, image_path: Path, mime_type: str | None) -> str:
        """把本地图片转成 data URL，供 OpenAI 兼容图片消息使用。"""

        content = image_path.read_bytes()
        encoded = base64.b64encode(content).decode("utf-8")
        return f"data:{mime_type or 'image/jpeg'};base64,{encoded}"

    def analyze_image(self, image_path: Path, mime_type: str | None = None) -> dict[str, Any]:
        """识别衣物图片属性。

        Args:
            image_path: 本地图片路径。
            mime_type: 图片 MIME 类型。

        Returns:
            dict[str, Any]: 与 Gemini 识图结果 shape 一致的属性对象。

        Raises:
            httpx.HTTPError: 远端请求失败时抛出。
            ValueError: 模型返回为空或不是合法 JSON 时抛出。
        """

        if not self.settings.glm_api_key:
            raise ValueError("GLM_API_KEY 未配置，无法使用 GLM-4.6V 识图")

        from backend.models.taxonomy import build_taxonomy_description

        self.logger.info("Calling GLM vision analyze_image image=%s", image_path)
        taxonomy_desc = build_taxonomy_description()
        prompt = (
            "请分析这是一件什么衣物，并只返回 JSON。"
            "字段固定为：category, subcategory, closet_section, color, secondary_color, "
            "season_tags, style_tags, formality, material, analysis_notes。"
            "closet_section 只能取 top/bottom/outerwear/shoes/accessory/other。"
            "season_tags 与 style_tags 必须是数组。"
            "\n\n重要：所有字段值必须使用中文（closet_section 和 formality 除外）。"
            "\n" + taxonomy_desc + "\n"
            "color 和 secondary_color 请用中文颜色名（如 黑色、白色、深蓝色）。"
            "material 请用中文材质名（如 皮革、棉、牛仔布）。"
            "style_tags 请用中文风格标签（如 休闲、街头、复古、优雅）。"
        )
        payload = {
            "model": self.settings.glm_vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": self._build_data_url(image_path, mime_type)}},
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        response = httpx.post(
            f"{self.settings.glm_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.glm_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if not str(content).strip():
            raise ValueError("GLM-4.6V analyze_image 返回为空")
        try:
            return json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError("GLM-4.6V analyze_image 返回了非 JSON 内容") from error
