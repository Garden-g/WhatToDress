from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.models.item import ClothingItem
from backend.tools.recall import calculate_forgotten_score


def test_calculate_forgotten_score_penalizes_dislike_and_unavailable():
    item = ClothingItem(
        category="衬衫",
        color="蓝色",
        closet_section="top",
        season_tags=["春", "秋"],
        style_tags=["通勤"],
        image_original_url="/api/images/original/test.jpg",
        image_white_bg_url=None,
        is_available=False,
        clean_status="dirty",
        dislike_flag=True,
        wear_count=0,
        last_worn_date=(datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    )

    result = calculate_forgotten_score(item)
    assert result.score >= 0
    assert "用户已明确不喜欢" in result.reasons
    assert "当前状态不可直接上身" in result.reasons

