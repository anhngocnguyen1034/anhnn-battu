# -*- coding: utf-8 -*-
"""
五行力量精算：考虑藏干、月令、十二长生（地势）的权重。
数据源优先使用 lunar_python.util.LunarUtil，与 china-testing 藏干权重体系兼容。
"""
import json
from typing import Any, Dict, List

try:
    from lunar_python.util import LunarUtil
    GAN_TO_ELEMENT = dict(LunarUtil.WU_XING_GAN)
    ZHI_HIDDEN_STEMS: Dict[str, List[str]] = {k: list(v) for k, v in LunarUtil.ZHI_HIDE_GAN.items()}
except Exception:
    GAN_TO_ELEMENT = {
        "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
        "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    }
    ZHI_HIDDEN_STEMS = {
        "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"], "卯": ["乙"],
        "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"], "午": ["丁", "己"], "未": ["己", "丁", "乙"],
        "申": ["庚", "壬", "戊"], "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
    }

# 地支藏干本中余气权重（参考 china-testing/bazi zhi5：子癸8，丑己5癸2辛1 等）
ZHI_HIDDEN_WEIGHTS: Dict[str, tuple] = {
    "子": (8,), "丑": (5, 2, 1), "寅": (5, 2, 1), "卯": (8,), "辰": (5, 2, 1), "巳": (5, 2, 1),
    "午": (5, 3), "未": (5, 2, 1), "申": (5, 2, 1), "酉": (8,), "戌": (5, 2, 1), "亥": (5, 3),
}

CHANGSHENG_POWER: Dict[str, float] = {
    "长生": 1.5, "沐浴": 1.2, "冠带": 1.3, "临官": 1.6, "帝旺": 2.0,
    "衰": 0.8, "病": 0.6, "死": 0.4, "墓": 0.5, "绝": 0.3, "胎": 0.7, "养": 0.9,
}


def calculate_wuxing_power(bazi_data: Dict[str, Any]) -> str:
    """五行力量精算：天干+月令加权+十二长生+地支藏干，归一化 0-100。"""
    pillars = bazi_data.get("pillars") or []
    dishi = bazi_data.get("dishi") or ["", "", "", ""]
    month_index = 1
    power: Dict[str, float] = {"金": 0.0, "木": 0.0, "水": 0.0, "火": 0.0, "土": 0.0}

    for i, pillar in enumerate(pillars):
        if len(pillar) < 2:
            continue
        gan, zhi = pillar[0], pillar[1]
        elem = GAN_TO_ELEMENT.get(gan, "")
        if elem:
            base = 10.0 * (2.0 if i == month_index else 1.0)
            coef = CHANGSHENG_POWER.get(dishi[i] if i < len(dishi) else "", 1.0)
            power[elem] += base * coef
        hidden = ZHI_HIDDEN_STEMS.get(zhi, [])
        w_default = (6, 3, 1)[: len(hidden)]
        weights = ZHI_HIDDEN_WEIGHTS.get(zhi, w_default)
        if len(weights) > len(hidden):
            weights = weights[: len(hidden)]
        elif len(weights) < len(hidden):
            weights = list(weights) + [1] * (len(hidden) - len(weights))
        mult = 1.5 if i == month_index else 1.0
        for w, stem in zip(weights, hidden):
            e = GAN_TO_ELEMENT.get(stem, "")
            if e:
                power[e] += w * mult

    total = sum(power.values())
    if total <= 0:
        return json.dumps({"power": dict(power), "strong": [], "weak": [], "balanced": False, "context": "无五行数据。"}, ensure_ascii=False)
    power_pct = {k: round(v * 100 / total, 1) for k, v in power.items()}
    strong = [k for k, v in power_pct.items() if v >= 20]
    weak = [k for k, v in power_pct.items() if v < 10]
    balanced = max(power_pct.values()) - min(power_pct.values()) <= 15
    return json.dumps({
        "power": power_pct, "strong": strong, "weak": weak, "balanced": balanced,
        "context": f"五行力量：{power_pct}。偏旺：{strong or '无'}；偏弱：{weak or '无'}；{'较均衡' if balanced else '有偏'}。",
    }, ensure_ascii=False)
