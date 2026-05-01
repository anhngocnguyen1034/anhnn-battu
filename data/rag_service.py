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
        except Exception as e:
            # Collection might be empty, log and continue
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