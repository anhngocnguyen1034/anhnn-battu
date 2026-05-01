# RAG古籍检索实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现RAG古籍检索系统，支持ChromaDB向量检索和精确匹配混合查询

**Architecture:**
- 使用ChromaDB作为向量数据库，text2vec-base-chinese作为embedding模型
- 支持精确匹配和语义搜索的混合检索
- 通过tools/bazi_tools.py暴露给ReAct Agent使用

**Tech Stack:** chromadb, sentence-transformers, text2vec-base-chinese

---

## 文件结构

```
data/
  classical_texts/          # 已存在：5个古籍JSON文件
  text_service.py          # 新增：统一古籍查询服务
  rag_service.py           # 新增：RAG检索服务
  chroma_db/                # 新增：ChromaDB持久化存储

agent/
  scholar_agent.py         # 新增：古籍Agent

tools/
  bazi_tools.py           # 修改：新增rag_retrieve工具

backend/
  requirements.txt         # 修改：新增chromadb依赖
```

---

## Task 1: 安装依赖并创建目录

**Files:**
- Modify: `backend/requirements.txt`
- Create: `data/text_service.py`
- Create: `data/rag_service.py`
- Create: `agent/scholar_agent.py`

- [ ] **Step 1: 添加RAG依赖到requirements.txt**

```txt
# RAG相关
chromadb>=0.4.0
sentence-transformers>=2.2.0
```

- [ ] **Step 2: 安装依赖**

Run: `pip install chromadb sentence-transformers`
Expected: Successfully installed chromadb, sentence-transformers

- [ ] **Step 3: 创建数据目录**

Run: `mkdir -p data/chroma_db`
Expected: 目录创建成功

- [ ] **Step 4: 提交**

```bash
git add backend/requirements.txt
git commit -m "chore: add RAG dependencies (chromadb, sentence-transformers)"
```

---

## Task 2: 实现 text_service.py

**Files:**
- Create: `data/text_service.py`

- [ ] **Step 1: 编写text_service.py**

```python
# -*- coding: utf-8 -*-
"""统一古籍查询服务 - 从JSON加载古籍数据"""
import json
import os
from typing import Any, Dict, List

_DATA_DIR = os.path.join(os.path.dirname(__file__), "classical_texts")

def _load_json(filename: str) -> Dict[str, Any]:
    """加载JSON文件"""
    path = os.path.join(_DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

class TextService:
    """古籍查询服务"""
    
    def __init__(self):
        self._data_cache = {}
        self._load_all_texts()
    
    def _load_all_texts(self):
        """加载所有古籍JSON"""
        texts = ["qiongtong_baojian", "di_tian_sui", "ziping_zhenquan", 
                "sanming_tonghui", "yuanhai_ziping"]
        for name in texts:
            self._data_cache[name] = _load_json(f"{name}.json")
    
    def query(self, source: str, category: str = "", key: str = "") -> List[Dict]:
        """
        查询古籍内容
        
        Args:
            source: 古籍名（穷通宝鉴/滴天髓/子平真诠/三命通会/渊海子平）
            category: 分类筛选
            key: 键名筛选
        
        Returns:
            匹配的古籍条目列表
        """
        data = self._data_cache.get(source, {})
        if not data:
            return []
        
        entries = data.get("entries", {})
        results = []
        
        for entry_key, entry in entries.items():
            # 分类筛选
            if category and entry.get("category", "") != category:
                continue
            # 键名筛选
            if key and key not in entry_key and key not in entry.get("key", ""):
                continue
            
            results.append({
                "key": entry_key,
                "source": source,
                **entry
            })
        
        return results
    
    def get_all_entries(self, source: str) -> List[Dict]:
        """获取某古籍的所有条目"""
        data = self._data_cache.get(source, {})
        entries = data.get("entries", {})
        return [
            {"key": k, "source": source, **v}
            for k, v in entries.items()
        ]
    
    def get_index(self) -> List[Dict]:
        """获取所有古籍索引"""
        index_path = os.path.join(_DATA_DIR, "index.json")
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f).get("texts", [])
        except:
            return []

# 全局单例
text_service = TextService()
```

- [ ] **Step 2: 测试text_service**

Run:
```python
from data.text_service import text_service
entries = text_service.get_all_entries("滴天髓")
print(f"滴天髓条目数: {len(entries)}")
results = text_service.query("穷通宝鉴", category="调候用神", key="甲")
print(f"穷通宝鉴甲日查询: {len(results)}条")
```
Expected: 滴天髓条目数: 19, 穷通宝鉴甲日查询: 1条

- [ ] **Step 3: 提交**

```bash
git add data/text_service.py
git commit -m "feat: add TextService for unified classical text query"
```

---

## Task 3: 实现 rag_service.py

**Files:**
- Create: `data/rag_service.py`

- [ ] **Step 1: 编写rag_service.py**

```python
# -*- coding: utf-8 -*-
"""RAG检索服务 - 基于ChromaDB的向量检索"""
import os
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from .text_service import text_service

class RAGService:
    """RAG检索服务"""
    
    def __init__(self, db_path: str = "data/chroma_db"):
        self.db_path = db_path
        self._client = None
        self._collection = None
        self._model = None
        self._initialized = False
    
    def initialize(self):
        """初始化ChromaDB和embedding模型"""
        if not CHROMA_AVAILABLE:
            raise RuntimeError("chromadb or sentence-transformers not installed")
        
        if self._initialized:
            return
        
        # 初始化ChromaDB
        os.makedirs(self.db_path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.db_path)
        
        # 创建或获取集合
        self._collection = self._client.get_or_create_collection(
            name="classical_texts",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 初始化embedding模型
        self._model = SentenceTransformer("shibing624/text2vec-base-chinese")
        
        self._initialized = True
    
    def index_all_texts(self):
        """索引所有古籍条目"""
        if not self._initialized:
            self.initialize()
        
        # 清空现有索引
        try:
            self._collection.delete(where={})
        except:
            pass
        
        # 遍历所有古籍
        sources = ["穷通宝鉴", "滴天髓", "子平真诠", "三命通会", "渊海子平"]
        documents = []
        metadatas = []
        ids = []
        
        for source in sources:
            entries = text_service.get_all_entries(source)
            for entry in entries:
                # 组合文档内容
                doc = self._build_document(entry)
                documents.append(doc)
                metadatas.append({
                    "source": source,
                    "category": entry.get("category", ""),
                    "key": entry.get("key", ""),
                    "key_field": entry.get("key", "")
                })
                ids.append(f"{source}_{entry.get('key', entry.get('key_field', ''))}")
        
        # 批量添加
        if documents:
            self._collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        return len(documents)
    
    def _build_document(self, entry: Dict) -> str:
        """构建检索文档"""
        parts = [
            entry.get("原文", ""),
            entry.get("解析", ""),
            entry.get("白话", ""),
            entry.get("喜忌", ""),
            entry.get("出处", "")
        ]
        return " ".join(filter(None, parts))
    
    def retrieve(self, query: str, chart_data: Optional[Dict] = None, top_k: int = 5) -> List[Dict]:
        """
        检索相关古籍
        
        Args:
            query: 用户问题
            chart_data: 八字数据（用于构建查询上下文）
            top_k: 返回条数
        
        Returns:
            检索结果列表
        """
        if not self._initialized:
            self.initialize()
        
        # 构建查询文本
        query_text = self._build_query_text(query, chart_data)
        
        # 向量检索
        results = self._collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
        
        # 格式化结果
        return self._format_results(results)
    
    def _build_query_text(self, query: str, chart_data: Optional[Dict] = None) -> str:
        """构建查询文本"""
        parts = [query]
        
        if chart_data:
            day_master = chart_data.get("day_master", "")
            month_zhi = chart_data.get("month_zhi", "")
            geju = chart_data.get("geju", "")
            
            if day_master:
                parts.append(f"{day_master}日主")
            if month_zhi:
                parts.append(f"{month_zhi}月")
            if geju:
                parts.append(geju)
        
        return " ".join(parts)
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """格式化检索结果"""
        formatted = []
        
        if not results.get("documents"):
            return formatted
        
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 0
            
            formatted.append({
                "source": metadata.get("source", ""),
                "category": metadata.get("category", ""),
                "key": metadata.get("key", ""),
                "content": doc,
                "score": 1 - distance,  # 转换为相似度
                "distance": distance
            })
        
        return formatted
    
    def search(self, query: str, source: str = "", category: str = "", top_k: int = 5) -> List[Dict]:
        """
        搜索古籍（带过滤条件）
        
        Args:
            query: 查询文本
            source: 古籍名过滤
            category: 分类过滤
            top_k: 返回条数
        
        Returns:
            检索结果
        """
        if not self._initialized:
            self.initialize()
        
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k * 2,  # 多取一些以便过滤
            where={"source": source} if source else None,
            where_document={"$contains": category} if category else None
        )
        
        return self._format_results(results)

# 全局单例
rag_service = RAGService()
```

- [ ] **Step 2: 测试rag_service初始化**

Run:
```python
from data.rag_service import rag_service
try:
    rag_service.initialize()
    print("RAG服务初始化成功")
except Exception as e:
    print(f"需要安装依赖: {e}")
```
Expected: RAG服务初始化成功 或 需要安装依赖提示

- [ ] **Step 3: 提交**

```bash
git add data/rag_service.py
git commit -m "feat: add RAGService with ChromaDB vector search"
```

---

## Task 4: 实现 scholar_agent.py

**Files:**
- Create: `agent/scholar_agent.py`

- [ ] **Step 1: 编写scholar_agent.py**

```python
# -*- coding: utf-8 -*-
"""古籍Agent - 负责古籍知识检索和融合"""
import json
from typing import Any, Dict, List, Optional

from data.text_service import text_service
from data.rag_service import rag_service

class ScholarAgent:
    """古籍知识Agent"""
    
    def __init__(self):
        self.text_service = text_service
        self.rag_service = rag_service
    
    def retrieve_knowledge(self, chart_data: Dict[str, Any], question: str = "") -> str:
        """
        检索相关古籍知识
        
        Args:
            chart_data: 八字数据（含day_master, pillars等）
            question: 用户问题（用于RAG检索）
        
        Returns:
            JSON格式的检索结果
        """
        results = {
            "exact_matches": [],
            "rag_matches": [],
            "fused_results": []
        }
        
        # 1. 精确匹配
        exact = self._exact_match(chart_data)
        results["exact_matches"] = exact
        
        # 2. RAG语义检索
        if question:
            try:
                rag_results = self.rag_service.retrieve(question, chart_data, top_k=5)
                results["rag_matches"] = rag_results
            except Exception as e:
                results["rag_matches"] = [{"error": str(e)}]
        
        # 3. 融合结果
        results["fused_results"] = self._fuse_results(exact, results["rag_matches"])
        
        return json.dumps(results, ensure_ascii=False)
    
    def _exact_match(self, chart_data: Dict) -> List[Dict]:
        """精确匹配古籍"""
        results = []
        day_master = chart_data.get("day_master", "")
        pillars = chart_data.get("pillars", [])
        
        # 穷通宝鉴：日主 + 月令
        if day_master and len(pillars) > 1:
            month_zhi = pillars[1][1] if len(pillars[1]) >= 2 else ""
            if month_zhi:
                from prompts.ancient_texts import get_qiongtong_for_tool
                qiongtong = get_qiongtong_for_tool(day_master, month_zhi)
                if qiongtong:
                    results.append({
                        "source": "穷通宝鉴",
                        "type": "exact",
                        "data": qiongtong
                    })
        
        # 滴天髓：日主
        if day_master:
            from prompts.ancient_texts import get_disitian_for_tool
            disitian = get_disitian_for_tool(day_master, "")
            if disitian:
                results.append({
                    "source": "滴天髓",
                    "type": "exact",
                    "data": disitian
                })
        
        # 子平真诠：格局
        geju = chart_data.get("geju", "")
        if geju:
            from prompts.ancient_texts import get_ziping_for_tool
            month_zhi = pillars[1][1] if len(pillars) > 1 else ""
            ziping = get_ziping_for_tool(day_master, month_zhi)
            if ziping:
                results.append({
                    "source": "子平真诠",
                    "type": "exact",
                    "data": ziping
                })
        
        return results
    
    def _fuse_results(self, exact: List, rag: List) -> List[Dict]:
        """融合精确匹配和RAG结果"""
        seen = {}
        fused = []
        
        # 先加入精确匹配（高优先级）
        for item in exact:
            source = item.get("source", "")
            key = f"{source}_{item.get('type', 'exact')}"
            if key not in seen:
                seen[key] = True
                fused.append({
                    "source": source,
                    "type": "exact",
                    "relevance": 1.0,
                    "data": item.get("data", {})
                })
        
        # 加入RAG结果
        for item in rag:
            if item.get("error"):
                continue
            source = item.get("source", "")
            key_val = item.get("key", "")
            key = f"{source}_{key_val}"
            if key not in seen:
                seen[key] = True
                fused.append({
                    "source": source,
                    "type": "rag",
                    "relevance": item.get("score", 0),
                    "key": key_val,
                    "content": item.get("content", "")[:200]
                })
        
        return fused[:10]  # 最多返回10条

# 全局单例
scholar_agent = ScholarAgent()
```

- [ ] **Step 2: 测试scholar_agent**

Run:
```python
from agent.scholar_agent import scholar_agent
chart_data = {"day_master": "甲", "pillars": [["甲子", "甲寅"], ["甲辰", "甲申"]]}
result = scholar_agent.retrieve_knowledge(chart_data, "甲日主寅月格局分析")
print(f"检索结果: {result[:200]}...")
```
Expected: 返回JSON格式的检索结果

- [ ] **Step 3: 提交**

```bash
git add agent/scholar_agent.py
git commit -m "feat: add ScholarAgent for classical text retrieval"
```

---

## Task 5: 新增rag_retrieve工具到bazi_tools.py

**Files:**
- Modify: `tools/bazi_tools.py`

- [ ] **Step 1: 添加rag_retrieve到imports**

```python
from data.rag_service import rag_service
from agent.scholar_agent import scholar_agent
```

- [ ] **Step 2: 添加rag_retrieve函数**

```python
def rag_retrieve(bazi_data: Dict[str, Any], query: str = "", top_k: int = 5) -> str:
    """
    基于RAG的古籍检索。根据八字数据和用户问题检索相关古籍条目。
    
    Args:
        bazi_data: 八字命盘数据
        query: 用户问题（可选，用于语义检索）
        top_k: 返回结果数量
    
    Returns:
        JSON格式的检索结果
    """
    try:
        results = scholar_agent.retrieve_knowledge(bazi_data, query)
        return results
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

- [ ] **Step 3: 更新TOOL_SCHEMAS**

```python
{
    "type": "function",
    "function": {
        "name": "rag_retrieve",
        "description": "基于RAG的古籍检索。根据八字数据和用户问题检索穷通宝鉴、滴天髓、子平真诠、三命通会等相关古籍条目，支持精确匹配和语义搜索。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "用户问题（可选）"},
                "top_k": {"type": "integer", "description": "返回结果数量，默认5", "default": 5}
            },
        },
    },
},
```

- [ ] **Step 4: 更新TOOL_REGISTRY**

```python
TOOL_REGISTRY = {
    ...
    "rag_retrieve": rag_retrieve,
    ...
}
```

- [ ] **Step 5: 更新dispatch_tool**

```python
if name == "rag_retrieve":
    return fn(bazi_data, arguments.get("query", ""), arguments.get("top_k", 5))
```

- [ ] **Step 6: 测试rag_retrieve工具**

Run:
```python
from tools.bazi_tools import dispatch_tool
result = dispatch_tool("rag_retrieve", {"query": "甲木特性", "top_k": 5}, {"day_master": "甲"})
print(f"rag_retrieve结果: {result[:300]}...")
```
Expected: 返回JSON格式的检索结果

- [ ] **Step 7: 提交**

```bash
git add tools/bazi_tools.py
git commit -m "feat: add rag_retrieve tool to bazi_tools"
```

---

## Task 6: 更新系统提示词

**Files:**
- Modify: `prompts/system_prompts.py`

- [ ] **Step 1: 更新TOOL_GUIDANCE中的RAG说明**

在TOOL_GUIDANCE中添加：

```python
**古籍查询工具**：
...
- `rag_retrieve`：基于RAG的古籍检索，返回精确匹配和语义搜索结果。当用户问题涉及多个古籍或需要广泛检索时使用。
...
```

- [ ] **Step 2: 提交**

```bash
git add prompts/system_prompts.py
git commit -m "feat: update system prompts with rag_retrieve tool"
```

---

## Task 7: 验证完整流程

- [ ] **Step 1: 验证导入**

Run:
```python
from data.text_service import text_service
from data.rag_service import rag_service
from agent.scholar_agent import scholar_agent
from tools.bazi_tools import TOOL_REGISTRY

print(f"TOOL_REGISTRY包含: {list(TOOL_REGISTRY.keys())}")
print(f"古籍数量: {len(text_service._data_cache)}")
```
Expected: 显示工具列表和古籍数量

- [ ] **Step 2: 验证API Key配置**

Run:
```python
from backend.config import settings
print(f"API Key已配置: {bool(settings.OPENAI_API_KEY)}")
print(f"Base URL: {settings.OPENAI_BASE_URL}")
```
Expected: API Key已配置=True, URL为MiniMax地址

- [ ] **Step 3: 提交所有更改**

```bash
git add -A
git commit -m "feat: complete RAG system implementation
- Add TextService for unified classical text query
- Add RAGService with ChromaDB vector search
- Add ScholarAgent for knowledge retrieval
- Add rag_retrieve tool to bazi_tools
- Update system prompts with RAG guidance
- Configure MiniMax API settings"
git push origin main
```

---

## 自检清单

**Spec覆盖检查:**
- [x] RAG检索增强生成设计（第5章）→ 实现rag_service.py
- [x] Agent工作流设计（第6章）→ 实现scholar_agent.py
- [x] 工具函数新增（第6.5章）→ 实现rag_retrieve工具
- [x] 集成方案（第7章）→ 修改bazi_tools.py + prompts

**占位符检查:**
- [x] 无TBD/TODO
- [x] 所有函数有完整实现
- [x] 所有步骤有具体代码

**类型一致性检查:**
- [x] text_service.query() 返回List[Dict]
- [x] rag_service.retrieve() 返回List[Dict]
- [x] scholar_agent.retrieve_knowledge() 返回str(JSON)
- [x] rag_retrieve工具参数与TOOL_SCHEMAS一致

---

## 实际实现状态

### 完成状态：✅ 已完成 (2026-05-01)

| Task | 状态 | 提交 |
|------|------|------|
| Task 1: 安装依赖 | ✅ 完成 | 02b274a |
| Task 2: text_service.py | ✅ 完成 | da8a535 |
| Task 3: rag_service.py | ✅ 完成 | a54d1cc |
| Task 4: scholar_agent.py | ✅ 完成 | b21faf9 |
| Task 5: rag_retrieve 工具 | ✅ 完成 | 5745999, c027c11 |
| Task 6: 系统提示词 | ✅ 完成 | d9bad3a |
| Task 7: 验证推送 | ✅ 完成 | - |

### 代码质量修复记录

| 问题 | 修复提交 | 状态 |
|------|---------|------|
| 硬编码路径 | 5ab957c | ✅ |
| top_k 参数忽略 | 50f61b0, c027c11 | ✅ |
| bare except 块 | 78d2d5c | ✅ |
| TDD 单元测试 | fe954b3 | ✅ |

### 单元测试覆盖

- tests/test_text_service.py - 3 tests
- tests/test_scholar_agent.py - 2 tests
- tests/test_rag_retrieve_tool.py - 2 tests

### 新增文件

```
data/
  text_service.py    # 统一古籍查询服务
  rag_service.py     # RAG 检索服务 (ChromaDB)

agent/
  scholar_agent.py   # 古籍知识 Agent

tests/
  test_text_service.py
  test_scholar_agent.py
  test_rag_retrieve_tool.py
```

### 工具清单

TOOL_REGISTRY 包含 14 个工具：
1. get_annual_fortune
2. get_dayun_stage
3. analyze_wuxing_balance
4. query_xing_chong_he_hai
5. explain_shensha
6. fact_check_ganzhi
7. query_qiongtong_guidance
8. query_disitian_guidance
9. query_ziping_guidance
10. query_sanming_guidance
11. query_classical_text
12. calculate_wuxing_power
13. analyze_geju
14. rag_retrieve ⭐ (新增)

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-01-rag-implementation-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**