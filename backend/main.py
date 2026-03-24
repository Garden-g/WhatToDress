"""FastAPI 入口。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse

from backend.agent.graph import build_agent_graph
from backend.agent.nodes import build_agent_node, build_tool_executor_node
from backend.config import Settings
from backend.models.api import (
    ApiEnvelope,
    ChatRequest,
    ChatResponseData,
    ConfirmWardrobeRequest,
    ForgottenItemResponse,
    ForgottenListResponse,
    HistoryListResponse,
    PreferenceResponse,
    RecommendationListResponse,
    UploadResponseData,
    WardrobeListResponse,
)
from backend.models.base import utc_now_iso
from backend.models.item import ClothingItemUpdate
from backend.models.preference import UserPreference, UserPreferenceUpdate
from backend.models.wear_log import WearLogCreate
from backend.providers.deepseek import DeepSeekProvider
from backend.providers.gemini import GeminiProvider
from backend.providers.glm import GlmProvider
from backend.providers.weather import WeatherProvider
from backend.storage.image_store import ImageStore
from backend.storage.json_store import JsonListStore, JsonObjectStore
from backend.tools.image import ImageToolService
from backend.tools.preference import PreferenceToolService
from backend.tools.recall import list_forgotten_items
from backend.tools.recommend import RecommendToolService
from backend.tools.wardrobe import WardrobeToolService
from backend.tools.weather import WeatherToolService
from backend.tools.wear_log import WearLogToolService


def setup_logging(settings: Settings) -> logging.Logger:
    """配置统一日志输出。"""

    logger = logging.getLogger("dress")
    logger.setLevel(settings.log_level)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(settings.data_dir / "logs" / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


class ApplicationContext:
    """集中保存应用依赖。"""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

        wardrobe_store = JsonListStore(settings.data_dir / "wardrobe.json")
        wear_log_store = JsonListStore(settings.data_dir / "wear_logs.json")
        outfit_store = JsonListStore(settings.data_dir / "outfits.json")
        preference_store = JsonObjectStore(
            settings.data_dir / "preferences.json",
            default_factory=lambda: UserPreference(updated_at=utc_now_iso()).model_dump(mode="json"),
        )

        self.image_store = ImageStore(settings.images_dir)
        self.wardrobe_service = WardrobeToolService(wardrobe_store, logger)
        self.preference_service = PreferenceToolService(preference_store, logger)
        self.wear_log_service = WearLogToolService(wear_log_store, self.wardrobe_service, logger)
        self.weather_service = WeatherToolService(WeatherProvider(settings, logger))

        self.deepseek_provider = DeepSeekProvider(settings, logger)
        self.gemini_provider = GeminiProvider(settings, logger)
        self.glm_provider = GlmProvider(settings, logger)
        self.image_service = ImageToolService(
            analysis_providers={
                "gemini": self.gemini_provider,
                "glm": self.glm_provider,
            },
            bg_provider=self.gemini_provider,
            image_store=self.image_store,
            logger=logger,
        )
        self.recommend_service = RecommendToolService(self.deepseek_provider)
        self.outfit_store = outfit_store

        tool_schemas = self._build_tool_schemas()
        tool_registry = self._build_tool_registry()

        self.agent_graph = build_agent_graph(
            agent_node=build_agent_node(
                provider=self.deepseek_provider,
                tool_schemas=tool_schemas,
                context_builder=self._build_context_snapshot,
                logger=logger,
            ),
            tool_executor_node=build_tool_executor_node(tool_registry=tool_registry, logger=logger),
        )

    def _build_context_snapshot(self) -> dict[str, Any]:
        """给 Agent 一个轻量上下文快照。"""

        wardrobe_count = len(self.wardrobe_service.list_items(include_unconfirmed=True))
        confirmed_count = len(self.wardrobe_service.list_items())
        history_count = len(self.wear_log_service.list_logs())
        preference = self.preference_service.get_preference()
        return {
            "wardrobe_count": wardrobe_count,
            "confirmed_count": confirmed_count,
            "history_count": history_count,
            "preferred_styles": preference.preferred_styles,
            "preferred_colors": preference.preferred_colors,
        }

    def _build_tool_schemas(self) -> list[dict[str, Any]]:
        """构建给 Agent 的工具描述。"""

        return [
            {
                "name": "wardrobe_query",
                "description": "按条件检索衣柜中的衣物",
                "arguments": ["category", "subcategory", "color", "closet_section", "style", "season", "is_available"],
            },
            {
                "name": "forgotten_recall",
                "description": "获取被遗忘但值得重新穿的衣物",
                "arguments": [],
            },
            {
                "name": "weather_search",
                "description": "根据城市或消息中的日期天气描述，获取天气信息",
                "arguments": ["message", "city", "day_label"],
            },
            {
                "name": "outfit_recommend",
                "description": "根据天气、场景、衣柜与偏好生成穿搭方案",
                "arguments": ["scenario", "weather_message"],
            },
            {
                "name": "user_preference",
                "description": "读取用户偏好",
                "arguments": [],
            },
        ]

    def _build_tool_registry(self) -> dict[str, Any]:
        """构建真正执行的工具映射。"""

        def wardrobe_query(**filters: Any) -> dict[str, Any]:
            items = self.wardrobe_service.query_items({**filters, "confirmed": True})
            return {
                "cards": [item.model_dump(mode="json") for item in items],
                "count": len(items),
            }

        def forgotten_recall() -> dict[str, Any]:
            forgotten = list_forgotten_items(self.wardrobe_service.list_items())
            return {
                "cards": [
                    {
                        **row["item"].model_dump(mode="json"),
                        "forgotten_score": row["forgotten_score"],
                        "forgotten_reasons": row["reasons"],
                    }
                    for row in forgotten
                ]
            }

        def weather_search(message: str | None = None, city: str | None = None, day_label: str | None = None) -> dict[str, Any]:
            weather = self.weather_service.weather_search(message=message, city=city, day_label=day_label)
            return {
                "cards": [weather],
                "weather": weather,
            }

        def user_preference() -> dict[str, Any]:
            preference = self.preference_service.get_preference()
            return {
                "cards": [preference.model_dump(mode="json")],
                "preference": preference.model_dump(mode="json"),
            }

        def outfit_recommend(scenario: str, weather_message: str | None = None) -> dict[str, Any]:
            weather = self.weather_service.weather_search(message=weather_message or scenario)
            forgotten = list_forgotten_items(self.wardrobe_service.list_items())
            recommendations = self.recommend_service.outfit_recommend(
                weather=weather,
                scenario=scenario,
                available_items=self.wardrobe_service.list_items(),
                forgotten_items=forgotten,
                recent_logs=[log.model_dump(mode="json") for log in self.wear_log_service.list_logs()],
                preferences=self.preference_service.get_preference(),
            )
            return {
                "cards": [item.model_dump(mode="json") for item in recommendations],
                "weather": weather,
            }

        return {
            "wardrobe_query": wardrobe_query,
            "forgotten_recall": forgotten_recall,
            "weather_search": weather_search,
            "user_preference": user_preference,
            "outfit_recommend": outfit_recommend,
        }


def success(data: Any) -> ApiEnvelope:
    """快速构造成功响应。"""

    return ApiEnvelope(success=True, data=data, error=None)


def failure(error: str) -> ApiEnvelope:
    """快速构造失败响应。

    Args:
        error: 要返回给前端的错误文本。

    Returns:
        ApiEnvelope: 统一失败包裹结构。
    """

    return ApiEnvelope(success=False, data=None, error=error)


def create_app(settings: Settings | None = None) -> FastAPI:
    """应用工厂。"""

    loaded_settings = settings or Settings.load()
    loaded_settings.ensure_directories()
    logger = setup_logging(loaded_settings)
    context = ApplicationContext(loaded_settings, logger)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("Application startup begin")
        loaded_settings.validate_runtime_secrets()
        logger.info(
            "Runtime secret summary gemini_auth_source=%s glm_enabled=%s deepseek_enabled=%s",
            loaded_settings.gemini_auth_source,
            bool(loaded_settings.glm_api_key),
            bool(loaded_settings.deepseek_api_key),
        )
        logger.info("Application startup complete")
        yield
        logger.info("Application shutdown")

    app = FastAPI(title="Dress Closet Agent", version="0.1.0", lifespan=lifespan)
    app.state.ctx = context
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request, call_next):  # type: ignore[override]
        logger.info("HTTP %s %s start", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception as error:
            # 这里额外兜底，是为了防止第三方 SDK 或中间层异常直接打断连接，
            # 否则前端只能看到浏览器原始的 "Failed to fetch"，定位成本很高。
            logger.error("Unhandled request error method=%s path=%s error=%s", request.method, request.url.path, error, exc_info=True)
            response = JSONResponse(
                status_code=500,
                content=failure("服务器内部错误，请查看后端日志。").model_dump(mode="json"),
            )
        logger.info("HTTP %s %s end status=%s", request.method, request.url.path, response.status_code)
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, error: HTTPException) -> JSONResponse:
        """把 FastAPI 的 HTTPException 统一转成前端约定格式。"""

        message = error.detail if isinstance(error.detail, str) else "请求失败"
        return JSONResponse(
            status_code=error.status_code,
            content=failure(message).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, error: Exception) -> JSONResponse:
        """兜底处理所有未捕获异常。"""

        logger.error("Unhandled application exception error=%s", error, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=failure("服务器内部错误，请查看后端日志。").model_dump(mode="json"),
        )

    @app.get("/api/wardrobe")
    def get_wardrobe(
        category: str | None = Query(default=None),
        subcategory: str | None = Query(default=None),
        color: str | None = Query(default=None),
        closet_section: str | None = Query(default=None),
        include_unconfirmed: bool = Query(default=False),
    ) -> ApiEnvelope:
        items = context.wardrobe_service.query_items(
            {
                "category": category,
                "subcategory": subcategory,
                "color": color,
                "closet_section": closet_section,
            },
            include_unconfirmed=include_unconfirmed,
        )
        return success(WardrobeListResponse(items=items).model_dump(mode="json"))

    @app.put("/api/wardrobe/{item_id}")
    def update_wardrobe_item(item_id: str, updates: ClothingItemUpdate) -> ApiEnvelope:
        try:
            item = context.wardrobe_service.update_item(item_id, updates)
            return success(item.model_dump(mode="json"))
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/wardrobe/{item_id}/confirm")
    def confirm_wardrobe_item(item_id: str, payload: ConfirmWardrobeRequest) -> ApiEnvelope:
        try:
            item = context.wardrobe_service.confirm_item(item_id, payload.updates)
            return success(item.model_dump(mode="json"))
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.delete("/api/wardrobe/{item_id}")
    def delete_wardrobe_item(item_id: str) -> ApiEnvelope:
        deleted = context.wardrobe_service.delete_item(item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="衣物不存在")
        return success({"deleted": True})

    @app.post("/api/upload")
    async def upload_item(
        file: UploadFile = File(...),
        vision_provider: str = Form(default="gemini"),
    ) -> ApiEnvelope:
        if not file.filename:
            raise HTTPException(status_code=400, detail="未提供文件名")
        if vision_provider not in {"gemini", "glm"}:
            raise HTTPException(status_code=400, detail="不支持的识图 provider")

        content = await file.read()
        file_name, original_path = context.image_store.save_original_bytes(content, file.content_type)
        original_url = context.image_store.build_api_url("original", file_name)

        try:
            analysis = context.image_service.image_analyze(
                original_path,
                provider_name=vision_provider,
                mime_type=file.content_type,
            )
        except Exception as error:
            logger.error("image_analyze failed: %s", error, exc_info=True)
            raise HTTPException(status_code=502, detail=f"衣物识别失败：{error}") from error

        draft = context.image_service.build_draft_item(
            analysis=analysis,
            original_image_url=original_url,
            white_bg_url=None,
        )
        white_bg_url, white_bg_note = context.image_service.bg_remove(original_path, draft.item_id, file.content_type)
        draft.image_white_bg_url = white_bg_url
        provider_note = f"provider={vision_provider}"
        draft.analysis_notes = f"{provider_note} | {draft.analysis_notes or ''} | {white_bg_note}".strip(" |")
        context.wardrobe_service.add_item(draft)
        return success(UploadResponseData(item=draft).model_dump(mode="json"))

    @app.get("/api/forgotten")
    def get_forgotten_items() -> ApiEnvelope:
        forgotten = list_forgotten_items(context.wardrobe_service.list_items())
        payload = ForgottenListResponse(
            items=[
                ForgottenItemResponse(
                    item=row["item"],
                    forgotten_score=row["forgotten_score"],
                    reasons=row["reasons"],
                )
                for row in forgotten
            ]
        )
        return success(payload.model_dump(mode="json"))

    @app.get("/api/history")
    def get_history() -> ApiEnvelope:
        logs = context.wear_log_service.list_logs()
        return success(HistoryListResponse(items=logs).model_dump(mode="json"))

    @app.post("/api/history")
    def create_history(payload: WearLogCreate) -> ApiEnvelope:
        log = context.wear_log_service.create_log(payload)
        return success(log.model_dump(mode="json"))

    @app.get("/api/preferences")
    def get_preferences() -> ApiEnvelope:
        preference = context.preference_service.get_preference()
        return success(PreferenceResponse(preference=preference).model_dump(mode="json"))

    @app.put("/api/preferences")
    def update_preferences(payload: UserPreferenceUpdate) -> ApiEnvelope:
        preference = context.preference_service.update_preference(payload)
        return success(PreferenceResponse(preference=preference).model_dump(mode="json"))

    @app.post("/api/chat")
    def chat(payload: ChatRequest) -> ApiEnvelope:
        result = context.agent_graph.invoke(
            {
                "user_message": payload.message,
                "chat_history": [message.model_dump(mode="json") for message in payload.history],
            }
        )
        data = ChatResponseData(
            reply=result.get("reply", "我已经处理好了。"),
            cards=result.get("cards", []),
            action=result.get("action", "query"),
        )
        return success(data.model_dump(mode="json"))

    @app.get("/api/images/{image_type}/{filename}")
    def get_image(image_type: str, filename: str):
        if image_type not in {"original", "white_bg"}:
            raise HTTPException(status_code=404, detail="图片类型不存在")
        path = loaded_settings.images_dir / image_type / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        return FileResponse(path)

    @app.get("/api/recommendations")
    def get_recommendations(
        scenario: str = Query(...),
        weather_message: str | None = Query(default=None),
    ) -> ApiEnvelope:
        weather = context.weather_service.weather_search(message=weather_message or scenario)
        forgotten = list_forgotten_items(context.wardrobe_service.list_items())
        items = context.recommend_service.outfit_recommend(
            weather=weather,
            scenario=scenario,
            available_items=context.wardrobe_service.list_items(),
            forgotten_items=forgotten,
            recent_logs=[log.model_dump(mode="json") for log in context.wear_log_service.list_logs()],
            preferences=context.preference_service.get_preference(),
        )
        return success(RecommendationListResponse(items=items).model_dump(mode="json"))

    return app


app = create_app()
