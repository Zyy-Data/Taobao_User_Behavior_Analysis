"""项目A 第3步：按9天内活跃天数给用户分层。
运行：python scripts/a3_layers.py
先看 output/a3_active_days_hist.png 的分布，再决定是否修改下面的阈值，然后重跑。
输出：output/a3_layers.csv、output/a3_user_level.csv（用于 Excel 透视表复核）
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
df = pd.read_csv(ROOT / "data" / "clean.csv", usecols=["user_id", "behavior_type", "date"])

# ====== 阈值：看完分布图后自己定，并把理由写进 README ======
LOW_MAX, MID_MAX = 2, 5     # 低:1~2天  中:3~5天  高:6天及以上
# ===========================================================

df["is_buy"] = (df["behavior_type"] == "buy").astype(int)
u = df.groupby("user_id").agg(active_days=("date", "nunique"),
                              buy_cnt=("is_buy", "sum")).reset_index()
u["has_buy"] = (u["buy_cnt"] > 0).astype(int)

# 分布图（图中用英文，避免中文字体问题）
plt.figure(figsize=(6, 3.5))
u["active_days"].value_counts().sort_index().plot(kind="bar")
plt.xlabel("active days (out of 9)"); plt.ylabel("users"); plt.tight_layout()
plt.savefig(OUT / "a3_active_days_hist.png", dpi=150)

max_days = int(u["active_days"].max())
u["layer"] = pd.cut(u["active_days"], bins=[0, LOW_MAX, MID_MAX, max(max_days, MID_MAX + 1)],
                    labels=["低活跃", "中活跃", "高活跃"])
u.to_csv(OUT / "a3_user_level.csv", index=False, encoding="utf-8-sig")

res = (u.groupby("layer", observed=True)
         .agg(用户数=("user_id", "count"), 购买用户数=("has_buy", "sum"), 人均购买次数=("buy_cnt", "mean"))
         .reset_index())
res["用户占比%"] = (res["用户数"] / res["用户数"].sum() * 100).round(2)
res["购买转化率%"] = (res["购买用户数"] / res["用户数"] * 100).round(2)
res["人均购买次数"] = res["人均购买次数"].round(2)
res.to_csv(OUT / "a3_layers.csv", index=False, encoding="utf-8-sig")
print(res.to_string(index=False))
assert res["用户数"].sum() == len(u), "各层人数之和应等于抽样用户数"
print("\n各层人数之和 = 抽样用户数 OK")
