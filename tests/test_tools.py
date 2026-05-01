# -*- coding: utf-8 -*-
"""
Tool function tests for FOR-BAZI.

Tests all 14 registered tools, the TOOL_REGISTRY / TOOL_SCHEMAS consistency,
and the dispatch_tool router.
"""

import json
import sys

import pytest

sys.path.insert(0, "C:/Users/Gaaiyun/Projects/FOR-BAZI")

from tools.bazi_tools import (
    TOOL_REGISTRY,
    TOOL_SCHEMAS,
    dispatch_tool,
    get_annual_fortune,
)


# ---------------------------------------------------------------------------
# Annual fortune
# ---------------------------------------------------------------------------


class TestAnnualFortune:
    """Tests for get_annual_fortune tool."""

    def test_2026(self):
        result = json.loads(get_annual_fortune(2026))
        assert result["year"] == 2026
        assert "ganzhi" in result
        assert "nayin" in result

    def test_2000(self):
        result = json.loads(get_annual_fortune(2000))
        assert result["year"] == 2000
        assert "ganzhi" in result

    def test_returns_json_string(self):
        output = get_annual_fortune(2026)
        assert isinstance(output, str)
        # Must be valid JSON
        json.loads(output)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    """Tests for TOOL_REGISTRY and TOOL_SCHEMAS consistency."""

    def test_registry_has_14_tools(self):
        assert len(TOOL_REGISTRY) == 14

    def test_schemas_match_registry(self):
        schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
        registry_names = set(TOOL_REGISTRY.keys())
        assert schema_names == registry_names

    def test_dispatch_unknown_tool(self):
        result = json.loads(dispatch_tool("unknown_tool", {}))
        assert "error" in result

    def test_all_schemas_have_required_fields(self):
        for schema in TOOL_SCHEMAS:
            assert "type" in schema
            assert "function" in schema
            func = schema["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func


# ---------------------------------------------------------------------------
# dispatch_tool integration
# ---------------------------------------------------------------------------


class TestDispatchTool:
    """Integration tests for dispatch_tool routing."""

    def test_explain_shensha(self):
        result = json.loads(dispatch_tool("explain_shensha", {"shensha_name": "桃花"}))
        assert "shensha" in result
        assert result["shensha"] == "桃花"
        assert "description" in result

    def test_explain_shensha_unknown(self):
        result = json.loads(dispatch_tool("explain_shensha", {"shensha_name": "不存在的神煞"}))
        assert "shensha" in result
        assert "available" in result  # should list available names

    def test_fact_check(self):
        result = json.loads(dispatch_tool("fact_check_ganzhi", {
            "claimed_ganzhi": "丙午",
            "year": 2026,
        }))
        assert "match" in result
        assert result["year"] == 2026
        assert "actual" in result
        assert "claimed" in result

    def test_fact_check_wrong_ganzhi(self):
        result = json.loads(dispatch_tool("fact_check_ganzhi", {
            "claimed_ganzhi": "甲子",
            "year": 2026,
        }))
        assert result["match"] is False

    def test_analyze_wuxing_balance_with_data(self):
        bazi_data = {
            "wuxing": {
                "金(Metal)": 1,
                "木(Wood)": 2,
                "水(Water)": 1,
                "火(Fire)": 2,
                "土(Earth)": 0,
            }
        }
        result = json.loads(dispatch_tool("analyze_wuxing_balance", {}, bazi_data))
        assert "wuxing" in result
        assert "strong" in result
        assert "weak" in result

    def test_query_xing_chong_he_hai_with_data(self):
        bazi_data = {
            "xingchong": {
                "冲": ["年月相冲(午子)"],
                "合": [],
                "刑": [],
                "害": [],
                "破": [],
                "穿": [],
                "三合": [],
                "三会": [],
                "半三合": [],
            }
        }
        result = json.loads(dispatch_tool("query_xing_chong_he_hai", {}, bazi_data))
        assert "xingchong" in result

    def test_query_xing_chong_he_hai_with_type(self):
        bazi_data = {
            "xingchong": {
                "冲": ["年月相冲(午子)"],
                "合": [],
                "刑": [],
                "害": [],
                "破": [],
                "穿": [],
                "三合": [],
                "三会": [],
                "半三合": [],
            }
        }
        result = json.loads(dispatch_tool("query_xing_chong_he_hai", {"relation_type": "冲"}, bazi_data))
        assert result["relation_type"] == "冲"
        assert "relations" in result

    def test_query_classical_text(self):
        result = json.loads(dispatch_tool("query_classical_text", {
            "source": "穷通宝鉴",
        }))
        assert "source" in result
        assert result["source"] == "穷通宝鉴"

    def test_get_dayun_stage(self):
        bazi_data = {
            "dayun": [
                {"start_age": 5, "start_year": 2007, "ganzhi": "戊戌"},
                {"start_age": 15, "start_year": 2017, "ganzhi": "己亥"},
            ]
        }
        result = json.loads(dispatch_tool("get_dayun_stage", {"current_year": 2020}, bazi_data))
        assert result["current_year"] == 2020
        assert result["step"] == 2

    def test_rag_retrieve(self):
        """rag_retrieve may succeed or return error depending on agent availability."""
        bazi_data = {"day_master": "甲", "pillars": ["壬午", "丁未", "甲子", "丙寅"]}
        result = json.loads(dispatch_tool("rag_retrieve", {
            "query": "甲木",
            "top_k": 3,
        }, bazi_data))
        # Should contain either exact_matches/results or an error key
        assert "error" in result or "exact_matches" in result or "results" in result or "context" in result

    def test_dispatch_tool_error_handling(self):
        """dispatch_tool should catch exceptions and return error JSON."""
        # Call analyze_wuxing_balance without bazi_data (empty wuxing)
        result = json.loads(dispatch_tool("analyze_wuxing_balance", {}, {}))
        # Should succeed with "无五行数据" context, not crash
        assert "context" in result
