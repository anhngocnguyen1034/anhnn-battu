"""Test review script - validates Bazi engine calculations for sample cases."""
import json
from datetime import datetime
from engine.bazi_engine import calculate_professional_bazi
from tools.wuxing_calculator import calculate_wuxing_power
from tools.geju_analyzer import analyze_geju

cases = [
    ("1990-05-20 10:30 Male",   datetime(1990, 5, 20, 10, 30, 0), "乾造 (Male)"),
    ("1985-01-15 03:00 Female", datetime(1985, 1, 15, 3, 0, 0),   "坤造 (Female)"),
    ("2000-08-08 12:00 Male",   datetime(2000, 8, 8, 12, 0, 0),   "乾造 (Male)"),
    ("1976-12-25 22:00 Male",   datetime(1976, 12, 25, 22, 0, 0), "乾造 (Male)"),
    ("1995-06-01 06:00 Female", datetime(1995, 6, 1, 6, 0, 0),    "坤造 (Female)"),
]

for label, dt, gender_str in cases:
    bazi = calculate_professional_bazi(dt, gender_str)
    pillars = bazi["pillars"]
    dm = bazi["day_master"]
    dishi = bazi.get("dishi", [])
    xc = bazi.get("xingchong", {})
    wx = json.loads(calculate_wuxing_power(bazi))
    gj = json.loads(analyze_geju(bazi))
    print(f"=== {label} ===")
    print(f"  pillars: {pillars}  dm: {dm}  dishi: {dishi}")
    print(f"  power: {wx.get('power', {})}")
    print(f"  strong: {wx.get('strong', [])}  weak: {wx.get('weak', [])}")
    print(f"  geju: {gj.get('格局', '')}  type: {gj.get('类型', '')}  strength: {gj.get('日主强弱', '')}  ratio: {gj.get('五行占比', '')}")
    print(f"  tougan: {gj.get('透干位置', '')}  is_tougan: {gj.get('月干透干', '')}")
    for k in ["冲", "合", "刑", "害", "破", "三合", "三会", "半三合"]:
        v = xc.get(k, [])
        if v:
            print(f"  {k}: {v}")
    print()
