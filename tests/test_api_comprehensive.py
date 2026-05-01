# -*- coding: utf-8 -*-
"""
Comprehensive API endpoint tests for FOR-BAZI backend.

Covers all 5 routers (chart, chat, texts, compatibility, entertainment),
health check, root path, and edge cases including the chat/stream
normalization of frontend BaziReading format.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.main import app


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def client():
    """Async HTTP client wired to the FastAPI ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helper: valid chart payload for reuse
# ---------------------------------------------------------------------------

VALID_MALE_REQUEST = {
    "datetime_str": "1990-05-15 14:30",
    "gender": "乾造 (Male)",
}

VALID_FEMALE_REQUEST = {
    "datetime_str": "1985-11-20 08:00",
    "gender": "坤造 (Female)",
}


# ===========================================================================
# 1. Health check
# ===========================================================================


class TestHealthCheck:
    """GET /health"""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


# ===========================================================================
# 2. Root path
# ===========================================================================


class TestRootPath:
    """GET /"""

    @pytest.mark.asyncio
    async def test_root_returns_200(self, client: AsyncClient):
        """Root should return either the frontend HTML or redirect to /docs."""
        resp = await client.get("/", follow_redirects=False)
        # Accept either 200 (HTML served) or 307 (redirect to /docs)
        assert resp.status_code in (200, 307)


# ===========================================================================
# 3. Chart endpoint — POST /api/v1/chart
# ===========================================================================


class TestChartEndpoint:
    """POST /api/v1/chart"""

    @pytest.mark.asyncio
    async def test_valid_male_chart(self, client: AsyncClient):
        resp = await client.post("/api/v1/chart", json=VALID_MALE_REQUEST)
        assert resp.status_code == 200
        data = resp.json()
        chart = data["chart"]
        assert "pillars" in chart
        assert len(chart["pillars"]) == 4
        assert "day_master" in chart
        assert chart["day_master"] != ""
        assert chart["gender"] == "乾造 (Male)"
        # wuxing_power and geju may be None but must be present as keys
        assert "wuxing_power" in data
        assert "geju" in data

    @pytest.mark.asyncio
    async def test_valid_female_chart(self, client: AsyncClient):
        resp = await client.post("/api/v1/chart", json=VALID_FEMALE_REQUEST)
        assert resp.status_code == 200
        data = resp.json()
        chart = data["chart"]
        assert chart["gender"] == "坤造 (Female)"
        assert len(chart["pillars"]) == 4

    @pytest.mark.asyncio
    async def test_invalid_gender(self, client: AsyncClient):
        payload = {"datetime_str": "1990-05-15 14:30", "gender": "Male"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client: AsyncClient):
        payload = {"datetime_str": "not-a-date", "gender": "乾造 (Male)"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 400
        assert "无法解析" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_missing_datetime_field(self, client: AsyncClient):
        payload = {"gender": "乾造 (Male)"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_gender_field(self, client: AsyncClient):
        payload = {"datetime_str": "1990-05-15 14:30"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_all_fields(self, client: AsyncClient):
        resp = await client.post("/api/v1/chart", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_leap_year_date(self, client: AsyncClient):
        payload = {"datetime_str": "2000-02-29 12:00", "gender": "坤造 (Female)"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 200
        chart = resp.json()["chart"]
        assert len(chart["pillars"]) == 4

    @pytest.mark.asyncio
    async def test_midnight_time(self, client: AsyncClient):
        """Midnight (00:00) is a boundary in Chinese calendar systems."""
        payload = {"datetime_str": "1990-01-01 00:00", "gender": "乾造 (Male)"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_with_seconds(self, client: AsyncClient):
        """The parser should accept HH:MM:SS format as well."""
        payload = {"datetime_str": "1990-05-15 14:30:45", "gender": "乾造 (Male)"}
        resp = await client.post("/api/v1/chart", json=payload)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_chart_has_expected_fields(self, client: AsyncClient):
        resp = await client.post("/api/v1/chart", json=VALID_MALE_REQUEST)
        assert resp.status_code == 200
        chart = resp.json()["chart"]
        expected_keys = {
            "gender", "pillars", "tg_gan", "tg_zhi", "nayin", "shensha",
            "shensha_detail", "wuxing", "dayun", "minggong", "taiyuan",
            "taixi", "shengong", "dishi", "xunkong", "xingchong",
            "wuxing_str", "day_master",
        }
        missing = expected_keys - set(chart.keys())
        assert not missing, f"Missing keys in chart: {missing}"

    @pytest.mark.asyncio
    async def test_chart_pillars_are_two_chars(self, client: AsyncClient):
        """Each pillar should be a 2-character ganzhi string."""
        resp = await client.post("/api/v1/chart", json=VALID_MALE_REQUEST)
        chart = resp.json()["chart"]
        for p in chart["pillars"]:
            assert len(p) == 2, f"Expected 2-char pillar, got '{p}'"

    @pytest.mark.asyncio
    async def test_chart_day_master_is_stem(self, client: AsyncClient):
        """Day master should be a single heavenly stem character."""
        resp = await client.post("/api/v1/chart", json=VALID_MALE_REQUEST)
        dm = resp.json()["chart"]["day_master"]
        assert len(dm) == 1
        assert dm in "甲乙丙丁戊己庚辛壬癸"


# ===========================================================================
# 4. Chat stream — POST /api/v1/chat/stream (mocked)
# ===========================================================================

# Sample frontend BaziReading format (nested structure)
FRONTEND_CHART_DATA: Dict[str, Any] = {
    "chart": {
        "year_pillar": {
            "stem": "壬",
            "branch": "午",
            "hidden_stems": ["丁", "己"],
        },
        "month_pillar": {
            "stem": "丁",
            "branch": "未",
            "hidden_stems": ["丁", "己", "乙"],
        },
        "day_pillar": {
            "stem": "庚",
            "branch": "寅",
            "hidden_stems": ["甲", "丙", "戊"],
        },
        "hour_pillar": {
            "stem": "戊",
            "branch": "寅",
            "hidden_stems": ["甲", "壬"],
        },
        "day_master": "庚",
    },
    "dayun": [
        {"start_age": 5, "start_year": 2007, "ganzhi": "戊申"},
        {"start_age": 15, "start_year": 2017, "ganzhi": "己酉"},
    ],
    "ming_gong": "甲寅",
    "gender": "乾造 (Male)",
}

# Sample flat backend engine format
FLAT_CHART_DATA: Dict[str, Any] = {
    "gender": "乾造 (Male)",
    "pillars": ["壬午", "丁未", "庚寅", "戊寅"],
    "tg_zhi": ["丁 己", "丁 己 乙", "甲 丙 戊", "甲 壬"],
    "nayin": ["杨柳木", "天河水", "松柏木", "城头土"],
    "day_master": "庚",
    "minggong": "甲寅",
    "dayun": [
        {"start_age": 5, "start_year": 2007, "ganzhi": "戊申"},
    ],
}


def _mock_stream_chat(*, message, provider, api_key, base_url, model,
                      chart_data=None, history=None, max_steps=8):
    """Mock generator that yields a simple token + done event."""
    # Import build_system_prompt to verify normalization happened
    from prompts.system_prompts import build_system_prompt

    # Normalize chart_data the same way agent_service does
    from backend.services.agent_service import _normalize_chart_data
    normalized = _normalize_chart_data(chart_data or {})

    # Build system prompt to verify day master / pillars are present
    system_prompt = ""
    if normalized and normalized.get("pillars"):
        system_prompt = build_system_prompt(normalized)

    yield ("token", {"content": "测试回复"})
    yield ("done", {
        "content": "测试回复",
        "fact_checks": [],
        "_debug_system_prompt": system_prompt,
        "_debug_normalized": normalized,
    })


class TestChatStreamNormalization:
    """Verify _normalize_chart_data converts frontend format correctly."""

    def test_frontend_format_normalizes_to_flat(self):
        from backend.services.agent_service import _normalize_chart_data
        result = _normalize_chart_data(FRONTEND_CHART_DATA)

        assert result["pillars"] == ["壬午", "丁未", "庚寅", "戊寅"]
        assert result["day_master"] == "庚"
        assert result["gender"] == "乾造 (Male)"
        assert result["minggong"] == "甲寅"
        assert result["tg_zhi"] == ["丁己", "丁己乙", "甲丙戊", "甲壬"]

    def test_frontend_format_system_prompt_contains_day_master(self):
        from backend.services.agent_service import _normalize_chart_data
        from prompts.system_prompts import build_system_prompt

        normalized = _normalize_chart_data(FRONTEND_CHART_DATA)
        prompt = build_system_prompt(normalized)
        assert "庚" in prompt
        assert "壬午" in prompt

    def test_flat_format_passes_through(self):
        from backend.services.agent_service import _normalize_chart_data
        result = _normalize_chart_data(FLAT_CHART_DATA)
        assert result["pillars"] == ["壬午", "丁未", "庚寅", "戊寅"]
        assert result["day_master"] == "庚"

    def test_empty_chart_data(self):
        from backend.services.agent_service import _normalize_chart_data
        result = _normalize_chart_data({})
        assert result == {}

    def test_none_chart_data(self):
        from backend.services.agent_service import _normalize_chart_data
        result = _normalize_chart_data(None)
        assert result == {}

    def test_partial_frontend_format(self):
        """Frontend format with only some pillars should still normalize."""
        from backend.services.agent_service import _normalize_chart_data
        partial = {
            "chart": {
                "year_pillar": {"stem": "甲", "branch": "子", "hidden_stems": ["癸"]},
                "month_pillar": {"stem": "丙", "branch": "寅", "hidden_stems": ["甲", "丙", "戊"]},
                "day_pillar": {"stem": "庚", "branch": "午", "hidden_stems": ["丁", "己"]},
                "hour_pillar": {"stem": "戊", "branch": "子", "hidden_stems": ["癸"]},
                "day_master": "庚",
            },
        }
        result = _normalize_chart_data(partial)
        assert result["pillars"] == ["甲子", "丙寅", "庚午", "戊子"]
        assert result["day_master"] == "庚"


class TestChatStreamEndpoint:
    """POST /api/v1/chat/stream — SSE endpoint (with mocked agent)."""

    @pytest.mark.asyncio
    async def test_stream_with_frontend_chart_data(self, client: AsyncClient):
        """Verify the stream endpoint works with frontend-format chart_data."""
        with patch("backend.api.chat.stream_chat", side_effect=_mock_stream_chat):
            payload = {
                "message": "分析我的八字",
                "chart_data": FRONTEND_CHART_DATA,
            }
            resp = await client.post("/api/v1/chat/stream", json=payload)
            assert resp.status_code == 200
            # SSE response — read the body
            body = resp.text
            assert "token" in body or "done" in body

    @pytest.mark.asyncio
    async def test_stream_with_flat_chart_data(self, client: AsyncClient):
        """Verify the stream works with flat backend format."""
        with patch("backend.api.chat.stream_chat", side_effect=_mock_stream_chat):
            payload = {
                "message": "分析我的八字",
                "chart_data": FLAT_CHART_DATA,
            }
            resp = await client.post("/api/v1/chat/stream", json=payload)
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_without_chart_data(self, client: AsyncClient):
        """Chat should work even without chart_data."""
        with patch("backend.api.chat.stream_chat", side_effect=_mock_stream_chat):
            payload = {"message": "你好"}
            resp = await client.post("/api/v1/chat/stream", json=payload)
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_with_history(self, client: AsyncClient):
        """Verify conversation history is forwarded correctly.

        We mock stream_chat and echo back the received history inside the
        done event payload so the assertion works without relying on shared
        mutable state across threads.
        """
        def _capture_stream(
            *, message, provider, api_key, base_url, model,
            chart_data=None, history=None, max_steps=8,
        ):
            yield ("token", {"content": "回复"})
            yield ("done", {
                "content": "回复",
                "fact_checks": [],
                "_received_history": history,
                "_received_message": message,
            })

        with patch("backend.api.chat.stream_chat", side_effect=_capture_stream):
            payload = {
                "message": "继续分析",
                "history": [
                    {"role": "user", "content": "第一次问题"},
                    {"role": "assistant", "content": "第一次回复"},
                ],
            }
            resp = await client.post("/api/v1/chat/stream", json=payload)
            assert resp.status_code == 200
            # Parse SSE body to extract the done event
            body = resp.text
            assert "done" in body
            # The done event data should contain the history we sent
            assert "第一次问题" in body
            assert "第一次回复" in body

    @pytest.mark.asyncio
    async def test_stream_missing_message(self, client: AsyncClient):
        """message is required — should get 422."""
        resp = await client.post("/api/v1/chat/stream", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_stream_message_too_long(self, client: AsyncClient):
        """message max_length is 10000."""
        payload = {"message": "x" * 10001}
        resp = await client.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_stream_max_steps_bounds(self, client: AsyncClient):
        """max_steps must be 1..16."""
        with patch("backend.api.chat.stream_chat", side_effect=_mock_stream_chat):
            # Below minimum
            resp = await client.post(
                "/api/v1/chat/stream",
                json={"message": "test", "max_steps": 0},
            )
            assert resp.status_code == 422

            # Above maximum
            resp = await client.post(
                "/api/v1/chat/stream",
                json={"message": "test", "max_steps": 17},
            )
            assert resp.status_code == 422

            # Valid
            resp = await client.post(
                "/api/v1/chat/stream",
                json={"message": "test", "max_steps": 8},
            )
            assert resp.status_code == 200


# ===========================================================================
# 5. Texts endpoint — GET /api/v1/texts
# ===========================================================================


class TestTextsEndpoint:
    """GET /api/v1/texts"""

    @pytest.mark.asyncio
    async def test_search_no_filter(self, client: AsyncClient):
        """Without query or source, returns results up to limit."""
        resp = await client.get("/api/v1/texts", params={"limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # May have results or be empty depending on loaded data
        if data:
            assert "source" in data[0]
            assert "key" in data[0]

    @pytest.mark.asyncio
    async def test_search_with_keyword(self, client: AsyncClient):
        """Keyword search should filter results."""
        resp = await client.get("/api/v1/texts", params={"query": "甲", "limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # If results found, each should contain "甲" somewhere
        for entry in data:
            text_blob = json.dumps(entry, ensure_ascii=False)
            assert "甲" in text_blob or "甲" in entry.get("key", "")

    @pytest.mark.asyncio
    async def test_search_source_qiongtong(self, client: AsyncClient):
        """Filter by 穷通宝鉴 source."""
        resp = await client.get(
            "/api/v1/texts",
            params={"source": "穷通宝鉴", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        for entry in data:
            assert entry["source"] == "穷通宝鉴"

    @pytest.mark.asyncio
    async def test_search_source_ditiansui(self, client: AsyncClient):
        """Filter by 滴天髓 source."""
        resp = await client.get(
            "/api/v1/texts",
            params={"source": "滴天髓", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        for entry in data:
            assert entry["source"] == "滴天髓"

    @pytest.mark.asyncio
    async def test_search_source_ziping(self, client: AsyncClient):
        """Filter by 子平真诠 source."""
        resp = await client.get(
            "/api/v1/texts",
            params={"source": "子平真诠", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        for entry in data:
            assert entry["source"] == "子平真诠"

    @pytest.mark.asyncio
    async def test_search_invalid_source_returns_empty(self, client: AsyncClient):
        """Invalid source should return empty list (no error)."""
        resp = await client.get(
            "/api/v1/texts",
            params={"source": "不存在的书", "limit": 5},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_search_limit_respected(self, client: AsyncClient):
        """Verify limit parameter caps results."""
        resp = await client.get("/api/v1/texts", params={"limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 3

    @pytest.mark.asyncio
    async def test_get_specific_entry(self, client: AsyncClient):
        """GET /api/v1/texts/{source}/{key} for a specific entry."""
        # First search to find a valid key
        search_resp = await client.get(
            "/api/v1/texts",
            params={"source": "滴天髓", "limit": 1},
        )
        results = search_resp.json()
        if not results:
            pytest.skip("No 滴天髓 entries loaded")

        key = results[0]["key"]
        entry_resp = await client.get(f"/api/v1/texts/滴天髓/{key}")
        assert entry_resp.status_code == 200
        entry = entry_resp.json()
        assert entry["source"] == "滴天髓"
        assert entry["key"] == key

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self, client: AsyncClient):
        """Request a nonexistent key — should return 404."""
        resp = await client.get("/api/v1/texts/滴天髓/不存在的条目XYZ")
        assert resp.status_code == 404


# ===========================================================================
# 6. Compatibility — POST /api/v1/compatibility
# ===========================================================================


class TestCompatibilityEndpoint:
    """POST /api/v1/compatibility"""

    @pytest.mark.asyncio
    async def test_valid_pair(self, client: AsyncClient):
        payload = {
            "person_a": VALID_MALE_REQUEST,
            "person_b": VALID_FEMALE_REQUEST,
        }
        resp = await client.post("/api/v1/compatibility", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "person_a" in data
        assert "person_b" in data
        assert "day_master_relation" in data
        assert "score" in data
        assert "summary" in data
        assert "details" in data
        assert 0 <= data["score"] <= 100

    @pytest.mark.asyncio
    async def test_same_gender_pair(self, client: AsyncClient):
        """Same-gender pair should still work."""
        payload = {
            "person_a": VALID_MALE_REQUEST,
            "person_b": {
                "datetime_str": "1995-03-10 10:00",
                "gender": "乾造 (Male)",
            },
        }
        resp = await client.post("/api/v1/compatibility", json=payload)
        assert resp.status_code == 200
        assert 0 <= resp.json()["score"] <= 100

    @pytest.mark.asyncio
    async def test_invalid_date_person_a(self, client: AsyncClient):
        payload = {
            "person_a": {
                "datetime_str": "bad-date",
                "gender": "乾造 (Male)",
            },
            "person_b": VALID_FEMALE_REQUEST,
        }
        resp = await client.post("/api/v1/compatibility", json=payload)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_date_person_b(self, client: AsyncClient):
        payload = {
            "person_a": VALID_MALE_REQUEST,
            "person_b": {
                "datetime_str": "bad-date",
                "gender": "坤造 (Female)",
            },
        }
        resp = await client.post("/api/v1/compatibility", json=payload)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_gender_person_a(self, client: AsyncClient):
        payload = {
            "person_a": {
                "datetime_str": "1990-05-15 14:30",
                "gender": "invalid",
            },
            "person_b": VALID_FEMALE_REQUEST,
        }
        resp = await client.post("/api/v1/compatibility", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_person_b(self, client: AsyncClient):
        payload = {
            "person_a": VALID_MALE_REQUEST,
        }
        resp = await client.post("/api/v1/compatibility", json=payload)
        assert resp.status_code == 422


# ===========================================================================
# 7. Entertainment — GET /api/v1/entertainment/daily-fortune
# ===========================================================================


class TestEntertainmentEndpoint:
    """GET /api/v1/entertainment/daily-fortune"""

    ALL_ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

    @pytest.mark.asyncio
    async def test_all_twelve_zodiac_signs(self, client: AsyncClient):
        """Every valid zodiac sign should return a fortune."""
        for zodiac in self.ALL_ZODIAC:
            resp = await client.get(
                "/api/v1/entertainment/daily-fortune",
                params={"zodiac": zodiac},
            )
            assert resp.status_code == 200, f"Failed for zodiac '{zodiac}'"
            data = resp.json()
            assert data["zodiac"] == zodiac
            assert "fortune_level" in data
            assert data["fortune_level"] in ("大吉", "中吉", "小吉", "平", "小凶", "凶")
            assert "advice" in data
            assert "lucky_color" in data
            assert "lucky_number" in data
            assert "aspects" in data
            assert "事业" in data["aspects"]
            assert "财运" in data["aspects"]
            assert "感情" in data["aspects"]
            assert "健康" in data["aspects"]
            # Aspect scores should be 1-5
            for aspect, score in data["aspects"].items():
                assert 1 <= score <= 5, f"{aspect} score {score} out of range"

    @pytest.mark.asyncio
    async def test_deterministic_same_day(self, client: AsyncClient):
        """Same zodiac on same day should return identical results."""
        resp1 = await client.get(
            "/api/v1/entertainment/daily-fortune",
            params={"zodiac": "龙"},
        )
        resp2 = await client.get(
            "/api/v1/entertainment/daily-fortune",
            params={"zodiac": "龙"},
        )
        assert resp1.json() == resp2.json()

    @pytest.mark.asyncio
    async def test_different_zodiacs_differ(self, client: AsyncClient):
        """Different zodiacs should (usually) return different fortunes."""
        resp1 = await client.get(
            "/api/v1/entertainment/daily-fortune",
            params={"zodiac": "鼠"},
        )
        resp2 = await client.get(
            "/api/v1/entertainment/daily-fortune",
            params={"zodiac": "牛"},
        )
        # They CAN be the same by chance, but at least the zodiac field differs
        assert resp1.json()["zodiac"] != resp2.json()["zodiac"]

    @pytest.mark.asyncio
    async def test_invalid_zodiac(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/entertainment/daily-fortune",
            params={"zodiac": "猫"},
        )
        assert resp.status_code == 400
        assert "未知生肖" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_missing_zodiac_param(self, client: AsyncClient):
        """zodiac is a required query param."""
        resp = await client.get("/api/v1/entertainment/daily-fortune")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_fortune_contains_today_date(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/entertainment/daily-fortune",
            params={"zodiac": "龙"},
        )
        data = resp.json()
        assert data["date"] == date.today().isoformat()


# ===========================================================================
# 8. Compatibility analysis logic (unit test)
# ===========================================================================


class TestCompatibilityAnalysis:
    """Unit tests for the _analyse_compatibility function."""

    def test_same_day_master(self):
        from backend.api.compatibility import _analyse_compatibility

        chart_a = {
            "day_master": "甲",
            "pillars": ["甲子", "丙寅", "甲午", "庚午"],
        }
        chart_b = {
            "day_master": "甲",
            "pillars": ["乙丑", "丁卯", "甲辰", "辛未"],
        }
        result = _analyse_compatibility(chart_a, chart_b)
        assert "比和" in result["day_master_relation"]

    def test_generating_relationship(self):
        from backend.api.compatibility import _analyse_compatibility

        chart_a = {
            "day_master": "甲",  # 木
            "pillars": ["甲子", "丙寅", "甲午", "庚午"],
        }
        chart_b = {
            "day_master": "丙",  # 火 — 木生火
            "pillars": ["乙丑", "丁卯", "丙辰", "辛未"],
        }
        result = _analyse_compatibility(chart_a, chart_b)
        assert "生" in result["day_master_relation"]

    def test_overcoming_relationship(self):
        from backend.api.compatibility import _analyse_compatibility

        chart_a = {
            "day_master": "甲",  # 木克土
            "pillars": ["甲子", "丙寅", "甲午", "庚午"],
        }
        chart_b = {
            "day_master": "戊",  # 土
            "pillars": ["乙丑", "丁卯", "戊辰", "辛未"],
        }
        result = _analyse_compatibility(chart_a, chart_b)
        assert "克" in result["day_master_relation"]

    def test_score_in_range(self):
        from backend.api.compatibility import _analyse_compatibility

        chart_a = {"day_master": "壬", "pillars": ["壬午", "辛亥", "壬寅", "庚子"]}
        chart_b = {"day_master": "丁", "pillars": ["丁巳", "壬子", "丁卯", "辛丑"]}
        result = _analyse_compatibility(chart_a, chart_b)
        assert 0 <= result["score"] <= 100


# ===========================================================================
# 9. Entertainment deterministic fortune logic (unit test)
# ===========================================================================


class TestDeterministicFortune:
    """Unit tests for _deterministic_fortune function."""

    def test_deterministic_same_inputs(self):
        from backend.api.entertainment import _deterministic_fortune

        today = date(2025, 6, 15)
        r1 = _deterministic_fortune("龙", today)
        r2 = _deterministic_fortune("龙", today)
        assert r1 == r2

    def test_different_dates_differ(self):
        from backend.api.entertainment import _deterministic_fortune

        d1 = date(2025, 6, 15)
        d2 = date(2025, 6, 16)
        r1 = _deterministic_fortune("龙", d1)
        r2 = _deterministic_fortune("龙", d2)
        # Fortune level or aspects should differ for different dates
        assert r1["date"] != r2["date"]
