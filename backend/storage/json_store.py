"""JSON 存储层。"""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any, Callable


class JsonFileStore:
    """最基础的 JSON 文件仓储。"""

    def __init__(self, file_path: Path, default_factory: Callable[[], Any]) -> None:
        self.file_path = file_path
        self.default_factory = default_factory
        self._lock = RLock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """确保文件存在。"""

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.write(self.default_factory())

    def read(self) -> Any:
        """读取整个 JSON 文件。"""

        with self._lock:
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def write(self, value: Any) -> None:
        """写入整个 JSON 文件。"""

        with self._lock:
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(value, file, ensure_ascii=False, indent=2)


class JsonListStore(JsonFileStore):
    """专门用于存储列表对象的仓储。"""

    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path=file_path, default_factory=list)

    def list_all(self) -> list[dict[str, Any]]:
        """读取全部记录。"""

        data = self.read()
        return data if isinstance(data, list) else []

    def get_by_id(self, record_id: str, id_field: str) -> dict[str, Any] | None:
        """根据主键获取记录。"""

        for item in self.list_all():
            if item.get(id_field) == record_id:
                return item
        return None

    def upsert(self, record: dict[str, Any], id_field: str) -> dict[str, Any]:
        """新增或覆盖一条记录。"""

        with self._lock:
            items = self.list_all()
            replaced = False
            for index, item in enumerate(items):
                if item.get(id_field) == record.get(id_field):
                    items[index] = record
                    replaced = True
                    break

            if not replaced:
                items.append(record)

            self.write(items)
            return record

    def delete(self, record_id: str, id_field: str) -> bool:
        """删除一条记录。"""

        with self._lock:
            items = self.list_all()
            filtered = [item for item in items if item.get(id_field) != record_id]
            changed = len(filtered) != len(items)
            if changed:
                self.write(filtered)
            return changed


class JsonObjectStore(JsonFileStore):
    """用于单对象存储，比如用户偏好。"""

    def __init__(self, file_path: Path, default_factory: Callable[[], dict[str, Any]]) -> None:
        super().__init__(file_path=file_path, default_factory=default_factory)

    def get_object(self) -> dict[str, Any]:
        """获取整个对象。"""

        data = self.read()
        return data if isinstance(data, dict) else self.default_factory()

    def update_object(self, updates: dict[str, Any]) -> dict[str, Any]:
        """更新对象。"""

        with self._lock:
            data = self.get_object()
            data.update(updates)
            self.write(data)
            return data

