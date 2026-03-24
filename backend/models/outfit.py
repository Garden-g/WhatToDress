"""穿搭推荐相关模型。"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .base import utc_now_iso
from .item import ClothingItem


class OutfitRecommendation(BaseModel):
    """单套穿搭推荐结果。"""

    outfit_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    items: list[ClothingItem]
    scenario: str
    reason: str
    tips: str
    created_at: str = Field(default_factory=utc_now_iso)
    accepted_or_not: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

