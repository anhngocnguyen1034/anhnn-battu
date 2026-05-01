# -*- coding: utf-8 -*-
"""
GET /api/v1/daily-fortune — lightweight daily fortune by zodiac sign.

This is a fun / entertainment endpoint; it does NOT perform real bazi
calculation.  Returns a deterministic pseudo-random fortune seeded by
the current date + zodiac sign.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entertainment", tags=["entertainment"])

# Zodiac signs in traditional Chinese order
ZODIAC_SIGNS: List[str] = [
    "鼠", "牛", "虎", "兔", "龙", "蛇",
    "马", "羊", "猴", "鸡", "狗", "猪",
]

# Fortune templates keyed by score bucket
_FORTUNE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "大吉": {
        "level": "大吉",
        "advice": "今日诸事皆宜，贵人相助，可大胆行动。",
        "lucky_color": "红色",
        "lucky_number": 9,
    },
    "中吉": {
        "level": "中吉",
        "advice": "运势不错，适合推进重要事务，但需留意细节。",
        "lucky_color": "金色",
        "lucky_number": 6,
    },
    "小吉": {
        "level": "小吉",
        "advice": "平稳向好，适合处理日常事务，不宜冒进。",
        "lucky_color": "绿色",
        "lucky_number": 3,
    },
    "平": {
        "level": "平",
        "advice": "运势平平，按部就班即可，不宜做重大决定。",
        "lucky_color": "白色",
        "lucky_number": 1,
    },
    "小凶": {
        "level": "小凶",
        "advice": "今日宜守不宜攻，避免与人争执，低调行事。",
        "lucky_color": "蓝色",
        "lucky_number": 4,
    },
    "凶": {
        "level": "凶",
        "advice": "今日不宜冒险，凡事三思而后行，注意安全。",
        "lucky_color": "黑色",
        "lucky_number": 0,
    },
}

_LEVELS = list(_FORTUNE_TEMPLATES.keys())


def _deterministic_fortune(zodiac: str, today: date) -> Dict[str, Any]:
    """
    Generate a deterministic fortune based on date + zodiac.

    Uses a SHA-256 hash of ``YYYY-MM-DD|zodiac`` to pick a fortune level,
    ensuring the same sign always gets the same fortune on a given day
    without any randomness.
    """
    seed_str = f"{today.isoformat()}|{zodiac}"
    digest = hashlib.sha256(seed_str.encode()).hexdigest()
    bucket = int(digest[:8], 16) % len(_LEVELS)
    level = _LEVELS[bucket]
    template = _FORTUNE_TEMPLATES[level]

    # Derive aspect scores from different hash segments
    aspects = {
        "事业": (int(digest[8:10], 16) % 5) + 1,
        "财运": (int(digest[10:12], 16) % 5) + 1,
        "感情": (int(digest[12:14], 16) % 5) + 1,
        "健康": (int(digest[14:16], 16) % 5) + 1,
    }

    return {
        "zodiac": zodiac,
        "date": today.isoformat(),
        "fortune_level": template["level"],
        "advice": template["advice"],
        "lucky_color": template["lucky_color"],
        "lucky_number": template["lucky_number"],
        "aspects": aspects,
    }


@router.get(
    "/daily-fortune",
    summary="Daily fortune by zodiac sign",
    description=(
        "Returns a deterministic pseudo-random daily fortune for the given "
        "Chinese zodiac sign.  Purely for entertainment."
    ),
)
async def get_daily_fortune(
    zodiac: str = Query(
        ...,
        description="生肖名称，如 '鼠', '牛', '虎' 等",
        examples=["龙"],
    ),
) -> Dict[str, Any]:
    """
    Get today's fortune for a zodiac sign.

    The result is deterministic per (date, zodiac) pair — the same sign
    always gets the same fortune on the same day.
    """
    zodiac = zodiac.strip()
    if zodiac not in ZODIAC_SIGNS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"未知生肖 '{zodiac}'，有效值: {', '.join(ZODIAC_SIGNS)}",
        )

    return _deterministic_fortune(zodiac, date.today())
