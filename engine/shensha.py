"""
八字神煞（Shen Sha）计算模块

本模块基于传统八字命理规则，根据四柱干支计算各类神煞。
与黄历（calendar-level）的吉神凶煞不同，这里是真正的命局神煞——
以日干、日支、年支为太极点，遍历四柱地支查找神煞落宫。

神煞一览：
    1. 桃花（Peach Blossom）  — 人缘、异性缘、才艺
    2. 驿马（Travel Star）     — 奔波、出行、变动
    3. 天乙贵人（Tianyi Noble） — 贵人相助、逢凶化吉
    4. 华盖（Canopy）          — 孤高、学术、宗教、艺术
    5. 羊刃（Yang Blade）      — 刚烈、果断、灾厄
    6. 禄神（Lu Star）         — 俸禄、财源、衣食
    7. 文昌（Literary Star）   — 聪明、学业、文才
    8. 将星（General Star）    — 领导力、权柄、威严

返回格式：
    Dict[int, List[str]]，key 为柱索引（0=年, 1=月, 2=日, 3=时），
    value 为该柱地支上查到的神煞名称列表。
"""

from typing import Dict, List


# ── 地支序号映射 ──────────────────────────────────────────────────────────
_ZHI_INDEX = {z: i for i, z in enumerate("子丑寅卯辰巳午未申酉戌亥")}


def _zhi_at(pillars: List[str], pos: int) -> str:
    """取指定柱的地支（干支字符串的第 2 个字符）。"""
    p = pillars[pos]
    return p[1] if len(p) >= 2 else ""


# ══════════════════════════════════════════════════════════════════════════
# 三合局 → 神煞映射表
# ══════════════════════════════════════════════════════════════════════════

# 桃花：年支或日支所属三合局的"沐浴"位（即桃花位）
#   申子辰（水局）→ 酉    寅午戌（火局）→ 卯
#   巳酉丑（金局）→ 午    亥卯未（木局）→ 子
_TAOHUA: Dict[str, str] = {
    "申": "酉", "子": "酉", "辰": "酉",
    "寅": "卯", "午": "卯", "戌": "卯",
    "巳": "午", "酉": "午", "丑": "午",
    "亥": "子", "卯": "子", "未": "子",
}

# 驿马：年支或日支所属三合局的"冲"位
#   申子辰 → 寅    寅午戌 → 申
#   巳酉丑 → 亥    亥卯未 → 巳
_YIMA: Dict[str, str] = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

# 华盖：年支或日支所属三合局的"墓"位
#   申子辰 → 辰    寅午戌 → 戌
#   巳酉丑 → 丑    亥卯未 → 未
_HUAGAI: Dict[str, str] = {
    "申": "辰", "子": "辰", "辰": "辰",
    "寅": "戌", "午": "戌", "戌": "戌",
    "巳": "丑", "酉": "丑", "丑": "丑",
    "亥": "未", "卯": "未", "未": "未",
}

# 将星：年支或日支所属三合局的"帝旺"位
#   申子辰 → 子    寅午戌 → 午
#   巳酉丑 → 酉    亥卯未 → 卯
_JIANGXING: Dict[str, str] = {
    "申": "子", "子": "子", "辰": "子",
    "寅": "午", "午": "午", "戌": "午",
    "巳": "酉", "酉": "酉", "丑": "酉",
    "亥": "卯", "卯": "卯", "未": "卯",
}


# ══════════════════════════════════════════════════════════════════════════
# 日干 → 神煞映射表
# ══════════════════════════════════════════════════════════════════════════

# 天乙贵人：最吉之神，主贵人相助
#   甲戊庚 → 丑未    乙己 → 子申
#   丙丁   → 亥酉    壬癸 → 卯巳
#   辛     → 寅午
_TIANYI: Dict[str, List[str]] = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["寅", "午"],
}

# 禄神：日干临官之位，主衣食俸禄
#   甲→寅  乙→卯  丙→巳  丁→午  戊→巳
#   己→午  庚→申  辛→酉  壬→亥  癸→子
_LU: Dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

# 羊刃（阳干专属）：日干帝旺之位，主刚烈果断
#   甲→卯  丙→午  戊→午  庚→酉  壬→子
#   阴干无羊刃（部分流派用"飞刃"，此处暂不取）
_YANGREN: Dict[str, str] = {
    "甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子",
}

# 文昌：主聪明才学、利考试文章
#   甲→巳  乙→午  丙→申  丁→酉  戊→申
#   己→酉  庚→亥  辛→子  壬→寅  癸→卯
_WENCHANG: Dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}


# ══════════════════════════════════════════════════════════════════════════
# 公开 API
# ══════════════════════════════════════════════════════════════════════════

def calculate_shensha(pillars: List[str]) -> Dict[int, List[str]]:
    """
    根据四柱干支计算八字神煞。

    参数：
        pillars: 四柱干支列表，顺序为 [年柱, 月柱, 日柱, 时柱]，
                 每柱为两位字符串，如 ["庚午", "壬午", "甲子", "丙寅"]。

    返回：
        Dict[int, List[str]]，key 为柱索引 (0=年, 1=月, 2=日, 3=时)，
        value 为该柱地支上出现的神煞名称列表。
        例如: {0: ["禄神"], 2: ["桃花", "天乙贵人"], ...}

    计算逻辑：
        1. 取年支、日支作为三合局神煞的太极点；
        2. 取日干作为天干类神煞的太极点；
        3. 遍历四柱地支，逐一查找是否命中各类神煞。
    """
    if len(pillars) < 4:
        return {i: [] for i in range(4)}

    # 提取年支、日支、日干
    year_zhi = _zhi_at(pillars, 0)
    day_zhi = _zhi_at(pillars, 2)
    day_gan = pillars[2][0] if len(pillars[2]) >= 1 else ""

    # 初始化结果：每柱一个空列表
    result: Dict[int, List[str]] = {i: [] for i in range(4)}

    # ── 三合局类神煞（桃花、驿马、华盖、将星）───────────────────────────
    # 这些神煞以年支和日支所属三合局来定位，查四柱地支是否出现目标支。
    # 正统命理中，桃花和华盖一般年日同看，驿马和将星以日支为主；
    # 此处为全面起见，年支日支均查。

    for pillar_idx in range(4):
        zhi = _zhi_at(pillars, pillar_idx)
        if not zhi:
            continue

        # 桃花：查年支、日支对应的桃花位
        if year_zhi and _TAOHUA.get(year_zhi) == zhi:
            result[pillar_idx].append("桃花")
        if day_zhi and day_zhi != year_zhi and _TAOHUA.get(day_zhi) == zhi:
            # 避免年支日支相同时重复计桃花
            if "桃花" not in result[pillar_idx]:
                result[pillar_idx].append("桃花")

        # 驿马：以日支为主（年支辅之，部分流派仅取日支）
        if day_zhi and _YIMA.get(day_zhi) == zhi:
            result[pillar_idx].append("驿马")
        elif year_zhi and year_zhi != day_zhi and _YIMA.get(year_zhi) == zhi:
            if "驿马" not in result[pillar_idx]:
                result[pillar_idx].append("驿马")

        # 华盖：查年支、日支对应的华盖位
        if year_zhi and _HUAGAI.get(year_zhi) == zhi:
            result[pillar_idx].append("华盖")
        if day_zhi and day_zhi != year_zhi and _HUAGAI.get(day_zhi) == zhi:
            if "华盖" not in result[pillar_idx]:
                result[pillar_idx].append("华盖")

        # 将星：以日支为主
        if day_zhi and _JIANGXING.get(day_zhi) == zhi:
            result[pillar_idx].append("将星")
        elif year_zhi and year_zhi != day_zhi and _JIANGXING.get(year_zhi) == zhi:
            if "将星" not in result[pillar_idx]:
                result[pillar_idx].append("将星")

    # ── 天干类神煞（天乙贵人、羊刃、禄神、文昌）─────────────────────────
    # 这些神煞以日干为太极点，查四柱地支是否出现目标支。

    if day_gan:
        # 天乙贵人
        tianyi_targets = _TIANYI.get(day_gan, [])
        for pillar_idx in range(4):
            zhi = _zhi_at(pillars, pillar_idx)
            if zhi and zhi in tianyi_targets:
                result[pillar_idx].append("天乙贵人")

        # 禄神
        lu_target = _LU.get(day_gan, "")
        if lu_target:
            for pillar_idx in range(4):
                zhi = _zhi_at(pillars, pillar_idx)
                if zhi == lu_target:
                    result[pillar_idx].append("禄神")

        # 羊刃（仅阳干）
        yangren_target = _YANGREN.get(day_gan, "")
        if yangren_target:
            for pillar_idx in range(4):
                zhi = _zhi_at(pillars, pillar_idx)
                if zhi == yangren_target:
                    result[pillar_idx].append("羊刃")

        # 文昌
        wenchang_target = _WENCHANG.get(day_gan, "")
        if wenchang_target:
            for pillar_idx in range(4):
                zhi = _zhi_at(pillars, pillar_idx)
                if zhi == wenchang_target:
                    result[pillar_idx].append("文昌")

    return result


def format_shensha_for_pillars(shensha_dict: Dict[int, List[str]]) -> List[str]:
    """
    将神煞字典格式化为四柱列表形式，方便直接嵌入返回结果。

    返回：
        List[str]，长度 4，每项为空格分隔的神煞名称字符串。
        例如: ["禄神", "桃花 天乙贵人", "", "文昌"]
    """
    return [
        " ".join(shensha_dict.get(i, []))
        for i in range(4)
    ]


__all__ = ["calculate_shensha", "format_shensha_for_pillars"]
