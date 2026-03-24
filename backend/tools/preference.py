"""用户偏好工具。"""

from __future__ import annotations

import logging

from backend.models.base import utc_now_iso
from backend.models.preference import UserPreference, UserPreferenceUpdate
from backend.storage.json_store import JsonObjectStore


class PreferenceToolService:
    """负责读取和更新用户偏好。"""

    def __init__(self, store: JsonObjectStore, logger: logging.Logger) -> None:
        self.store = store
        self.logger = logger

    def get_preference(self) -> UserPreference:
        """获取当前用户偏好。"""

        return UserPreference.model_validate(self.store.get_object())

    def update_preference(self, updates: UserPreferenceUpdate) -> UserPreference:
        """更新偏好。"""

        current = self.get_preference()
        merged = current.model_copy(update=updates.model_dump(exclude_unset=True))
        merged.updated_at = utc_now_iso()
        self.logger.info("user_preference update")
        self.store.write(merged.model_dump(mode="json"))
        return merged

