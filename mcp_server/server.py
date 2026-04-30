# -*- coding: utf-8 -*-
"""
FOR-BAZI MCP Server
====================
Model Context Protocol (MCP) server for Chinese calendar and Bazi (八字) calculations.
Exposes Bazi engine functions as MCP tools for use with Claude Desktop and other MCP clients.

Run:
    python -m mcp_server.server

Or directly:
    python mcp_server/server.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# ── Ensure project root is on sys.path so we can import engine / tools / prompts ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from lunar_python import Solar

# ── Import project modules ──
from engine.bazi_engine import calculate_professional_bazi
from engine.shensha import calculate_shensha, format_shensha_for_pillars
from tools.bazi_tools import (
    get_annual_fortune,
    query_xing_chong_he_hai,
    query_qiongtong_guidance,
    explain_shensha,
)
from prompts.ancient_texts import get_qiongtong_for_tool

# ══════════════════════════════════════════════════════════════════════════
# MCP Server
# ══════════════════════════════════════════════════════════════════════════

server = Server("for-bazi")

# ── Tool definitions ──────────────────────────────────────────────────────

TOOLS: List[types.Tool] = [
    types.Tool(
        name="get_bazi",
        description=(
            "计算八字命盘 (Calculate a full Bazi / Four Pillars chart). "
            "Given a solar datetime and gender, return the four pillars, hidden stems, "
            "nayin, shensha, dayun, wuxing balance, xingchong, and more. "
            "接受公历出生日期时间与性别，返回四柱、藏干、纳音、神煞、大运、五行、刑冲合害等完整命盘信息。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "公历出生日期时间，格式：YYYY-MM-DD HH:MM:SS，如 '1990-05-15 08:30:00'",
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female"],
                    "description": "性别：male (乾造) 或 female (坤造)",
                },
            },
            "required": ["datetime_str", "gender"],
        },
    ),
    types.Tool(
        name="get_annual_ganzhi",
        description=(
            "查询某年的干支与纳音 (Get the Ganzhi / Heavenly Stems and Earthly Branches for a given year). "
            "Given a Gregorian year, return its ganzhi and nayin. "
            "接受公历年份，返回该年干支和纳音。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "year": {
                    "type": "integer",
                    "description": "公历年份，如 2026",
                },
            },
            "required": ["year"],
        },
    ),
    types.Tool(
        name="get_lunar_date",
        description=(
            "将公历日期转换为农历日期 (Convert a solar date to a lunar date). "
            "Given a solar date, return the corresponding lunar date with zodiac, festival info, etc. "
            "接受公历日期，返回对应农历日期、生肖、节气等信息。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "date_str": {
                    "type": "string",
                    "description": "公历日期，格式：YYYY-MM-DD，如 '1990-05-15'",
                },
            },
            "required": ["date_str"],
        },
    ),
    types.Tool(
        name="get_dayun",
        description=(
            "获取大运序列 (Get the Dayun / Major Luck Period sequence for a Bazi chart). "
            "Given a birth datetime and gender, return the full dayun sequence with start ages and ganzhi. "
            "接受出生日期时间与性别，返回大运序列（起始年龄、起始年份、干支）。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "公历出生日期时间，格式：YYYY-MM-DD HH:MM:SS",
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female"],
                    "description": "性别：male 或 female",
                },
            },
            "required": ["datetime_str", "gender"],
        },
    ),
    types.Tool(
        name="get_shensha",
        description=(
            "获取神煞信息 (Get Shen Sha / Spirit Sha for a Bazi chart). "
            "Given a birth datetime and gender, calculate and return all shensha (auspicious/inauspicious stars) "
            "for each pillar. 接受出生日期时间与性别，返回四柱各柱的神煞（桃花、驿马、华盖、天乙贵人、羊刃、禄神、文昌、将星等）。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "公历出生日期时间，格式：YYYY-MM-DD HH:MM:SS",
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female"],
                    "description": "性别：male 或 female",
                },
            },
            "required": ["datetime_str", "gender"],
        },
    ),
    types.Tool(
        name="check_xingchong",
        description=(
            "检查刑冲合害关系 (Check Xing/Chong/He/Hai relationships between pillars). "
            "Given a birth datetime and gender, analyze the six clashes, six combinations, "
            "punishments, harms, three-harmony, and three-meeting relationships in the chart. "
            "接受出生日期时间与性别，分析四柱间的冲、合、刑、害、破、三合、三会、半三合关系。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "公历出生日期时间，格式：YYYY-MM-DD HH:MM:SS",
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female"],
                    "description": "性别：male 或 female",
                },
                "relation_type": {
                    "type": "string",
                    "description": "可选，指定查询的关系类型：刑、冲、合、害、破、三合、三会、半三合。不传则返回所有关系。",
                },
            },
            "required": ["datetime_str", "gender"],
        },
    ),
    types.Tool(
        name="get_qiongtong_guidance",
        description=(
            "查询穷通宝鉴调候用神 (Get Qiongtong Baojian guidance for a day master + month). "
            "Given a day master heavenly stem and month earthly branch, return the seasonal adjustment "
            "guidance from the classic text Qiongtong Baojian. "
            "接受日主天干和月支，返回《穷通宝鉴》调候用神指引（用神、原文、白话释义）。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "day_master": {
                    "type": "string",
                    "description": "日主天干，如 '甲'、'乙'、'丙' 等",
                },
                "month_zhi": {
                    "type": "string",
                    "description": "月支地支，如 '寅'、'卯'、'辰' 等",
                },
            },
            "required": ["day_master", "month_zhi"],
        },
    ),
]


# ── list_tools handler ────────────────────────────────────────────────────

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return TOOLS


# ── Helper: parse datetime string ────────────────────────────────────────

def _parse_datetime(dt_str: str) -> datetime:
    """Parse a datetime string in common formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(
        f"无法解析日期时间字符串 '{dt_str}'。"
        f"请使用格式：YYYY-MM-DD HH:MM:SS"
    )


def _gender_str(gender: str) -> str:
    """Convert gender enum to the format expected by the engine."""
    return "乾造 (Male)" if gender == "male" else "坤造 (Female)"


def _parse_date(date_str: str) -> datetime:
    """Parse a date string (no time component)."""
    formats = ["%Y-%m-%d", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(
        f"无法解析日期字符串 '{date_str}'。"
        f"请使用格式：YYYY-MM-DD"
    )


# ── call_tool handler ─────────────────────────────────────────────────────

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> list[types.TextContent]:
    """Dispatch tool calls to the appropriate handler."""

    try:
        result = await _dispatch(name, arguments)
    except ValueError as e:
        result = {"error": str(e)}
    except Exception as e:
        result = {"error": f"工具调用失败: {type(e).__name__}: {e}"}

    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def _dispatch(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Route a tool call to its implementation."""

    # ── get_bazi ──────────────────────────────────────────────────────
    if name == "get_bazi":
        dt = _parse_datetime(arguments["datetime_str"])
        gender = _gender_str(arguments["gender"])
        bazi_data = calculate_professional_bazi(dt, gender)
        # Restructure for cleaner JSON output
        return {
            "gender": bazi_data["gender"],
            "pillars": {
                "year": bazi_data["pillars"][0],
                "month": bazi_data["pillars"][1],
                "day": bazi_data["pillars"][2],
                "time": bazi_data["pillars"][3],
            },
            "day_master": bazi_data["day_master"],
            "ten_gods": {
                "year": bazi_data["tg_gan"][0],
                "month": bazi_data["tg_gan"][1],
                "day": "日主",
                "time": bazi_data["tg_gan"][3],
            },
            "ten_gods_zhi": {
                "year": bazi_data["tg_zhi"][0],
                "month": bazi_data["tg_zhi"][1],
                "day": bazi_data["tg_zhi"][2],
                "time": bazi_data["tg_zhi"][3],
            },
            "nayin": {
                "year": bazi_data["nayin"][0],
                "month": bazi_data["nayin"][1],
                "day": bazi_data["nayin"][2],
                "time": bazi_data["nayin"][3],
            },
            "shensha": {
                "year": bazi_data["shensha"][0],
                "month": bazi_data["shensha"][1],
                "day": bazi_data["shensha"][2],
                "time": bazi_data["shensha"][3],
            },
            "wuxing": bazi_data["wuxing"],
            "dayun": bazi_data["dayun"],
            "minggong": bazi_data["minggong"],
            "taiyuan": bazi_data["taiyuan"],
            "taixi": bazi_data["taixi"],
            "shengong": bazi_data["shengong"],
            "dishi": {
                "year": bazi_data["dishi"][0],
                "month": bazi_data["dishi"][1],
                "day": bazi_data["dishi"][2],
                "time": bazi_data["dishi"][3],
            },
            "xunkong": {
                "year": bazi_data["xunkong"][0],
                "month": bazi_data["xunkong"][1],
                "day": bazi_data["xunkong"][2],
                "time": bazi_data["xunkong"][3],
            },
            "xingchong": bazi_data["xingchong"],
        }

    # ── get_annual_ganzhi ─────────────────────────────────────────────
    elif name == "get_annual_ganzhi":
        year = int(arguments["year"])
        raw = json.loads(get_annual_fortune(year))
        return raw

    # ── get_lunar_date ────────────────────────────────────────────────
    elif name == "get_lunar_date":
        dt = _parse_date(arguments["date_str"])
        solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, 12, 0, 0)
        lunar = solar.getLunar()
        return {
            "solar_date": arguments["date_str"],
            "lunar_year": lunar.getYearInChinese(),
            "lunar_month": lunar.getMonthInChinese(),
            "lunar_day": lunar.getDayInChinese(),
            "lunar_full": f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}日",
            "year_ganzhi": lunar.getYearInGanZhi(),
            "month_ganzhi": lunar.getMonthInGanZhi(),
            "day_ganzhi": lunar.getDayInGanZhi(),
            "time_ganzhi": lunar.getTimeInGanZhi(),
            "zodiac": lunar.getYearShengXiao(),
            "year_nayin": lunar.getYearNaYin(),
            "is_leap_month": lunar.getMonth() < 0,
            "jieqi": lunar.getJieQi(),
            "first_day_of_month_jieqi": lunar.getCurrentJieQi(),
        }

    # ── get_dayun ─────────────────────────────────────────────────────
    elif name == "get_dayun":
        dt = _parse_datetime(arguments["datetime_str"])
        gender = _gender_str(arguments["gender"])
        bazi_data = calculate_professional_bazi(dt, gender)
        return {
            "gender": bazi_data["gender"],
            "pillars": bazi_data["pillars"],
            "day_master": bazi_data["day_master"],
            "dayun": bazi_data["dayun"],
        }

    # ── get_shensha ───────────────────────────────────────────────────
    elif name == "get_shensha":
        dt = _parse_datetime(arguments["datetime_str"])
        gender = _gender_str(arguments["gender"])
        bazi_data = calculate_professional_bazi(dt, gender)
        pillars = bazi_data["pillars"]
        labels = ["年柱", "月柱", "日柱", "时柱"]
        shensha_by_pillar = {}
        for i, label in enumerate(labels):
            names = bazi_data["shensha"][i]
            shensha_by_pillar[label] = {
                "pillar": pillars[i],
                "shensha": names if names else "无",
            }
        return {
            "pillars": pillars,
            "day_master": bazi_data["day_master"],
            "shensha_by_pillar": shensha_by_pillar,
            "shensha_detail": {
                str(k): v for k, v in (bazi_data.get("shensha_detail") or {}).items()
            },
        }

    # ── check_xingchong ───────────────────────────────────────────────
    elif name == "check_xingchong":
        dt = _parse_datetime(arguments["datetime_str"])
        gender = _gender_str(arguments["gender"])
        bazi_data = calculate_professional_bazi(dt, gender)
        relation_type = arguments.get("relation_type", "")
        bazi_data_for_tool = {
            "pillars": bazi_data["pillars"],
            "xingchong": bazi_data["xingchong"],
        }
        raw = json.loads(query_xing_chong_he_hai(bazi_data_for_tool, relation_type))
        raw["pillars"] = bazi_data["pillars"]
        return raw

    # ── get_qiongtong_guidance ────────────────────────────────────────
    elif name == "get_qiongtong_guidance":
        day_master = arguments["day_master"].strip()
        month_zhi = arguments["month_zhi"].strip()
        # Validate inputs
        valid_gan = set("甲乙丙丁戊己庚辛壬癸")
        valid_zhi = set("子丑寅卯辰巳午未申酉戌亥")
        if day_master not in valid_gan:
            return {"error": f"无效的日主天干 '{day_master}'，应为：{'、'.join(sorted(valid_gan))}"}
        if month_zhi not in valid_zhi:
            return {"error": f"无效的月支 '{month_zhi}'，应为：{'、'.join(sorted(valid_zhi))}"}
        result = get_qiongtong_for_tool(day_master, month_zhi)
        return result

    else:
        return {"error": f"未知工具: {name}", "available": [t.name for t in TOOLS]}


# ══════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════

async def main():
    """Run the MCP server over stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="for-bazi",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
