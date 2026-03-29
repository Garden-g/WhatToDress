"""一次性数据迁移脚本：把 wardrobe.json 中的英文值翻译为中文。

使用方法：
    python -m backend.migrate_chinese

注意：
    - 运行前请先备份 data/wardrobe.json
    - 此脚本幂等：已经是中文的值不会被重复翻译
    - 无法识别的英文值会保留原样（通过日志记录）
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.models.taxonomy import (
    CATEGORY_EN_TO_ZH,
    COLOR_EN_TO_ZH,
    MATERIAL_EN_TO_ZH,
    SEASON_EN_TO_ZH,
    STYLE_EN_TO_ZH,
    SUBCATEGORY_EN_TO_ZH,
)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WARDROBE_PATH = PROJECT_ROOT / "data" / "wardrobe.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("migrate")


def translate_value(value: str, mapping: dict[str, str], field_name: str) -> str:
    """尝试用映射表翻译单个值，找不到则保留原样并记录日志。"""
    if not value or not value.strip():
        return value
    result = mapping.get(value.strip())
    if result:
        return result
    # 尝试不区分大小写匹配
    lower_map = {k.lower(): v for k, v in mapping.items()}
    result = lower_map.get(value.strip().lower())
    if result:
        return result
    logger.warning("字段 %s 无法翻译值: '%s'，保留原样", field_name, value)
    return value


def translate_list(values: list[str], mapping: dict[str, str], field_name: str) -> list[str]:
    """翻译列表中的每个值。"""
    return [translate_value(v, mapping, field_name) for v in values]


def migrate_item(item: dict) -> dict:
    """翻译单件衣物的所有需要中文化的字段。"""
    # name: 用 subcategory 翻译后的值作为 name
    if item.get("name"):
        item["name"] = translate_value(item["name"], SUBCATEGORY_EN_TO_ZH, "name")

    # category
    if item.get("category"):
        item["category"] = translate_value(item["category"], CATEGORY_EN_TO_ZH, "category")

    # subcategory
    if item.get("subcategory"):
        item["subcategory"] = translate_value(item["subcategory"], SUBCATEGORY_EN_TO_ZH, "subcategory")

    # color
    if item.get("color"):
        item["color"] = translate_value(item["color"], COLOR_EN_TO_ZH, "color")

    # secondary_color
    if item.get("secondary_color"):
        item["secondary_color"] = translate_value(item["secondary_color"], COLOR_EN_TO_ZH, "secondary_color")

    # season_tags
    if item.get("season_tags"):
        item["season_tags"] = translate_list(item["season_tags"], SEASON_EN_TO_ZH, "season_tags")

    # style_tags
    if item.get("style_tags"):
        item["style_tags"] = translate_list(item["style_tags"], STYLE_EN_TO_ZH, "style_tags")

    # material
    if item.get("material"):
        item["material"] = translate_value(item["material"], MATERIAL_EN_TO_ZH, "material")

    return item


def main() -> None:
    """执行迁移。"""
    if not WARDROBE_PATH.exists():
        logger.error("wardrobe.json 不存在: %s", WARDROBE_PATH)
        return

    with open(WARDROBE_PATH, encoding="utf-8") as f:
        items = json.load(f)

    logger.info("读取到 %d 件衣物", len(items))

    for i, item in enumerate(items):
        logger.info("--- 迁移第 %d 件: %s ---", i + 1, item.get("name", "未命名"))
        items[i] = migrate_item(item)

    with open(WARDROBE_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    logger.info("迁移完成，已写入 %s", WARDROBE_PATH)


if __name__ == "__main__":
    main()
