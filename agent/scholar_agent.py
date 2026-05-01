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
