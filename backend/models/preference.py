"""用户偏好模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .base import utc_now_iso


TemperatureSensitivity = Literal["怕冷", "怕热", "normal"]


class UserPreference(BaseModel):
    """保存用户偏好设置。"""

    user_id: str = "default-user"
    preferred_styles: list[str] = Field(default_factory=list)
    avoid_styles: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    avoid_colors: list[str] = Field(default_factory=list)
    temperature_sensitivity: TemperatureSensitivity = "normal"
    fit_preference: str = "不限"
    comfort_priority: str = "中"
    formality_preference: str = "smart_casual"
    updated_at: str = Field(default_factory=utc_now_iso)


class UserPreferenceUpdate(BaseModel):
    """用户偏好更新模型。"""

    preferred_styles: list[str] | None = None
    avoid_styles: list[str] | None = None
    preferred_colors: list[str] | None = None
    avoid_colors: list[str] | None = None
    temperature_sensitivity: TemperatureSensitivity | None = None
    fit_preference: str | None = None
    comfort_priority: str | None = None
    formality_preference: str | None = None

