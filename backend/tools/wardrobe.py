"""衣柜工具。"""

from __future__ import annotations

import logging
from typing import Any

from backend.models.base import utc_now_iso
from backend.models.item import ClothingItem, ClothingItemUpdate
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
        """根据简单过滤条件检索衣物。"""

        items = self.list_items(include_unconfirmed=include_unconfirmed)
        results: list[ClothingItem] = []

        for item in items:
            if filters.get("confirmed") is True and not item.confirmed:
                continue
            if filters.get("confirmed") is False and item.confirmed:
                continue
            if filters.get("closet_section") and item.closet_section != filters["closet_section"]:
                continue
            if filters.get("category") and filters["category"] not in (item.category or ""):
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

        self.logger.info("wardrobe_query filters=%s matched=%s", filters, len(results))
        return results

