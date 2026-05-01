# 古籍知识库调研与集成设计文档

> FOR-BAZI 项目古籍资源扩展方案
> 创建日期：2026-05-01
> 版本：1.0

---

## 1. 背景与目标

### 1.1 当前状态

FOR-BAZI 项目已集成以下古籍内容（硬编码在 `prompts/ancient_texts.py`）：

| 古籍 | 覆盖范围 | 条目数 | 格式 |
|------|----------|--------|------|
| 穷通宝鉴 | 完整（10天干 × 4季节） | 40 条 | Python dict |
| 滴天髓 | 部分（甲/乙/丙/丁 + 通用理法） | 12 条 | Python dict |
| 子平真诠 | 8 个基本格局 | 8 条 | Python dict |
| 三命通会 | 缺失 | 0 | - |
| 渊海子平 | 缺失 | 0 | - |
| 神峰通考 | 缺失 | 0 | - |

### 1.2 目标

1. **补全现有古籍**：滴天髓戊/己/庚/辛/壬/癸 六条十干体性
2. **扩展子平真诠**：特殊格局（从格、化格、专旺格、建禄格、月刃格）
3. **新增三命通会**：60 日柱条目（至少 12 个日柱）
4. **新增其他古籍**：渊海子平、神峰通考核心内容
5. **数据结构化**：迁移至 JSON 格式，便于 AI 查询和检索
6. **质量保证**：每条数据标注来源，人工校验

### 1.3 成功标准

- 古籍覆盖率达到 80% 以上（滴天髓/子平真诠/三命通会）
- 所有数据存储为 JSON 格式
- AI 可通过工具查询古籍内容
- RAG 检索准确率 > 80%（相关条目在前5条中）
- Agent 工作流可自动检索和引用古籍
- MingLi-Bench 测试成绩提升 5% 以上

---

## 2. 调研范围

### 2.1 目标古籍清单

| 古籍 | 作者 | 朝代 | 核心内容 | 优先级 |
|------|------|------|----------|--------|
| 滴天髓 | 京图（传）/ 任铁樵注 | 宋/清 | 十干体性、用神、配合 | 高 |
| 子平真诠 | 沈孝瞻 | 清 | 格局论法、月令取格 | 高 |
| 三命通会 | 万民英 | 明 | 日柱论命、神煞、纳音 | 中 |
| 渊海子平 | 徐子平（传）/ 徐大升编 | 宋 | 子平法基础、格局 | 中 |
| 神峰通考 | 张楠 | 明 | 神煞、纳音、命例 | 低 |
| 穷通宝鉴 | 余春台编 | 清 | 调候用神 | 已完成 |

### 2.2 数据维度

每条古籍条目应包含：

| 字段 | 必需 | 说明 |
|------|------|------|
| `原文` | 是 | 古籍原文（繁体或简体） |
| `出处` | 是 | 具体篇目/章节 |
| `category` | 是 | 分类（十干体性/格局/神煞/理法等） |
| `key` | 是 | 索引键（日主/格局名/神煞名等） |
| `tags` | 否 | 标签，便于搜索 |

**可选字段（AI 实时生成）：**
- `白话`：白话翻译
- `应用`：实际应用说明

---

## 3. 调研方法

### 3.1 GitHub 搜索策略

**搜索关键词：**
```
中文：
- "八字古籍" + "dataset" / "JSON" / "数据"
- "滴天髓" + "数据" / "结构化"
- "子平真诠" + "dataset"
- "三命通会" + "JSON"
- "命理" + "古籍" + "开源"
- "命理" + "知识图谱"

英文：
- "bazi" + "dataset" / "classical texts"
- "chinese fortune telling" + "data"
- "four pillars" + "dataset"
- "ming li" + "knowledge base"
```

**筛选标准：**
- 星标 > 10（质量基本保障）
- 有结构化数据（JSON/CSV/数据库）
- 最近 2 年有更新（活跃维护）
- 许可证允许使用（MIT/Apache/BSD）

**重点检查项目：**
1. `chinese-poetry/chinese-poetry`（49k 星）— 数据组织方式参考
2. `6tail/lunar-python` — 历法数据参考
3. `SylarLong/iztro` — 紫微斗数数据结构参考
4. `ctext.org` API — 古籍原文获取

### 3.2 权威网站爬取

**目标网站：**

| 网站 | URL | 内容 | API/爬取 |
|------|-----|------|----------|
| 中国哲学书电子化计划 | ctext.org | 先秦至清代古籍 | 有公开 API |
| 国学大师 | guoxuedashi.com | 命理古籍全文 | 需爬取 |
| 汉典 | zdic.net | 字义、读音 | 需爬取 |

**爬取策略：**
- 遵守 robots.txt
- 限速请求（每秒不超过 1 次）
- 缓存结果到本地
- 标注来源 URL

### 3.3 AI 补充

对于社区和爬取都无法获取的内容：
- 使用 Claude/GPT 生成结构化内容
- 生成后人工校验
- 标注为 "AI 生成 + 人工校验"

---

## 4. 数据格式设计

### 4.1 目录结构

```
data/
  classical_texts/
    index.json                # 索引文件
    di_tian_sui.json          # 滴天髓
    ziping_zhenquan.json      # 子平真诠
    sanming_tonghui.json      # 三命通会
    yuanhai_ziping.json       # 渊海子平
    shenfeng_tongkao.json     # 神峰通考
    qiongtong_baojian.json    # 穷通宝鉴
```

### 4.2 索引文件 (index.json)

```json
{
  "version": "1.0",
  "last_updated": "2026-05-01",
  "texts": [
    {
      "id": "di_tian_sui",
      "name": "滴天髓",
      "author": "京图（传）/ 任铁樵注",
      "dynasty": "宋/清",
      "description": "八字命理核心理法，论十干体性、用神、配合",
      "file": "di_tian_sui.json",
      "entry_count": 16,
      "categories": ["十干体性", "理法", "用神"]
    }
  ]
}
```

### 4.3 滴天髓 (di_tian_sui.json)

```json
{
  "source": "滴天髓",
  "version": "1.0",
  "last_updated": "2026-05-01",
  "metadata": {
    "author": "京图（传）/ 任铁樵注",
    "dynasty": "宋/清",
    "total_entries": 16
  },
  "entries": {
    "十干体性_甲": {
      "category": "十干体性",
      "key": "甲",
      "原文": "甲木参天，脱胎要火。春不容金，秋不容土。火炽乘龙，水宕骑虎。地润天和，植立千古。",
      "出处": "滴天髓·十干体性篇",
      "tags": ["甲木", "十干", "体性"]
    },
    "十干体性_戊": {
      "category": "十干体性",
      "key": "戊",
      "原文": "戊土固重，既中且正。静翕动辟，万物司命。水润物生，火燥物病。若在艮坤，怕冲宜静。",
      "出处": "滴天髓·十干体性篇",
      "tags": ["戊土", "十干", "体性"]
    }
  }
}
```

### 4.4 子平真诠 (ziping_zhenquan.json)

```json
{
  "source": "子平真诠",
  "version": "1.0",
  "last_updated": "2026-05-01",
  "metadata": {
    "author": "沈孝瞻",
    "dynasty": "清",
    "total_entries": 20
  },
  "entries": {
    "正官格": {
      "category": "格局",
      "key": "正官格",
      "原文": "正官格者，月令透正官，四柱无伤官破之，谓之正官格。",
      "成格条件": "月令藏干透正官；正官不被合化变质；无伤官直克正官；官星有财星生扶或有印星护官。",
      "破格条件": "伤官见官；官杀混杂；正官被合化为忌神；无根无气官星虚浮。",
      "喜忌": "喜：财生官、印护官、官印相生。忌：伤官破格、比劫抗官、官杀混杂。",
      "出处": "子平真诠·论正官",
      "tags": ["正官", "格局", "月令"]
    },
    "从财格": {
      "category": "特殊格局",
      "key": "从财格",
      "原文": "从财格者，日主无根无气，满盘皆财，不得不从。",
      "成格条件": "日主无根无气；财星满盘；无印比生扶。",
      "破格条件": "日主得根；印比出现生扶。",
      "喜忌": "喜：财星、食伤。忌：印比、官杀（泄财气）。",
      "出处": "子平真诠·论从格",
      "tags": ["从格", "财格", "特殊格局"]
    }
  }
}
```

### 4.5 三命通会 (sanming_tonghui.json)

```json
{
  "source": "三命通会",
  "version": "1.0",
  "last_updated": "2026-05-01",
  "metadata": {
    "author": "万民英",
    "dynasty": "明",
    "total_entries": 60
  },
  "entries": {
    "甲子日": {
      "category": "日柱",
      "key": "甲子",
      "原文": "甲木栋梁，子水智谋。甲子日生，聪明秀气，文才出众。",
      "日柱特性": "甲坐子，正印坐下，聪明好学。",
      "出处": "三命通会·论日柱",
      "tags": ["甲子", "日柱", "正印"]
    }
  }
}
```

---

## 5. RAG 检索增强生成设计

### 5.1 为什么需要 RAG

古籍数据只是原材料，要让 AI 有效利用这些命理知识，需要：

1. **精准检索**：根据用户八字特征，自动检索相关古籍条目
2. **上下文注入**：将检索到的知识注入 AI 的上下文中
3. **知识融合**：AI 结合古籍知识和用户八字进行分析

### 5.2 RAG 架构

```
用户输入八字
    ↓
特征提取（日主、月令、格局、十神等）
    ↓
多路检索：
  ├── 精确匹配：日主 + 月令 → 穷通宝鉴
  ├── 格局匹配：格局名 → 子平真诠
  ├── 日柱匹配：日柱干支 → 三命通会
  ├── 理法匹配：日主 → 滴天髓
  └── 语义搜索：用户问题 → 向量检索
    ↓
知识融合 + 重排序
    ↓
注入 AI 上下文
    ↓
AI 分析生成
```

### 5.3 检索策略

**精确匹配（规则引擎）：**
- 日主 + 月令 → 穷通宝鉴调候用神
- 格局名 → 子平真诠格局论法
- 日柱干支 → 三命通会日柱特性
- 日主 → 滴天髓十干体性

**语义搜索（向量检索）：**
- 将古籍条目向量化（使用 embedding 模型）
- 用户问题向量化
- 余弦相似度匹配
- 适用场景：用户提问涉及多个维度

**混合检索：**
- 精确匹配优先（高置信度）
- 语义搜索补充（覆盖边缘情况）
- 结果去重 + 重排序

### 5.4 向量数据库选择

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| ChromaDB | 轻量、Python 原生、易集成 | 性能一般 | 中小规模（<10万条） |
| Milvus | 高性能、分布式 | 部署复杂 | 大规模生产环境 |
| FAISS | Facebook 出品、性能好 | 仅支持内存 | 本地高性能检索 |
| SQLite + FTS5 | 无需额外依赖 | 功能有限 | 轻量级全文搜索 |

**推荐：ChromaDB**
- 理由：Python 原生、轻量级、适合项目规模
- 已在 `bazi_agent` 项目中验证可行

### 5.5 Embedding 模型选择

| 模型 | 维度 | 中文支持 | 推荐 |
|------|------|----------|------|
| text2vec-base-chinese | 768 | 优秀 | 本地部署 |
| m3e-base | 768 | 优秀 | 本地部署 |
| OpenAI text-embedding-3-small | 1536 | 良好 | API 调用 |
| Azure OpenAI | 1536 | 良好 | 企业级 |

**推荐：text2vec-base-chinese**
- 理由：中文效果好、可本地部署、无 API 成本

---

## 6. Agent 工作流设计

### 6.1 当前 Agent 架构

当前项目使用 ReAct（Reasoning + Acting）模式：
- AI 推理 → 选择工具 → 执行 → 观察结果 → 继续推理
- 9 个工具函数（排盘、五行、格局、神煞等）

### 6.2 增强后的 Agent 架构

```
用户提问
    ↓
意图识别（分析用户需求类型）
    ↓
┌─────────────────────────────────────────────┐
│  多 Agent 协作：                              │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 排盘Agent │  │ 命理Agent │  │ 古籍Agent │  │
│  │ (计算)    │  │ (分析)    │  │ (知识)    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
│       └──────────────┼──────────────┘        │
│                      ↓                       │
│              知识融合 + 推理                   │
│                      ↓                       │
│              生成分析报告                      │
└─────────────────────────────────────────────┘
```

### 6.3 Agent 角色定义

**排盘Agent（Calculator）：**
- 职责：八字排盘、五行计算、格局判定
- 工具：现有 9 个工具函数
- 输出：结构化八字数据

**命理Agent（Analyst）：**
- 职责：综合分析、运势预测、建议生成
- 工具：流年分析、大运分析、神煞查询
- 输出：命理分析报告

**古籍Agent（Scholar）：**
- 职责：古籍知识检索、引经据典、白话翻译
- 工具：`query_classical_text`、RAG 检索
- 输出：古籍引文 + 解读

### 6.4 工作流编排

**单轮分析流程：**
```python
async def analyze_bazi(user_input):
    # 1. 排盘Agent：计算八字
    chart = await calculator_agent.calculate(user_input)
    
    # 2. 古籍Agent：检索相关知识
    knowledge = await scholar_agent.retrieve(chart)
    
    # 3. 命理Agent：综合分析
    analysis = await analyst_agent.analyze(chart, knowledge)
    
    # 4. 生成报告
    return generate_report(chart, knowledge, analysis)
```

**多轮对话流程：**
```python
async def chat_stream(message, history, chart_data):
    # 1. 意图识别
    intent = classify_intent(message)
    
    # 2. 根据意图选择Agent
    if intent == "calculation":
        response = await calculator_agent.process(message)
    elif intent == "analysis":
        # 需要古籍知识
        knowledge = await scholar_agent.retrieve(chart_data, message)
        response = await analyst_agent.process(message, knowledge)
    elif intent == "knowledge":
        response = await scholar_agent.process(message)
    
    # 3. 流式输出
    return stream_response(response)
```

### 6.5 新增工具函数

**古籍查询工具：**
```python
def query_classical_text(
    source: str,       # 古籍名
    category: str,     # 分类
    key: str,          # 索引键
    query: str = ""    # 关键词
) -> Dict[str, Any]:
    """查询古籍内容，返回结构化数据"""
```

**RAG 检索工具：**
```python
def rag_retrieve(
    query: str,                    # 用户问题
    chart_data: Dict[str, Any],    # 八字数据
    top_k: int = 5                 # 返回条目数
) -> List[Dict[str, Any]]:
    """基于八字特征的RAG检索"""
```

**知识融合工具：**
```python
def fuse_knowledge(
    chart_data: Dict[str, Any],      # 八字数据
    classical_texts: List[Dict],      # 古籍条目
    user_question: str                # 用户问题
) -> str:
    """融合古籍知识和八字数据，生成上下文"""
```

### 6.6 Prompt 工程

**系统提示词增强：**
```
你是玄冥，一位精通命理的AI助手。

## 知识来源
你拥有以下古籍知识：
- 《穷通宝鉴》：调候用神
- 《滴天髓》：十干体性、理法
- 《子平真诠》：格局论法
- 《三命通会》：日柱论命

## 分析原则
1. 引经据典：分析时引用古籍原文
2. 白话解读：用现代语言解释古籍含义
3. 实际应用：结合用户八字给出具体建议
4. 客观中立：不夸大、不恐吓

## 工具使用
- 使用 query_classical_text 查询古籍
- 使用 rag_retrieve 检索相关知识
- 使用现有工具计算八字数据
```

---

## 7. 集成方案

### 7.1 后端改造

**新增文件：**
- `data/text_service.py` — 统一古籍查询服务
- `data/rag_service.py` — RAG 检索服务
- `agent/scholar_agent.py` — 古籍Agent

**修改文件：**
- `prompts/ancient_texts.py` — 从 JSON 加载而非硬编码
- `tools/bazi_tools.py` — 新增古籍查询和 RAG 工具
- `agent/react_agent.py` — 增强工作流编排
- `prompts/system_prompts.py` — 增强系统提示词
- `backend/requirements.txt` — 新增依赖（chromadb, sentence-transformers）

**向后兼容：**
- 现有 API 接口不变
- 现有工具函数保持，新增工具函数

### 7.2 RAG 服务实现

```python
# data/rag_service.py
import chromadb
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self, db_path="data/chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.model = SentenceTransformer("shibing624/text2vec-base-chinese")
        
        # 创建集合
        self.collection = self.client.get_or_create_collection(
            name="classical_texts",
            metadata={"hnsw:space": "cosine"}
        )
    
    def index_texts(self, texts: List[Dict]):
        """索引古籍条目"""
        documents = []
        metadatas = []
        ids = []
        
        for text in texts:
            # 组合字段作为文档
            doc = f"{text['原文']} {text.get('白话', '')} {text.get('应用', '')}"
            documents.append(doc)
            metadatas.append({
                "source": text["source"],
                "category": text["category"],
                "key": text["key"]
            })
            ids.append(f"{text['source']}_{text['key']}")
        
        # 批量添加
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def retrieve(self, query: str, chart_data: Dict, top_k: int = 5) -> List[Dict]:
        """基于八字特征的RAG检索"""
        # 构建查询
        query_text = self._build_query(query, chart_data)
        
        # 向量检索
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
        
        return self._format_results(results)
    
    def _build_query(self, query: str, chart_data: Dict) -> str:
        """构建查询文本"""
        day_master = chart_data.get("day_master", "")
        month_zhi = chart_data.get("month_zhi", "")
        geju = chart_data.get("geju", "")
        
        return f"{day_master}日主 {month_zhi}月 {geju} {query}"
```

### 7.3 古籍Agent实现

```python
# agent/scholar_agent.py
from typing import Dict, Any, List

class ScholarAgent:
    """古籍知识Agent"""
    
    def __init__(self, text_service, rag_service):
        self.text_service = text_service
        self.rag_service = rag_service
    
    async def retrieve(self, chart_data: Dict, question: str) -> Dict[str, Any]:
        """检索相关古籍知识"""
        # 1. 精确匹配
        exact_matches = self._exact_match(chart_data)
        
        # 2. RAG 语义检索
        rag_results = self.rag_service.retrieve(question, chart_data)
        
        # 3. 融合结果
        return self._fuse_results(exact_matches, rag_results)
    
    def _exact_match(self, chart_data: Dict) -> List[Dict]:
        """精确匹配"""
        results = []
        
        # 穷通宝鉴：日主 + 月令
        day_master = chart_data.get("day_master", "")
        month_zhi = chart_data.get("month_zhi", "")
        qiongtong = self.text_service.query("穷通宝鉴", day_master, month_zhi)
        if qiongtong:
            results.append(qiongtong)
        
        # 子平真诠：格局
        geju = chart_data.get("geju", "")
        ziping = self.text_service.query("子平真诠", geju, "")
        if ziping:
            results.append(ziping)
        
        # 滴天髓：日主
        disitian = self.text_service.query("滴天髓", "十干体性", day_master)
        if disitian:
            results.append(disitian)
        
        return results
    
    def _fuse_results(self, exact: List, rag: List) -> Dict:
        """融合结果"""
        # 去重
        seen = set()
        fused = []
        
        for item in exact + rag:
            key = f"{item['source']}_{item['key']}"
            if key not in seen:
                seen.add(key)
                fused.append(item)
        
        # 按相关性排序
        fused.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return {
            "items": fused[:10],  # 最多返回10条
            "count": len(fused)
        }
```

### 7.4 AI 查询工具

**新增工具：`query_classical_text`**

```python
def query_classical_text(
    source: str,      # 古籍名（滴天髓/子平真诠/三命通会等）
    category: str,    # 分类（十干体性/格局/日柱等）
    key: str,         # 索引键（日主/格局名/日柱等）
    query: str = ""   # 关键词搜索（可选）
) -> Dict[str, Any]:
    """
    查询古籍内容。
    返回结构化 JSON，包含原文、出处、标签等。
    """
```

**新增工具：`rag_retrieve`**

```python
def rag_retrieve(
    query: str,                    # 用户问题
    chart_data: Dict[str, Any],    # 八字数据
    top_k: int = 5                 # 返回条目数
) -> List[Dict[str, Any]]:
    """
    基于八字特征的RAG检索。
    自动提取日主、月令、格局等特征进行检索。
    """
```

### 7.5 前端展示

**古籍搜索页面增强：**
- 按古籍分类筛选
- 按日主/格局/十神筛选
- 原文 + 白话对照显示（白话由 AI 实时生成）

**聊天界面增强：**
- 显示 AI 引用的古籍来源
- 支点击查看古籍原文
- 高亮显示关键引文

---

## 8. 质量控制

### 6.1 数据来源标注

每条数据必须标注来源：
- 来自开源项目：标注项目 URL 和许可证
- 来自网站爬取：标注 URL 和爬取日期
- AI 生成：标注 "AI 生成 + 人工校验"

### 6.2 人工校验

- 抽样校验 10% 数据
- 重点校验：十干体性、格局成格/破格条件
- 校验方法：与权威古籍版本对照

### 6.3 测试验证

- 使用 MingLi-Bench 测试 AI 命理能力
- 对比集成前后的测试成绩
- 目标：准确率提升 5% 以上

---

## 9. 实施计划

### Phase 1：调研与数据收集（1-2 天）

1. GitHub 搜索相关项目
2. 评估并 clone 高质量项目
3. 从 ctext.org API 获取古籍原文
4. 整理数据为统一 JSON 格式

### Phase 2：数据结构化（1 天）

1. 设计 JSON Schema
2. 转换现有 Python dict 为 JSON
3. 整理新收集的数据
4. 人工校验关键数据

### Phase 3：RAG 基础设施（1-2 天）

1. 安装 ChromaDB + sentence-transformers
2. 实现 `data/rag_service.py`
3. 索引所有古籍条目
4. 测试检索效果

### Phase 4：Agent 工作流（1-2 天）

1. 实现 `agent/scholar_agent.py`
2. 增强 `agent/react_agent.py` 工作流
3. 新增古籍查询和 RAG 工具
4. 增强系统提示词

### Phase 5：后端集成（1 天）

1. 新增 `data/text_service.py`
2. 修改 `prompts/ancient_texts.py` 从 JSON 加载
3. 集成 RAG 服务到 API
4. 测试后端功能

### Phase 6：前端增强（1 天）

1. 增强古籍搜索页面
2. 添加分类筛选
3. 聊天界面显示古籍引用
4. 测试前端功能

### Phase 7：验证与优化（0.5 天）

1. 运行 MingLi-Bench 测试
2. 对比集成前后成绩
3. 优化检索性能
4. 调整 Prompt 效果

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 开源项目数据质量差 | 古籍内容不准确 | 人工校验 + 多源交叉验证 |
| ctext.org API 限流 | 数据获取慢 | 缓存 + 限速请求 |
| 版权问题 | 法律风险 | 仅使用公开 API + 开源项目数据 |
| JSON 文件过大 | 加载慢 | 分文件存储 + 懒加载 |
| AI 生成内容不准确 | 命理分析错误 | 人工校验 + 标注来源 |
| RAG 检索不准 | 古籍引用错误 | 混合检索 + 人工校验 |
| Embedding 模型效果差 | 语义搜索不准 | 多模型对比 + 微调 |
| Agent 工作流复杂 | 调试困难 | 日志追踪 + 单元测试 |

### 10.1 新增依赖

```txt
# RAG 相关
chromadb>=0.4.0
sentence-transformers>=2.2.0

# 可选：更好的中文 embedding
# text2vec>=1.0.0
```

---

## 11. 附录

### 9.1 现有古籍内容清单

**穷通宝鉴（完整）：**
- 10 天干 × 4 季节 = 40 条
- 每条包含：用神、原文、白话

**滴天髓（部分）：**
- 十干体性：甲/乙/丙/丁（4 条）
- 通用理法：通神论_天干/地支、情通论、流通论、日主衰旺论、月令提纲论、用神论、配合论、生克制化_总论、合化论（10 条）
- 缺失：戊/己/庚/辛/壬/癸 六条十干体性

**子平真诠（部分）：**
- 基本格局：正官格/七杀格/正财格/偏财格/食神格/伤官格/正印格/偏印格（8 条）
- 缺失：特殊格局（从格/化格/专旺格/建禄格/月刃格）

### 9.2 参考资源

- `docs/RESOURCES.md` — 已调研的 18 个开源资源
- `chinese-poetry/chinese-poetry` — 数据组织方式参考
- `ctext.org` API — 古籍原文获取
- `MingLi-Bench` — AI 命理能力评测基准

---

## 12. 修订记录

| 版本 | 日期 | 修订内容 |
|------|------|----------|
| 1.0 | 2026-05-01 | 初始版本 |
| 1.1 | 2026-05-01 | 新增 RAG 检索增强设计、Agent 工作流设计、ChromaDB 向量数据库方案 |
