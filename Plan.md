# 衣柜 Agent / Closet OS — 项目架构文档

> 版本：v0.1 规划稿  
> 日期：2026-03-23  
> 状态：待开发

---

## 一、项目是什么？

一个面向个人日常穿衣决策的**对话式数字衣柜系统**。

核心价值不是"AI 推荐穿搭"，而是**把被遗忘的衣服重新召回到日常决策里**。  
产品主逻辑：**找回衣服 → 理解约束 → 生成搭配 → 记录反馈 → 下次更准**

---

## 二、技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | React + Vite + Tailwind CSS | 保留 `1.jsx` 的衣柜 3D 翻转动画效果 |
| 后端 | Python 3.11 + FastAPI | 主力语言 |
| Agent 框架 | LangGraph | 有向图状态机，流程可控，便于后续扩展复杂逻辑 |
| 视觉识别 | Gemini Vision API | 衣物属性识别 + 白底抠图 |
| 对话/路由 | DeepSeek-Chat (V3) | 支持 function calling，做 Agent 路由决策 |
| 深度推理 | DeepSeek-Reasoner (R1) | 用于穿搭推荐，需综合多因素 chain-of-thought |
| 天气 | Web Search（via LangChain tool） | 不依赖专用天气 API，轻量实现 |
| 数据库 | 本地 JSON 文件 | v0.1 先跑通，后续可迁移 PostgreSQL |
| 图片存储 | 本地文件系统 | `data/images/original/` + `data/images/white_bg/` |
| 备用抠图 | rembg（本地 Python 库） | Gemini 抠图效果差时的兜底方案 |

---

## 三、双 LLM 分工设计

```
用户消息
  │
  ▼
DeepSeek-Chat (V3) ── 意图识别 + Tool Calling 路由 ── 简单对话直接回复
  │
  ├──▶ image_analyze tool ──────▶ Gemini Vision   （图片识别、属性提取）
  ├──▶ bg_remove tool ──────────▶ Gemini Vision   （白底抠图生成）
  └──▶ outfit_recommend tool ───▶ DeepSeek-R1     （深度穿搭推理）
```

**为什么这样分？**
- DeepSeek-V3 支持 function calling，适合做 ReAct loop 的大脑
- DeepSeek-R1 擅长复杂推理，用在需要综合天气/场景/遗忘状态/偏好的穿搭推荐
- Gemini Vision 多模态能力强，图像任务全给它

---

## 四、LangGraph Agent 架构

### 4.1 图结构

```
START
  │
  ▼
agent_node（DeepSeek-V3 决策）
  │
  ├──── 需要调 Tool ──▶ tool_executor_node ──▶ 返回 agent_node
  │
  └──── 无需 Tool ────▶ END（直接回复用户）
```

### 4.2 AgentState 状态定义

```
ClosetAgentState:
  - messages            # 对话消息历史（LangGraph 自动累加）
  - uploaded_image_path # 本轮上传的图片路径（可为空）
  - wardrobe_context    # 本轮检索到的衣物上下文（供 LLM 参考）
  - weather_context     # 天气上下文
  - user_preferences    # 用户偏好快照
```

---

## 五、Tools 清单

| Tool 名称 | 功能 | 输入 | 输出 | 调用 |
|---|---|---|---|---|
| `wardrobe_query` | 按条件检索衣柜 | 自然语言条件 → JSON filter | 匹配衣物列表 | 纯逻辑，读 JSON |
| `wardrobe_add` | 入库新衣物 | 衣物属性 dict | 新增衣物对象 | 纯逻辑，写 JSON |
| `wardrobe_update` | 更新衣物状态/属性 | item_id + 更新字段 | 更新后对象 | 纯逻辑，改 JSON |
| `image_analyze` | 图片识别提取衣物属性 | 图片路径 | 品类/颜色/风格/季节/材质/正式度 | Gemini Vision |
| `bg_remove` | 白底抠图 | 原始图片路径 | 白底图路径 | Gemini Vision / rembg 兜底 |
| `weather_search` | 查询天气 | 城市名 + 日期 | 气温/降水/风力 dict | Web Search |
| `forgotten_recall` | 计算遗忘分，召回衣物 | 天数阈值（默认 90 天） | 遗忘衣物列表 + 分数 | 纯算法逻辑 |
| `outfit_recommend` | 生成穿搭方案 | 场景/天气/偏好/可用衣物/遗忘衣物 | 搭配列表 + 理由 | DeepSeek-R1 |
| `wear_log` | 记录穿着历史 | item_ids + 日期 + 场景 | 记录确认 | 纯逻辑，写 JSON |
| `user_preference` | 读写用户偏好 | 偏好字段 | 偏好对象 | 纯逻辑，读写 JSON |

---

## 六、核心数据模型

### 6.1 ClothingItem（衣物）

```
item_id           # 唯一 ID
name              # 名称（可选）
category          # 品类（上装/外套/下装/鞋/配件等）
subcategory       # 子品类（T恤/衬衫/牛仔裤等）
color             # 主色
secondary_color   # 辅色（可选）
season_tags       # 适合季节（春/夏/秋/冬/四季）
style_tags        # 风格标签（休闲/商务/运动等）
formality         # 正式度（casual/smart_casual/formal）
material          # 材质（可选）
brand             # 品牌（可选）
image_original_url  # 原始图路径
image_white_bg_url  # 白底图路径
is_available      # 当前是否可穿（True/False）
clean_status      # 可用状态（clean/dirty/washing/ironing/storage）
storage_location  # 存放位置（可选备注）
last_worn_date    # 上次穿着日期
wear_count        # 累计穿着次数
favorite_score    # 喜好分（用户打分/历史行为推断）
dislike_flag      # 是否明确不喜欢（True=不再推荐）
created_at        # 入库时间
updated_at        # 最后更新时间
```

### 6.2 WearLog（穿着记录）

```
log_id
item_ids          # 当天穿了哪些单品
date
occasion          # 场景（通勤/约会/运动等）
weather_snapshot  # 当天天气快照
user_feedback     # 用户反馈（满意/一般/不满意）
created_at
```

### 6.3 UserPreference（用户偏好）

```
user_id
preferred_styles  # 偏好风格列表
avoid_styles      # 回避风格列表
preferred_colors  # 偏好颜色
avoid_colors      # 回避颜色
temperature_sensitivity  # 体感偏好（怕冷/怕热/正常）
fit_preference    # 版型偏好（宽松/修身/不限）
comfort_priority  # 舒适优先级（高/中/低）
formality_preference  # 正式度偏好
updated_at
```

### 6.4 Outfit（推荐结果）

```
outfit_id
item_ids          # 包含哪些单品
scenario          # 推荐场景
reason            # 推荐理由
created_at
accepted_or_not   # 用户是否采纳
```

---

## 七、核心数据流（三大场景）

### 场景 A：拍照入库

```
用户上传图片
  │
  ▼
FastAPI 接收 → 保存 data/images/original/{id}.jpg
  │
  ├──▶ Gemini Vision: image_analyze
  │    → {category, color, style, season, formality, material}
  │
  ├──▶ Gemini Vision / rembg: bg_remove
  │    → data/images/white_bg/{id}.jpg
  │
  └──▶ 组装 ClothingItem → 写入 wardrobe.json
       → 返回前端：衣物卡片 + 识别属性（用户可修改确认）
```

### 场景 B：自然语言查询

```
用户："我有什么蓝色衬衫"
  │
  ▼
FastAPI /api/chat → LangGraph Agent
  │
  ▼
DeepSeek-V3：识别意图=查询，决定调用 wardrobe_query
  │
  ▼
wardrobe_query(color="蓝色", category="衬衫")
  │
  ▼
返回匹配结果 → Agent 组织自然语言回复 + 衣物卡片数据 → 前端渲染
```

### 场景 C：穿搭推荐（含遗忘召回）

```
用户："明天18度下雨通勤穿什么"
  │
  ▼
DeepSeek-V3：识别意图=推荐，依次调用：
  │
  ├──▶ weather_search("城市 明天天气")
  │    → {temp:18, rain:True, wind:"微风"}
  │
  ├──▶ forgotten_recall(days=60)
  │    → [被遗忘但当季适合的衣物列表]
  │
  ├──▶ wardrobe_query(is_available=True, season=当季)
  │    → [所有可用衣物]
  │
  └──▶ outfit_recommend(
         weather={temp:18, rain:True},
         scenario="通勤",
         available_items=[...],
         forgotten_items=[...],   ← 优先推荐被遗忘的
         recent_wears=[...],      ← 避免重复穿搭
         preferences={...}
       )
       │
       ▼ DeepSeek-R1 深度推理
       → 3套搭配方案 + 推荐理由 → 前端卡片展示
```

---

## 八、被遗忘衣物算分逻辑

遗忘分越高 = 越值得召回

```
forgotten_score 计算规则：

  基础分 = min(未穿天数 / 30, 5) × 20     最多 100 分
  +  max(0, 3 - 累计穿着次数) × 10         穿次少加分
  +  15（如果当季但没穿）
  -  50（如果用户明确标记不喜欢）            直接不召回
  -  30（如果当前状态不可用）               降低优先级

  阈值：score >= 60 进入"遗忘衣物"列表
```

---

## 九、API 端点规划

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/chat` | POST | 主对话接口，消息发给 LangGraph Agent |
| `/api/upload` | POST | 上传图片，触发识别 + 抠图流程 |
| `/api/wardrobe` | GET | 获取完整衣柜列表（支持筛选参数） |
| `/api/wardrobe/{id}` | PUT | 手动修改衣物属性 |
| `/api/wardrobe/{id}` | DELETE | 删除衣物 |
| `/api/wardrobe/{id}/confirm` | POST | 用户校正属性后确认入库 |
| `/api/forgotten` | GET | 获取被遗忘衣物列表 |
| `/api/history` | GET | 获取穿着历史（支持日期范围参数） |
| `/api/preferences` | GET/PUT | 读写用户偏好 |
| `/api/images/{type}/{filename}` | GET | 获取衣物图片（type: original/white_bg） |

---

## 十、项目目录结构

```
Dress/
├── 1.jsx                          # 现有前端原型（UI 参考，衣柜动画来源）
├── CONTEXT.md                     # 本文件
│
├── frontend/                      # React 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                # 主路由
│       ├── main.jsx               # 入口
│       ├── api/
│       │   └── client.js          # 封装后端 API 调用
│       ├── components/
│       │   ├── Layout.jsx         # 导航 + 整体布局
│       │   ├── WardrobeView.jsx   # 衣柜页（3D 翻转动画，从 1.jsx 移植）
│       │   ├── ChatView.jsx       # 对话界面
│       │   ├── RecommendView.jsx  # 推荐页
│       │   ├── HistoryView.jsx    # 穿搭历史页
│       │   ├── ItemCard.jsx       # 衣物卡片组件（复用）
│       │   ├── UploadModal.jsx    # 拍照/上传弹窗
│       │   └── WeatherCard.jsx    # 天气展示卡片
│       └── styles/
│           └── index.css          # Tailwind 入口
│
├── backend/                       # Python 后端
│   ├── requirements.txt
│   ├── main.py                    # FastAPI 入口，注册路由
│   ├── config.py                  # API Keys、路径等配置（从环境变量读取）
│   │
│   ├── agent/                     # LangGraph Agent 核心
│   │   ├── __init__.py
│   │   ├── graph.py               # LangGraph 图定义（节点、边、编译）
│   │   ├── state.py               # ClosetAgentState 类型定义
│   │   ├── nodes.py               # agent_node、tool_executor_node 实现
│   │   └── prompts.py             # System Prompts（DeepSeek-V3 / R1 分别维护）
│   │
│   ├── tools/                     # Agent 可调用的 Tools
│   │   ├── __init__.py
│   │   ├── wardrobe.py            # wardrobe_query / wardrobe_add / wardrobe_update
│   │   ├── image.py               # image_analyze / bg_remove（调 Gemini Vision）
│   │   ├── weather.py             # weather_search（Web Search）
│   │   ├── recall.py              # forgotten_recall（遗忘分算法）
│   │   ├── recommend.py           # outfit_recommend（调 DeepSeek-R1）
│   │   ├── wear_log.py            # wear_log（记录穿着）
│   │   └── preference.py         # user_preference（读写偏好）
│   │
│   ├── models/                    # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── item.py                # ClothingItem
│   │   ├── wear_log.py            # WearLog
│   │   ├── outfit.py              # Outfit
│   │   └── preference.py          # UserPreference
│   │
│   └── storage/                   # 存储层（JSON + 文件系统）
│       ├── __init__.py
│       ├── json_store.py          # JSON 文件读写封装
│       └── image_store.py         # 图片文件路径管理
│
└── data/                          # 本地数据（不进 git）
    ├── wardrobe.json
    ├── wear_logs.json
    ├── outfits.json
    ├── preferences.json
    └── images/
        ├── original/              # 原始上传照片
        └── white_bg/              # 白底处理后的图片
```

---

## 十一、Python 依赖清单

```
# backend/requirements.txt

fastapi>=0.115.0
uvicorn>=0.30.0
python-multipart          # 文件上传支持

langgraph>=0.2.0
langchain-google-genai>=2.0.0    # Gemini Vision
langchain-openai>=0.2.0          # DeepSeek（使用 OpenAI 兼容接口）
langchain-community>=0.3.0       # Web Search tool

pydantic>=2.0
pillow                            # 图片基础处理
rembg                             # 本地抠图（Gemini 兜底方案）

python-dotenv                     # 读取 .env 配置
```

---

## 十二、环境变量（.env）

```
GEMINI_API_KEY=xxx
DEEPSEEK_API_KEY=xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DATA_DIR=../data
IMAGES_DIR=../data/images
```

---

## 十三、版本规划

### v0.1 验证版（当前目标）
- [x] 架构设计完成
- [ ] 项目骨架搭建（FastAPI + React + Vite）
- [ ] 数据模型 + JSON 存储层
- [ ] 图片上传 + Gemini 识图 + 抠图
- [ ] LangGraph Agent 骨架（ReAct loop 跑通）
- [ ] wardrobe_query / update / add tools
- [ ] forgotten_recall 遗忘召回
- [ ] outfit_recommend 基础推荐
- [ ] 前端对接（衣柜展示 + 对话界面）
- [ ] 完整 MVP 闭环联调

### v0.2 可用版（后续）
- 穿着历史记录
- 天气联动（weather_search 优化）
- 用户偏好记忆与动态修正
- 旧衣新搭

### v0.3 成品雏形（后续）
- 利用率分析 + cost per wear
- 断舍离建议
- 购物缺口分析
- 旅行打包 / 胶囊衣橱

---

## 十四、关键风险与应对

| 风险 | 应对 |
|---|---|
| Gemini 抠图质量不稳定 | 用 rembg 本地模型兜底；保留原图供重新处理 |
| 入库步骤繁琐用户放弃 | 一键拍照自动识别，用户只需确认/简单修正 |
| 对话指代解析歧义（"那件""上次那套"）| 在 Agent State 中维护上轮对话的衣物上下文 |
| DeepSeek-R1 推荐空洞 | 推荐逻辑有规则层兜底（天气约束/状态约束/重复间隔约束）|
| 被遗忘衣物分数不准 | 算法参数可配置，后续根据用户反馈调整权重 |

---

## 十五、MVP 最小闭环验收标准

1. 用户能拍照 → 系统自动生成白底图 + 提取标签 → 入库成功
2. 用户能问："我有什么蓝色衬衫" → 系统正确返回衣物卡片
3. 系统能主动展示超过 60 天未穿的衣物列表
4. 用户能问："今天 18 度通勤怎么穿" → 系统**优先推荐被遗忘但适合的单品**生成搭配建议
5. 用户能说："今天穿了这套" → 系统记录穿着历史

满足以上 5 条 = v0.1 验收通过。
