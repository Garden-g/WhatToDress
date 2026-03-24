"""穿搭推荐工具。"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend.models.item import ClothingItem
from backend.models.outfit import OutfitRecommendation
from backend.models.preference import UserPreference
from backend.providers.deepseek import DeepSeekProvider


def _is_recently_worn(item: ClothingItem, recent_ids: set[str]) -> bool:
    """判断衣物是否在近期穿着中出现过。"""

    return item.item_id in recent_ids


def _sort_candidates(items: list[ClothingItem], recent_ids: set[str], preferred_colors: list[str]) -> list[ClothingItem]:
    """按推荐优先级排序衣物。"""

    def score(item: ClothingItem) -> tuple[int, int, int]:
        color_bonus = 1 if item.color in preferred_colors else 0
        recent_penalty = -1 if _is_recently_worn(item, recent_ids) else 0
        return (color_bonus, item.favorite_score, recent_penalty)

    return sorted(items, key=score, reverse=True)


class RecommendToolService:
    """根据规则生成候选穿搭，并尽量用 DeepSeek-R1 润色推荐理由。"""

    def __init__(self, provider: DeepSeekProvider) -> None:
        self.provider = provider

    def _group_items(self, items: list[ClothingItem]) -> dict[str, list[ClothingItem]]:
        """按衣柜区域分组。"""

        grouped: dict[str, list[ClothingItem]] = defaultdict(list)
        for item in items:
            grouped[item.closet_section].append(item)
        return grouped

    def _needs_outerwear(self, weather: dict[str, Any]) -> bool:
        """根据天气判断是否需要外套。"""

        temp = float(weather.get("temp") or 20)
        rain_probability = int(weather.get("rain_probability") or 0)
        wind_speed = float(weather.get("wind_speed") or 0)
        return temp <= 20 or rain_probability >= 40 or wind_speed >= 20

    def _build_candidate_outfits(
        self,
        available_items: list[ClothingItem],
        forgotten_items: list[dict[str, Any]],
        recent_ids: set[str],
        preferences: UserPreference,
        weather: dict[str, Any],
        scenario: str,
    ) -> list[OutfitRecommendation]:
        """先用规则层构造稳定的候选穿搭。"""

        filtered = [
            item
            for item in available_items
            if item.confirmed and item.is_available and not item.dislike_flag and item.clean_status not in {"dirty", "washing"}
        ]
        grouped = self._group_items(filtered)
        tops = _sort_candidates(grouped.get("top", []), recent_ids, preferences.preferred_colors)
        bottoms = _sort_candidates(grouped.get("bottom", []), recent_ids, preferences.preferred_colors)
        outers = _sort_candidates(grouped.get("outerwear", []), recent_ids, preferences.preferred_colors)
        shoes = _sort_candidates(grouped.get("shoes", []), recent_ids, preferences.preferred_colors)

        forgotten_ids = {row["item"].item_id for row in forgotten_items}

        def pick(seq: list[ClothingItem], index: int) -> ClothingItem | None:
            if not seq:
                return None
            return seq[index % len(seq)]

        outfits: list[OutfitRecommendation] = []
        needs_outer = self._needs_outerwear(weather)

        for index in range(3):
            selection: list[ClothingItem] = []
            top = pick(tops, index)
            bottom = pick(bottoms, index)
            shoe = pick(shoes, index)
            outer = pick(outers, index)

            if top:
                selection.append(top)
            if bottom:
                selection.append(bottom)
            if needs_outer and outer:
                selection.append(outer)
            if shoe:
                selection.append(shoe)

            if index == 0 and forgotten_items:
                forgotten_item = forgotten_items[0]["item"]
                if forgotten_item not in selection and forgotten_item.closet_section in {"top", "outerwear", "bottom", "shoes"}:
                    selection = [item for item in selection if item.closet_section != forgotten_item.closet_section]
                    selection.append(forgotten_item)

            has_forgotten = any(item.item_id in forgotten_ids for item in selection)
            name = "遗忘唤醒方案" if has_forgotten else f"{scenario}方案 {index + 1}"

            outfits.append(
                OutfitRecommendation(
                    name=name,
                    scenario=scenario,
                    items=selection,
                    reason="规则层已生成候选，等待推理模型补充更自然的理由。",
                    tips="如果你今天想更稳妥一点，可以优先选颜色更百搭的单品。",
                    metadata={
                        "has_forgotten_item": has_forgotten,
                        "weather": weather,
                    },
                )
            )

        return outfits

    def outfit_recommend(
        self,
        weather: dict[str, Any],
        scenario: str,
        available_items: list[ClothingItem],
        forgotten_items: list[dict[str, Any]],
        recent_logs: list[dict[str, Any]],
        preferences: UserPreference,
    ) -> list[OutfitRecommendation]:
        """生成 3 套穿搭建议。"""

        recent_ids = {item_id for log in recent_logs[:5] for item_id in log.get("item_ids", [])}
        outfits = self._build_candidate_outfits(
            available_items=available_items,
            forgotten_items=forgotten_items,
            recent_ids=recent_ids,
            preferences=preferences,
            weather=weather,
            scenario=scenario,
        )

        payload = {
            "weather": weather,
            "scenario": scenario,
            "preferences": preferences.model_dump(mode="json"),
            "outfits": [
                {
                    "name": outfit.name,
                    "items": [item.model_dump(mode="json") for item in outfit.items],
                    "metadata": outfit.metadata,
                }
                for outfit in outfits
            ],
        }
        try:
            enriched = self.provider.reason_outfits(payload)
            for index, outfit in enumerate(outfits):
                if index >= len(enriched):
                    break
                outfit.name = enriched[index].get("name", outfit.name)
                outfit.reason = enriched[index].get("reason", outfit.reason)
                outfit.tips = enriched[index].get("tips", outfit.tips)
        except Exception:
            for outfit in outfits:
                outfit.reason = (
                    f"根据 {weather.get('temp')}°C、{weather.get('condition')} 和 {scenario} 场景，"
                    "这套更符合温度、正式度和可穿状态的平衡。"
                )
                outfit.tips = "优先从可穿、近期没怎么穿过、且颜色不冲突的单品里组合。"

        return outfits
