# Dress

一个用于管理个人衣柜、上传识别衣物、查询穿搭和生成推荐的前后端分离项目。

## 项目结构

- `frontend/`：前端，基于 `Vite + React + TypeScript`
- `backend/`：后端，基于 `FastAPI`
- `data/`：本地运行时数据和日志目录

## 运行环境

- Python `3.11`
- Node.js `20+`
- npm `10+`

## 启动前准备

### 1. 安装后端依赖

在项目根目录执行：

```bash
pip install -r backend/requirements.txt
```

### 2. 安装前端依赖

进入前端目录执行：

```bash
cd frontend
npm install
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件，至少需要这些配置：

```env
DEEPSEEK_API_KEY=你的_deepseek_key
GOOGLE_API_KEY=你的_google_key
```

说明：

- `DEEPSEEK_API_KEY`：后端启动必填
- 识图能力至少要有一个可用密钥：
  - `GOOGLE_API_KEY`
  - `GEMINI_API_KEY`
  - `GLM_API_KEY`

如果你使用 Gemini，后端会优先读取 `GOOGLE_API_KEY`，没有时再读取 `GEMINI_API_KEY`。

## 启动项目

需要分别启动后端和前端。

### 启动后端

在项目根目录执行：

```bash
python -m uvicorn backend.main:app --reload
```

后端默认地址：

- `http://127.0.0.1:8000`

接口示例：

- `http://127.0.0.1:8000/api/wardrobe`

### 启动前端

在 `frontend/` 目录执行：

```bash
npm run dev
```

前端默认地址：

- `http://localhost:5173`

## 启动成功后的访问方式

- 前端页面：`http://localhost:5173`
- 后端接口：`http://127.0.0.1:8000`

## 常见问题

### 后端启动时报缺少环境变量

说明根目录 `.env` 没配好。后端启动时会校验：

- `DEEPSEEK_API_KEY`
- `GOOGLE_API_KEY` / `GEMINI_API_KEY` / `GLM_API_KEY` 这三者至少一个

### 前端能打开，但接口请求失败

先确认：

- 后端是否已经启动
- 后端地址是否还是 `127.0.0.1:8000`
- `.env` 中的模型密钥是否有效

### 启动日志出现 `rembg dependency is unavailable`

这是白底图回退能力不可用的提示，不会阻止项目基础启动。
