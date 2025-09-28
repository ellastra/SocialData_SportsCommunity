import os
import pandas as pd
from collections import Counter
from konlpy.tag import Okt
import re
import matplotlib.pyplot as plt

BASE_DIR = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis"
IN_PATH  = os.path.join(BASE_DIR, "2024Bahrain.csv")
KW_PATH  = os.path.join(BASE_DIR, "bahrain_keywords_90s.csv")  # 저장/읽기 공통 경로

# --- 키워드 집계 ---
df = pd.read_csv(IN_PATH, sep=",")
df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)
df["post_timestamp"] = pd.to_datetime(df["post_timestamp"], errors="coerce")
df = df[df["post_timestamp"].dt.hour >= 0]

grouped = df.groupby(pd.Grouper(key="post_timestamp", freq="90s"))  # 'S' -> 's'

okt = Okt()
results = []

for time_bin, group in grouped:
    if group.empty:
        continue
    texts = (group["post_title"].fillna("") + " " + group["post_content"].fillna("")).tolist()

    tokens = []
    for text in texts:
        text = re.sub(r"[^가-힣a-zA-Z0-9 ]", " ", text)
        tokens += [w for w in okt.nouns(text) if len(w) > 1]

    counter = Counter(tokens)
    top_words = counter.most_common(10)

    for word, freq in top_words:
        results.append({"time_bin": time_bin, "word": word, "freq": freq})

keywords_df = pd.DataFrame(results)
# 저장 경로 통일!
keywords_df.to_csv(KW_PATH, index=False, encoding="utf-8-sig")
print(f"[저장 완료] {KW_PATH}")

# --- 시각화: 특정 구간 막대 그래프 ---
kw = pd.read_csv(KW_PATH, parse_dates=["time_bin"])
kw = kw.sort_values("time_bin")

# 보고 싶은 구간 선택 (예: 가장 최근 구간)
time_bin = kw["time_bin"].iloc[-1]
subset = kw[kw["time_bin"] == time_bin].nlargest(10, "freq")

plt.figure(figsize=(8,5))
plt.barh(subset["word"], subset["freq"])
plt.gca().invert_yaxis()
plt.title(f"Top Keywords @ {time_bin}")
plt.xlabel("Frequency")
plt.tight_layout()
plt.show()