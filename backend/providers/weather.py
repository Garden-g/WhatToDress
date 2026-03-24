"""天气提供者。"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import httpx

from backend.config import Settings


class WeatherProvider:
    """根据城市和日期返回轻量天气信息。"""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def resolve_target_date(self, day_label: str | None) -> date:
        """把自然语言日期标签映射成具体日期。"""

        today = datetime.utcnow().date()
        if not day_label or day_label in {"today", "今天"}:
            return today
        if day_label in {"tomorrow", "明天"}:
            return today + timedelta(days=1)
        if day_label in {"day_after_tomorrow", "后天"}:
            return today + timedelta(days=2)
        return today

    def get_weather(self, city: str | None = None, day_label: str | None = None) -> dict[str, Any]:
        """获取指定城市和日期的天气快照。"""

        target_city = city or self.settings.default_city
        target_date = self.resolve_target_date(day_label)
        self.logger.info("Calling weather provider city=%s date=%s", target_city, target_date.isoformat())

        geo_response = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": target_city, "count": 1, "language": "zh", "format": "json"},
            timeout=self.settings.request_timeout_seconds,
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        results = geo_data.get("results") or []
        if not results:
            raise ValueError(f"未找到城市：{target_city}")

        location = results[0]
        forecast_response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "timezone": "auto",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode,windspeed_10m_max",
                "forecast_days": 3,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        forecast_response.raise_for_status()
        daily = forecast_response.json().get("daily", {})
        date_strings = daily.get("time", [])
        try:
            index = date_strings.index(target_date.isoformat())
        except ValueError as error:
            raise ValueError("天气接口未返回目标日期数据") from error

        temp_max = daily.get("temperature_2m_max", [None])[index]
        temp_min = daily.get("temperature_2m_min", [None])[index]
        rain_probability = daily.get("precipitation_probability_max", [0])[index]
        wind_speed = daily.get("windspeed_10m_max", [0])[index]
        return {
            "city": location.get("name", target_city),
            "date": target_date.isoformat(),
            "temp": round(((temp_max or 0) + (temp_min or 0)) / 2, 1),
            "temp_max": temp_max,
            "temp_min": temp_min,
            "rain_probability": rain_probability,
            "wind_speed": wind_speed,
            "condition": "有雨风险" if rain_probability and rain_probability >= 40 else "天气稳定",
        }
