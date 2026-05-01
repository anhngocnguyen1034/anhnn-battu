# -*- coding: utf-8 -*-
"""
Request / response models for the /chart endpoint.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .common import BaziChartData, GejuData, WuxingPowerData


class ChartRequest(BaseModel):
    """POST /api/v1/chart — calculate a full bazi chart."""

    datetime_str: str = Field(
        ...,
        max_length=25,
        description="公历出生时间，格式 'YYYY-MM-DD HH:MM' 或 'YYYY-MM-DD HH:MM:SS'",
        examples=["1990-05-15 14:30"],
    )
    gender: str = Field(
        ...,
        description="性别：'乾造 (Male)' 或 '坤造 (Female)'",
        examples=["乾造 (Male)"],
    )

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("乾造 (Male)", "坤造 (Female)"):
            raise ValueError("gender must be '乾造 (Male)' or '坤造 (Female)'")
        return v


class ChartResponse(BaseModel):
    """Full bazi chart response including derived analyses."""

    chart: BaziChartData = Field(..., description="八字原局数据")
    wuxing_power: Optional[WuxingPowerData] = Field(
        default=None, description="五行力量精算（含藏干权重）"
    )
    geju: Optional[Dict[str, Any]] = Field(
        default=None, description="格局判定结果"
    )
