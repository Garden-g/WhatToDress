"""衣物相关数据模型。"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .base import utc_now_iso


ClosetSection = Literal["top", "bottom", "outerwear", "shoes", "accessory", "other"]
CleanStatus = Literal["clean", "dirty", "washing", "ironing", "storage"]
FormalityLevel = Literal["casual", "smart_casual", "formal"]


class ClothingItem(BaseModel):
    """表示一件具体衣物。

    这里的数据模型同时服务于：
    1. JSON 存储
    2. API 返回
    3. 推荐算法输入

    因此前端需要的展示字段和业务逻辑需要的约束字段都放在一起。
    """

    item_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str | None = None
    category: str
    subcategory: str | None = None
    closet_section: ClosetSection = "other"
    color: str
    secondary_color: str | None = None
    season_tags: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    formality: FormalityLevel = "casual"
    material: str | None = None
    brand: str | None = None
    image_original_url: str
    image_white_bg_url: str | None = None
    is_available: bool = True
    clean_status: CleanStatus = "clean"
    storage_location: str | None = None
    last_worn_date: str | None = None
    wear_count: int = 0
    favorite_score: int = 50
    dislike_flag: bool = False
    analysis_notes: str | None = None
    confirmed: bool = True
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class ClothingItemUpdate(BaseModel):
    """衣物可更新字段。"""

    name: str | None = None
    category: str | None = None
    subcategory: str | None = None
    closet_section: ClosetSection | None = None
    color: str | None = None
    secondary_color: str | None = None
    season_tags: list[str] | None = None
    style_tags: list[str] | None = None
    formality: FormalityLevel | None = None
    material: str | None = None
    brand: str | None = None
    image_white_bg_url: str | None = None
    is_available: bool | None = None
    clean_status: CleanStatus | None = None
    storage_location: str | None = None
    last_worn_date: str | None = None
    wear_count: int | None = None
    favorite_score: int | None = None
    dislike_flag: bool | None = None
    analysis_notes: str | None = None
    confirmed: bool | None = None

