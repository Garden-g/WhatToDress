"""API 请求与响应模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .item import ClothingItem, ClothingItemUpdate
from .outfit import OutfitRecommendation
from .preference import UserPreference, UserPreferenceUpdate
from .wear_log import WearLog, WearLogCreate


class ApiEnvelope(BaseModel):
    """统一响应包裹结构。"""

    success: bool
    data: Any = None
    error: str | None = None


class ChatMessageDTO(BaseModel):
    """前端聊天消息格式。"""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """聊天接口请求体。"""

    message: str
    history: list[ChatMessageDTO] = Field(default_factory=list)


class ChatResponseData(BaseModel):
    """聊天接口的业务数据部分。"""

    reply: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    action: Literal["query", "recommend", "clarify", "confirm"]


class UploadResponseData(BaseModel):
    """上传接口返回的待确认衣物。"""

    item: ClothingItem


VisionProviderName = Literal["gemini", "glm"]


class ConfirmWardrobeRequest(BaseModel):
    """确认上传草稿时的请求体。"""

    updates: ClothingItemUpdate = Field(default_factory=ClothingItemUpdate)


class WardrobeListResponse(BaseModel):
    """衣柜列表返回数据。"""

    items: list[ClothingItem]


class ForgottenItemResponse(BaseModel):
    """遗忘衣物卡片数据。"""

    item: ClothingItem
    forgotten_score: int
    reasons: list[str] = Field(default_factory=list)


class ForgottenListResponse(BaseModel):
    """遗忘衣物列表返回结构。"""

    items: list[ForgottenItemResponse]


class RecommendationListResponse(BaseModel):
    """推荐列表返回结构。"""

    items: list[OutfitRecommendation]


class HistoryListResponse(BaseModel):
    """穿搭历史列表返回结构。"""

    items: list[WearLog]


class PreferenceResponse(BaseModel):
    """偏好接口返回结构。"""

    preference: UserPreference
