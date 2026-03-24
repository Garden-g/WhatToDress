from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from backend.providers.glm import GlmProvider
from backend.tests.conftest import build_test_settings


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "request failed",
                request=httpx.Request("POST", "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


def test_glm_provider_analyze_image_parses_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = build_test_settings(tmp_path)
    provider = GlmProvider(settings, logger=__import__("logging").getLogger("test"))
    image_path = tmp_path / "shirt.png"
    image_path.write_bytes(b"fake-image")

    def fake_post(*_, **__):
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"category":"衬衫","subcategory":"蓝衬衫","closet_section":"top",'
                                '"color":"蓝色","secondary_color":null,"season_tags":["春"],'
                                '"style_tags":["通勤"],"formality":"smart_casual",'
                                '"material":"棉","analysis_notes":"glm ok"}'
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    result = provider.analyze_image(image_path, "image/png")
    assert result["category"] == "衬衫"
    assert result["analysis_notes"] == "glm ok"


def test_glm_provider_analyze_image_rejects_non_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = build_test_settings(tmp_path)
    provider = GlmProvider(settings, logger=__import__("logging").getLogger("test"))
    image_path = tmp_path / "shirt.png"
    image_path.write_bytes(b"fake-image")

    def fake_post(*_, **__):
        return DummyResponse({"choices": [{"message": {"content": "not json"}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(ValueError, match="非 JSON"):
        provider.analyze_image(image_path, "image/png")
