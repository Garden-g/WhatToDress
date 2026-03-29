"""服装分类体系常量与辅助函数。

这里集中定义中文分类体系，确保衣柜数据、视觉识别、查询逻辑
三方使用同一套标准值，避免出现"上衣"查不到"皮夹克"的问题。

设计决策：
  - category / subcategory / color / season 等面向用户的值统一用中文
  - closet_section / formality / clean_status 保持英文枚举（代码逻辑用，不面向用户）
"""

from __future__ import annotations

# ── 大类 → 子类映射 ──────────────────────────────────────────
# key = 中文大类名（也是 category 字段应存储的值）
# value = dict:
#   closet_section: 对应的英文枚举值
#   subcategories: 该大类下的所有子类列表
CATEGORY_TAXONOMY: dict[str, dict] = {
    "上衣": {
        "closet_section": "top",
        "subcategories": [
            "T恤", "短袖", "长袖T恤", "衬衫", "卫衣",
            "毛衣", "针织衫", "背心", "Polo衫", "打底衫",
        ],
    },
    "外套": {
        "closet_section": "outerwear",
        "subcategories": [
            "夹克", "皮夹克", "西装外套", "风衣", "大衣",
            "羽绒服", "牛仔外套", "棒球服", "冲锋衣", "马甲",
        ],
    },
    "裤装": {
        "closet_section": "bottom",
        "subcategories": [
            "牛仔裤", "休闲裤", "西裤", "短裤", "运动裤",
            "工装裤", "阔腿裤", "紧身裤", "九分裤",
        ],
    },
    "裙装": {
        "closet_section": "bottom",
        "subcategories": [
            "半身裙", "连衣裙", "百褶裙", "A字裙",
            "包臀裙", "长裙", "短裙",
        ],
    },
    "鞋履": {
        "closet_section": "shoes",
        "subcategories": [
            "运动鞋", "皮鞋", "靴子", "凉鞋", "拖鞋",
            "帆布鞋", "高跟鞋", "乐福鞋", "板鞋",
        ],
    },
    "配饰": {
        "closet_section": "accessory",
        "subcategories": [
            "帽子", "围巾", "手表", "项链", "手链",
            "眼镜", "腰带", "包", "耳环", "戒指", "领带",
        ],
    },
}

# ── 反向索引：子类 → 大类 ────────────────────────────────────
# 方便从 subcategory 快速定位属于哪个大类
SUBCATEGORY_TO_CATEGORY: dict[str, str] = {}
for _cat, _info in CATEGORY_TAXONOMY.items():
    for _sub in _info["subcategories"]:
        SUBCATEGORY_TO_CATEGORY[_sub] = _cat

# ── 所有合法大类名集合 ───────────────────────────────────────
ALL_CATEGORIES: set[str] = set(CATEGORY_TAXONOMY.keys())

# ── 所有合法子类名集合 ───────────────────────────────────────
ALL_SUBCATEGORIES: set[str] = set(SUBCATEGORY_TO_CATEGORY.keys())

# ── 季节标准值 ───────────────────────────────────────────────
SEASONS_ZH: list[str] = ["春季", "夏季", "秋季", "冬季"]

# ── 英文 → 中文常用映射（用于数据迁移） ─────────────────────
SEASON_EN_TO_ZH: dict[str, str] = {
    "spring": "春季", "Spring": "春季",
    "summer": "夏季", "Summer": "夏季",
    "autumn": "秋季", "Autumn": "秋季", "fall": "秋季", "Fall": "秋季",
    "winter": "冬季", "Winter": "冬季",
}

COLOR_EN_TO_ZH: dict[str, str] = {
    "black": "黑色", "Black": "黑色",
    "white": "白色", "White": "白色",
    "red": "红色", "Red": "红色",
    "blue": "蓝色", "Blue": "蓝色",
    "green": "绿色", "Green": "绿色",
    "yellow": "黄色", "Yellow": "黄色",
    "gray": "灰色", "Gray": "灰色", "grey": "灰色", "Grey": "灰色",
    "brown": "棕色", "Brown": "棕色",
    "pink": "粉色", "Pink": "粉色",
    "purple": "紫色", "Purple": "紫色",
    "orange": "橙色", "Orange": "橙色",
    "beige": "米色", "Beige": "米色",
    "cream": "米白色", "Cream": "米白色",
    "navy": "藏青色", "Navy": "藏青色",
    "khaki": "卡其色", "Khaki": "卡其色",
    "burgundy": "酒红色", "Burgundy": "酒红色",
    "olive": "橄榄绿", "Olive": "橄榄绿",
    "tan": "棕褐色", "Tan": "棕褐色",
    "ivory": "象牙色", "Ivory": "象牙色",
}

STYLE_EN_TO_ZH: dict[str, str] = {
    "casual": "休闲", "Casual": "休闲",
    "formal": "正式", "Formal": "正式",
    "streetwear": "街头", "Streetwear": "街头",
    "retro": "复古", "Retro": "复古",
    "vintage": "复古", "Vintage": "复古",
    "sporty": "运动", "Sporty": "运动",
    "elegant": "优雅", "Elegant": "优雅",
    "chic": "优雅", "Chic": "优雅",
    "minimalist": "极简", "Minimalist": "极简",
    "modern": "现代", "Modern": "现代",
    "classic": "经典", "Classic": "经典",
    "edgy": "前卫", "Edgy": "前卫",
    "bohemian": "波西米亚", "Bohemian": "波西米亚",
    "preppy": "学院风", "Preppy": "学院风",
    "lace": "蕾丝", "Lace": "蕾丝",
    "asymmetrical": "不对称", "Asymmetrical": "不对称",
}

MATERIAL_EN_TO_ZH: dict[str, str] = {
    "leather": "皮革", "Leather": "皮革",
    "cotton": "棉", "Cotton": "棉",
    "denim": "牛仔布", "Denim": "牛仔布",
    "silk": "丝绸", "Silk": "丝绸",
    "wool": "羊毛", "Wool": "羊毛",
    "polyester": "涤纶", "Polyester": "涤纶",
    "nylon": "尼龙", "Nylon": "尼龙",
    "linen": "亚麻", "Linen": "亚麻",
    "cashmere": "羊绒", "Cashmere": "羊绒",
    "suede": "麂皮", "Suede": "麂皮",
    "velvet": "天鹅绒", "Velvet": "天鹅绒",
    "chiffon": "雪纺", "Chiffon": "雪纺",
    "Leather/Faux Leather": "皮革/仿皮",
    "Woven fabric": "编织面料",
    "woven fabric": "编织面料",
}

# ── 英文大类/子类 → 中文（用于数据迁移） ────────────────────
CATEGORY_EN_TO_ZH: dict[str, str] = {
    "outerwear": "外套", "Outerwear": "外套",
    "Jacket": "外套", "jacket": "外套",
    "top": "上衣", "Top": "上衣",
    "Shirt": "上衣", "shirt": "上衣",
    "bottom": "裤装", "Bottom": "裤装",
    "Pants": "裤装", "pants": "裤装",
    "dress": "裙装", "Dress": "裙装",
    "shoes": "鞋履", "Shoes": "鞋履",
    "accessory": "配饰", "Accessory": "配饰",
}

SUBCATEGORY_EN_TO_ZH: dict[str, str] = {
    "leather jacket": "皮夹克", "Leather Jacket": "皮夹克",
    "Blazer": "西装外套", "blazer": "西装外套",
    "denim jacket": "牛仔外套", "Denim Jacket": "牛仔外套",
    "down jacket": "羽绒服", "Down Jacket": "羽绒服",
    "trench coat": "风衣", "Trench Coat": "风衣",
    "coat": "大衣", "Coat": "大衣",
    "t-shirt": "T恤", "T-Shirt": "T恤", "T-shirt": "T恤", "tee": "T恤",
    "shirt": "衬衫", "Shirt": "衬衫",
    "hoodie": "卫衣", "Hoodie": "卫衣",
    "sweater": "毛衣", "Sweater": "毛衣",
    "vest": "背心", "Vest": "背心",
    "jeans": "牛仔裤", "Jeans": "牛仔裤",
    "shorts": "短裤", "Shorts": "短裤",
    "dress pants": "西裤", "Dress Pants": "西裤",
    "sneakers": "运动鞋", "Sneakers": "运动鞋",
    "boots": "靴子", "Boots": "靴子",
}


# ── 辅助函数 ─────────────────────────────────────────────────

def get_closet_section(category: str) -> str | None:
    """根据中文大类名返回对应的 closet_section 英文枚举值。

    Args:
        category: 中文大类名，如 "上衣"、"外套"。

    Returns:
        对应的 closet_section 值，找不到则返回 None。
    """
    info = CATEGORY_TAXONOMY.get(category)
    return info["closet_section"] if info else None


def expand_category_to_sections(category_query: str) -> list[str]:
    """把用户查询的分类名展开为可能匹配的 closet_section 列表。

    支持：
    - 大类名直接匹配 → 返回对应 closet_section
    - 子类名 → 返回所属大类的 closet_section
    - 都不命中 → 返回空列表

    Args:
        category_query: 用户查询词，如 "上衣"、"皮夹克"。

    Returns:
        匹配的 closet_section 值列表。
    """
    # 精确匹配大类
    if category_query in CATEGORY_TAXONOMY:
        return [CATEGORY_TAXONOMY[category_query]["closet_section"]]

    # 精确匹配子类
    parent = SUBCATEGORY_TO_CATEGORY.get(category_query)
    if parent:
        return [CATEGORY_TAXONOMY[parent]["closet_section"]]

    # 模糊匹配：查询词包含在大类名中，或大类名包含在查询词中
    sections = []
    for cat_name, info in CATEGORY_TAXONOMY.items():
        if category_query in cat_name or cat_name in category_query:
            sections.append(info["closet_section"])
    return sections


def build_taxonomy_description() -> str:
    """生成供 LLM 使用的分类体系文本描述。

    用于嵌入到 system prompt 中，让模型了解合法的分类值。

    Returns:
        格式化的分类体系文字说明。
    """
    lines = ["服装分类体系（category 只能取以下大类，subcategory 从对应子类中选取）："]
    for cat_name, info in CATEGORY_TAXONOMY.items():
        subs = "、".join(info["subcategories"])
        lines.append(f"  - {cat_name}（closet_section={info['closet_section']}）：{subs}")
    lines.append(f"季节标签只能取：{'、'.join(SEASONS_ZH)}")
    lines.append("颜色、材质、风格标签统一使用中文。")
    return "\n".join(lines)
