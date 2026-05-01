# -*- coding: utf-8 -*-
"""
Comprehensive engine data-pipeline tests for FOR-BAZI.

Covers:
  1. Engine output format (all expected fields present & correct types)
  2. Calculation accuracy across multiple birth dates (pillars, day_master,
     ten gods, wuxing count, nayin, shensha, xingchong, etc.)
  3. bazi_service.calculate_chart structure
  4. System prompt built from engine output contains correct data
  5. Tool functions work with raw engine output
  6. Edge-case handling (new-year boundary, lunar-new-year period)
"""

import json
from datetime import datetime

import pytest

from engine.bazi_engine import calculate_professional_bazi
from backend.services.bazi_service import calculate_chart
from prompts.system_prompts import build_system_prompt
from tools.bazi_tools import (
    dispatch_tool,
    get_annual_fortune,
    get_dayun_stage,
    analyze_wuxing_balance,
    query_xing_chong_he_hai,
    explain_shensha,
    fact_check_ganzhi,
    calculate_wuxing_power,
    analyze_geju,
)
from tools.wuxing_calculator import calculate_wuxing_power as wuxing_power_fn
from tools.geju_analyzer import analyze_geju as geju_fn

# ════════════════════════════════════════════════════════════════════════════
# Test data: (year, month, day, hour, minute, gender_str, label)
# ════════════════════════════════════════════════════════════════════════════

TEST_CASES = [
    (2002, 7, 21, 3, 30, "乾造 (Male)", "Male 2002-07-21 03:30"),
    (2000, 3, 15, 12, 0, "坤造 (Female)", "Female 2000-03-15 12:00"),
    (1990, 1, 1, 0, 0, "乾造 (Male)", "Male 1990-01-01 00:00 (new year edge)"),
    (2024, 2, 10, 23, 59, "坤造 (Female)", "Female 2024-02-10 23:59 (lunar new year edge)"),
]

# Known expected values from independent verification with lunar_python
EXPECTED_PILLARS = {
    "Male 2002-07-21 03:30": ["壬午", "丁未", "庚寅", "戊寅"],
    "Female 2000-03-15 12:00": ["庚辰", "己卯", "壬申", "丙午"],
    "Male 1990-01-01 00:00 (new year edge)": ["己巳", "丙子", "丙寅", "戊子"],
    "Female 2024-02-10 23:59 (lunar new year edge)": ["甲辰", "丙寅", "甲辰", "丙子"],
}

EXPECTED_DAY_MASTER = {
    "Male 2002-07-21 03:30": "庚",
    "Female 2000-03-15 12:00": "壬",
    "Male 1990-01-01 00:00 (new year edge)": "丙",
    "Female 2024-02-10 23:59 (lunar new year edge)": "甲",
}

EXPECTED_TG_GAN = {
    "Male 2002-07-21 03:30": ["食神", "正官", "日主", "偏印"],
    "Female 2000-03-15 12:00": ["偏印", "正官", "日主", "偏财"],
    "Male 1990-01-01 00:00 (new year edge)": ["伤官", "比肩", "日主", "食神"],
    "Female 2024-02-10 23:59 (lunar new year edge)": ["比肩", "食神", "日主", "食神"],
}

EXPECTED_TG_ZHI = {
    "Male 2002-07-21 03:30": [
        "正官 正印",
        "正印 正官 正财",
        "偏财 七杀 偏印",
        "偏财 七杀 偏印",
    ],
    "Female 2000-03-15 12:00": [
        "七杀 伤官 劫财",
        "伤官",
        "偏印 比肩 七杀",
        "正财 正官",
    ],
    "Male 1990-01-01 00:00 (new year edge)": [
        "比肩 偏财 食神",
        "正官",
        "偏印 比肩 食神",
        "正官",
    ],
    "Female 2024-02-10 23:59 (lunar new year edge)": [
        "偏财 劫财 正印",
        "比肩 食神 偏财",
        "偏财 劫财 正印",
        "正印",
    ],
}

EXPECTED_NAYIN = {
    "Male 2002-07-21 03:30": ["杨柳木", "天河水", "松柏木", "城头土"],
    "Female 2000-03-15 12:00": ["白蜡金", "城头土", "剑锋金", "天河水"],
    "Male 1990-01-01 00:00 (new year edge)": ["大林木", "涧下水", "炉中火", "霹雳火"],
    "Female 2024-02-10 23:59 (lunar new year edge)": ["覆灯火", "炉中火", "覆灯火", "涧下水"],
}

EXPECTED_WUXING = {
    "Male 2002-07-21 03:30": {"金(Metal)": 1, "木(Wood)": 2, "水(Water)": 1, "火(Fire)": 2, "土(Earth)": 2},
    "Female 2000-03-15 12:00": {"金(Metal)": 2, "木(Wood)": 1, "水(Water)": 1, "火(Fire)": 2, "土(Earth)": 2},
    "Male 1990-01-01 00:00 (new year edge)": {"金(Metal)": 0, "木(Wood)": 1, "水(Water)": 2, "火(Fire)": 3, "土(Earth)": 2},
    "Female 2024-02-10 23:59 (lunar new year edge)": {"金(Metal)": 0, "木(Wood)": 3, "水(Water)": 1, "火(Fire)": 2, "土(Earth)": 2},
}


def _make_chart(year, month, day, hour, minute, gender):
    """Helper: build chart data from parameters."""
    dt = datetime(year, month, day, hour, minute)
    return calculate_professional_bazi(dt, gender)


def _all_chart_data():
    """Helper: generate (label, chart_data) for all test cases."""
    results = []
    for y, m, d, h, mi, g, label in TEST_CASES:
        results.append((label, _make_chart(y, m, d, h, mi, g)))
    return results


# ════════════════════════════════════════════════════════════════════════════
# 1. Engine output format tests
# ════════════════════════════════════════════════════════════════════════════

class TestEngineOutputFormat:
    """Verify all expected fields exist with correct types."""

    REQUIRED_KEYS = {
        "pillars", "tg_gan", "tg_zhi", "nayin", "day_master", "gender",
        "wuxing", "dayun", "minggong", "taiyuan", "dishi", "xunkong",
        "shensha", "xingchong",
    }

    @pytest.fixture(scope="class")
    def sample_chart(self):
        return _make_chart(2002, 7, 21, 3, 30, "乾造 (Male)")

    def test_all_required_keys_present(self, sample_chart):
        missing = self.REQUIRED_KEYS - set(sample_chart.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_pillars_format(self, sample_chart):
        pillars = sample_chart["pillars"]
        assert isinstance(pillars, list)
        assert len(pillars) == 4
        for p in pillars:
            assert isinstance(p, str)
            assert len(p) == 2

    def test_tg_gan_format(self, sample_chart):
        tg_gan = sample_chart["tg_gan"]
        assert isinstance(tg_gan, list)
        assert len(tg_gan) == 4
        assert tg_gan[2] == "日主"

    def test_tg_zhi_format(self, sample_chart):
        tg_zhi = sample_chart["tg_zhi"]
        assert isinstance(tg_zhi, list)
        assert len(tg_zhi) == 4
        for z in tg_zhi:
            assert isinstance(z, str)

    def test_nayin_format(self, sample_chart):
        nayin = sample_chart["nayin"]
        assert isinstance(nayin, list)
        assert len(nayin) == 4
        for n in nayin:
            assert isinstance(n, str)
            assert len(n) > 0

    def test_wuxing_format(self, sample_chart):
        wuxing = sample_chart["wuxing"]
        assert isinstance(wuxing, dict)
        expected_keys = {"金(Metal)", "木(Wood)", "水(Water)", "火(Fire)", "土(Earth)"}
        assert expected_keys == set(wuxing.keys())
        for v in wuxing.values():
            assert isinstance(v, int)
            assert v >= 0

    def test_dayun_format(self, sample_chart):
        dayun = sample_chart["dayun"]
        assert isinstance(dayun, list)
        if dayun:
            for dy in dayun:
                assert "start_age" in dy
                assert "start_year" in dy
                assert "ganzhi" in dy
                assert isinstance(dy["start_age"], int)
                assert isinstance(dy["start_year"], int)
                assert isinstance(dy["ganzhi"], str)

    def test_dishi_format(self, sample_chart):
        dishi = sample_chart["dishi"]
        assert isinstance(dishi, list)
        assert len(dishi) == 4
        for d in dishi:
            assert isinstance(d, str)

    def test_xunkong_format(self, sample_chart):
        xunkong = sample_chart["xunkong"]
        assert isinstance(xunkong, list)
        assert len(xunkong) == 4
        for xk in xunkong:
            assert isinstance(xk, str)

    def test_shensha_format(self, sample_chart):
        shensha = sample_chart["shensha"]
        assert isinstance(shensha, list)
        assert len(shensha) == 4
        for s in shensha:
            assert isinstance(s, str)

    def test_xingchong_format(self, sample_chart):
        xc = sample_chart["xingchong"]
        assert isinstance(xc, dict)
        expected_types = {"冲", "合", "刑", "害", "破", "穿", "三合", "三会", "半三合"}
        assert expected_types.issubset(set(xc.keys()))
        for v in xc.values():
            assert isinstance(v, list)

    def test_day_master_format(self, sample_chart):
        dm = sample_chart["day_master"]
        assert isinstance(dm, str)
        assert len(dm) == 1
        assert dm in "甲乙丙丁戊己庚辛壬癸"

    def test_gender_stored(self, sample_chart):
        assert sample_chart["gender"] == "乾造 (Male)"

    def test_minggong_taiyuan_present(self, sample_chart):
        assert "minggong" in sample_chart
        assert isinstance(sample_chart["minggong"], str)
        assert "taiyuan" in sample_chart
        assert isinstance(sample_chart["taiyuan"], str)

    def test_additional_palaces(self, sample_chart):
        assert "taixi" in sample_chart
        assert "shengong" in sample_chart
        assert "shensha_detail" in sample_chart
        assert "wuxing_str" in sample_chart


# ════════════════════════════════════════════════════════════════════════════
# 2. Calculation accuracy tests (parametrized across all test dates)
# ════════════════════════════════════════════════════════════════════════════

class TestCalculationAccuracy:
    """Verify pillars, day_master, ten gods, nayin, and wuxing counts."""

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_pillars_correct(self, year, month, day, hour, minute, gender, label):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["pillars"] == EXPECTED_PILLARS[label], (
            f"Pillars mismatch for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_day_master_correct(self, year, month, day, hour, minute, gender, label):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["day_master"] == EXPECTED_DAY_MASTER[label], (
            f"Day master mismatch for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_tg_gan_correct(self, year, month, day, hour, minute, gender, label):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["tg_gan"] == EXPECTED_TG_GAN[label], (
            f"Ten gods (gan) mismatch for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_tg_zhi_correct(self, year, month, day, hour, minute, gender, label):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["tg_zhi"] == EXPECTED_TG_ZHI[label], (
            f"Ten gods (zhi) mismatch for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_nayin_correct(self, year, month, day, hour, minute, gender, label):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["nayin"] == EXPECTED_NAYIN[label], (
            f"Nayin mismatch for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_wuxing_count_correct(self, year, month, day, hour, minute, gender, label):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["wuxing"] == EXPECTED_WUXING[label], (
            f"Wuxing count mismatch for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_wuxing_total_equals_8(self, year, month, day, hour, minute, gender, label):
        """Wuxing counts should total 8 (4 pillars x 2 chars)."""
        chart = _make_chart(year, month, day, hour, minute, gender)
        total = sum(chart["wuxing"].values())
        assert total == 8, f"Wuxing total is {total}, expected 8 for {label}"


# ════════════════════════════════════════════════════════════════════════════
# 3. Edge-case specific tests
# ════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Boundary condition tests."""

    def test_new_year_1990_lunar_year(self):
        """1990-01-01 is before lunar new year, so year pillar should be 己巳."""
        chart = _make_chart(1990, 1, 1, 0, 0, "乾造 (Male)")
        assert chart["pillars"][0] == "己巳"

    def test_lunar_new_year_day_2024(self):
        """2024-02-10 is the lunar new year day; year pillar should be 甲辰."""
        chart = _make_chart(2024, 2, 10, 23, 59, "坤造 (Female)")
        assert chart["pillars"][0][0] == "甲"
        assert chart["pillars"][0][1] == "辰"

    def test_dayun_nonempty(self):
        """Dayun should be non-empty for all test cases."""
        for y, m, d, h, mi, g, label in TEST_CASES:
            chart = _make_chart(y, m, d, h, mi, g)
            assert len(chart["dayun"]) > 0, f"Dayun empty for {label}"

    def test_dayun_start_year_after_birth(self):
        """Dayun start years should be >= birth year."""
        for y, m, d, h, mi, g, label in TEST_CASES:
            chart = _make_chart(y, m, d, h, mi, g)
            for dy in chart["dayun"]:
                assert dy["start_year"] >= y, (
                    f"Dayun start_year {dy['start_year']} < birth year {y} for {label}"
                )


# ════════════════════════════════════════════════════════════════════════════
# 4. BaziService integration tests
# ════════════════════════════════════════════════════════════════════════════

class TestBaziService:
    """Verify calculate_chart returns correct structure."""

    @pytest.fixture
    def service_result(self):
        return calculate_chart("2002-07-21 03:30", "乾造 (Male)")

    def test_result_has_chart_key(self, service_result):
        assert "chart" in service_result

    def test_result_has_wuxing_power_key(self, service_result):
        assert "wuxing_power" in service_result

    def test_result_has_geju_key(self, service_result):
        assert "geju" in service_result

    def test_chart_is_dict(self, service_result):
        assert isinstance(service_result["chart"], dict)

    def test_wuxing_power_is_dict(self, service_result):
        assert isinstance(service_result["wuxing_power"], dict)
        wp = service_result["wuxing_power"]
        assert "power" in wp
        assert "strong" in wp
        assert "weak" in wp
        assert "balanced" in wp

    def test_geju_is_dict(self, service_result):
        assert isinstance(service_result["geju"], dict)
        gj = service_result["geju"]
        assert "格局类型" in gj
        assert "格局名称" in gj
        assert "日主强弱" in gj

    def test_chart_data_matches_engine(self, service_result):
        """Service chart data should match direct engine output."""
        dt = datetime(2002, 7, 21, 3, 30)
        direct = calculate_professional_bazi(dt, "乾造 (Male)")
        assert service_result["chart"]["pillars"] == direct["pillars"]
        assert service_result["chart"]["day_master"] == direct["day_master"]

    def test_cache_returns_same_result(self):
        """Calling twice with same params should return identical data."""
        r1 = calculate_chart("2000-03-15 12:00", "坤造 (Female)")
        r2 = calculate_chart("2000-03-15 12:00", "坤造 (Female)")
        assert r1["chart"]["pillars"] == r2["chart"]["pillars"]

    def test_invalid_datetime_raises(self):
        with pytest.raises(ValueError):
            calculate_chart("not-a-date", "乾造 (Male)")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            calculate_chart("2002/07/21 03:30", "乾造 (Male)")


# ════════════════════════════════════════════════════════════════════════════
# 5. System prompt tests
# ════════════════════════════════════════════════════════════════════════════

class TestSystemPrompt:
    """Verify system prompt contains correct engine data."""

    @pytest.fixture
    def chart_2002(self):
        return _make_chart(2002, 7, 21, 3, 30, "乾造 (Male)")

    @pytest.fixture
    def prompt_2002(self, chart_2002):
        return build_system_prompt(chart_2002)

    def test_prompt_contains_day_master(self, prompt_2002, chart_2002):
        assert chart_2002["day_master"] in prompt_2002

    def test_prompt_contains_gender(self, prompt_2002):
        assert "乾造 (Male)" in prompt_2002

    def test_prompt_contains_pillars(self, prompt_2002, chart_2002):
        for pillar in chart_2002["pillars"]:
            assert pillar in prompt_2002, f"Pillar {pillar} missing from prompt"

    def test_prompt_contains_nayin(self, prompt_2002, chart_2002):
        for n in chart_2002["nayin"]:
            assert n in prompt_2002, f"Nayin {n} missing from prompt"

    def test_prompt_contains_minggong(self, prompt_2002, chart_2002):
        assert chart_2002["minggong"] in prompt_2002

    def test_prompt_contains_taiyuan(self, prompt_2002, chart_2002):
        assert chart_2002["taiyuan"] in prompt_2002

    def test_prompt_contains_dayun(self, prompt_2002, chart_2002):
        """Prompt should contain at least the first dayun ganzhi."""
        if chart_2002["dayun"]:
            assert chart_2002["dayun"][0]["ganzhi"] in prompt_2002

    def test_prompt_contains_persona(self, prompt_2002):
        assert "玄冥" in prompt_2002

    def test_prompt_contains_tool_guidance(self, prompt_2002):
        assert "get_annual_fortune" in prompt_2002

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_prompt_contains_all_pillars_across_cases(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        prompt = build_system_prompt(chart)
        for pillar in chart["pillars"]:
            assert pillar in prompt, f"Pillar {pillar} missing for {label}"


# ════════════════════════════════════════════════════════════════════════════
# 6. Tool function tests (consume raw engine output)
# ════════════════════════════════════════════════════════════════════════════

class TestToolsWithEngineOutput:
    """Verify tools work with raw engine output (not normalized frontend data)."""

    @pytest.fixture
    def chart_2002(self):
        return _make_chart(2002, 7, 21, 3, 30, "乾造 (Male)")

    @pytest.fixture
    def chart_2000(self):
        return _make_chart(2000, 3, 15, 12, 0, "坤造 (Female)")

    # -- get_annual_fortune --

    def test_annual_fortune_2026(self):
        result = json.loads(get_annual_fortune(2026))
        assert result["year"] == 2026
        assert result["ganzhi"] == "乙巳"
        assert "nayin" in result

    def test_annual_fortune_2000(self):
        result = json.loads(get_annual_fortune(2000))
        assert result["year"] == 2000
        assert isinstance(result["ganzhi"], str)
        assert len(result["ganzhi"]) == 2

    # -- get_dayun_stage --

    def test_dayun_stage_2026(self, chart_2002):
        result = json.loads(get_dayun_stage(chart_2002, 2026))
        assert result["current_year"] == 2026
        assert result["step"] is not None
        assert "ganzhi" in result
        assert result["step"] == 2  # 2nd dayun: 己酉 starting 2018

    def test_dayun_stage_before_first(self, chart_2002):
        """Year before first dayun (2008) returns no active stage."""
        result = json.loads(get_dayun_stage(chart_2002, 2005))
        # First dayun starts at 2008, so 2005 has no match -> step is None
        assert result["step"] is None

    def test_dayun_stage_during_first(self, chart_2002):
        """Year during first dayun should return step 1."""
        result = json.loads(get_dayun_stage(chart_2002, 2010))
        assert result["step"] == 1

    # -- analyze_wuxing_balance --

    def test_wuxing_balance_structure(self, chart_2002):
        result = json.loads(analyze_wuxing_balance(chart_2002))
        assert "wuxing" in result
        assert "total" in result
        assert "strong" in result
        assert "weak" in result
        assert "balanced" in result

    def test_wuxing_balance_total(self, chart_2002):
        result = json.loads(analyze_wuxing_balance(chart_2002))
        assert result["total"] == 8

    def test_wuxing_balance_with_zero_element(self, chart_2000):
        """All test charts should report correctly even with 0-count elements."""
        result = json.loads(analyze_wuxing_balance(chart_2000))
        assert "wuxing" in result
        total = result["total"]
        assert total > 0

    def test_wuxing_balance_balanced_fix(self):
        """Verify that perfectly equal distribution is reported as balanced."""
        # Construct artificial data where all elements are equal
        fake_chart = {
            "wuxing": {
                "金(Metal)": 2, "木(Wood)": 2, "水(Water)": 2,
                "火(Fire)": 2, "土(Earth)": 2,
            }
        }
        result = json.loads(analyze_wuxing_balance(fake_chart))
        assert result["balanced"] is True, (
            "Equal distribution should be reported as balanced"
        )

    # -- query_xing_chong_he_hai --

    def test_xingchong_structure(self, chart_2002):
        result = json.loads(query_xing_chong_he_hai(chart_2002))
        assert "xingchong" in result
        assert "summary" in result
        assert isinstance(result["summary"], list)

    def test_xingchong_known_relation(self, chart_2002):
        """2002 chart has 年月六合(午未)."""
        result = json.loads(query_xing_chong_he_hai(chart_2002))
        xc = result["xingchong"]
        assert len(xc["合"]) > 0, "Expected 合 relations for 2002 chart"

    def test_xingchong_with_type_filter(self, chart_2002):
        result = json.loads(query_xing_chong_he_hai(chart_2002, "合"))
        assert "relation_type" in result
        assert result["relation_type"] == "合"
        assert "description" in result

    # -- explain_shensha --

    def test_explain_taohua(self):
        result = json.loads(explain_shensha("桃花"))
        assert result["shensha"] == "桃花"
        assert "description" in result

    def test_explain_unknown_shensha(self):
        result = json.loads(explain_shensha("不存在的神煞"))
        assert "available" in result

    # -- fact_check_ganzhi --

    def test_fact_check_correct(self):
        result = json.loads(fact_check_ganzhi("乙巳", 2026))
        assert result["match"] is True

    def test_fact_check_incorrect(self):
        result = json.loads(fact_check_ganzhi("丙午", 2026))
        assert result["match"] is False
        assert result["actual"] == "乙巳"

    # -- calculate_wuxing_power (via dispatch) --

    def test_wuxing_power_dispatch(self, chart_2002):
        result_str = dispatch_tool("calculate_wuxing_power", {}, chart_2002)
        result = json.loads(result_str)
        assert "power" in result
        power = result["power"]
        assert set(power.keys()) == {"金", "木", "水", "火", "土"}
        # Percentages should sum to ~100
        total = sum(power.values())
        assert abs(total - 100.0) < 1.0, f"Power total is {total}, expected ~100"

    # -- analyze_geju (via dispatch) --

    def test_geju_dispatch(self, chart_2002):
        result_str = dispatch_tool("analyze_geju", {}, chart_2002)
        result = json.loads(result_str)
        assert "格局类型" in result
        assert "格局名称" in result
        assert "日主强弱" in result
        assert "月令" in result

    # -- query_qiongtong_guidance (via dispatch) --

    def test_qiongtong_dispatch(self, chart_2002):
        result_str = dispatch_tool("query_qiongtong_guidance", {}, chart_2002)
        result = json.loads(result_str)
        # Should return some structured result (even if empty guidance)
        assert isinstance(result, dict)

    # -- dispatch_tool with unknown tool --

    def test_dispatch_unknown_tool(self):
        result_str = dispatch_tool("nonexistent_tool", {}, {})
        result = json.loads(result_str)
        assert "error" in result

    # -- dispatch_tool for all charts --

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_all_tools_succeed_across_cases(
        self, year, month, day, hour, minute, gender, label
    ):
        """All major tools should return valid JSON for every test case."""
        chart = _make_chart(year, month, day, hour, minute, gender)

        # Tools that take bazi_data
        for tool_name in [
            "analyze_wuxing_balance",
            "calculate_wuxing_power",
            "analyze_geju",
            "query_xing_chong_he_hai",
            "get_dayun_stage",
        ]:
            args = {"current_year": 2026} if tool_name == "get_dayun_stage" else {}
            result_str = dispatch_tool(tool_name, args, chart)
            result = json.loads(result_str)
            assert "error" not in result or "context" in result, (
                f"Tool {tool_name} returned error for {label}: {result}"
            )


# ════════════════════════════════════════════════════════════════════════════
# 7. Wuxing power calculator direct tests
# ════════════════════════════════════════════════════════════════════════════

class TestWuxingCalculator:
    """Direct tests on the refined wuxing power calculator."""

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_wuxing_power_returns_valid_json(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        result = json.loads(wuxing_power_fn(chart))
        assert "power" in result
        assert set(result["power"].keys()) == {"金", "木", "水", "火", "土"}

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_wuxing_power_sums_to_100(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        result = json.loads(wuxing_power_fn(chart))
        total = sum(result["power"].values())
        assert abs(total - 100.0) < 1.0, (
            f"Power total {total} not ~100 for {label}"
        )

    def test_strong_and_weak_labels(self):
        chart = _make_chart(2002, 7, 21, 3, 30, "乾造 (Male)")
        result = json.loads(wuxing_power_fn(chart))
        # Fire should be strong (47.5%)
        assert "火" in result["strong"], "Fire should be classified as strong"
        # Gold should be weak (3.8%)
        assert "金" in result["weak"], "Metal should be classified as weak"


# ════════════════════════════════════════════════════════════════════════════
# 8. Geju analyzer direct tests
# ════════════════════════════════════════════════════════════════════════════

class TestGejuAnalyzer:
    """Direct tests on the geju (pattern) analyzer."""

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_geju_returns_valid_structure(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        result = json.loads(geju_fn(chart))
        assert "格局类型" in result
        assert "格局名称" in result
        assert "月令" in result
        assert "月令主气" in result
        assert "日主强弱" in result
        assert "日主力量占比" in result

    def test_geju_2002_day_master_weak(self):
        """2002 chart (庚 day master) should show weak day master."""
        chart = _make_chart(2002, 7, 21, 3, 30, "乾造 (Male)")
        result = json.loads(geju_fn(chart))
        assert "身弱" in result["日主强弱"] or "从格" in result["格局类型"]

    def test_geju_1990_has_month_zhi(self):
        """Geju should reference the correct month branch."""
        chart = _make_chart(1990, 1, 1, 0, 0, "乾造 (Male)")
        result = json.loads(geju_fn(chart))
        assert result["月令"] == "子"

    def test_geju_strength_ratio_positive(self):
        """Day master power ratio should be positive."""
        chart = _make_chart(2000, 3, 15, 12, 0, "坤造 (Female)")
        result = json.loads(geju_fn(chart))
        assert result["日主力量占比"] > 0


# ════════════════════════════════════════════════════════════════════════════
# 9. Cross-field consistency tests
# ════════════════════════════════════════════════════════════════════════════

class TestCrossFieldConsistency:
    """Verify internal consistency between engine output fields."""

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_day_master_equals_day_pillar_gan(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        day_pillar_gan = chart["pillars"][2][0]
        assert chart["day_master"] == day_pillar_gan, (
            f"day_master != day pillar gan for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_tg_gan_middle_is_day_master_label(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert chart["tg_gan"][2] == "日主", (
            f"tg_gan[2] should be '日主' for {label}"
        )

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_wuxing_str_matches_wuxing_count(
        self, year, month, day, hour, minute, gender, label
    ):
        """wuxing_str field should match the sum in wuxing dict."""
        chart = _make_chart(year, month, day, hour, minute, gender)
        wx_str = chart.get("wuxing_str", "")
        wx_dict = chart["wuxing"]
        assert wx_dict["金(Metal)"] == wx_str.count("金")
        assert wx_dict["木(Wood)"] == wx_str.count("木")
        assert wx_dict["水(Water)"] == wx_str.count("水")
        assert wx_dict["火(Fire)"] == wx_str.count("火")
        assert wx_dict["土(Earth)"] == wx_str.count("土")

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_shensha_detail_is_dict(
        self, year, month, day, hour, minute, gender, label
    ):
        chart = _make_chart(year, month, day, hour, minute, gender)
        assert isinstance(chart["shensha_detail"], dict)
        for key in chart["shensha_detail"]:
            assert isinstance(key, int)
            assert isinstance(chart["shensha_detail"][key], list)

    @pytest.mark.parametrize(
        "year,month,day,hour,minute,gender,label",
        TEST_CASES,
        ids=[tc[-1] for tc in TEST_CASES],
    )
    def test_shensha_list_matches_detail(
        self, year, month, day, hour, minute, gender, label
    ):
        """shensha list should be the formatted version of shensha_detail."""
        chart = _make_chart(year, month, day, hour, minute, gender)
        detail = chart["shensha_detail"]
        formatted = chart["shensha"]
        for i in range(4):
            expected = " ".join(detail.get(i, []))
            assert formatted[i] == expected, (
                f"Shensha mismatch at index {i} for {label}: "
                f"'{formatted[i]}' vs '{expected}'"
            )
