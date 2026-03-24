"""图片存储层。"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4


class ImageStore:
    """统一管理原图和白底图的本地存储路径。"""

    def __init__(self, images_dir: Path) -> None:
        self.images_dir = images_dir
        self.original_dir = images_dir / "original"
        self.white_bg_dir = images_dir / "white_bg"
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.white_bg_dir.mkdir(parents=True, exist_ok=True)

    def _suffix_from_mime(self, mime_type: str | None) -> str:
        """根据 MIME 类型推断文件后缀。"""

        if not mime_type:
            return ".jpg"
        suffix = mimetypes.guess_extension(mime_type) or ".jpg"
        return ".jpg" if suffix == ".jpe" else suffix

    def save_original_bytes(self, content: bytes, mime_type: str | None) -> tuple[str, Path]:
        """保存原始上传图片。"""

        file_name = f"{uuid4()}{self._suffix_from_mime(mime_type)}"
        file_path = self.original_dir / file_name
        file_path.write_bytes(content)
        return file_name, file_path

    def save_white_background_bytes(self, source_id: str, content: bytes, suffix: str = ".png") -> tuple[str, Path]:
        """保存白底图。"""

        file_name = f"{source_id}{suffix}"
        file_path = self.white_bg_dir / file_name
        file_path.write_bytes(content)
        return file_name, file_path

    def build_api_url(self, image_type: str, file_name: str) -> str:
        """生成供前端访问的 API 路径。"""

        return f"/api/images/{image_type}/{file_name}"
