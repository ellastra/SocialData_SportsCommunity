# -*- coding: utf-8 -*-
"""
목표
- 게시물(POSTS_PATH)을 불러와 텍스트 정리 및 욕설 탐지
- Verstappen 랩 파일(bahrain_2024_laps_kst.csv)의 lap_start_kst/lap_end_kst로 랩별 중앙시각(lap_mid_kst) 계산
- 각 게시물을 가장 가까운 lap_mid_kst에 매칭해 'lap' 부여
- 랩 단위로 '게시물 수 대비 욕설 포함 게시물 비율(toxic_ratio)' 계산
- CSV 저장 + 선그래프 저장

필요 파일
- POSTS_PATH:       post_timestamp, post_title, post_content 포함
- LAP_FILE:         lap_number, lap_start_kst, lap_end_kst 포함
- SLANG_PATH:       첫 열=단어, (선택) 두 번째 열=가중치
"""

import pandas as pd
import re
from pathlib import Path
import matplotlib.pyplot as plt

# --------------------
# 경로 설정 (필요시 수정)
# --------------------
POSTS_PATH = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_RawData/Round24_UnitedArabEmirates_Final.csv"
SLANG_PATH = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_RawData/slang.csv"

OUT_TABLE  = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/uae_toxicity_per_lap.csv"
OUT_PLOT   = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/uae_toxicity_per_lap.png"

# 추가: 랩 파일 및 매칭 결과 출력 경로
LAP_FILE   = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_RawData/uae_2024_laps_kst.csv"
OUT_MERGED = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_RawData/Round1_UnitedArabEmirates_posts_with_lap.csv"


# --------------------
# 유틸
# --------------------
def ensure_kst(series: pd.Series) -> pd.Series:
    """문자열/naive/aware 섞여 있어도 모두 Asia/Seoul tz-aware로 통일"""
    dt = pd.to_datetime(series, errors="coerce")
    # tz 정보가 없으면 로컬라이즈, 있으면 변환
    if getattr(dt.dt, "tz", None) is None:
        return dt.dt.tz_localize("Asia/Seoul")
    else:
        return dt.dt.tz_convert("Asia/Seoul")

def clean_text(s: str) -> str:
    s = str(s)
    s = s.lower()                 # 영문 소문자화
    s = re.sub(r"[\r\n]+", " ", s)
    s = re.sub(r"[^가-힣a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_slang_regexes(slang_csv_path: str):
    slang_df = pd.read_csv(slang_csv_path)
    slang_df.columns = slang_df.columns.astype(str).str.strip()
    word_col = slang_df.columns[0]
    slang_df[word_col] = slang_df[word_col].astype(str).str.strip().str.lower()

    if len(slang_df.columns) >= 2:
        weight_col = slang_df.columns[1]
        slang_df[weight_col] = pd.to_numeric(slang_df[weight_col], errors="coerce").fillna(1.0)
    else:
        weight_col = "weight"
        slang_df[weight_col] = 1.0

    slang_df = slang_df.dropna(subset=[word_col]).drop_duplicates(subset=[word_col])

    regexes = []
    for term, w in zip(slang_df[word_col], slang_df[weight_col]):
        if re.search(r"[a-z0-9]", term):
            pat = re.compile(rf"\b{re.escape(term)}\b", flags=re.IGNORECASE)
        else:
            pat = re.compile(re.escape(term))
        regexes.append((pat, float(w)))
    return regexes

def slang_score(text: str, regexes) -> float:
    score = 0.0
    for pat, w in regexes:
        cnt = len(pat.findall(text))
        if cnt:
            score += cnt * w
    return score


# --------------------
# 1) 데이터 로드 & 정리 (게시물)
# --------------------
posts = pd.read_csv(POSTS_PATH, sep=",", encoding="utf-8-sig")
posts.columns = posts.columns.str.strip().str.replace("\ufeff", "", regex=False)

# 타임스탬프
posts["post_timestamp"] = pd.to_datetime(posts["post_timestamp"], errors="coerce")
posts = posts.dropna(subset=["post_timestamp"])
posts["post_timestamp"] = ensure_kst(posts["post_timestamp"])

# 텍스트 결합/정리
posts["text"] = (posts.get("post_title", "").fillna("") + " " +
                 posts.get("post_content", "").fillna("")).map(clean_text)
posts = posts[posts["text"].str.len() > 0].copy()

# --------------------
# 2) 욕설 사전 → regex 리스트
# --------------------
regexes = load_slang_regexes(SLANG_PATH)

# --------------------
# 3) 랩 파일 로드 & 랩 중앙시각 계산 + posts에 lap 매칭(없을 때만)
# --------------------
laps = pd.read_csv(LAP_FILE, encoding="utf-8-sig")
# 기대 컬럼: lap_number, lap_start_kst, lap_end_kst
if "lap_number" not in laps.columns:
    raise ValueError("Lap file must contain 'lap_number' column.")
for col in ["lap_start_kst", "lap_end_kst"]:
    if col not in laps.columns:
        raise ValueError("Lap file must contain 'lap_start_kst' and 'lap_end_kst' columns.")

laps["lap_start_kst"] = ensure_kst(laps["lap_start_kst"])
laps["lap_end_kst"]   = ensure_kst(laps["lap_end_kst"])
laps["lap_mid_kst"]   = laps["lap_start_kst"] + (laps["lap_end_kst"] - laps["lap_start_kst"]) / 2
ver_mid = laps[["lap_number", "lap_mid_kst"]].copy().rename(columns={"lap_number": "lap"})

# posts에 이미 lap이 들어있으면 그대로 사용하고, 없으면 가장 가까운 lap_mid_kst로 매칭
use_existing_lap = "lap" in posts.columns and pd.api.types.is_numeric_dtype(posts["lap"])
if use_existing_lap:
    print("[INFO] Detected preassigned 'lap' in posts. Skipping lap matching.")
    posts_lap = posts.copy()
else:
    print("[INFO] No 'lap' in posts. Matching each post to nearest lap midpoint (VER).")
    posts["_key"] = 1
    ver_mid["_key"] = 1
    combo = posts.merge(ver_mid, on="_key", how="left")
    combo["abs_diff"] = (combo["post_timestamp"] - combo["lap_mid_kst"]).abs()

    nearest = (
        combo.sort_values(["post_timestamp", "abs_diff"])
             .groupby("post_timestamp", as_index=False)
             .first()[["post_timestamp", "lap", "lap_mid_kst", "abs_diff"]]
    )
    posts_lap = posts.merge(nearest, on="post_timestamp", how="left")

# 매칭 결과(또는 기존 lap 포함)를 저장: '실시간 lap + 게시물' 병합본
# 참고로 타임존이 포함된 datetime은 문자열로 저장하는 것이 이후 조인에 안전
save_df = posts_lap.copy()
if "lap_mid_kst" in save_df.columns:
    save_df["lap_mid_kst"] = pd.to_datetime(save_df["lap_mid_kst"]).dt.strftime("%Y-%m-%d %H:%M:%S")
save_df["post_timestamp"] = pd.to_datetime(save_df["post_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
save_df.to_csv(OUT_MERGED, index=False, encoding="utf-8-sig")
print(f"[DONE] Merged posts with lap → {OUT_MERGED}")

# --------------------
# 5) 각 글의 욕설 점수 및 독성 플래그
# --------------------
posts_lap["toxicity_score"] = posts_lap["text"].map(lambda t: slang_score(t, regexes))
posts_lap["toxic_flag"] = posts_lap["toxicity_score"] > 0

# --------------------
# 6) 랩 단위 집계: 게시물 수 대비 욕 포함 비율
# --------------------
agg = posts_lap.groupby("lap", as_index=False).agg(
    post_count=("toxic_flag", "size"),
    toxic_count=("toxic_flag", "sum")
)
agg["toxic_ratio"] = agg["toxic_count"] / agg["post_count"]

# 보기용 중앙시각 문자열
lap_mid_map = ver_mid.set_index("lap")["lap_mid_kst"]
agg["lap_mid_kst"] = agg["lap"].map(lap_mid_map)
agg["lap_mid_kst_str"] = pd.to_datetime(agg["lap_mid_kst"]).dt.strftime("%Y-%m-%d %H:%M:%S")

# --------------------
# 7) CSV 저장
# --------------------
out_df = agg[["lap", "lap_mid_kst_str", "post_count", "toxic_count", "toxic_ratio"]].sort_values("lap")
out_df.to_csv(OUT_TABLE, index=False, encoding="utf-8-sig")
print(f"[저장 완료] {OUT_TABLE}")
print(out_df.head(10))

# --------------------
# 8) 그래프 저장 (matplotlib 단일 플롯, 색상 지정 X)
# --------------------
import matplotlib.pyplot as plt

plt.figure(figsize=(11, 4))
plt.plot(out_df["lap"], out_df["toxic_ratio"], marker="o")

plt.title("Bahrain 2024 — Toxic Post Ratio by Lap")
plt.xlabel("Lap")
plt.ylabel("Toxic Post Ratio")

# x축: 2랩 간격으로 눈금 표시
min_lap = int(out_df["lap"].min())
max_lap = int(out_df["lap"].max())
plt.xticks(list(range(min_lap - (min_lap % 2), max_lap + 1, 2)))

plt.tight_layout()
plt.savefig(OUT_PLOT)
print(f"[그래프 저장] {OUT_PLOT}")
plt.show()  # 그래프 창 열기