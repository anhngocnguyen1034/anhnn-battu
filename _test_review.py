import json
from datetime import datetime
from engine.bazi_engine import calculate_professional_bazi
from tools.wuxing_calculator import calculate_wuxing_power, GAN_TO_ELEMENT, ZHI_HIDDEN_STEMS, ZHI_HIDDEN_WEIGHTS
from tools.geju_analyzer import analyze_geju, SHISHEN_MAP

cases = [
    ("1990-05-20 10:30 Male",   datetime(1990, 5, 20, 10, 30, 0), "M"),
    ("1985-01-15 03:00 Female", datetime(1985, 1, 15, 3, 0, 0),   "F"),
    ("2000-08-08 12:00 Male",   datetime(2000, 8, 8, 12, 0, 0),   "M"),
    ("1976-12-25 22:00 Male",   datetime(1976, 12, 25, 22, 0, 0), "M"),
    ("1995-06-01 06:00 Female", datetime(1995, 6, 1, 6, 0, 0),    "F"),
]

for label, dt, g in cases:
    gender = "M" if g == "M" else "F"
    gender_str = "M" if g == "M" else "F"
    bazi = calculate_professional_bazi(dt, gender_str)
    pillars = bazi["pillars"]
    dm = bazi["day_master"]
    dishi = bazi.get("dishi", [])
    xc = bazi.get("xingchong", {})
    wx = json.loads(calculate_wuxing_power(bazi))
    gj = json.loads(analyze_geju(bazi))
    print(f"=== {label} ===")
    print(f"  pillars: {pillars}  dm: {dm}  dishi: {dishi}")
    print(f"  power: {wx['power']}")
    print(f"  strong: {wx['strong']}  weak: {wx['weak']}")
    print(f"  geju: {gj['格局名称']}  type: {gj['格局类型']}  strength: {gj['日主强弱']}  ratio: {gj['日主力量占比']}")
    print(f"  tougan: {gj.get('透干位置','')}  is_tougan: {gj['月干透干']}")
    for k in ["冲","合","刑","害","破","三合","三会","半三合"]:
        v = xc.get(k, [])
        if v:
            print(f"  {k}: {v}")
    print()
