# -*- coding: utf-8 -*-
"""
POST /api/v1/chart — calculate a full bazi chart.

Accepts a datetime string and gender, runs the engine + derived analyses,
and returns the complete chart payload.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.schemas.chart import ChartRequest, ChartResponse
from backend.services.bazi_service import calculate_chart

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chart", tags=["chart"])


@router.post(
    "",
    response_model=ChartResponse,
    summary="Calculate full bazi chart",
    description=(
        "Given a Gregorian birth datetime and gender, compute the four-pillar "
        "bazi chart including wuxing power, geju (pattern), shensha, dayun, "
        "and inter-branch relationships."
    ),
)
async def post_chart(req: ChartRequest) -> ChartResponse:
    """
    Calculate and return a complete bazi chart.

    The result is cached so repeated requests with identical parameters
    return instantly without re-running lunar-python calculations.
    """
    try:
        result = calculate_chart(req.datetime_str, req.gender)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Chart calculation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="八字计算内部错误") from exc

    return ChartResponse(
        chart=result["chart"],
        wuxing_power=result.get("wuxing_power"),
        geju=result.get("geju"),
    )
