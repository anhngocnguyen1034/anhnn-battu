# FOR-BAZI · 玄冥 Cyber-Bazi

> 专业八字命理 AI 系统 — 排盘、五行精算、格局判定、大运流年、AI 对话解读

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/React-18-61dafb?logo=react" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Tauri-v2-ffc131?logo=tauri" alt="Tauri">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 项目简介

FOR-BAZI 是一套完整的八字命理分析系统，融合传统命理学与现代 AI 技术，提供：

- **精准排盘** — 基于 lunar-python 的四柱八字计算，含藏干、纳音、十二长生
- **五行精算** — 天干地支加权分析，雷达图 + 柱状图可视化
- **格局判定** — 建禄、从格、专旺等格局自动识别
- **大运流年** — 十年大运 + 流年干支，交互式时间轴
- **神煞分析** — 天乙贵人、将星、驿马等 20+ 神煞自动标注
- **AI 对话** — 基于 ReAct Agent 的流式命理咨询，支持多模型切换
- **十神详解** — 十神关系映射与性格特征分析
- **合婚匹配** — 双命盘五行关系 + 地支交互分析
- **古籍参考** — 经典命理文献检索
- **娱乐功能** — 每日运势、生肖问答

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tauri v2 Shell (Rust, 3-10MB EXE)            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           React 18 + Vite + TypeScript                    │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ 10 Pages│ │ ECharts  │ │ Zustand  │ │ shadcn/ui    │  │  │
│  │  │ (Lazy)  │ │ (Radar/  │ │ (Persist │ │ + Tailwind   │  │  │
│  │  │         │ │  Bar/    │ │  Store)  │ │ CSS Vars     │  │  │
│  │  │         │ │  Line)   │ │          │ │              │  │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └──────────────┘  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ SSE Streaming                         │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │              FastAPI Backend (Python)                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ /chart   │ │ /chat/   │ │ /texts   │ │ /compati-   │  │  │
│  │  │          │ │ stream   │ │          │ │ bility      │  │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬──────┘  │  │
│  └───────┼────────────┼────────────┼───────────────┼─────────┘  │
│          │            │            │               │             │
│  ┌───────▼────────────▼────────────▼───────────────▼─────────┐  │
│  │              Python Engine Layer (Unchanged)               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ bazi_    │ │ wuxing_  │ │ geju_    │ │ react_      │  │  │
│  │  │ engine   │ │ calculator│ │ analyzer │ │ agent       │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │  │
│  │  │ shensha  │ │ ancient_ │ │ api_     │                  │  │
│  │  │          │ │ texts    │ │ adapter  │                  │  │
│  │  └──────────┘ └──────────┘ └──────────┘                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
FOR-BAZI/
├── engine/                    # 核心命理引擎
│   ├── bazi_engine.py         # 四柱八字计算（基于 lunar-python）
│   └── shensha.py             # 神煞判定
│
├── tools/                     # 分析工具
│   ├── wuxing_calculator.py   # 五行力量精算
│   ├── geju_analyzer.py       # 格局判定
│   └── bazi_tools.py          # Agent 可调用工具集
│
├── agent/                     # AI Agent 层
│   ├── react_agent.py         # ReAct 循环（Thought→Action→Observation→Answer）
│   ├── api_adapter.py         # 统一 OpenAI/Anthropic API 适配
│   └── context_manager.py     # 上下文管理
│
├── prompts/                   # 提示词模板
│   ├── system_prompts.py      # 系统提示词
│   └── ancient_texts.py       # 古籍文献数据库
│
├── backend/                   # FastAPI 后端（新增）
│   ├── main.py                # 应用入口，路由注册，CORS
│   ├── config.py              # Pydantic Settings 配置
│   ├── api/                   # API 路由
│   │   ├── chart.py           # POST /api/v1/chart
│   │   ├── chat.py            # POST /api/v1/chat/stream (SSE)
│   │   ├── texts.py           # GET  /api/v1/texts
│   │   ├── compatibility.py   # POST /api/v1/compatibility
│   │   └── entertainment.py   # GET  /api/v1/entertainment/daily-fortune
│   ├── schemas/               # Pydantic 数据模型
│   │   ├── common.py          # 共享模型（BaziChartData, WuxingPowerData）
│   │   ├── chart.py           # ChartRequest / ChartResponse
│   │   └── chat.py            # ChatRequest / ChatSSEEvent
│   └── services/              # 业务逻辑层
│       ├── bazi_service.py    # 排盘服务（256条LRU缓存）
│       ├── agent_service.py   # Agent 流式服务
│       └── text_service.py    # 古籍检索服务
│
├── frontend/                  # React 前端（新增）
│   ├── src/
│   │   ├── App.tsx            # 路由配置（lazy-loaded）
│   │   ├── main.tsx           # 入口
│   │   ├── index.css          # Tailwind + shadcn 暗色主题
│   │   ├── components/
│   │   │   ├── bazi/          # 命盘组件
│   │   │   │   ├── PillarCard.tsx      # 单柱卡片（玻璃态）
│   │   │   │   ├── FourPillarGrid.tsx  # 四柱网格
│   │   │   │   ├── WuxingRadar.tsx     # 五行雷达图（ECharts）
│   │   │   │   ├── WuxingBar.tsx       # 五行柱状图（ECharts）
│   │   │   │   └── DayunTimeline.tsx   # 大运时间轴（ECharts）
│   │   │   ├── chat/          # AI 对话组件
│   │   │   │   ├── ChatPanel.tsx       # 对话面板
│   │   │   │   ├── ChatMessage.tsx     # 消息气泡（Markdown）
│   │   │   │   ├── ChatInput.tsx       # 输入框（自动伸缩）
│   │   │   │   └── ToolCallStatus.tsx  # 工具调用状态
│   │   │   ├── layout/        # 布局组件
│   │   │   │   ├── AppShell.tsx        # 侧边栏 + 主内容
│   │   │   │   └── Sidebar.tsx         # 导航侧边栏
│   │   │   └── ui/            # shadcn/ui 组件（13个）
│   │   ├── pages/             # 页面组件（10个）
│   │   │   ├── BaziCalculator.tsx      # 排盘输入
│   │   │   ├── ChartVisualization.tsx  # 命盘可视化
│   │   │   ├── LuckPillars.tsx         # 大运流年
│   │   │   ├── ElementsAnalysis.tsx    # 五行分析
│   │   │   ├── TenGods.tsx             # 十神详解
│   │   │   ├── ShenSha.tsx             # 神煞分析
│   │   │   ├── AnnualForecast.tsx      # 流年运势
│   │   │   ├── AIReading.tsx           # AI 解读
│   │   │   ├── Chat.tsx                # AI 问事
│   │   │   └── Settings.tsx            # 设置
│   │   ├── stores/            # Zustand 状态管理
│   │   │   ├── useBaziStore.ts         # 命盘数据（persist）
│   │   │   ├── useChatStore.ts         # 对话历史（persist）
│   │   │   └── useSettingsStore.ts     # 设置（API key, 主题）
│   │   ├── hooks/
│   │   │   └── useChatSSE.ts           # SSE 流式 Hook
│   │   ├── lib/
│   │   │   ├── api.ts                 # Axios API 客户端
│   │   │   ├── response-adapter.ts    # 后端→前端数据适配
│   │   │   ├── wuxing-colors.ts       # 五行配色系统
│   │   │   └── utils.ts               # 工具函数
│   │   └── types/
│   │       └── bazi.ts                # TypeScript 类型定义
│   ├── index.html
│   ├── vite.config.ts         # Vite 配置 + API 代理
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── mcp_server/                # MCP 工具服务器
│   ├── server.py
│   └── README.md
│
├── streamlit_app.py           # Streamlit 旧版（保留作为备用）
├── launcher.py                # 启动脚本
├── requirements.txt           # Python 依赖（Streamlit 版）
└── docs/                      # 文档
    ├── ARCHITECTURE.md        # 架构详解
    ├── API.md                 # API 接口文档
    ├── DEPLOYMENT.md          # 部署指南
    └── RESEARCH_IMPROVEMENTS.md  # 调研与改进记录
```

## 快速开始

### 环境要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端 + 命理引擎 |
| Node.js | 18+ | 前端构建 |
| Rust | 1.70+ | Tauri 桌面应用（可选） |

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/FOR-BAZI.git
cd FOR-BAZI
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装后端依赖
pip install -r backend/requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# AI 模型 API Key（至少配置一个）
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 后端配置（可选）
BAZI_DEBUG=false
BAZI_HOST=0.0.0.0
BAZI_PORT=8000
```

### 4. 启动后端

```bash
# 方式一：直接运行
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：使用启动脚本
python launcher.py
```

后端启动后访问：
- API 文档：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端启动后访问：http://localhost:5173

### 6. 构建桌面应用（可选）

```bash
# 安装 Rust（如果尚未安装）
# https://rustup.rs/

# 安装 Tauri CLI
npm install -g @tauri-apps/cli

# 构建 EXE
cd frontend
npx tauri build
```

产出物：`frontend/src-tauri/target/release/FOR-BAZI.exe`（约 3-10MB）

---

## 功能模块

### 1. 排盘计算（Bazi Calculator）

输入出生日期、时间和性别，系统自动计算：

- 四柱八字（年柱、月柱、日柱、时柱）
- 天干地支、藏干、纳音
- 日主及其五行属性
- 十二长生（地势）
- 旬空
- 命宫、胎元、身宫、胎息

### 2. 命盘可视化（Chart Visualization）

- 四柱卡片展示，五行配色
- 五行雷达图 + 柱状图（ECharts）
- 大运时间轴
- 格局判定结果
- 专业/基础视图切换

### 3. 五行分析（Elements Analysis）

- 五行力量百分比计算（含藏干权重）
- 强弱评估（身强/身弱/从格）
- 喜用神 / 忌神判定
- 各元素来源柱位标注

### 4. 十神分析（Ten Gods）

- 四柱十神映射
- 十神详解（比肩、劫财、食神、伤官等）
- 性格特征分析

### 5. 神煞分析（Shen Sha）

- 20+ 常见神煞自动标注
- 按柱位分组展示
- 每个神煞附带详细解释

### 6. 大运流年（Luck Pillars）

- 十年大运时间轴（ECharts）
- 流年干支逐年展示
- 当前大运高亮
- 流年五行与日主关系分析

### 7. AI 解读（AI Reading）

- 一键生成全面命理分析
- SSE 流式输出，实时显示
- 工具调用状态展示
- 支持 OpenAI、Anthropic、MiMo、DeepSeek 等多模型

### 8. AI 问事（Chat）

- 交互式命理咨询
- 命盘摘要侧边栏
- Markdown 渲染
- 对话历史持久化

### 9. 合婚匹配（Compatibility）

- 双命盘五行关系分析
- 地支六合、六冲检测
- 综合匹配度评分（0-100）

### 10. 古籍参考（Classical Texts）

- 经典命理文献检索
- 按来源筛选
- 关键词高亮

---

## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18 | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 6.x | 构建工具 |
| Tailwind CSS | 4.x | 原子化 CSS |
| shadcn/ui | latest | UI 组件库 |
| ECharts | 5.x | 图表可视化 |
| Zustand | 5.x | 状态管理 |
| React Router | 7.x | 路由 |
| React Markdown | 9.x | Markdown 渲染 |
| Axios | 1.x | HTTP 客户端 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.110+ | Web 框架 |
| uvicorn | 0.29+ | ASGI 服务器 |
| sse-starlette | 2.0+ | SSE 流式响应 |
| Pydantic | 2.6+ | 数据验证 |
| lunar-python | 1.4+ | 农历/八字计算 |
| openai | 1.14+ | OpenAI API |
| anthropic | 0.39+ | Anthropic API |

### 桌面

| 技术 | 版本 | 用途 |
|------|------|------|
| Tauri | v2 | 桌面应用框架 |
| Rust | 1.70+ | Tauri 后端 |
| WebView2 | - | Windows 内置浏览器引擎 |

---

## API 接口

### 计算命盘

```http
POST /api/v1/chart
Content-Type: application/json

{
  "datetime_str": "2002-07-21 03:30",
  "gender": "乾造 (Male)"
}
```

### 流式对话

```http
POST /api/v1/chat/stream
Content-Type: application/json

{
  "message": "请分析我的八字格局",
  "provider": "OpenAI",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "chart_data": { ... },
  "history": [{"role": "user", "content": "..."}],
  "max_steps": 8
}
```

响应为 SSE 流，事件类型：`token`、`status`、`tool_call`、`done`、`error`

### 合婚匹配

```http
POST /api/v1/compatibility
Content-Type: application/json

{
  "person_a": {
    "datetime_str": "2002-07-21 03:30",
    "gender": "乾造 (Male)"
  },
  "person_b": {
    "datetime_str": "2003-05-15 14:00",
    "gender": "坤造 (Female)"
  }
}
```

完整 API 文档见 [docs/API.md](docs/API.md)

---

## 配置说明

### AI 模型配置

在前端设置页面或 `.env` 文件中配置：

| 环境变量 | 说明 |
|---------|------|
| `OPENAI_API_KEY` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | Anthropic API Key |
| `OPENAI_BASE_URL` | 自定义 OpenAI 兼容 API 地址 |

支持的模型提供商：
- **OpenAI** — GPT-4o, GPT-4-turbo 等
- **Anthropic** — Claude 3.5 Sonnet, Claude 3 Opus 等
- **MiMo** — 小米 MiMo 模型
- **DeepSeek** — DeepSeek-V2 等
- **自定义** — 任何 OpenAI 兼容 API

### 后端配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `BAZI_DEBUG` | `false` | 调试模式 |
| `BAZI_HOST` | `0.0.0.0` | 监听地址 |
| `BAZI_PORT` | `8000` | 监听端口 |
| `BAZI_CORS_ORIGINS` | `["http://localhost:5173"]` | CORS 允许源 |

---

## 开发指南

### 前端开发

```bash
cd frontend

# 启动开发服务器（带热更新）
npm run dev

# 类型检查
npx tsc --noEmit

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

### 后端开发

```bash
# 启动开发服务器（带自动重载）
python -m uvicorn backend.main:app --reload

# 运行测试
python -m pytest tests/ -v

# 查看 API 文档
open http://localhost:8000/docs
```

### 添加新页面

1. 在 `frontend/src/pages/` 创建页面组件
2. 在 `frontend/src/App.tsx` 添加路由
3. 在 `frontend/src/components/layout/Sidebar.tsx` 添加导航项

### 添加新 API 端点

1. 在 `backend/api/` 创建路由文件
2. 在 `backend/schemas/` 定义请求/响应模型
3. 在 `backend/services/` 实现业务逻辑
4. 在 `backend/main.py` 注册路由

---

## 配色系统

项目使用五行配色系统：

| 五行 | 颜色 | Hex | 用途 |
|------|------|-----|------|
| 金 (Metal) | 金黄 | `#d4af37` | 主色调、日主高亮 |
| 木 (Wood) | 翠绿 | `#50c878` | 木元素、喜用神 |
| 水 (Water) | 深蓝 | `#1e90ff` | 水元素 |
| 火 (Fire) | 赤红 | `#e94560` | 火元素、忌神 |
| 土 (Earth) | 土黄 | `#c9a96e` | 土元素 |

---

## 示例命盘

以 `男，2002-07-21 03:30` 为例：

| 柱位 | 干支 | 纳音 | 十神 |
|------|------|------|------|
| 年柱 | 壬午 | 杨柳木 | 食神 |
| 月柱 | 丁未 | 天河水 | 正官 |
| 日柱 | 庚寅 | 松柏木 | 日主 |
| 时柱 | 戊寅 | 城头土 | 偏印 |

- **日主**: 庚金，身弱从格
- **最旺**: 火（47.5%）
- **最弱**: 金（3.8%）
- **喜用神**: 金
- **格局**: 从格

---

## 相关项目

- [lunar-python](https://github.com 6tail/lunar-python) — 农历/八字计算库
- [8Char-Uni-App](https://github.com/rxnh86/8char-Uni-App) — 八字排盘参考
- [china-testing/bazi](https://github.com/china-testing/bazi) — 五行/格局参考
- [shadcn/ui](https://ui.shadcn.com/) — UI 组件库
- [ECharts](https://echarts.apache.org/) — 图表库
- [Tauri](https://tauri.app/) — 桌面应用框架

---

## 许可证

MIT License

---

## 致谢

- 感谢 [6tail/lunar-python](https://github.com/6tail/lunar-python) 提供精准的农历计算
- 感谢 [shadcn/ui](https://ui.shadcn.com/) 提供优秀的 UI 组件
- 感谢所有开源社区的贡献者
