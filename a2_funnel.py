"""项目A 第2步：用户级漏斗（pandas 版 + SQL 版）并核对。
运行：python scripts/a2_funnel.py
输出：output/a2_funnel.csv、output/a2_first_cart_to_buy.csv
口径：层1=有浏览；层2=层1 且 有加购或收藏；层3=层2 且 有购买（严格嵌套）
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
df = pd.read_csv(ROOT / "data" / "clean.csv",
                 usecols=["user_id", "item_id", "behavior_type", "dt", "date", "hour"])

# ---------- pandas 版 ----------
L1 = set(df.loc[df["behavior_type"] == "pv", "user_id"])
L2 = set(df.loc[df["behavior_type"].isin(["cart", "fav"]), "user_id"]) & L1
L3 = set(df.loc[df["behavior_type"] == "buy", "user_id"]) & L2
direct_buy = set(df.loc[df["behavior_type"] == "buy", "user_id"]) - L2   # 没有加购/收藏就购买的用户

funnel = pd.DataFrame({
    "层级": ["1 浏览", "2 加购/收藏", "3 购买"],
    "用户数": [len(L1), len(L2), len(L3)],
})
funnel["相邻转化率%"] = (funnel["用户数"] / funnel["用户数"].shift(1) * 100).round(2)
funnel["相对浏览转化率%"] = (funnel["用户数"] / funnel.loc[0, "用户数"] * 100).round(2)
funnel.to_csv(OUT / "a2_funnel.csv", index=False, encoding="utf-8-sig")
print(funnel.to_string(index=False))
print(f"抽样总用户数：{df['user_id'].nunique():,}；未经加购/收藏直接购买的用户：{len(direct_buy):,}（不计入漏斗）")

# ---------- SQL 版（SQLite，Python 自带） ----------
conn = sqlite3.connect(":memory:")
df.to_sql("user_behavior", conn, index=False)

sql_funnel = """
WITH u AS (
  SELECT user_id,
         MAX(behavior_type = 'pv')                  AS has_pv,
         MAX(behavior_type IN ('cart','fav'))       AS has_cf,
         MAX(behavior_type = 'buy')                 AS has_buy
  FROM user_behavior
  GROUP BY user_id
)
SELECT SUM(has_pv)                           AS l1,
       SUM(has_pv AND has_cf)                AS l2,
       SUM(has_pv AND has_cf AND has_buy)    AS l3
FROM u;
"""
l1, l2, l3 = conn.execute(sql_funnel).fetchone()
print(f"\nSQL 版：层1={l1:,}  层2={l2:,}  层3={l3:,}")
assert (l1, l2, l3) == (len(L1), len(L2), len(L3)), "pandas 与 SQL 结果不一致，请排查口径！"
print("pandas 与 SQL 各层人数完全一致 OK")

# ---------- 窗口函数：每个用户首次加购、首次购买时间 ----------
sql_window = """
WITH ranked AS (
  SELECT user_id, behavior_type, dt,
         ROW_NUMBER() OVER (PARTITION BY user_id, behavior_type ORDER BY dt) AS rn
  FROM user_behavior
  WHERE behavior_type IN ('cart', 'buy')
)
SELECT c.user_id,
       c.dt AS first_cart,
       b.dt AS first_buy,
       ROUND((julianday(b.dt) - julianday(c.dt)) * 24, 2) AS hours_gap
FROM ranked c
JOIN ranked b ON c.user_id = b.user_id
WHERE c.behavior_type = 'cart' AND c.rn = 1
  AND b.behavior_type = 'buy'  AND b.rn = 1;
"""
gap = pd.read_sql(sql_window, conn)
gap.to_csv(OUT / "a2_first_cart_to_buy.csv", index=False, encoding="utf-8-sig")
after = gap[gap["hours_gap"] >= 0]
print(f"\n既有加购又有购买的用户：{len(gap):,}；其中首次购买晚于首次加购：{len(after):,}")
if len(after):
    print(f"首次加购到首次购买的间隔：中位数 {after['hours_gap'].median():.1f} 小时，"
          f"平均 {after['hours_gap'].mean():.1f} 小时")
