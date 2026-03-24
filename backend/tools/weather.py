"""天气工具。"""

from __future__ import annotations

import re
from typing import Any

from backend.providers.weather import WeatherProvider


def extract_weather_from_text(message: str) -> dict[str, Any] | None:
    """尝试直接从用户文本中抽取天气。"""

    temp_match = re.search(r"(-?\d{1,2})\s*度", message)
    rain = "雨" in message
    if not temp_match:
        return None

    temp = int(temp_match.group(1))
    return {
        "city": None,
        "date": None,
        "temp": temp,
        "temp_max": temp + 2,
        "temp_min": temp - 2,
        "rain_probability": 80 if rain else 10,
        "wind_speed": 10,
        "condition": "有雨风险" if rain else "天气稳定",
    }


class WeatherToolService:
    """天气工具服务。"""

    def __init__(self, provider: WeatherProvider) -> None:
        self.provider = provider

    def weather_search(self, message: str | None = None, city: str | None = None, day_label: str | None = None) -> dict[str, Any]:
        """优先从文本抽天气，否则走外部天气服务。"""

        if message:
            inline = extract_weather_from_text(message)
            if inline:
                inline["city"] = city or self.provider.settings.default_city
                inline["date"] = self.provider.resolve_target_date(day_label).isoformat()
                return inline
        return self.provider.get_weather(city=city, day_label=day_label)

