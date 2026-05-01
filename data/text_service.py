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
        """加载所有古籍JSON（使用中文名作为key）"""
        # 中文名与JSON文件名的映射
        name_map = {
            "穷通宝鉴": "qiongtong_baojian",
            "滴天髓": "di_tian_sui",
            "子平真诠": "ziping_zhenquan",
            "三命通会": "sanming_tonghui",
            "渊海子平": "yuanhai_ziping"
        }
        for cn_name, filename in name_map.items():
            self._data_cache[cn_name] = _load_json(f"{filename}.json")

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
        except Exception:
            return []

# 全局单例
text_service = TextService()