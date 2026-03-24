"""应用配置模块。

这个文件集中处理环境变量、目录路径和运行时校验。
之所以把配置统一收口，是为了避免业务代码到处直接读环境变量，
那样会让测试、排错和后续配置迁移都变得困难。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(slots=True)
class Settings:
    """保存应用运行所需配置。"""

    gemini_api_key: str
    google_api_key: str
    glm_api_key: str
    glm_base_url: str
    deepseek_api_key: str
    deepseek_base_url: str
    gemini_text_model: str
    gemini_image_model: str
    glm_vision_model: str
    deepseek_chat_model: str
    deepseek_reasoner_model: str
    data_dir: Path
    images_dir: Path
    default_city: str
    request_timeout_seconds: float
    log_level: str

    @classmethod
    def load(cls) -> "Settings":
        """从环境变量读取配置。

        Returns:
            Settings: 已完成路径标准化的配置对象。
        """

        data_dir = PROJECT_ROOT / os.getenv("DATA_DIR", "data")
        images_dir = PROJECT_ROOT / os.getenv("IMAGES_DIR", "data/images")

        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            google_api_key=os.getenv("GOOGLE_API_KEY", "").strip(),
            glm_api_key=os.getenv("GLM_API_KEY", "").strip(),
            glm_base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            gemini_text_model=os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash"),
            gemini_image_model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview"),
            glm_vision_model=os.getenv("GLM_VISION_MODEL", "glm-4.6v"),
            deepseek_chat_model=os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat"),
            deepseek_reasoner_model=os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-reasoner"),
            data_dir=data_dir,
            images_dir=images_dir,
            default_city=os.getenv("DEFAULT_CITY", "Shanghai"),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    @property
    def resolved_gemini_api_key(self) -> str:
        """返回 Gemini 实际应使用的密钥。

        Returns:
            str: 优先级已经处理好的 Gemini 密钥。

        为什么要做成独立属性：
        - 业务层只应该关心“现在能不能调 Gemini”，不应该重复写环境变量优先级判断。
        - 把优先级集中到配置层后，测试也只需要验证一处。
        """

        return self.google_api_key or self.gemini_api_key

    @property
    def gemini_auth_source(self) -> str:
        """返回当前 Gemini 密钥来源，便于日志排错。

        Returns:
            str: 当前使用的环境变量名，或 none。
        """

        if self.google_api_key:
            return "GOOGLE_API_KEY"
        if self.gemini_api_key:
            return "GEMINI_API_KEY"
        return "none"

    def ensure_directories(self) -> None:
        """确保运行期必须目录存在。

        Raises:
            OSError: 当目录创建失败时抛出。
        """

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        (self.images_dir / "original").mkdir(parents=True, exist_ok=True)
        (self.images_dir / "white_bg").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)

    def validate_runtime_secrets(self) -> None:
        """校验运行后端所需的关键密钥是否存在。

        这里故意在应用启动时而不是导入时校验。
        这样既满足“缺配置就启动失败”的要求，也不会影响测试导入模块。

        Raises:
            RuntimeError: 缺失关键密钥时抛出，阻止应用正常启动。
        """

        missing: list[str] = []
        if not self.deepseek_api_key:
            missing.append("DEEPSEEK_API_KEY")
        if not self.resolved_gemini_api_key and not self.glm_api_key:
            missing.append("GOOGLE_API_KEY 或 GEMINI_API_KEY 或 GLM_API_KEY（至少提供一个可用识图能力）")

        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"缺少必须的环境变量：{joined}")
