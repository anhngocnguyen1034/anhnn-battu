# -*- coding: utf-8 -*-
"""
八字命理工具体系：流年、大运、五行、神煞、刑冲合害、Fact-Check。
导出 TOOL_SCHEMAS（OpenAI function calling）、TOOL_REGISTRY、dispatch_tool。
"""
import json
import re
from typing import Any, Dict, List

from lunar_python import Solar

from prompts.ancient_texts import get_qiongtong_for_tool
from .wuxing_calculator import calculate_wuxing_power
from .geju_analyzer import analyze_geju


def get_annual_fortune(year: int) -> str:
    """
    计算指定公历年的流年干支与纳音。
    大模型易算错流年干支，此工具用 lunar-python 保证准确。
    """
    solar = Solar.fromYmdHms(year, 1, 1, 12, 0, 0)
    lunar = solar.getLunar()
    gz = lunar.getYearInGanZhi()
    wx = lunar.getYearNaYin()
    return json.dumps({
        "year": year,
        "ganzhi": gz,
        "nayin": wx,
        "context": f"当年干支为{gz}，纳音{wx}。可结合命主原局进行生克制化分析。"
    }, ensure_ascii=False)


def get_dayun_stage(bazi_data: Dict[str, Any], current_year: int) -> str:
    """
    根据命盘与大运列表，判定当前年份所处的大运阶段（第几步、干支、起止年龄/年份）。
    """
    dayun = bazi_data.get("dayun") or []
    for i, dy in enumerate(dayun):
        start_year = dy.get("start_year")
        start_age = dy.get("start_age", 0)
        if start_year is None:
            continue
        step = i + 1
        if current_year >= start_year:
            next_dy = dayun[i + 1] if i + 1 < len(dayun) else None
            end_year = next_dy.get("start_year") - 1 if next_dy else None
            end_age = next_dy.get("start_age", start_age + 10) - 1 if next_dy else start_age + 9
            return json.dumps({
                "current_year": current_year,
                "step": step,
                "ganzhi": dy.get("ganzhi", ""),
                "start_year": start_year,
                "start_age": start_age,
                "end_year": end_year,
                "end_age": end_age,
                "context": f"当前{current_year}年处于第{step}步大运「{dy.get('ganzhi', '')}」，起于{start_year}年（{start_age}岁）。"
            }, ensure_ascii=False)
    return json.dumps({"current_year": current_year, "step": None, "context": "未找到对应大运。"}, ensure_ascii=False)


def analyze_wuxing_balance(bazi_data: Dict[str, Any]) -> str:
    """
    五行能量统计与平衡分析：原局五行分布、偏旺/偏弱/中和的简要判断。
    """
    wuxing = bazi_data.get("wuxing") or {}
    vals = list(wuxing.values())
    if not vals:
        return json.dumps({"context": "无五行数据。"}, ensure_ascii=False)
    total = sum(vals)
    strong = [k for k, v in wuxing.items() if v >= 2]
    weak = [k for k, v in wuxing.items() if v == 0]
    balanced = 1 <= max(vals) - min(vals) <= 1 and total > 0
    return json.dumps({
        "wuxing": wuxing,
        "total": total,
        "strong": strong,
        "weak": weak,
        "balanced": balanced,
        "context": f"五行分布：{wuxing}。偏旺：{strong or '无'}；缺失：{weak or '无'}；整体{'较均衡' if balanced else '有偏'}。"
    }, ensure_ascii=False)


_XING_CHONG_HE_HAI = {
    "刑": "地支相刑：子卯、寅巳申、丑戌未、辰午酉亥自刑等，主是非、压力、健康隐患。",
    "冲": "地支六冲：子午、丑未、寅申、卯酉、辰戌、巳亥，主变动、冲突、机遇与挑战并存。",
    "合": "地支六合：子丑、寅亥、卯戌、辰酉、巳申、午未，主合和、人缘、合作。",
    "害": "地支六害：子未、丑午、寅巳、卯辰、申亥、酉戌，主暗中妨害、口舌、小人。",
    "破": "地支相破：子酉、卯午、辰丑、戌未等，主破损、不顺、暗中损耗。",
    "三合": "申子辰水、巳酉丑金、寅午戌火、亥卯未木，三字全为三合局，力量强。",
    "三会": "亥子丑水、寅卯辰木、巳午未火、申酉戌金，三会方局，气专力大。",
    "半三合": "三合局中两字（如申子、子辰、申辰），为半三合，有合意但力减。",
}


def query_xing_chong_he_hai(bazi_data: Dict[str, Any], relation_type: str = "") -> str:
    """
    查询命盘中的刑冲合害关系。
    如果指定 relation_type，返回该类型的释义；否则返回命盘中所有刑冲合害关系。
    """
    xingchong = bazi_data.get("xingchong") or {}
    
    if relation_type:
        desc = _XING_CHONG_HE_HAI.get(relation_type.strip(), "")
        if not desc:
            return json.dumps({
                "relation_type": relation_type,
                "context": "请传入：刑、冲、合、害、破、三合、三会、半三合 之一。",
                "all_types": list(_XING_CHONG_HE_HAI.keys()),
            }, ensure_ascii=False)
        
        relations = xingchong.get(relation_type, [])
        return json.dumps({
            "relation_type": relation_type,
            "description": desc,
            "relations": relations,
            "context": f"{desc} 命盘中{relation_type}关系：{', '.join(relations) if relations else '无'}。"
        }, ensure_ascii=False)
    
    summary = []
    for rtype, rels in xingchong.items():
        if rels:
            summary.append(f"{rtype}：{', '.join(rels)}")
    
    return json.dumps({
        "xingchong": xingchong,
        "summary": summary,
        "context": f"命盘刑冲合害关系：{'; '.join(summary) if summary else '无特殊刑冲合害'}。"
    }, ensure_ascii=False)


_SHENSHA_GLOSSARY = {
    "桃花": "子午卯酉为桃花，主异性缘、审美、情感；分墙内墙外。",
    "驿马": "寅申巳亥为驿马，主变动、出行、迁移、机遇。",
    "华盖": "主孤高、艺术、宗教缘、独立思考。",
    "文昌": "主学业、文采、考试、名声。",
    "将星": "主领导力、权威、组织能力。",
    "羊刃": "主刚强、胆大、易有伤灾或官非。",
    "劫煞": "主突发变故、破财、竞争。",
    "亡神": "主思虑、城府、亦主官禄。",
}


def explain_shensha(shensha_name: str) -> str:
    """
    神煞名词解释。传入神煞名称（如 桃花、驿马、华盖）返回简要释义。
    """
    name = shensha_name.strip()
    desc = _SHENSHA_GLOSSARY.get(name, "")
    if not desc:
        return json.dumps({
            "shensha": name,
            "context": f"未收录「{name}」的释义。",
            "available": list(_SHENSHA_GLOSSARY.keys()),
        }, ensure_ascii=False)
    return json.dumps({"shensha": name, "description": desc, "context": desc}, ensure_ascii=False)


def fact_check_ganzhi(claimed_ganzhi: str, year: int) -> str:
    """
    校验某年流年干支是否与 lunar-python 计算结果一致，用于 Fact-Check AI 输出。
    claimed_ganzhi: AI 或用户声称的该年干支，如「丙午」；year: 公历年份。
    """
    solar = Solar.fromYmdHms(year, 1, 1, 12, 0, 0)
    lunar = solar.getLunar()
    actual = lunar.getYearInGanZhi()
    claimed = (claimed_ganzhi or "").strip()
    match = claimed == actual
    return json.dumps({
        "year": year,
        "claimed": claimed,
        "actual": actual,
        "match": match,
        "context": f"声称{year}年干支为「{claimed}」，实际为「{actual}」，{'一致' if match else '不一致，请以实际为准'}。"
    }, ensure_ascii=False)


def query_qiongtong_guidance(bazi_data: Dict[str, Any]) -> str:
    """查询《穷通宝鉴》调候用神，基于命盘日主与月令。"""
    pillars = bazi_data.get("pillars") or []
    day_master = (bazi_data.get("day_master") or "").strip()
    month_zhi = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) >= 2 else ""
    result = get_qiongtong_for_tool(day_master, month_zhi)
    return json.dumps(result, ensure_ascii=False)


def extract_ganzhi_from_text(text: str) -> List[tuple]:
    """
    从文本中提取「年份 + 干支」组合，用于批量 fact-check。
    返回 [(year, claimed_ganzhi), ...]，年份为 None 表示未识别。
    """
    pattern = re.compile(r"(20\d{2}|19\d{2})年.*?[是为]?\s*[「\"]?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[」\"]?")
    out = []
    for m in pattern.finditer(text):
        out.append((int(m.group(1)), m.group(2)))
    return out


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_annual_fortune",
            "description": "当用户问及具体某一年的运势（如：2026年我会怎么样？我哪一年容易发财？），调用此工具获取该公历年的准确干支和纳音，用于流年命理分析。",
            "parameters": {
                "type": "object",
                "properties": {"year": {"type": "integer", "description": "公历年份，如 2026"}},
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dayun_stage",
            "description": "判定命主在指定年份所处的大运阶段（第几步、干支、起止年龄/年份）。需结合命盘使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_year": {"type": "integer", "description": "要查询的公历年份"},
                },
                "required": ["current_year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_wuxing_balance",
            "description": "分析命盘五行能量分布与平衡（偏旺、缺失、均衡）。需传入命盘数据。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_xing_chong_he_hai",
            "description": "查询命盘中的刑冲合害关系。可指定 relation_type（刑/冲/合/害）查看特定类型，或不传参数查看所有关系。",
            "parameters": {
                "type": "object",
                "properties": {
                    "relation_type": {"type": "string", "description": "可选：刑、冲、合、害 之一，不传则返回所有"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_shensha",
            "description": "神煞名词解释。传入神煞名称（如桃花、驿马、华盖）返回简要释义。",
            "parameters": {
                "type": "object",
                "properties": {"shensha_name": {"type": "string", "description": "神煞名称"}},
                "required": ["shensha_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fact_check_ganzhi",
            "description": "校验某年流年干支是否与历法计算一致。用于核对 AI 或文本中的干支表述是否正确。",
            "parameters": {
                "type": "object",
                "properties": {
                    "claimed_ganzhi": {"type": "string", "description": "声称的干支，如 丙午"},
                    "year": {"type": "integer", "description": "公历年份"},
                },
                "required": ["claimed_ganzhi", "year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_qiongtong_guidance",
            "description": "查询《穷通宝鉴》调候用神条文。根据命盘日主与月令返回用神、原文与白话释义。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_wuxing_power",
            "description": "五行力量精算：考虑藏干、月令、十二长生的权重，返回各五行力量占比（0-100）及偏旺/偏弱判断。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_geju",
            "description": "格局判定：根据月令主气、透干、日主强弱判断正格/身旺/身弱/从格及格局名称。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_REGISTRY = {
    "get_annual_fortune": get_annual_fortune,
    "get_dayun_stage": get_dayun_stage,
    "analyze_wuxing_balance": analyze_wuxing_balance,
    "query_xing_chong_he_hai": query_xing_chong_he_hai,
    "explain_shensha": explain_shensha,
    "fact_check_ganzhi": fact_check_ganzhi,
    "query_qiongtong_guidance": query_qiongtong_guidance,
    "calculate_wuxing_power": calculate_wuxing_power,
    "analyze_geju": analyze_geju,
}


def dispatch_tool(name: str, arguments: Dict[str, Any], bazi_data: Dict[str, Any] | None = None) -> str:
    """
    根据工具名和参数执行对应工具，返回 JSON 字符串。
    部分工具需要 bazi_data（命盘），若未传则可能报错或返回提示。
    """
    bazi_data = bazi_data or {}
    if name not in TOOL_REGISTRY:
        return json.dumps({"error": f"未知工具: {name}", "available": list(TOOL_REGISTRY.keys())}, ensure_ascii=False)
    fn = TOOL_REGISTRY[name]
    try:
        if name == "get_annual_fortune":
            return fn(arguments.get("year", 0))
        if name == "get_dayun_stage":
            return fn(bazi_data, arguments.get("current_year", 0))
        if name == "analyze_wuxing_balance":
            return fn(bazi_data)
        if name == "query_xing_chong_he_hai":
            return fn(bazi_data, arguments.get("relation_type", ""))
        if name == "explain_shensha":
            return fn(arguments.get("shensha_name", ""))
        if name == "fact_check_ganzhi":
            return fn(
                arguments.get("claimed_ganzhi", ""),
                arguments.get("year", 0),
            )
        if name in ("query_qiongtong_guidance", "calculate_wuxing_power", "analyze_geju"):
            return fn(bazi_data)
        return json.dumps({"error": "未实现的工具分支"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name}, ensure_ascii=False)
