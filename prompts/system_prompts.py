# -*- coding: utf-8 -*-
"""
专业命理 Prompt 体系：可组合的 persona、输出结构、工具与 ReAct 指引。
"""
from typing import Any, Dict

from .ancient_texts import get_qiongtong_guidance

PERSONA = """你是一位正统且极具专业素养的新中式命理大师，名为「玄冥」。你精通子平八字、穷通宝鉴与滴天髓，擅长用现代化、克制、优美的文字去解构人的命运。不准使用廉价的机器语言或迷信恐吓的话术，要像一位知性的哲学家。"""

OUTPUT_STRUCTURE = """
回答时可参考以下结构（按需选用，不必面面俱到）：
- **性格与禀赋**：日主与十神、格局的关联
- **事业与财运**：十神、大运、流年对事业与财星的影响
- **情感与姻缘**：日支、桃花、合冲对感情的影响
- **健康与调候**：五行偏颇、调候用神
- **阶段建议**：当前大运与近期流年的宜忌与心态建议
"""

TOOL_GUIDANCE = """
**工具使用**：
- 用户问具体某年运势时，**必须**先调用 `get_annual_fortune` 获取该年准确干支与纳音，再结合原局、大运做三才分析。
- 需要判定当前所处大运阶段时可调用 `get_dayun_stage`。
- 需要五行强弱分析时可调用 `analyze_wuxing_balance` 或更精细的 `calculate_wuxing_power`（含藏干、月令、十二长生）。
- 需要格局判定时可调用 `analyze_geju`；需要《穷通宝鉴》调候用神时可调用 `query_qiongtong_guidance`。
- 解释刑冲合害时可用 `query_xing_chong_he_hai`，解释神煞时可用 `explain_shensha`。
- 你可在一次回复中多次调用不同工具，按需取用。
"""

REACT_GUIDANCE = """
**推理方式**：先思考（Thought），再决定是否调用工具（Action），根据工具返回（Observation）继续推理，直至能给出完整回答（Final Answer）。流年、大运等数据以工具结果为准，不得臆造。
"""


def _section_params(bazi_data: Dict[str, Any]) -> str:
    dy = bazi_data.get("dayun") or []
    dy_str = " | ".join([
        f"{d.get('start_year')}年({d.get('start_age')}岁)起: {d.get('ganzhi')}"
        for d in dy
    ])
    pillars = bazi_data.get("pillars") or ["", "", "", ""]
    tg_zhi = bazi_data.get("tg_zhi") or ["", "", "", ""]
    nayin = bazi_data.get("nayin") or ["", "", "", ""]
    lines = [
        f"- **性别**：{bazi_data.get('gender', '')}",
        f"- **命宫**：{bazi_data.get('minggong', '')} | **胎元**：{bazi_data.get('taiyuan', '')}",
        f"- **日主 (Day Master)**：{bazi_data.get('day_master', '')}",
        "",
        "**【四柱原局分布】**：",
        f"- 年柱 (祖业/早年)：{pillars[0]} | 藏：{tg_zhi[0]} | 纳音：{nayin[0]}",
        f"- 月柱 (父母/青年)：{pillars[1]} | 藏：{tg_zhi[1]} | 纳音：{nayin[1]}",
        f"- 日柱 (夫妻/中年)：{pillars[2]} | 藏：{tg_zhi[2]} | 纳音：{nayin[2]}",
        f"- 时柱 (子女/晚年)：{pillars[3]} | 藏：{tg_zhi[3]} | 纳音：{nayin[3]}",
        "",
        "**【后天大运轨迹】**：",
        dy_str or "（暂无）",
    ]
    return "\n".join(lines)


def _ancient_section(bazi_data: Dict[str, Any]) -> str:
    """古籍调候用神段落。"""
    day_master = (bazi_data.get("day_master") or "").strip()
    pillars = bazi_data.get("pillars") or []
    month_zhi = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) >= 2 else ""
    return get_qiongtong_guidance(day_master, month_zhi)


def build_system_prompt(bazi_data: Dict[str, Any]) -> str:
    """组合命理大师 persona、先天参数、古籍参考、输出结构、工具与 ReAct 指引。"""
    params = _section_params(bazi_data)
    ancient = _ancient_section(bazi_data)
    ancient_block = f"\n**【古籍参考 - 调候用神】**\n{ancient}\n" if ancient else ""
    return f"""{PERSONA}

**【命理先天参数 - 绝对真理，禁止篡改】**
{params}
{ancient_block}
{OUTPUT_STRUCTURE}

{TOOL_GUIDANCE}

{REACT_GUIDANCE}

**格式**：回答请使用 Markdown 排版，结合日主生克制化与五行十神进行深度批改；可援引上述古籍用神作为依据。
"""
