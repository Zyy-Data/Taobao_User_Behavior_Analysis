"""项目A 第1步：按用户抽样 + 清洗。
运行：python scripts/a1_sample_clean.py
输入：data/raw/UserBehavior.csv（天池原始文件，无表头）
输出：data/clean.csv、output/a1_clean_log.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "UserBehavior.csv"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

COLS = ["user_id", "item_id", "category_id", "behavior_type", "timestamp"]
START, END = "2017-11-25", "2017-12-04"   # 北京时间，左闭右开，即 11.25 至 12.03

# 1) 分块读取，只保留 user_id % 100 == 0 的用户（约1%用户，保留其全部行为）
parts, total = [], 0
for chunk in pd.read_csv(RAW, names=COLS, chunksize=1_000_000):
    total += len(chunk)
    parts.append(chunk[chunk["user_id"] % 100 == 0])
df = pd.concat(parts, ignore_index=True)
sampled = len(df)
print(f"原始全量行数：{total:,}；按用户抽样后：{sampled:,}")

log = [("原始全量行数", 0, total), ("按用户抽样(user_id%100==0)", total - sampled, sampled)]

def step(name, new_df):
    """记录一步清洗剔除了多少行"""
    global df
    log.append((name, len(df) - len(new_df), len(new_df)))
    df = new_df

# 2) 清洗
step("删除含缺失值的行", df.dropna())
step("删除非法行为类型", df[df["behavior_type"].isin(["pv", "cart", "fav", "buy"])])

# 时间戳转北京时间
df["dt"] = (pd.to_datetime(df["timestamp"], unit="s", utc=True)
            .dt.tz_convert("Asia/Shanghai").dt.tz_localize(None))
step("删除超出 2017-11-25~12-03 的异常时间戳", df[(df["dt"] >= START) & (df["dt"] < END)])
step("删除重复记录", df.drop_duplicates(["user_id", "item_id", "behavior_type", "timestamp"]))

# 3) 派生字段
df["date"] = df["dt"].dt.strftime("%Y-%m-%d")
df["hour"] = df["dt"].dt.hour

df.to_csv(ROOT / "data" / "clean.csv", index=False)

log_df = pd.DataFrame(log, columns=["步骤", "本步剔除行数", "剩余行数"])
log_df["占抽样总行数%"] = (log_df["本步剔除行数"] / sampled * 100).round(2)
log_df.loc[:1, "占抽样总行数%"] = None      # 前两行是抽样，不算清洗
log_df.to_csv(OUT / "a1_clean_log.csv", index=False, encoding="utf-8-sig")
print(log_df.to_string(index=False))
print(f"\n清洗后：{len(df):,} 行，{df['user_id'].nunique():,} 个用户")
print("日期范围：", df["date"].min(), "~", df["date"].max())
print("行为类型：", sorted(df["behavior_type"].unique()))
