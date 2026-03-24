"""穿着记录工具。"""

from __future__ import annotations

import logging

from backend.models.item import ClothingItemUpdate
from backend.models.wear_log import WearLog, WearLogCreate
from backend.storage.json_store import JsonListStore
from backend.tools.wardrobe import WardrobeToolService


class WearLogToolService:
    """负责写入穿着历史并同步更新衣物使用状态。"""

    def __init__(self, store: JsonListStore, wardrobe_service: WardrobeToolService, logger: logging.Logger) -> None:
        self.store = store
        self.wardrobe_service = wardrobe_service
        self.logger = logger

    def list_logs(self) -> list[WearLog]:
        """列出历史记录。"""

        logs = [WearLog.model_validate(item) for item in self.store.list_all()]
        return sorted(logs, key=lambda log: log.date, reverse=True)

    def create_log(self, payload: WearLogCreate) -> WearLog:
        """创建穿着记录并同步更新相关衣物。"""

        log = WearLog(
            item_ids=payload.item_ids,
            date=payload.date or WearLog(item_ids=[], occasion="").date,
            occasion=payload.occasion,
            weather_snapshot=payload.weather_snapshot,
            user_feedback=payload.user_feedback,
            outfit_name=payload.outfit_name,
        )
        self.store.upsert(log.model_dump(mode="json"), "log_id")
        self.logger.info("wear_log create log_id=%s item_count=%s", log.log_id, len(log.item_ids))

        for item_id in payload.item_ids:
            item = self.wardrobe_service.get_item(item_id)
            if not item:
                continue
            self.wardrobe_service.update_item(
                item_id,
                ClothingItemUpdate(
                    last_worn_date=log.date,
                    wear_count=item.wear_count + 1,
                ),
            )

        return log

