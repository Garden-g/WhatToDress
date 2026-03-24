"""图像工具。"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any

from backend.models.base import utc_now_iso
from backend.models.item import ClothingItem
from backend.providers.gemini import GeminiProvider
from backend.storage.image_store import ImageStore


class ImageToolService:
    """负责衣物图片分析与白底图处理。"""

    def __init__(
        self,
        analysis_providers: dict[str, Any],
        bg_provider: GeminiProvider,
        image_store: ImageStore,
        logger: logging.Logger,
    ) -> None:
        self.analysis_providers = analysis_providers
        self.bg_provider = bg_provider
        self.image_store = image_store
        self.logger = logger
        self._log_rembg_readiness()

    def _log_rembg_readiness(self) -> None:
        """在服务初始化时记录 rembg 是否可用。

        这里不直接抛错，是因为 rembg 只是白底图的兜底层。
        即使它不可用，上传识图主链路仍然应该能继续工作。
        """

        if importlib.util.find_spec("rembg") is None:
            self.logger.warning("rembg dependency is unavailable, white background fallback will be disabled")

    def image_analyze(
        self,
        image_path: Path,
        provider_name: str = "gemini",
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        """根据指定 provider 识别衣物属性。"""

        provider = self.analysis_providers.get(provider_name)
        if provider is None:
            raise ValueError(f"不支持的识图 provider：{provider_name}")
        self.logger.info("Using vision provider=%s for image analyze", provider_name)
        return provider.analyze_image(image_path=image_path, mime_type=mime_type)

    def _normalize_string(self, value: Any, default: str) -> str:
        """把任意输入收口成安全字符串。

        Args:
            value: 识图模型返回的原始值。
            default: 当原始值不可用时的回退值。

        Returns:
            str: 去空白后的字符串；如果无法使用，则返回默认值。
        """

        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        return default

    def _normalize_list_field(self, value: Any) -> list[str]:
        """把数组或逗号分隔字符串统一转成字符串列表。

        Args:
            value: 识图模型返回的原始标签值。

        Returns:
            list[str]: 去空白、去空值后的列表。
        """

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    def _normalize_formality(self, value: Any, notes: list[str]) -> str:
        """把模型返回的正式度映射到业务固定枚举。

        Args:
            value: 原始正式度文本。
            notes: 归一化备注列表，会在发生映射或回退时追加说明。

        Returns:
            str: `casual | smart_casual | formal` 之一。
        """

        normalized = self._normalize_string(value, "casual")
        lowered = normalized.lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "casual": "casual",
            "everyday": "casual",
            "daily": "casual",
            "smart_casual": "smart_casual",
            "business_casual": "smart_casual",
            "semi_formal": "smart_casual",
            "smart": "smart_casual",
            "formal": "formal",
            "business_formal": "formal",
        }
        result = mapping.get(lowered, "casual")
        if normalized != result:
            notes.append(f"normalized formality: {normalized} -> {result}")
            self.logger.warning("Normalized formality raw=%s normalized=%s", normalized, result)
        return result

    def _normalize_closet_section(self, value: Any, notes: list[str]) -> str:
        """把模型返回的挂放区域映射到业务固定枚举。

        Args:
            value: 原始挂放区域。
            notes: 归一化备注列表。

        Returns:
            str: 合法的 closet_section 值。
        """

        normalized = self._normalize_string(value, "other")
        lowered = normalized.lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "top": "top",
            "tops": "top",
            "shirt": "top",
            "upper": "top",
            "上装": "top",
            "bottom": "bottom",
            "bottoms": "bottom",
            "pants": "bottom",
            "trousers": "bottom",
            "skirt": "bottom",
            "下装": "bottom",
            "outerwear": "outerwear",
            "coat": "outerwear",
            "jacket": "outerwear",
            "外套": "outerwear",
            "shoes": "shoes",
            "shoe": "shoes",
            "footwear": "shoes",
            "鞋": "shoes",
            "accessory": "accessory",
            "accessories": "accessory",
            "配件": "accessory",
            "other": "other",
            "其他": "other",
        }
        result = mapping.get(lowered, "other")
        if normalized != result:
            notes.append(f"normalized closet_section: {normalized} -> {result}")
            self.logger.warning("Normalized closet_section raw=%s normalized=%s", normalized, result)
        return result

    def _normalize_analysis(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """把 provider 原始输出标准化成业务安全结构。

        Args:
            analysis: 外部识图 provider 返回的原始 JSON。

        Returns:
            dict[str, Any]: 已经过业务归一化的识图结构。
        """

        normalization_notes: list[str] = []
        normalized = {
            "name": self._normalize_string(
                analysis.get("name") or analysis.get("subcategory") or analysis.get("category"),
                "未命名衣物",
            ),
            "category": self._normalize_string(analysis.get("category"), "未识别"),
            "subcategory": self._normalize_string(analysis.get("subcategory"), ""),
            "closet_section": self._normalize_closet_section(analysis.get("closet_section"), normalization_notes),
            "color": self._normalize_string(analysis.get("color"), "未知"),
            "secondary_color": self._normalize_string(analysis.get("secondary_color"), ""),
            "season_tags": self._normalize_list_field(analysis.get("season_tags")),
            "style_tags": self._normalize_list_field(analysis.get("style_tags")),
            "formality": self._normalize_formality(analysis.get("formality"), normalization_notes),
            "material": self._normalize_string(analysis.get("material"), ""),
        }

        original_notes = self._normalize_string(analysis.get("analysis_notes"), "")
        joined_notes = " | ".join([*([original_notes] if original_notes else []), *normalization_notes]).strip(" |")
        normalized["analysis_notes"] = joined_notes or None
        return normalized

    def _build_safe_item_payload(
        self,
        normalized_analysis: dict[str, Any],
        original_image_url: str,
        white_bg_url: str | None,
    ) -> dict[str, Any]:
        """构造可交给 ClothingItem 的安全数据。

        Args:
            normalized_analysis: 已归一化的识图结果。
            original_image_url: 原图访问地址。
            white_bg_url: 白底图访问地址。

        Returns:
            dict[str, Any]: 经过最终安全兜底的衣物字典。
        """

        return {
            "name": normalized_analysis.get("name") or "未命名衣物",
            "category": normalized_analysis.get("category") or "未识别",
            "subcategory": normalized_analysis.get("subcategory") or None,
            "closet_section": normalized_analysis.get("closet_section") or "other",
            "color": normalized_analysis.get("color") or "未知",
            "secondary_color": normalized_analysis.get("secondary_color") or None,
            "season_tags": normalized_analysis.get("season_tags") or [],
            "style_tags": normalized_analysis.get("style_tags") or [],
            "formality": normalized_analysis.get("formality") or "casual",
            "material": normalized_analysis.get("material") or None,
            "image_original_url": original_image_url,
            "image_white_bg_url": white_bg_url,
            "analysis_notes": normalized_analysis.get("analysis_notes"),
            "confirmed": False,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }

    def bg_remove(self, image_path: Path, item_id: str, mime_type: str | None = None) -> tuple[str | None, str | None]:
        """生成白底图。

        Args:
            image_path: 本地原图路径。
            item_id: 当前衣物草稿 ID。
            mime_type: 图片 MIME 类型。

        Returns:
            tuple[str | None, str | None]:
                - 第一个值是白底图 URL；失败时为 None。
                - 第二个值是白底图阶段的说明文本，用于写入识别备注。

        Raises:
            本函数内部会吞掉 Gemini 与 rembg 的异常，并通过返回值表达降级结果。
            这样做是为了保证上传流程尽可能继续，至少把原图识别结果保存下来。
        """

        try:
            self.logger.info(
                "Starting bg_remove provider=gemini auth_source=%s image=%s item_id=%s",
                self.bg_provider.settings.gemini_auth_source,
                image_path,
                item_id,
            )
            content = self.bg_provider.remove_background_to_white(image_path=image_path, mime_type=mime_type)
            file_name, _ = self.image_store.save_white_background_bytes(item_id, content, suffix=".png")
            self.logger.info("bg_remove success provider=gemini item_id=%s", item_id)
            return self.image_store.build_api_url("white_bg", file_name), "Gemini white background success"
        except Exception as gemini_error:
            # 白底图是上传链路的重要体验点，因此这里记录 provider、认证来源和回退动作，
            # 方便后续快速判断是 Gemini 配置问题、模型返回问题还是 rembg 接管成功。
            self.logger.warning(
                "Gemini bg_remove failed, fallback rembg auth_source=%s item_id=%s error=%s",
                self.bg_provider.settings.gemini_auth_source,
                item_id,
                gemini_error,
            )

        try:
            from rembg import remove

            raw = image_path.read_bytes()
            output = remove(raw)
            file_name, _ = self.image_store.save_white_background_bytes(item_id, output, suffix=".png")
            self.logger.info("bg_remove success provider=rembg item_id=%s", item_id)
            return self.image_store.build_api_url("white_bg", file_name), "rembg fallback success"
        except ModuleNotFoundError as rembg_import_error:
            # 这里单独拆出依赖缺失，是因为它和“rembg 本身运行失败”是两类完全不同的问题。
            # 前者需要先补运行环境，后者才需要排查图片内容或库行为。
            self.logger.error(
                "rembg dependency missing item_id=%s error=%s",
                item_id,
                rembg_import_error,
                exc_info=True,
            )
            return None, "white background failed, rembg is not installed, original image kept"
        except Exception as rembg_error:
            self.logger.error("rembg fallback failed item_id=%s error=%s", item_id, rembg_error, exc_info=True)
            return None, "white background failed, original image kept"

    def build_draft_item(
        self,
        analysis: dict[str, Any],
        original_image_url: str,
        white_bg_url: str | None,
    ) -> ClothingItem:
        """把识图结果组装成待确认衣物对象。

        Args:
            analysis: provider 返回的原始识图结果。
            original_image_url: 原图访问地址。
            white_bg_url: 白底图访问地址。

        Returns:
            ClothingItem: 已通过业务归一化和安全兜底的待确认衣物。

        Raises:
            ValueError: 理论上不应抛出；如果最终仍失败，说明安全兜底本身也出现了问题。
        """

        normalized_analysis = self._normalize_analysis(analysis)
        payload = self._build_safe_item_payload(normalized_analysis, original_image_url, white_bg_url)

        try:
            return ClothingItem(**payload)
        except Exception as error:
            # 这里保留最后一道兜底，是为了防止未来模型输出再冒出新的非法值时，
            # 上传流程重新退化成 500。我们宁可回退到最保守值，也不要把用户流程直接打断。
            self.logger.warning("Draft item validation fallback triggered error=%s", error, exc_info=True)
            fallback_notes = " | ".join(
                filter(
                    None,
                    [
                        payload.get("analysis_notes"),
                        "fallback defaults applied after validation failure",
                    ],
                )
            )
            payload.update(
                {
                    "closet_section": "other",
                    "formality": "casual",
                    "season_tags": payload.get("season_tags") if isinstance(payload.get("season_tags"), list) else [],
                    "style_tags": payload.get("style_tags") if isinstance(payload.get("style_tags"), list) else [],
                    "analysis_notes": fallback_notes,
                }
            )
            return ClothingItem(**payload)
