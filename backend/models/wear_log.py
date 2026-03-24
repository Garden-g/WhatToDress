"""穿着历史相关模型。"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .base import utc_now_iso


class WearLog(BaseModel):
    """表示一次真实穿着记录。"""

    log_id: str = Field(default_factory=lambda: str(uuid4()))
    item_ids: list[str]
    date: str = Field(default_factory=utc_now_iso)
    occasion: str
    weather_snapshot: dict[str, Any] = Field(default_factory=dict)
    user_feedback: str | None = None
    outfit_name: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class WearLogCreate(BaseModel):
    """创建穿着记录时需要的入参。"""

    item_ids: list[str]
    date: str | None = None
    occasion: str
    weather_snapshot: dict[str, Any] = Field(default_factory=dict)
    user_feedback: str | None = None
    outfit_name: str | None = None

