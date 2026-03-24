# Dress / 衣柜 Agent 上下文

## 这个项目是做什么的？

这是一个面向个人穿衣决策的数字衣柜系统。

核心目标不是单纯“生成穿搭建议”，而是把用户已经拥有、但平时容易被遗忘的衣服重新拉回日常决策里。项目 v0.1 重点验证 5 个闭环：

1. 拍照上传衣物并识别入库。
2. 用自然语言查询衣柜。
3. 计算并展示“遗忘衣物”。
4. 结合天气、场景和偏好给出穿搭方案。
5. 记录“今天穿了这套”，让下次推荐更准。

## 入口在哪里？

- 前端入口：[frontend/src/main.tsx](/D:/Coding_Project/Dress/frontend/src/main.tsx)
- 前端主应用：[frontend/src/App.tsx](/D:/Coding_Project/Dress/frontend/src/App.tsx)
- 后端入口：[backend/main.py](/D:/Coding_Project/Dress/backend/main.py)
- Agent 图入口：[backend/agent/graph.py](/D:/Coding_Project/Dress/backend/agent/graph.py)

## 请求/任务从哪里进，从哪里出？

- 图片上传：
  - 前端 `UploadModal` 选择文件。
  - 用户可选 `Gemini` 或 `GLM-4.6V` 做识图。
  - 请求进入 `/api/upload`。
  - 后端保存原图、按 provider 调识图、再尝试白底处理。
  - 返回“待确认衣物”给前端。
  - 前端再调用 `/api/wardrobe/{id}/confirm` 完成正式入库。

- 自然语言问衣 / 穿搭推荐：
  - 前端 `ChatView` 或 `RecommendView` 触发 `/api/chat`。
  - 后端把请求送入 LangGraph 最小图。
  - Agent 根据用户输入决定调哪些工具。
  - 工具结果再回给 Agent 组织回复。
  - 最终返回 `reply + cards + action` 给前端。

- 穿着记录：
  - 前端在推荐结果里点击“就穿这套”，或后续直接调历史接口。
  - 请求进入 `/api/history`。
  - 后端写入穿着历史，并更新衣物的最近穿着时间与穿着次数。

## 关键模块分别负责什么？

- `frontend/src/components/`
  - 页面级组件和主要交互。
  - `WardrobeView` 保留原型中的挂衣区、裤装区、鞋架区拟物动效。
  - `RecommendView` 负责场景、温度、风格输入和推荐展示。
  - `ChatView` 负责自然语言问衣。
  - `HistoryView` 负责穿搭时间轴。
  - `UploadModal` 负责上传与确认入库流程。

- `backend/models/`
  - 所有核心 Pydantic 数据模型。
  - 包括衣物、穿着记录、偏好、推荐结果和 API 请求/响应模型。

- `backend/storage/`
  - JSON 文件读写和图片文件路径管理。
  - 业务层不直接操作裸 JSON。

- `backend/providers/`
  - 外部服务适配层。
  - `deepseek.py` 负责对话路由和推荐理由生成。
  - `gemini.py` 负责衣物图片分析和白底图尝试生成。
    - Gemini Developer API 环境变量优先读 `GOOGLE_API_KEY`，再回退 `GEMINI_API_KEY`。
    - 白底图主模型默认是 Nano Banana 2，也就是 `gemini-3.1-flash-image-preview`。
  - `glm.py` 负责 `GLM-4.6V` 衣物图片分析。

- `backend/tools/`
  - Agent 可调用的具体工具逻辑。
  - 包括衣柜查询、遗忘召回、穿搭推荐、偏好读写、天气查询等。

- `backend/agent/`
  - LangGraph 状态定义、节点逻辑和图编排。

## 关键状态 / 数据结构 / 事件名在哪定义？

- 衣物模型：[backend/models/item.py](/D:/Coding_Project/Dress/backend/models/item.py)
- 穿着历史模型：[backend/models/wear_log.py](/D:/Coding_Project/Dress/backend/models/wear_log.py)
- 偏好模型：[backend/models/preference.py](/D:/Coding_Project/Dress/backend/models/preference.py)
- 推荐模型：[backend/models/outfit.py](/D:/Coding_Project/Dress/backend/models/outfit.py)
- API 模型：[backend/models/api.py](/D:/Coding_Project/Dress/backend/models/api.py)
- Agent 状态：[backend/agent/state.py](/D:/Coding_Project/Dress/backend/agent/state.py)
- 前端共享类型：[frontend/src/types/index.ts](/D:/Coding_Project/Dress/frontend/src/types/index.ts)

## 新需求通常改哪里？

- 改接口：
  - 先看 [backend/main.py](/D:/Coding_Project/Dress/backend/main.py)
  - 再看对应 `tools/` 和 `models/api.py`

- 改推荐逻辑：
  - 优先看 [backend/tools/recommend.py](/D:/Coding_Project/Dress/backend/tools/recommend.py)
  - 如果是 Agent 路由问题，再看 [backend/agent/nodes.py](/D:/Coding_Project/Dress/backend/agent/nodes.py)

- 改遗忘召回：
  - 看 [backend/tools/recall.py](/D:/Coding_Project/Dress/backend/tools/recall.py)

- 改上传识别 / 白底图：
  - 看 [backend/tools/image.py](/D:/Coding_Project/Dress/backend/tools/image.py)
  - 再看 `providers/gemini.py`、`providers/glm.py` 与 `storage/image_store.py`
  - 注意：`vision_provider` 只控制“识图模型”，不控制白底图模型。

- 改前端样式和布局：
  - 先看 [frontend/src/components/WardrobeView.tsx](/D:/Coding_Project/Dress/frontend/src/components/WardrobeView.tsx)
  - 再看 [frontend/src/styles/index.css](/D:/Coding_Project/Dress/frontend/src/styles/index.css)

## 哪些地方别随便碰？

- `WardrobeView` 里的挂衣区和鞋架区交互细节不要随手简化。
  - 这是整个原型最有辨识度的视觉资产。

- `forgotten_score` 公式不要随意改权重。
  - 当前权重直接对应产品核心主张，调整会改变推荐方向。

- 外部 Provider 适配层不要把第三方响应结构泄漏到业务层。
  - 一旦 SDK 或接口变动，应该只改 `providers/`。

## 如何本地跑通？

### 后端

1. 准备 Python 3.11。
2. 进入 `backend/`。
3. 安装依赖：`pip install -r requirements.txt`
4. 在项目根目录创建 `.env`，至少填：
   - `DEEPSEEK_API_KEY`
   - `GOOGLE_API_KEY` 或 `GEMINI_API_KEY` 或 `GLM_API_KEY`（至少一个可用识图能力）
   - 如果要走 Gemini 识图或白底图，优先配置 `GOOGLE_API_KEY`；旧环境可继续用 `GEMINI_API_KEY`
   - 可选：`GEMINI_IMAGE_MODEL=gemini-3.1-flash-image-preview`
5. 启动：

```bash
uvicorn backend.main:app --reload
```

### 前端

1. 准备 Node.js 20+。
2. 进入 `frontend/`。
3. 安装依赖：`npm install`
4. 启动：

```bash
npm run dev
```

## 如何验证？

1. 上传一张衣物图，确认能返回待确认衣物。
   - 如果上传时选择 `GLM-4.6V`，它只影响识图，不影响白底图 provider。
   - 如果上传时选择 `Gemini`，报错信息应显示具体后端错误，而不是只看到 `Failed to fetch`。
2. 修改属性后确认入库，衣柜页应能看到新衣物。
3. 问“我有什么蓝色衬衫”，对话页应返回衣物卡片。
4. 推荐页输入“18 度 + 通勤”，应返回 3 套方案。
5. 点击“就穿这套”，历史页应出现一条记录。
6. 查看 `data/logs/app.log`，应能看到接口入口、工具调用、白底图 provider 与异常日志。
