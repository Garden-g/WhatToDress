from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient

from backend.main import create_app
from backend.tests.conftest import build_test_settings


def test_upload_confirm_and_query_flow(client, app):
    ctx = app.state.ctx

    def fake_analyze(*_, **__):
        return {
            "category": "衬衫",
            "subcategory": "蓝色衬衫",
            "closet_section": "top",
            "color": "蓝色",
            "season_tags": ["春", "秋"],
            "style_tags": ["通勤"],
            "formality": "smart_casual",
            "material": "棉",
            "analysis_notes": "测试识别结果"
        }

    def fake_bg_remove(*_, **__):
        return "/api/images/white_bg/fake.png", "test fallback"

    ctx.image_service.image_analyze = fake_analyze
    ctx.image_service.bg_remove = fake_bg_remove

    response = client.post(
        "/api/upload",
        files={"file": ("shirt.png", BytesIO(b"fake-image-content"), "image/png")}
    )
    assert response.status_code == 200
    data = response.json()["data"]["item"]
    assert data["confirmed"] is False

    confirm_response = client.post(
        f"/api/wardrobe/{data['item_id']}/confirm",
        json={"updates": {"name": "通勤蓝衬衫", "confirmed": True}}
    )
    assert confirm_response.status_code == 200

    wardrobe_response = client.get("/api/wardrobe?color=蓝色")
    assert wardrobe_response.status_code == 200
    items = wardrobe_response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "通勤蓝衬衫"


def test_upload_supports_glm_provider(client, app):
    ctx = app.state.ctx

    def fake_analyze(*_, **kwargs):
        provider_name = kwargs.get("provider_name")
        return {
            "category": "针织衫",
            "subcategory": "米色针织衫",
            "closet_section": "top",
            "color": "米色",
            "season_tags": ["秋", "冬"],
            "style_tags": ["温柔"],
            "formality": "casual",
            "material": "羊毛",
            "analysis_notes": f"测试识别结果-{provider_name}"
        }

    def fake_bg_remove(*_, **__):
        return "/api/images/white_bg/fake-glm.png", "test fallback"

    ctx.image_service.image_analyze = fake_analyze
    ctx.image_service.bg_remove = fake_bg_remove

    response = client.post(
        "/api/upload",
        files={"file": ("knit.png", BytesIO(b"fake-image-content"), "image/png")},
        data={"vision_provider": "glm"}
    )
    assert response.status_code == 200
    data = response.json()["data"]["item"]
    assert data["confirmed"] is False
    assert "provider=glm" in data["analysis_notes"]


def test_upload_rejects_invalid_provider(client):
    response = client.post(
        "/api/upload",
        files={"file": ("shirt.png", BytesIO(b"fake-image-content"), "image/png")},
        data={"vision_provider": "unknown"}
    )
    assert response.status_code == 400
    assert "不支持的识图 provider" in response.text


def test_upload_flow_accepts_google_api_key_only(tmp_path):
    """验证只配置 GOOGLE_API_KEY 时，上传链路仍能正常启动并返回结果。

    这里不用真实外部 API，而是替换 image_service 的方法。
    测试目标不是第三方连通性，而是确认启动校验和上传流程不会因为 GEMINI_API_KEY 为空而被阻断。
    """

    settings = build_test_settings(tmp_path)
    settings.google_api_key = "google-api-key"
    settings.gemini_api_key = ""
    application = create_app(settings)
    ctx = application.state.ctx

    def fake_analyze(*_, **__):
        return {
            "category": "外套",
            "subcategory": "灰色夹克",
            "closet_section": "outerwear",
            "color": "灰色",
            "season_tags": ["秋"],
            "style_tags": ["通勤"],
            "formality": "smart_casual",
            "material": "棉",
            "analysis_notes": "测试 google api key"
        }

    def fake_bg_remove(*_, **__):
        return "/api/images/white_bg/fake-google.png", "Gemini white background success"

    ctx.image_service.image_analyze = fake_analyze
    ctx.image_service.bg_remove = fake_bg_remove

    with TestClient(application) as test_client:
        response = test_client.post(
            "/api/upload",
            files={"file": ("jacket.png", BytesIO(b"fake-image-content"), "image/png")},
            data={"vision_provider": "gemini"}
        )

    assert response.status_code == 200
    data = response.json()["data"]["item"]
    assert data["image_white_bg_url"] == "/api/images/white_bg/fake-google.png"
    assert "provider=gemini" in data["analysis_notes"]


def test_upload_returns_stable_error_when_gemini_analysis_fails(client, app):
    """验证 Gemini 识图失败时，接口返回稳定 JSON 错误而不是断连。

    这个用例直接模拟 provider 抛错。
    只要前端还能拿到 502 和可读文本，就说明这次异常包装达到了目标。
    """

    app.state.ctx.image_service.image_analyze = lambda *_, **__: (_ for _ in ()).throw(
        ValueError("Gemini analyze_image 失败：模拟异常")
    )

    response = client.post(
        "/api/upload",
        files={"file": ("shirt.png", BytesIO(b"fake-image-content"), "image/png")},
        data={"vision_provider": "gemini"}
    )

    assert response.status_code == 502
    payload = response.json()
    assert payload["success"] is False
    assert "衣物识别失败" in payload["error"]


def test_upload_normalizes_gemini_enum_and_list_fields(client, app):
    """验证 Gemini 的常见漂移输出会在入模前被归一化。

    这个用例覆盖了当前真实报错的 `Smart Casual`，
    同时也验证逗号分隔标签和中文挂放区域会被后端统一收口。
    """

    ctx = app.state.ctx

    def fake_analyze(*_, **__):
        return {
            "category": "外套",
            "subcategory": "leather jacket",
            "closet_section": "外套",
            "color": "black",
            "season_tags": "spring, autumn, winter",
            "style_tags": "casual, streetwear, vintage",
            "formality": "Smart Casual",
            "material": "leather",
            "analysis_notes": "原始 Gemini 结果"
        }

    def fake_bg_remove(*_, **__):
        return "/api/images/white_bg/fake-normalized.png", "Gemini white background success"

    ctx.image_service.image_analyze = fake_analyze
    ctx.image_service.bg_remove = fake_bg_remove

    response = client.post(
        "/api/upload",
        files={"file": ("jacket.png", BytesIO(b"fake-image-content"), "image/png")},
        data={"vision_provider": "gemini"}
    )

    assert response.status_code == 200
    item = response.json()["data"]["item"]
    assert item["formality"] == "smart_casual"
    assert item["closet_section"] == "outerwear"
    assert item["season_tags"] == ["spring", "autumn", "winter"]
    assert item["style_tags"] == ["casual", "streetwear", "vintage"]
    assert "normalized formality: Smart Casual -> smart_casual" in item["analysis_notes"]


def test_upload_unknown_formality_falls_back_to_casual(client, app):
    """验证未知正式度不会再把上传打成 500。"""

    ctx = app.state.ctx

    def fake_analyze(*_, **__):
        return {
            "category": "衬衫",
            "subcategory": "白衬衫",
            "closet_section": "tops",
            "color": "white",
            "season_tags": ["spring"],
            "style_tags": ["minimal"],
            "formality": "Executive Luxury",
            "material": "cotton",
            "analysis_notes": "原始未知正式度"
        }

    def fake_bg_remove(*_, **__):
        return "/api/images/white_bg/fake-fallback.png", "Gemini white background success"

    ctx.image_service.image_analyze = fake_analyze
    ctx.image_service.bg_remove = fake_bg_remove

    response = client.post(
        "/api/upload",
        files={"file": ("shirt.png", BytesIO(b"fake-image-content"), "image/png")},
        data={"vision_provider": "gemini"}
    )

    assert response.status_code == 200
    item = response.json()["data"]["item"]
    assert item["formality"] == "casual"
    assert item["closet_section"] == "top"
    assert "normalized formality: Executive Luxury -> casual" in item["analysis_notes"]


def test_chat_endpoint_uses_agent_graph(client, app):
    app.state.ctx.agent_graph.invoke = lambda *_args, **_kwargs: {
        "reply": "你有 1 件蓝色衬衫。",
        "cards": [{"item_id": "shirt-1", "category": "衬衫", "color": "蓝色"}],
        "action": "query"
    }

    response = client.post(
        "/api/chat",
        json={"message": "我有什么蓝色衬衫", "history": []}
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["action"] == "query"
    assert "蓝色衬衫" in payload["reply"]
