# -*- coding: utf-8 -*-
"""
Bazi calculation service — wraps engine + tools with in-memory caching.

All heavy computation (lunar-python, shensha, wuxing power, geju) goes
through here so the API routers stay thin.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from engine.bazi_engine import calculate_professional_bazi
from tools.wuxing_calculator import calculate_wuxing_power
from tools.geju_analyzer import analyze_geju

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal cache key helper
# ---------------------------------------------------------------------------


def _cache_key(dt_str: str, gender: str) -> str:
    """Build a deterministic cache key from request parameters."""
    return f"{dt_str}|{gender}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Simple dict-based LRU-ish cache (avoids unbounded growth).
_chart_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_MAX = 256
_cache_lock = threading.Lock()


def calculate_chart(datetime_str: str, gender: str) -> Dict[str, Any]:
    """
    Calculate a full bazi chart and attach derived analyses.

    Args:
        datetime_str: Birth datetime in ``YYYY-MM-DD HH:MM`` format.
        gender: ``'乾造 (Male)'`` or ``'坤造 (Female)'``.

    Returns:
        dict with keys ``chart``, ``wuxing_power``, ``geju``.

    Raises:
        ValueError: If *datetime_str* cannot be parsed.
    """
    key = _cache_key(datetime_str, gender)
    with _cache_lock:
        if key in _chart_cache:
            logger.debug("Cache hit for %s", key)
            return _chart_cache[key]

    # Parse datetime
    try:
        dt = datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(
                f"无法解析日期时间 '{datetime_str}'，"
                "请使用 'YYYY-MM-DD HH:MM' 格式"
            ) from exc

    # Core calculation
    chart_data = calculate_professional_bazi(dt, gender)

    # Derived: wuxing power (refined)
    try:
        wuxing_raw = calculate_wuxing_power(chart_data)
        wuxing_power = json.loads(wuxing_raw) if isinstance(wuxing_raw, str) else wuxing_raw
    except (KeyError, ValueError, TypeError):
        logger.warning("wuxing_power calculation failed", exc_info=True)
        wuxing_power = None

    # Derived: geju (pattern)
    try:
        geju_raw = analyze_geju(chart_data)
        geju = json.loads(geju_raw) if isinstance(geju_raw, str) else geju_raw
    except (KeyError, ValueError, TypeError):
        logger.warning("geju analysis failed", exc_info=True)
        geju = None

    result: Dict[str, Any] = {
        "chart": chart_data,
        "wuxing_power": wuxing_power,
        "geju": geju,
    }

    # Evict oldest if cache is full
    with _cache_lock:
        if len(_chart_cache) >= _CACHE_MAX:
            oldest_key = next(iter(_chart_cache))
            del _chart_cache[oldest_key]
        _chart_cache[key] = result

    return result


def get_chart_from_data(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Re-run derived analyses on an already-computed chart dict.

    Useful when the client sends pre-computed ``chart_data`` (e.g. from a
    previous /chart call) and we need wuxing_power + geju without
    recalculating the engine.

    Args:
        chart_data: Dict matching ``calculate_professional_bazi`` output.

    Returns:
        dict with ``wuxing_power`` and ``geju`` sub-dicts.
    """
    try:
        wuxing_raw = calculate_wuxing_power(chart_data)
        wuxing_power = json.loads(wuxing_raw) if isinstance(wuxing_raw, str) else wuxing_raw
    except (KeyError, ValueError, TypeError):
        wuxing_power = None

    try:
        geju_raw = analyze_geju(chart_data)
        geju = json.loads(geju_raw) if isinstance(geju_raw, str) else geju_raw
    except (KeyError, ValueError, TypeError):
        geju = None

    return {"wuxing_power": wuxing_power, "geju": geju}
