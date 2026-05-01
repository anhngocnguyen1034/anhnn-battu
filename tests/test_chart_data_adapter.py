# -*- coding: utf-8 -*-
"""
Tests for the chart_data normalization adapter in agent_service.

Verifies that the frontend BaziReading format is correctly converted
to the flat backend engine format expected by tools and system prompts.
"""

import json
import sys

import pytest

sys.path.insert(0, "C:/Users/Gaaiyun/Projects/FOR-BAZI")

from backend.services.agent_service import _normalize_chart_data


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

# Simulates the backend engine's native flat format.
FLAT_ENGINE_DATA = {
    "gender": "乾造 (Male)",
    "pillars": ["壬午", "丁未", "庚寅", "戊寅"],
    "tg_gan": ["食神", "正官", "日主", "偏印"],
    "tg_zhi": ["丁己", "丁己乙", "甲丙戊", "甲壬"],
    "nayin": ["杨柳木", "天河水", "松柏木", "城头土"],
    "day_master": "庚",
    "minggong": "甲寅",
    "taiyuan": "戊戌",
    "shengong": "丙寅",
    "taixi": "乙巳",
    "dishi": ["", "冠带", "临官", "绝"],
    "xunkong": ["午未", "寅卯", "午未", "申酉"],
    "shensha": ["太极贵人", "天乙贵人", "文昌", "驿马"],
    "shensha_detail": {"year": ["太极贵人"], "month": ["天乙贵人"], "day": ["文昌"], "hour": ["驿马"]},
    "wuxing": {"金": 1, "木": 2, "水": 1, "火": 2, "土": 3},
    "xingchong": {"寅申冲": ["日时冲"]},
    "dayun": [
        {"start_age": 5, "start_year": 2007, "ganzhi": "戊申"},
        {"start_age": 15, "start_year": 2017, "ganzhi": "己酉"},
    ],
}


# Simulates the frontend BaziReading format (nested).
FRONTEND_BAZI_READING = {
    "chart": {
        "year_pillar": {"stem": "壬", "branch": "午", "hidden_stems": ["丁", "己"], "element": "水", "nayin": "杨柳木"},
        "month_pillar": {"stem": "丁", "branch": "未", "hidden_stems": ["丁", "己", "乙"], "element": "火", "nayin": "天河水"},
        "day_pillar": {"stem": "庚", "branch": "寅", "hidden_stems": ["甲", "丙", "戊"], "element": "金", "nayin": "松柏木"},
        "hour_pillar": {"stem": "戊", "branch": "寅", "hidden_stems": ["甲", "壬"], "element": "土", "nayin": "城头土"},
        "day_master": "庚",
        "day_master_element": "金",
    },
    "element_balance": {"金": 1, "木": 2, "水": 1, "火": 2, "土": 3},
    "ten_gods": [],
    "luck_pillars": [],
    "annual_pillars": [],
    "strengths": ["五行偏强: 土"],
    "weaknesses": ["五行偏弱: 水"],
    "favorable_elements": ["水"],
    "unfavorable_elements": ["土"],
    "summary": "格局: 正官格",
    "pillar_annotations": {
        "year": {"ten_god_gan": "食神", "ten_god_zhi": "丁己", "nayin": "杨柳木", "shensha": ["太极贵人"], "dishi": "", "xunkong": "午未"},
        "month": {"ten_god_gan": "正官", "ten_god_zhi": "丁己乙", "nayin": "天河水", "shensha": ["天乙贵人"], "dishi": "冠带", "xunkong": "寅卯"},
        "day": {"ten_god_gan": "日主", "ten_god_zhi": "甲丙戊", "nayin": "松柏木", "shensha": ["文昌"], "dishi": "临官", "xunkong": "午未"},
        "hour": {"ten_god_gan": "偏印", "ten_god_zhi": "甲壬", "nayin": "城头土", "shensha": ["驿马"], "dishi": "绝", "xunkong": "申酉"},
    },
    "wuxing_power": {"金": 15.2, "木": 25.1, "水": 10.3, "火": 22.0, "土": 27.4},
    "dayun": [
        {"stem": "戊", "branch": "申", "ganzhi": "戊申", "start_age": 5, "end_age": 14, "start_year": 2007, "end_year": 2016, "is_current": False},
        {"stem": "己", "branch": "酉", "ganzhi": "己酉", "start_age": 15, "end_age": 24, "start_year": 2017, "end_year": 2026, "is_current": True},
    ],
    "ming_gong": "甲寅",
    "tai_yuan": "戊戌",
    "shen_gong": "丙寅",
    "tai_xi": "乙巳",
    "geju": {"geju_type": "正官格", "description": "庚金生于未月", "favorable_elements": ["水"], "unfavorable_elements": ["土"]},
    "xingchong": ["寅申冲: 日时冲"],
    "all_shensha": [
        {"name": "太极贵人", "pillar": "年柱", "description": ""},
        {"name": "天乙贵人", "pillar": "月柱", "description": ""},
        {"name": "文昌", "pillar": "日柱", "description": ""},
        {"name": "驿马", "pillar": "时柱", "description": ""},
    ],
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNormalizePassThrough:
    """Flat engine format should pass through unchanged."""

    def test_flat_data_passes_through(self):
        result = _normalize_chart_data(FLAT_ENGINE_DATA)
        assert result is FLAT_ENGINE_DATA

    def test_empty_dict_passes_through(self):
        result = _normalize_chart_data({})
        assert result == {}

    def test_none_returns_falsy(self):
        result = _normalize_chart_data(None)
        assert not result


class TestNormalizeFrontendFormat:
    """Frontend BaziReading format should be converted to flat format."""

    def test_pillars_reconstructed(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["pillars"] == ["壬午", "丁未", "庚寅", "戊寅"]

    def test_day_master_extracted(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["day_master"] == "庚"

    def test_nayin_extracted(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["nayin"] == ["杨柳木", "天河水", "松柏木", "城头土"]

    def test_tg_zhi_from_pillar_annotations(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["tg_zhi"] == ["丁己", "丁己乙", "甲丙戊", "甲壬"]

    def test_tg_gan_from_pillar_annotations(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["tg_gan"] == ["食神", "正官", "日主", "偏印"]

    def test_dishi_from_pillar_annotations(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["dishi"] == ["", "冠带", "临官", "绝"]

    def test_xunkong_from_pillar_annotations(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["xunkong"] == ["午未", "寅卯", "午未", "申酉"]

    def test_minggong_converted(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["minggong"] == "甲寅"

    def test_taiyuan_converted(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["taiyuan"] == "戊戌"

    def test_shengong_converted(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["shengong"] == "丙寅"

    def test_taixi_converted(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["taixi"] == "乙巳"

    def test_wuxing_from_element_balance(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["wuxing"] == {"金": 1, "木": 2, "水": 1, "火": 2, "土": 3}

    def test_dayun_preserved(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert len(result["dayun"]) == 2
        assert result["dayun"][0]["ganzhi"] == "戊申"

    def test_shensha_from_all_shensha(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert "太极贵人" in result["shensha"]
        assert "天乙贵人" in result["shensha"]

    def test_xingchong_preserved(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert "寅申冲: 日时冲" in result["xingchong"]

    def test_wuxing_power_preserved(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["wuxing_power"]["金"] == 15.2

    def test_geju_preserved(self):
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        assert result["geju"]["geju_type"] == "正官格"


class TestToolsWorkWithNormalizedData:
    """Verify that tools can actually use the normalized data."""

    def test_geju_analyzer_with_normalized_data(self):
        from tools.geju_analyzer import analyze_geju
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        geju = analyze_geju(result)
        parsed = json.loads(geju) if isinstance(geju, str) else geju
        assert parsed is not None
        # Should not say "命盘数据不完整"
        assert "不完整" not in str(parsed)

    def test_wuxing_calculator_with_normalized_data(self):
        from tools.wuxing_calculator import calculate_wuxing_power
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        power = calculate_wuxing_power(result)
        parsed = json.loads(power) if isinstance(power, str) else power
        assert parsed is not None
        assert "power" in parsed

    def test_system_prompt_with_normalized_data(self):
        from prompts.system_prompts import build_system_prompt
        result = _normalize_chart_data(FRONTEND_BAZI_READING)
        prompt = build_system_prompt(result)
        assert "庚" in prompt  # day master
        assert "壬午" in prompt  # year pillar
        assert "丁未" in prompt  # month pillar
        assert "庚寅" in prompt  # day pillar
        assert "戊寅" in prompt  # hour pillar
        assert "甲寅" in prompt  # ming gong
