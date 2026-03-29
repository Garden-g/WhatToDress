"""衣柜工具。"""

from __future__ import annotations

import logging
from typing import Any

from backend.models.base import utc_now_iso
from backend.models.item import ClothingItem, ClothingItemUpdate
from backend.models.taxonomy import (
    ALL_CATEGORIES,
    CATEGORY_TAXONOMY,
    SUBCATEGORY_TO_CATEGORY,
    expand_category_to_sections,
)
from backend.storage.json_store import JsonListStore


class WardrobeToolService:
    """处理衣柜数据增删改查。"""

    def __init__(self, store: JsonListStore, logger: logging.Logger) -> None:
        self.store = store
        self.logger = logger

    def list_items(self, *, include_unconfirmed: bool = False) -> list[ClothingItem]:
        """列出衣物。"""

        items = [ClothingItem.model_validate(item) for item in self.store.list_all()]
        if include_unconfirmed:
            return items
        return [item for item in items if item.confirmed]

    def get_item(self, item_id: str) -> ClothingItem | None:
        """读取单个衣物。"""

        raw = self.store.get_by_id(item_id, "item_id")
        return ClothingItem.model_validate(raw) if raw else None

    def add_item(self, item: ClothingItem) -> ClothingItem:
        """保存衣物。"""

        self.logger.info("wardrobe_add item_id=%s", item.item_id)
        item.updated_at = utc_now_iso()
        self.store.upsert(item.model_dump(mode="json"), "item_id")
        return item

    def update_item(self, item_id: str, updates: ClothingItemUpdate) -> ClothingItem:
        """更新衣物。"""

        existing = self.get_item(item_id)
        if not existing:
            raise ValueError(f"衣物不存在：{item_id}")

        merged = existing.model_copy(update=updates.model_dump(exclude_unset=True))
        merged.updated_at = utc_now_iso()
        self.logger.info("wardrobe_update item_id=%s", item_id)
        self.store.upsert(merged.model_dump(mode="json"), "item_id")
        return merged

    def delete_item(self, item_id: str) -> bool:
        """删除衣物。"""

        self.logger.info("wardrobe_delete item_id=%s", item_id)
        return self.store.delete(item_id, "item_id")

    def confirm_item(self, item_id: str, updates: ClothingItemUpdate) -> ClothingItem:
        """确认上传草稿并转为正式衣物。"""

        confirmed = self.update_item(item_id, updates)
        if not confirmed.confirmed:
            confirmed.confirmed = True
            confirmed.updated_at = utc_now_iso()
            self.store.upsert(confirmed.model_dump(mode="json"), "item_id")
        return confirmed

    def query_items(self, filters: dict[str, Any], *, include_unconfirmed: bool = False) -> list[ClothingItem]:
        """根据过滤条件检索衣物，内置分类体系感知和自动回退。

        分类匹配策略（按优先级）：
        1. 如果 category 是已知大类名（如"上衣""外套"），展开为 closet_section 匹配
        2. 如果 category 是已知子类名（如"皮夹克"），在 subcategory 中查找
        3. 兜底：对 category 和 subcategory 做子串包含匹配

        回退机制：
        - 精确过滤无结果时，自动放宽到 closet_section 级别再查一次
        - 返回结果中会标记是否触发了回退（通过日志记录）
        """

        items = self.list_items(include_unconfirmed=include_unconfirmed)
        results = self._apply_filters(items, filters)

        # 回退机制：如果精确匹配无结果，放宽到 closet_section 级别
        if not results and filters.get("category"):
            broadened_filters = {k: v for k, v in filters.items() if k != "category" and k != "subcategory"}
            sections = expand_category_to_sections(filters["category"])
            if sections:
                broadened_filters["closet_section"] = sections[0]
                results = self._apply_filters(items, broadened_filters)
                if results:
                    self.logger.info(
                        "wardrobe_query broadened category=%s → closet_section=%s matched=%s",
                        filters["category"], sections[0], len(results),
                    )

        # 终极回退：如果还是没结果，返回所有确认过的衣物
        if not results and any(filters.get(k) for k in ["category", "subcategory", "color", "style", "season"]):
            results = [item for item in items if item.confirmed]
            if results:
                self.logger.info(
                    "wardrobe_query ultimate fallback: returning all %s confirmed items",
                    len(results),
                )

        self.logger.info("wardrobe_query filters=%s matched=%s", filters, len(results))
        return results

    def _apply_filters(self, items: list[ClothingItem], filters: dict[str, Any]) -> list[ClothingItem]:
        """对衣物列表应用过滤条件（内部方法）。"""

        results: list[ClothingItem] = []

        # 预处理 category 过滤器：判断是大类、子类还是普通字串
        filter_category = filters.get("category", "")
        category_sections: list[str] = []  # 如果是大类，用 closet_section 匹配
        category_as_sub: str = ""  # 如果是子类，在 subcategory 里匹配
        category_as_text: str = ""  # 都不是，做子串匹配

        if filter_category:
            if filter_category in ALL_CATEGORIES:
                # 大类名 → 展开为 closet_section
                category_sections = expand_category_to_sections(filter_category)
            elif filter_category in SUBCATEGORY_TO_CATEGORY:
                # 子类名 → 直接在 subcategory 里匹配
                category_as_sub = filter_category
            else:
                # 兜底：子串包含匹配
                category_as_text = filter_category

        for item in items:
            if filters.get("confirmed") is True and not item.confirmed:
                continue
            if filters.get("confirmed") is False and item.confirmed:
                continue

            # closet_section 过滤（直接指定的 + 大类展开的）
            if filters.get("closet_section") and item.closet_section != filters["closet_section"]:
                continue
            if category_sections and item.closet_section not in category_sections:
                continue

            # 子类精确匹配
            if category_as_sub and category_as_sub not in (item.subcategory or ""):
                continue

            # 子串兜底匹配（同时查 category 和 subcategory）
            if category_as_text:
                cat_text = (item.category or "") + " " + (item.subcategory or "")
                if category_as_text not in cat_text:
                    continue

            if filters.get("subcategory") and filters["subcategory"] not in (item.subcategory or ""):
                continue
            if filters.get("color") and filters["color"] not in item.color:
                continue
            if filters.get("style") and filters["style"] not in " ".join(item.style_tags):
                continue
            if filters.get("season") and filters["season"] not in item.season_tags:
                continue
            if "is_available" in filters and item.is_available != bool(filters["is_available"]):
                continue
            results.append(item)

        return results

