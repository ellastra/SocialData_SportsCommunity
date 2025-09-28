import pandas as pd
import re
from datetime import timedelta

# --------------------
# 경로 설정
# --------------------
POSTS_PATH = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/2024Bahrain.csv"
SLANG_PATH = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/slang.csv"
OUT_PATH   = "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/bahrain_toxicity_90s.csv"

# --------------------
# 1) 데이터 로드 & 정리
# --------------------
df = pd.read_csv(POSTS_PATH, sep=",")
df.columns = df.columns.str.strip().str.replace("\ufeff","", regex=False)
df["post_timestamp"] = pd.to_datetime(df["post_timestamp"], errors="coerce")
df = df.dropna(subset=["post_timestamp"])

# 텍스트 결합 (title + content)
def clean_text(s: str) -> str:
    s = str(s)
    s = s.lower()  # 영문은 소문자 정규화 (한글은 영향 없음)
    s = re.sub(r"[\r\n]+", " ", s)
    s = re.sub(r"[^가-힣a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

df["text"] = (df["post_title"].fillna("") + " " + df["post_content"].fillna("")).map(clean_text)
df = df[df["text"].str.len() > 0]

# --------------------
# 2) 욕설 사전 로드 (가중치 지원)
#    - slang.csv 첫 열: 단어
#    - 두 번째 열이 있으면 가중치로 사용, 없으면 1
# --------------------
slang_df = pd.read_csv(SLANG_PATH)
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
slang_list = list(zip(slang_df[word_col].tolist(), slang_df[weight_col].tolist()))

# 간단/안전한 카운팅: 각 욕설 패턴을 정규식으로 카운트
# - 한글 단어는 부분일치 허용
# - 영문/숫자 단어는 단어경계(\b) 걸어 과잉매칭 방지
regexes = []
for term, w in slang_list:
    if re.search(r"[a-z0-9]", term):
        # 영문/숫자 → 단어 경계 사용
        pat = re.compile(rf"\b{re.escape(term)}\b", flags=re.IGNORECASE)
    else:
        # 한글 → 부분일치(띄어쓰기 없이도 쓰이는 경우 많음)
        pat = re.compile(re.escape(term))
    regexes.append((pat, float(w)))

def slang_score(text: str) -> float:
    score = 0.0
    for pat, w in regexes:
        # 등장 횟수 × 가중치
        cnt = len(pat.findall(text))
        if cnt:
            score += cnt * w
    return score

# --------------------
# 3) 각 글의 부정 점수 계산
# --------------------
df["toxicity"] = df["text"].map(slang_score)

# --------------------
# 4) 00시부터 90초(랩타임) 단위 집계
#     - 평균 점수: 구간 전체의 상대적 부정성
#     - 합계 점수: 구간의 총 부정 강도(글 수 영향 포함)
#     - 글 수: 구간 활동량
# --------------------
mask = df["post_timestamp"].dt.hour >= 0  # (필요시 날짜 조건 추가 가능)
df_sub = df[mask].copy()

grouped = df_sub.groupby(pd.Grouper(key="post_timestamp", freq="90S"))
out = grouped.agg(
    mean_toxicity=("toxicity", "mean"),
    sum_toxicity=("toxicity", "sum"),
    post_count=("toxicity", "size")
).reset_index().rename(columns={"post_timestamp": "time_bin_start"})

# 끝시간 컬럼(가독성)
out["time_bin_end"] = out["time_bin_start"] + pd.to_timedelta(90, unit="s")

# 컬럼 순서 정리
out = out[["time_bin_start", "time_bin_end", "post_count", "mean_toxicity", "sum_toxicity"]]

# --------------------
# 5) CSV 저장
# --------------------
out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
print(f"[저장 완료] {OUT_PATH}")
print(out.head(10))