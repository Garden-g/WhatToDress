"""数据模型基础工具。"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """返回 ISO 8601 UTC 时间字符串。

    Returns:
        str: 带时区的 ISO 8601 字符串。
    """

    return datetime.now(timezone.utc).isoformat()

