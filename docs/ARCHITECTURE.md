# FOR-BAZI 架构文档

> 系统架构、模块职责、数据流详细说明

---

## 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面层                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Tauri v2 Shell (Rust, 3-10MB)                │  │
│  │              或 Web 浏览器                                 │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │           React 18 + Vite + TypeScript                    │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Pages (10)  │  Components  │  Stores (3)  │  Hooks │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ HTTP / SSE                           │
├──────────────────────────┼──────────────────────────────────────┤
│                        服务层                                   │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │              FastAPI Backend (Python)                      │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  API Routes (5) │  Schemas (4)  │  Services (3)     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│                        引擎层                                   │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │              Python Engine (Unchanged)                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ bazi_    │ │ wuxing_  │ │ geju_    │ │ react_      │  │  │
│  │  │ engine   │ │ calculator│ │ analyzer │ │ agent       │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │  │
│  │  │ shensha  │ │ ancient_ │ │ api_     │                  │  │
│  │  │          │ │ texts    │ │ adapter  │                  │  │
│  │  └──────────┘ └──────────┘ └──────────┘                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│                        外部服务                                 │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │  │
│  │  │ OpenAI   │ │ Anthropic│ │ lunar-   │                  │  │
│  │  │ API      │ │ API      │ │ python   │                  │  │
│  │  └──────────┘ └──────────┘ └──────────┘                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 模块职责

### 前端层（frontend/）

#### 页面组件（src/pages/）

| 页面 | 路由 | 职责 |
|------|------|------|
| BaziCalculator | `/` | 出生信息输入，触发排盘计算 |
| ChartVisualization | `/chart` | 四柱展示、五行图表、大运时间轴 |
| LuckPillars | `/luck` | 大运十年运程 + 流年逐年分析 |
| ElementsAnalysis | `/elements` | 五行力量雷达图、柱状图、详细分解 |
| TenGods | `/ten-gods` | 十神映射、详解、性格分析 |
| ShenSha | `/shensha` | 神煞按柱位分组展示 |
| AnnualForecast | `/annual` | 当前流年运势、近十年流年一览 |
| AIReading | `/ai-reading` | 一键 AI 全面分析（SSE 流式） |
| Chat | `/chat` | 交互式 AI 命理咨询 |
| Settings | `/settings` | API 配置、主题、导出导入 |

#### 组件（src/components/）

| 组件 | 职责 |
|------|------|
| `bazi/PillarCard` | 单柱展示（天干地支、五行配色、玻璃态） |
| `bazi/FourPillarGrid` | 四柱网格布局 |
| `bazi/WuxingRadar` | 五行雷达图（ECharts） |
| `bazi/WuxingBar` | 五行柱状图（ECharts） |
| `bazi/DayunTimeline` | 大运时间轴（ECharts） |
| `chat/ChatPanel` | 对话主面板 |
| `chat/ChatMessage` | 消息气泡（Markdown 渲染） |
| `chat/ChatInput` | 输入框（自动伸缩） |
| `chat/ToolCallStatus` | 工具调用状态面板 |
| `layout/AppShell` | 侧边栏 + 主内容布局 |
| `layout/Sidebar` | 导航侧边栏（五行图标） |

#### 状态管理（src/stores/）

| Store | 持久化 | 职责 |
|-------|--------|------|
| `useBaziStore` | localStorage | 命盘数据、计算历史、加载状态 |
| `useChatStore` | localStorage | 对话消息历史 |
| `useSettingsStore` | localStorage | API Key、Provider、主题、语言 |

#### 数据适配（src/lib/response-adapter.ts）

将后端扁平数组转换为前端嵌套对象：

```
后端: pillars: ["壬午", "丁未", "庚寅", "戊寅"]
      wuxing: {"金(Metal)": 1, ...}
      tg_gan: ["食神", "正官", "日主", "偏印"]

前端: chart.year_pillar: {stem: "壬", branch: "午", element: "水", hidden_stems: ["丁","己"]}
      element_balance: {金: 1, 木: 2, 水: 1, 火: 2, 土: 2}
      ten_gods: [{name: "食神", character: "壬", element: "水", is_favorable: true}]
```

---

### 后端层（backend/）

#### API 路由（api/）

| 路由 | 方法 | 职责 |
|------|------|------|
| `api/chart.py` | POST | 接收出生信息，调用引擎计算，缓存结果 |
| `api/chat.py` | POST | SSE 流式对话，包装 Agent 循环 |
| `api/texts.py` | GET | 古籍文献关键词检索 |
| `api/compatibility.py` | POST | 双命盘计算 + 匹配度分析 |
| `api/entertainment.py` | GET | 每日运势（娱乐） |

#### 数据模型（schemas/）

| 文件 | 模型 | 用途 |
|------|------|------|
| `common.py` | BaziChartData, WuxingPowerData, GejuData, XingChongData | 共享数据结构 |
| `chart.py` | ChartRequest, ChartResponse | 排盘请求/响应 |
| `chat.py` | ChatRequest, ChatSSEEvent | 对话请求/事件 |

#### 服务层（services/）

| 服务 | 职责 |
|------|------|
| `bazi_service.py` | 封装引擎调用，256条LRU缓存，并发安全 |
| `agent_service.py` | 封装 ReAct Agent，SSE 事件生成 |
| `text_service.py` | 封装古籍检索 |

---

### 引擎层（engine/, tools/, agent/）

#### 核心引擎（engine/）

| 文件 | 职责 |
|------|------|
| `bazi_engine.py` | 四柱八字计算主逻辑（基于 lunar-python） |
| `shensha.py` | 神煞判定（天乙贵人、将星、驿马等） |

#### 分析工具（tools/）

| 文件 | 职责 |
|------|------|
| `wuxing_calculator.py` | 五行力量精算（天干+月令+藏干加权） |
| `geju_analyzer.py` | 格局判定（建禄、从格、专旺等） |
| `bazi_tools.py` | Agent 可调用的工具集 |

#### AI Agent（agent/）

| 文件 | 职责 |
|------|------|
| `react_agent.py` | ReAct 循环（Thought→Action→Observation→Answer） |
| `api_adapter.py` | 统一 OpenAI/Anthropic API 调用 |
| `context_manager.py` | 上下文管理 |

---

## 数据流

### 排盘计算流程

```
用户输入 (birth_date, birth_time, gender)
    │
    ▼
前端 BaziCalculator.tsx
    │ calculate()
    ▼
useBaziStore.calculate()
    │ calculateBazi(input)
    ▼
api.ts: calculateBazi()
    │ POST /api/v1/chart
    │ {datetime_str: "2002-07-21 03:30", gender: "乾造 (Male)"}
    ▼
backend api/chart.py: post_chart()
    │
    ▼
bazi_service.py: calculate_chart()
    │ 检查缓存 → 缓存命中则直接返回
    │ 缓存未命中 → 调用引擎
    ▼
bazi_engine.py: calculate_professional_bazi()
    │ 调用 lunar-python 计算四柱
    │ 计算藏干、纳音、神煞、大运等
    ▼
wuxing_calculator.py: calculate_wuxing_power()
    │ 天干+月令+藏干加权计算
    ▼
geju_analyzer.py: analyze_geju()
    │ 格局判定
    ▼
返回 {chart, wuxing_power, geju}
    │
    ▼
api.ts: adaptChartResponse()
    │ 转换扁平数组 → 嵌套对象
    ▼
useBaziStore: setReading()
    │ 存储到 localStorage
    ▼
前端页面渲染
```

### AI 对话流程

```
用户输入消息
    │
    ▼
Chat.tsx: handleSend()
    │ addMessage(userMsg)
    ▼
useChatSSE: sendMessage()
    │
    ▼
api.ts: chatStream()
    │ POST /api/v1/chat/stream (SSE)
    │ 转换为后端 ChatRequest 格式
    ▼
backend api/chat.py: post_chat_stream()
    │
    ▼
agent_service.py: stream_chat()
    │ 启动 ReAct Agent 循环
    ▼
react_agent.py: run_react_loop_streaming()
    │
    ├─→ Thought: 分析用户问题
    ├─→ Action: 调用工具（get_bazi_chart, search_texts, ...）
    ├─→ Observation: 获取工具结果
    ├─→ ... 重复 ...
    └─→ Final Answer: 生成回答
    │
    ▼
SSE 事件流返回前端
    │
    ├─→ onToken: 实时更新文本
    ├─→ onStatus: 更新状态提示
    ├─→ onToolCall: 更新工具调用状态
    └─→ onDone: 完成，保存消息
    │
    ▼
前端渲染 Markdown 内容
```

---

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 前端框架 | React 18 + Vite | 快速 HMR，小包体积，Tauri 原生支持 |
| UI 库 | shadcn/ui | 完全 CSS 控制，Tailwind 原生，可组合 |
| 状态管理 | Zustand + persist | 极简样板，无需 Provider，自动持久化 |
| 图表库 | ECharts | 原生中文支持，雷达图/柱状图/时间轴 |
| 后端框架 | FastAPI | 异步，SSE 支持，自动 OpenAPI 文档 |
| 桌面框架 | Tauri v2 | 3-10MB EXE，WebView2，Rust 安全性 |
| 流式协议 | SSE（非 WebSocket） | 更简单，单向足够，浏览器原生支持 |
| 数据适配 | 响应适配器 | 后端保持扁平数组，前端保持嵌套对象，适配器桥接 |
| 缓存策略 | LRU 256条 | 避免重复计算，内存可控 |

---

## 缓存策略

### 后端缓存

- **命盘计算**: 256条 LRU 缓存，key 为 `datetime_str|gender`
- **缓存命中**: 直接返回，跳过所有计算
- **缓存淘汰**: FIFO 淘汰最旧条目

### 前端缓存

- **Zustand persist**: 命盘数据、对话历史、设置持久化到 localStorage
- **页面级缓存**: useMemo 缓存派生数据（图表配置、排序结果等）

---

## 错误处理

### 前端

- **API 错误**: Axios 拦截器统一处理，提取 `detail` 字段
- **SSE 错误**: `onError` 回调，支持重试（最多2次，指数退避）
- **UI 错误**: 错误状态展示，支持重试按钮

### 后端

- **验证错误**: Pydantic 自动返回 422 + 详细字段错误
- **业务错误**: HTTPException 返回 400/500 + 错误描述
- **引擎异常**: 捕获并记录日志，返回通用错误信息

---

## 安全考虑

- **API Key**: 仅在前端 localStorage 存储，不传输至后端持久化
- **CORS**: 仅允许 localhost 和 tauri://localhost
- **输入验证**: Pydantic 严格验证所有输入
- **无 SQL 注入**: 无数据库，纯计算服务
- **无 XSS**: React 默认转义，Markdown 渲染使用 remark-gfm
