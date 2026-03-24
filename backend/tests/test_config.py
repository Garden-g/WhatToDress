from __future__ import annotations

import pytest

from backend.config import Settings


def test_settings_prefers_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 Gemini Developer API 的官方环境变量优先级。

    这里锁定的约定是：
    - 如果同时存在 GOOGLE_API_KEY 和 GEMINI_API_KEY
    - 当前代码必须优先使用 GOOGLE_API_KEY

    这样做是为了与官方 SDK 文档保持一致，
    避免后续再次误接到 Google Cloud 专用变量上。
    """

    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")

    settings = Settings.load()

    assert settings.resolved_gemini_api_key == "google-key"
    assert settings.gemini_auth_source == "GOOGLE_API_KEY"


def test_settings_falls_back_to_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证对历史 GEMINI_API_KEY 配置的兼容兜底。"""

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")

    settings = Settings.load()

    assert settings.resolved_gemini_api_key == "gemini-key"
    assert settings.gemini_auth_source == "GEMINI_API_KEY"


def test_validate_runtime_secrets_accepts_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证只配置 GOOGLE_API_KEY 时启动校验仍然通过。"""

    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")

    settings = Settings.load()

    settings.validate_runtime_secrets()
