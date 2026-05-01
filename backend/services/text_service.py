# -*- coding: utf-8 -*-
"""
Text service — search and retrieve classical bazi texts.

Wraps the three reference books exposed by ``prompts.ancient_texts``:
  - ``QIONGTONG_BAOJIAN``  (穷通宝鉴)
  - ``DI_TIAN_SUI``         (滴天髓)
  - ``ZIPING_ZHENQUAN``     (子平真诠)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from prompts.ancient_texts import (
    DI_TIAN_SUI,
    QIONGTONG_BAOJIAN,
    ZIPING_ZHENQUAN,
)

logger = logging.getLogger(__name__)

# Source label -> data dict mapping
_SOURCES: Dict[str, Dict] = {
    "穷通宝鉴": QIONGTONG_BAOJIAN,
    "滴天髓": DI_TIAN_SUI,
    "子平真诠": ZIPING_ZHENQUAN,
}


def search_texts(
    query: str = "",
    source: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search classical texts by keyword across one or all sources.

    Matching is simple substring search on all string values in each entry.
    Results are capped at *limit* items.

    Args:
        query: Free-text search keyword (e.g. "甲", "伤官", "调候").
               If empty, returns all entries (up to *limit*).
        source: Filter to a single source name
                (``"穷通宝鉴"``, ``"滴天髓"``, or ``"子平真诠"``).
                ``None`` searches all three.
        limit: Maximum number of results to return.

    Returns:
        List of dicts, each containing ``source``, ``key``, and the
        matching entry's fields.
    """
    results: List[Dict[str, Any]] = []
    query_lower = query.strip().lower() if query else ""

    sources_to_search = {}
    if source:
        src = _SOURCES.get(source.strip())
        if src is None:
            return results
        sources_to_search[source.strip()] = src
    else:
        sources_to_search = _SOURCES

    for src_name, data_dict in sources_to_search.items():
        for key, entry in data_dict.items():
            if not isinstance(entry, dict):
                continue

            # If query is provided, check for substring match
            if query_lower:
                text_blob = " ".join(
                    str(v) for v in entry.values() if isinstance(v, str)
                ).lower()
                if query_lower not in text_blob and query_lower not in key.lower():
                    continue

            results.append({
                "source": src_name,
                "key": key,
                **entry,
            })

            if len(results) >= limit:
                return results

    return results


def get_entry(source: str, key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single entry by source name and key.

    Args:
        source: One of ``"穷通宝鉴"``, ``"滴天髓"``, ``"子平真诠"``.
        key: Entry key (e.g. ``"十干体性_甲"`` or ``"正官格"``).

    Returns:
        The entry dict, or ``None`` if not found.
    """
    data = _SOURCES.get(source.strip())
    if data is None:
        return None
    entry = data.get(key)
    if entry is None:
        return None
    if isinstance(entry, dict):
        return {"source": source, "key": key, **entry}
    return None
