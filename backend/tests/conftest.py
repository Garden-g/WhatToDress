from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


def build_test_settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "data"
    images_dir = data_dir / "images"
    return Settings(
        gemini_api_key="test-gemini-key",
        google_api_key="",
        glm_api_key="test-glm-key",
        glm_base_url="https://open.bigmodel.cn/api/paas/v4",
        deepseek_api_key="test-deepseek-key",
        deepseek_base_url="https://api.deepseek.com",
        gemini_text_model="gemini-2.5-flash",
        gemini_image_model="gemini-3.1-flash-image-preview",
        glm_vision_model="glm-4.6v",
        deepseek_chat_model="deepseek-chat",
        deepseek_reasoner_model="deepseek-reasoner",
        data_dir=data_dir,
        images_dir=images_dir,
        default_city="Shanghai",
        request_timeout_seconds=5,
        log_level="INFO"
    )


@pytest.fixture()
def app(tmp_path: Path):
    settings = build_test_settings(tmp_path)
    settings.ensure_directories()
    application = create_app(settings)
    return application


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client
