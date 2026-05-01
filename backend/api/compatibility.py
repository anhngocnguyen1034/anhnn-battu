# -*- coding: utf-8 -*-
"""
POST /api/v1/compatibility — compare two bazi charts.

A lightweight compatibility analysis based on day-master five-element
relationships and inter-chart branch interactions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.schemas.common import BaziChartData
from backend.services.bazi_service import calculate_chart

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compatibility", tags=["compatibility"])


# -- Request / Response models -------------------------------------------


class ChartInput(BaseModel):
    """Birth info for one party."""

    datetime_str: str = Field(
        ...,
        description="公历出生时间 'YYYY-MM-DD HH:MM'",
        examples=["1990-05-15 14:30"],
    )
    gender: str = Field(
        ...,
        description="性别：'乾造 (Male)' 或 '坤造 (Female)'",
    )

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("乾造 (Male)", "坤造 (Female)"):
            raise ValueError("gender must be '乾造 (Male)' or '坤造 (Female)'")
        return v


class CompatibilityRequest(BaseModel):
    """Compare two charts for compatibility."""

    person_a: ChartInput = Field(..., description="甲方出生信息")
    person_b: ChartInput = Field(..., description="乙方出生信息")


class CompatibilityResponse(BaseModel):
    """Compatibility analysis result."""

    person_a: BaziChartData
    person_b: BaziChartData
    day_master_relation: str = Field(description="日主五行关系描述")
    score: int = Field(description="综合匹配度评分 0-100")
    summary: str = Field(description="综合评语")
    details: List[str] = Field(default_factory=list, description="详细分析要点")


# -- Five-element relationship logic -------------------------------------

_GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_OVERCOME = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

_GAN_TO_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}


def _analyse_compatibility(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Perform a basic compatibility analysis between two charts.

    Logic:
      - Day-master five-element relationship (generate / overcome / same)
      - Branch clashes and combinations between the two charts
      - Produces a score 0-100 and human-readable summary.
    """
    dm_a = (chart_a.get("day_master") or "").strip()
    dm_b = (chart_b.get("day_master") or "").strip()
    wx_a = _GAN_TO_WUXING.get(dm_a, "")
    wx_b = _GAN_TO_WUXING.get(dm_b, "")

    details: List[str] = []
    score = 50  # baseline

    # -- Day-master relationship --
    if not wx_a or not wx_b:
        relation = "无法判断日主关系"
        details.append(relation)
    elif wx_a == wx_b:
        relation = f"日主同为{wx_a}，比和之象"
        details.append(relation)
        score += 10
    elif _GENERATE.get(wx_a) == wx_b:
        relation = f"{dm_a}({wx_a})生{dm_b}({wx_b})，甲方生助乙方"
        details.append(relation)
        score += 15
    elif _GENERATE.get(wx_b) == wx_a:
        relation = f"{dm_b}({wx_b})生{dm_a}({wx_a})，乙方生助甲方"
        details.append(relation)
        score += 15
    elif _OVERCOME.get(wx_a) == wx_b:
        relation = f"{dm_a}({wx_a})克{dm_b}({wx_b})，甲方克制乙方"
        details.append(relation)
        score -= 10
    elif _OVERCOME.get(wx_b) == wx_a:
        relation = f"{dm_b}({wx_b})克{dm_a}({wx_a})，乙方克制甲方"
        details.append(relation)
        score -= 10
    else:
        relation = "日主五行关系待细辨"
        details.append(relation)

    # -- Branch interactions between the two charts --
    pillars_a = chart_a.get("pillars") or []
    pillars_b = chart_b.get("pillars") or []
    zhi_a = [p[1] for p in pillars_a if len(p) >= 2]
    zhi_b = [p[1] for p in pillars_b if len(p) >= 2]

    _chong_map = {"子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥"}
    _he_map = {"子": "丑", "寅": "亥", "卯": "戌", "辰": "酉", "巳": "申", "午": "未"}

    clashes = []
    combos = []
    labels_a = ["年", "月", "日", "时"]
    labels_b = ["年", "月", "日", "时"]

    for i, za in enumerate(zhi_a):
        for j, zb in enumerate(zhi_b):
            if _chong_map.get(za) == zb or _chong_map.get(zb) == za:
                clashes.append(f"A-{labels_a[i]}({za}) 与 B-{labels_b[j]}({zb}) 相冲")
            if _he_map.get(za) == zb or _he_map.get(zb) == za:
                combos.append(f"A-{labels_a[i]}({za}) 与 B-{labels_b[j]}({zb}) 六合")

    if combos:
        details.append(f"地支六合: {', '.join(combos)}")
        score += len(combos) * 5
    if clashes:
        details.append(f"地支六冲: {', '.join(clashes)}")
        score -= len(clashes) * 5

    # -- Xingchong within each chart --
    xc_a = chart_a.get("xingchong") or {}
    xc_b = chart_b.get("xingchong") or {}
    for label, xc in [("甲方", xc_a), ("乙方", xc_b)]:
        he_list = xc.get("合", [])
        if he_list:
            details.append(f"{label}原局合多: {', '.join(he_list)}")
            score += 3

    # Clamp score
    score = max(0, min(100, score))

    # Build summary
    if score >= 75:
        summary = "日主配合良好，地支多合少冲，整体匹配度较高。"
    elif score >= 50:
        summary = "日主关系中性，地支互动有合有冲，整体尚可。"
    else:
        summary = "日主相克或地支冲多合少，需双方共同努力调和。"

    return {
        "day_master_relation": relation,
        "score": score,
        "summary": summary,
        "details": details,
    }


# -- Endpoint ------------------------------------------------------------


@router.post(
    "",
    response_model=CompatibilityResponse,
    summary="Compare two bazi charts",
    description="Calculate both charts and perform a basic compatibility analysis.",
)
async def post_compatibility(req: CompatibilityRequest) -> CompatibilityResponse:
    """Calculate and compare two bazi charts for compatibility."""
    try:
        result_a = calculate_chart(req.person_a.datetime_str, req.person_a.gender)
        result_b = calculate_chart(req.person_b.datetime_str, req.person_b.gender)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Compatibility calculation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="合婚计算内部错误") from exc

    analysis = _analyse_compatibility(result_a["chart"], result_b["chart"])

    return CompatibilityResponse(
        person_a=result_a["chart"],
        person_b=result_b["chart"],
        **analysis,
    )
