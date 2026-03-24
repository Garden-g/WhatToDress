"""Gemini 多模态适配层。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from backend.config import Settings


class GeminiProvider:
    """封装 Gemini 图像分析与图像编辑能力。"""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """延迟初始化 Gemini 客户端。

        为什么不在 __init__ 里直接创建：
        - 测试导入模块时还没进入 FastAPI lifespan
        - 真正的“缺少密钥就失败”应由应用启动校验负责，而不是导入阶段提前炸掉
        """

        if self.client is None:
            resolved_api_key = self.settings.resolved_gemini_api_key
            if not resolved_api_key:
                raise ValueError("Gemini 相关环境变量未配置，无法初始化客户端")

            # 这里显式记录密钥来源，是为了排查“明明配置了 key 但实际走的是哪一个”。
            self.logger.info("Initializing Gemini client auth_source=%s", self.settings.gemini_auth_source)
            self.client = genai.Client(
                api_key=resolved_api_key,
                http_options=types.HttpOptions(
                    timeout=int(self.settings.request_timeout_seconds * 1000),
                ),
            )
        return self.client

    def _generate_content(
        self,
        *,
        model: str,
        contents: list[Any],
        config: types.GenerateContentConfig,
        action_name: str,
    ) -> Any:
        """统一调用 Gemini，并把第三方异常转成可读错误。

        Args:
            model: 本次请求使用的模型名。
            contents: 发送给 Gemini 的消息内容。
            config: Gemini SDK 的生成配置。
            action_name: 调用动作名，用于日志和报错。

        Returns:
            Any: Gemini SDK 返回的原始响应对象。

        Raises:
            ValueError: 当 SDK 调用失败或返回不可用结果时抛出。
        """

        try:
            return self._get_client().models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as error:
            # 这里故意把第三方 SDK 的异常包装成 ValueError。
            # 原因是上层业务只需要一个稳定、可展示给前端的失败信息，
            # 不应该依赖底层 SDK 的异常层级和消息格式。
            self.logger.error("Gemini %s failed model=%s error=%s", action_name, model, error, exc_info=True)
            raise ValueError(f"Gemini {action_name} 失败：{error}") from error

    def analyze_image(self, image_path: Path, mime_type: str | None = None) -> dict[str, Any]:
        """识别衣物图片属性。

        Args:
            image_path: 本地衣物图片路径。
            mime_type: 图片的 MIME 类型。

        Returns:
            dict[str, Any]: 与业务层约定一致的衣物属性 JSON。

        Raises:
            ValueError: 当 Gemini 调用失败、返回为空或返回非 JSON 时抛出。
        """

        prompt = (
            "请分析这是一件什么衣物，并只返回 JSON。"
            "字段固定为：category, subcategory, closet_section, color, secondary_color, "
            "season_tags, style_tags, formality, material, analysis_notes。"
            "closet_section 只能取 top/bottom/outerwear/shoes/accessory/other。"
            "formality 只能取 casual/smart_casual/formal。"
            "season_tags 与 style_tags 必须是数组。"
        )

        self.logger.info(
            "Calling Gemini analyze_image image=%s auth_source=%s",
            image_path,
            self.settings.gemini_auth_source,
        )
        response = self._generate_content(
            model=self.settings.gemini_text_model,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type or "image/jpeg"),
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
            action_name="analyze_image",
        )
        text = response.text or ""
        if not text.strip():
            raise ValueError("Gemini analyze_image 返回为空")
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError("Gemini analyze_image 返回了非 JSON 内容") from error

    def remove_background_to_white(self, image_path: Path, mime_type: str | None = None) -> bytes:
        """尝试用 Gemini 生成纯白底商品图。

        Args:
            image_path: 本地衣物图片路径。
            mime_type: 图片 MIME 类型。

        Returns:
            bytes: 可直接落盘的图片二进制内容。

        Raises:
            ValueError: 当 Gemini 调用失败或没有返回图片数据时抛出。
        """

        prompt = (
            "Edit this clothing photo into a clean ecommerce product image. "
            "Keep the original garment design, silhouette, material, color, and details faithful to the source photo. "
            "Remove the distracting background and place the clothing on a pure white studio background. "
            "Do not add props, hands, mannequins, extra objects, or extra garments. "
            "Do not redesign the clothing."
        )

        self.logger.info(
            "Calling Gemini remove_background image=%s auth_source=%s",
            image_path,
            self.settings.gemini_auth_source,
        )
        response = self._generate_content(
            model=self.settings.gemini_image_model,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type or "image/jpeg"),
            ],
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            action_name="remove_background",
        )

        for candidate in response.candidates or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in content.parts or []:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    return inline_data.data

        raise ValueError("Gemini 未返回可保存的白底图片")
