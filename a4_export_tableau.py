"""项目A 第4步：导出聚合小表给 Tableau（不要把上百万行直接丢进 Tableau）。
运行：python scripts/a4_export_tableau.py
输出：output/tableau_a/ 下三个 CSV
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
T = OUT / "tableau_a"
T.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "data" / "clean.csv", usecols=["behavior_type", "date", "hour"])
dh = (df.groupby(["date", "hour", "behavior_type"]).size()
        .reset_index(name="cnt"))
dh.to_csv(T / "date_hour_behavior.csv", index=False, encoding="utf-8-sig")

pd.read_csv(OUT / "a2_funnel.csv").to_csv(T / "funnel.csv", index=False, encoding="utf-8-sig")
pd.read_csv(OUT / "a3_layers.csv").to_csv(T / "layers.csv", index=False, encoding="utf-8-sig")

# 高峰小时：pv 与 buy 各自最多的小时
hh = df.groupby(["hour", "behavior_type"]).size().unstack(fill_value=0)
print("pv 峰值小时：", int(hh["pv"].idxmax()), "点；buy 峰值小时：", int(hh["buy"].idxmax()), "点")
print("已导出到", T)
