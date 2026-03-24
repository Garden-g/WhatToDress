"""遗忘召回工具。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.models.item import ClothingItem


FORGOTTEN_THRESHOLD = 60


@dataclass(slots=True)
class ForgottenScoreResult:
    """保存遗忘分结果，便于给前端解释。"""

    score: int
    reasons: list[str]


def _days_since(last_worn_date: str | None) -> int:
    """计算距离上次穿着的天数。"""

    if not last_worn_date:
        return 365

    last_worn = datetime.fromisoformat(last_worn_date)
    now = datetime.now(timezone.utc)
    return max((now - last_worn).days, 0)


def calculate_forgotten_score(item: ClothingItem) -> ForgottenScoreResult:
    """按产品规划中的公式计算遗忘分。"""

    reasons: list[str] = []
    days = _days_since(item.last_worn_date)
    score = min(days / 30, 5) * 20
    reasons.append(f"距上次穿着约 {days} 天")

    rare_bonus = max(0, 3 - item.wear_count) * 10
    if rare_bonus:
        reasons.append("累计穿着次数偏少")
    score += rare_bonus

    if item.season_tags:
        reasons.append("当前季节可能可穿")
        score += 15

    if item.dislike_flag:
        reasons.append("用户已明确不喜欢")
        score -= 50

    if (not item.is_available) or item.clean_status in {"dirty", "washing"}:
        reasons.append("当前状态不可直接上身")
        score -= 30

    return ForgottenScoreResult(score=max(int(score), 0), reasons=reasons)


def list_forgotten_items(items: list[ClothingItem], threshold: int = FORGOTTEN_THRESHOLD) -> list[dict[str, object]]:
    """筛出达到阈值的遗忘衣物。"""

    results: list[dict[str, object]] = []
    for item in items:
        result = calculate_forgotten_score(item)
        if result.score >= threshold and item.confirmed:
            results.append(
                {
                    "item": item,
                    "forgotten_score": result.score,
                    "reasons": result.reasons,
                }
            )

    return sorted(results, key=lambda row: int(row["forgotten_score"]), reverse=True)
