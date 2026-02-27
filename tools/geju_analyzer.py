# -*- coding: utf-8 -*-
"""
格局判定：根据月令、透干、日主强弱判断正格/从格；取格顺序（月干透优先、年时透、坐根）。
十神数据源优先使用 lunar_python.util.LunarUtil.SHI_SHEN。
"""
import json
from typing import Any, Dict, List

from .wuxing_calculator import GAN_TO_ELEMENT, ZHI_HIDDEN_STEMS, calculate_wuxing_power

# 十神：优先从 LunarUtil.SHI_SHEN 构建（键为 日干+他干，如 "甲丙"->"食神"）
try:
    from lunar_python.util import LunarUtil
    _gans = list(LunarUtil.WU_XING_GAN.keys())
    SHISHEN_MAP: Dict[str, Dict[str, str]] = {}
    for day_gan in _gans:
        SHISHEN_MAP[day_gan] = {other: LunarUtil.SHI_SHEN.get(day_gan + other, "") for other in _gans}
except Exception:
    SHISHEN_MAP = {
        "甲": {"甲": "比肩", "乙": "劫财", "丙": "食神", "丁": "伤官", "戊": "偏财", "己": "正财", "庚": "七杀", "辛": "正官", "壬": "偏印", "癸": "正印"},
        "乙": {"甲": "劫财", "乙": "比肩", "丙": "伤官", "丁": "食神", "戊": "正财", "己": "偏财", "庚": "正官", "辛": "七杀", "壬": "正印", "癸": "偏印"},
        "丙": {"甲": "偏印", "乙": "正印", "丙": "比肩", "丁": "劫财", "戊": "食神", "己": "伤官", "庚": "偏财", "辛": "正财", "壬": "七杀", "癸": "正官"},
        "丁": {"甲": "正印", "乙": "偏印", "丙": "劫财", "丁": "比肩", "戊": "伤官", "己": "食神", "庚": "正财", "辛": "偏财", "壬": "正官", "癸": "七杀"},
        "戊": {"甲": "七杀", "乙": "正官", "丙": "偏印", "丁": "正印", "戊": "比肩", "己": "劫财", "庚": "食神", "辛": "伤官", "壬": "偏财", "癸": "正财"},
        "己": {"甲": "正官", "乙": "七杀", "丙": "正印", "丁": "偏印", "戊": "劫财", "己": "比肩", "庚": "伤官", "辛": "食神", "壬": "正财", "癸": "偏财"},
        "庚": {"甲": "偏财", "乙": "正财", "丙": "七杀", "丁": "正官", "戊": "偏印", "己": "正印", "庚": "比肩", "辛": "劫财", "壬": "食神", "癸": "伤官"},
        "辛": {"甲": "正财", "乙": "偏财", "丙": "正官", "丁": "七杀", "戊": "正印", "己": "偏印", "庚": "劫财", "辛": "比肩", "壬": "伤官", "癸": "食神"},
        "壬": {"甲": "食神", "乙": "伤官", "丙": "偏财", "丁": "正财", "戊": "七杀", "己": "正官", "庚": "偏印", "辛": "正印", "壬": "比肩", "癸": "劫财"},
        "癸": {"甲": "伤官", "乙": "食神", "丙": "正财", "丁": "偏财", "戊": "正官", "己": "七杀", "庚": "正印", "辛": "偏印", "壬": "劫财", "癸": "比肩"},
    }


def analyze_geju(bazi_data: Dict[str, Any]) -> str:
    """
    格局判定：月令主气、是否透干、日主强弱 -> 正格/身旺/身弱/从格。
    """
    pillars = bazi_data.get("pillars") or []
    day_master = (bazi_data.get("day_master") or "").strip()
    if not pillars or len(pillars) < 2 or not day_master:
        return json.dumps({"context": "命盘数据不完整。"}, ensure_ascii=False)

    month_pillar = pillars[1]
    month_gan = month_pillar[0] if len(month_pillar) >= 1 else ""
    month_zhi = month_pillar[1] if len(month_pillar) >= 2 else ""
    hidden = ZHI_HIDDEN_STEMS.get(month_zhi, [])
    month_main_qi = hidden[0] if hidden else ""
    year_gan = pillars[0][0] if len(pillars[0]) >= 1 else ""
    time_gan = pillars[3][0] if len(pillars) >= 4 and len(pillars[3]) >= 1 else ""

    # 日主五行力量（用精算结果）
    try:
        wuxing_result = json.loads(calculate_wuxing_power(bazi_data))
        power = wuxing_result.get("power", {})
    except Exception:
        power = bazi_data.get("wuxing") or {}
        power = {k.replace("(Metal)", "").replace("(Wood)", "").replace("(Water)", "").replace("(Fire)", "").replace("(Earth)", "").strip(): v for k, v in power.items()}

    dm_elem = GAN_TO_ELEMENT.get(day_master, "")
    dm_power = power.get(dm_elem, 0)
    if isinstance(dm_power, (int, float)):
        pass
    else:
        dm_power = float(dm_power) if dm_power else 0

    # 取格顺序：1) 月支藏干透月干 2) 透年/时干 3) 月干坐根；建禄/月劫（月令主气为比劫）
    shishen_name = ""
    tougan_where = ""
    if month_main_qi and (SHISHEN_MAP.get(day_master, {}) or {}).get(month_main_qi, "") in ("比肩", "劫财"):
        shishen_name = "建禄" if month_main_qi == day_master else "月劫"
        geju_name = f"{shishen_name}格"
        is_tougan = month_gan == month_main_qi
        tougan_where = "月干" if is_tougan else ""
    else:
        tougan_where = ""
        if month_gan and month_gan in hidden:
            shishen_name = (SHISHEN_MAP.get(day_master, {}) or {}).get(month_gan, "")
            tougan_where = "月干"
            is_tougan = True
        if not shishen_name and year_gan and year_gan in hidden:
            shishen_name = (SHISHEN_MAP.get(day_master, {}) or {}).get(year_gan, "")
            tougan_where = "年干"
            is_tougan = False
        if not shishen_name and time_gan and time_gan in hidden:
            shishen_name = (SHISHEN_MAP.get(day_master, {}) or {}).get(time_gan, "")
            tougan_where = "时干"
            is_tougan = False
        if not shishen_name and month_gan:
            for idx in (0, 2, 3):
                if idx != 1 and idx < len(pillars) and len(pillars[idx]) >= 2:
                    root_zhi = pillars[idx][1]
                    if month_gan in ZHI_HIDDEN_STEMS.get(root_zhi, []):
                        shishen_name = (SHISHEN_MAP.get(day_master, {}) or {}).get(month_gan, "")
                        tougan_where = "月干坐根"
                        break
        geju_name = f"{shishen_name}格" if shishen_name else "月令格"
        if not tougan_where and month_gan == month_main_qi:
            is_tougan = True
        elif not tougan_where:
            is_tougan = False

    # 身强/身弱/中和（按力量百分比粗判）
    total_power = sum(float(power.get(k, 0)) for k in ["金", "木", "水", "火", "土"])
    if total_power <= 0:
        total_power = 1
    dm_ratio = dm_power / total_power * 100 if total_power else 0
    max_other = max((power.get(k, 0) for k in ["金", "木", "水", "火", "土"] if k != dm_elem), default=0)
    if isinstance(max_other, (int, float)):
        max_other_ratio = max_other / total_power * 100 if total_power else 0
    else:
        max_other_ratio = 0

    if dm_ratio >= 35:
        strength = "身旺"
        geju_type = "正格（身旺）"
    elif dm_ratio <= 15 and max_other_ratio >= 40:
        strength = "身弱（从格可能）"
        geju_type = "从格"
        geju_name = "从财/从杀/从儿等（需细辨）"
    elif dm_ratio <= 20:
        strength = "身弱"
        geju_type = "正格（身弱）"
    else:
        strength = "中和"
        geju_type = "中和格"

    context_extra = f"透干位置：{tougan_where}。" if tougan_where else ""
    return json.dumps({
        "格局类型": geju_type,
        "格局名称": geju_name,
        "月令": month_zhi,
        "月令主气": month_main_qi,
        "月干透干": is_tougan,
        "透干位置": tougan_where or ("月干" if is_tougan else ""),
        "日主强弱": strength,
        "日主力量占比": round(dm_ratio, 1),
        "context": f"命局为{geju_type}，{geju_name}。月令{month_zhi}主气{month_main_qi}，{'透干' if is_tougan else '不透'}。{context_extra}日主{strength}。",
    }, ensure_ascii=False)
