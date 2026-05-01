# -*- coding: utf-8 -*-
"""
GET /api/v1/texts — search classical bazi texts.

Provides keyword search across 穷通宝鉴, 滴天髓, and 子平真诠.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from backend.services.text_service import get_entry, search_texts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/texts", tags=["texts"])


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="Search classical texts",
    description=(
        "Search across the three classical reference books by keyword. "
        "Optionally filter by source name."
    ),
)
async def get_texts(
    query: str = Query(default="", description="搜索关键词（如 '甲', '伤官', '调候'）"),
    source: Optional[str] = Query(
        default=None,
        description="限定来源：'穷通宝鉴' / '滴天髓' / '子平真诠'",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="最大返回条数"),
) -> List[Dict[str, Any]]:
    """
    Search classical texts by keyword and optional source filter.

    Returns a list of matching entries, each containing ``source``, ``key``,
    and the entry's fields (原文, 白话, 用神, 应用, etc.).
    """
    return search_texts(query=query, source=source, limit=limit)


@router.get(
    "/{source}/{key}",
    response_model=Optional[Dict[str, Any]],
    summary="Get a single text entry",
    description="Retrieve a specific entry by source name and key.",
)
async def get_text_entry(source: str, key: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single classical text entry by source and key."""
    entry = get_entry(source, key)
    if entry is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"未找到来源 '{source}' 中键为 '{key}' 的条目",
        )
    return entry
