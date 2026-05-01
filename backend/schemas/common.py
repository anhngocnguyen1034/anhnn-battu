# -*- coding: utf-8 -*-
"""
Shared Pydantic models used across multiple API routers.

These mirror the data structures produced by the engine, tools, and agent
modules so that every endpoint returns consistently typed, validated JSON.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Bazi chart data
# ---------------------------------------------------------------------------


class XingChongData(BaseModel):
    """Inter-branch relationship data (clash, combination, punishment, etc.)."""

    chong: List[str] = Field(default_factory=list, alias="冲")
    he: List[str] = Field(default_factory=list, alias="合")
    xing: List[str] = Field(default_factory=list, alias="刑")
    hai: List[str] = Field(default_factory=list, alias="害")
    po: List[str] = Field(default_factory=list, alias="破")
    san_he: List[str] = Field(default_factory=list, alias="三合")
    san_hui: List[str] = Field(default_factory=list, alias="三会")
    ban_san_he: List[str] = Field(default_factory=list, alias="半三合")

    model_config = {"populate_by_name": True}


class DayunItem(BaseModel):
    """A single major-luck period (da yun)."""

    start_age: int = 0
    start_year: int = 0
    ganzhi: str = ""


class BaziChartData(BaseModel):
    """
    Full bazi chart payload returned by the engine.

    Field names match ``calculate_professional_bazi()`` output keys exactly
    so the service layer can pass them through without mapping.
    """

    gender: str = ""
    pillars: List[str] = Field(default_factory=list, description="四柱干支 [年, 月, 日, 时]")
    tg_gan: List[str] = Field(default_factory=list, description="天干十神")
    tg_zhi: List[str] = Field(default_factory=list, description="地支藏干十神")
    nayin: List[str] = Field(default_factory=list, description="纳音")
    shensha: List[str] = Field(default_factory=list, description="神煞列表")
    shensha_detail: Optional[Dict[Any, Any]] = Field(default=None, description="神煞详细信息")
    wuxing: Dict[str, int] = Field(default_factory=dict, description="五行力量（基础计数）")
    dayun: List[DayunItem] = Field(default_factory=list, description="大运列表")
    minggong: str = ""
    taiyuan: str = ""
    taixi: str = ""
    shengong: str = ""
    dishi: List[str] = Field(default_factory=list, description="十二长生（地势）")
    xunkong: List[str] = Field(default_factory=list, description="旬空")
    xingchong: Optional[XingChongData] = Field(default=None, description="刑冲合害")
    wuxing_str: str = ""
    day_master: str = Field(default="", description="日主天干")


class WuxingPowerData(BaseModel):
    """Refined wuxing power analysis (from wuxing_calculator)."""

    power: Dict[str, float] = Field(default_factory=dict)
    strong: List[str] = Field(default_factory=list)
    weak: List[str] = Field(default_factory=list)
    balanced: bool = False
    context: str = ""


class GejuData(BaseModel):
    """Pattern / structure analysis result (from geju_analyzer)."""

    geju_type: str = Field(default="", alias="格局类型")
    geju_name: str = Field(default="", alias="格局名称")
    month_zhi: str = Field(default="", alias="月令")
    month_main_qi: str = Field(default="", alias="月令主气")
    is_tougan: bool = Field(default=False, alias="月干透干")
    tougan_position: str = Field(default="", alias="透干位置")
    strength: str = Field(default="", alias="日主强弱")
    dm_ratio: float = Field(default=0.0, alias="日主力量占比")
    context: str = ""

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Generic wrappers
# ---------------------------------------------------------------------------


class APIError(BaseModel):
    """Standard error envelope."""

    detail: str
    code: str = "INTERNAL_ERROR"
