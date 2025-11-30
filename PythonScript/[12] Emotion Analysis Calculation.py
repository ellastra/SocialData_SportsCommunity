import pandas as pd
import os

# =========================================================
# 1. 설정 및 데이터 로드
# =========================================================
# 앞서 병합한 파일 경로
csv_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_emotion_with_event.csv'
# 결과 저장 경로
output_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_event_emotion_proportions.xlsx'

print(f"데이터 로드 중: {csv_path}")
df = pd.read_csv(csv_path)

# 컬럼명 공백 제거 (오류 방지)
df.columns = df.columns.str.strip()
print(f"로드된 컬럼 목록: {list(df.columns)}")

# =========================================================
# 2. 감정 라벨 매핑 (ID -> Name) & 컬럼 자동 탐색
# =========================================================
id2label = {
    0: "anger",
    1: "disgust",
    2: "fear",
    3: "happiness",
    4: "sadness",
    5: "surprise"
}
EMOTIONS = ["anger", "disgust", "fear", "happiness", "sadness", "surprise", "neutral"]

# Label 컬럼 자동 찾기
label_col = None
candidates = ['pred_label', 'pred_label_id', 'label', 'Label']
for col in candidates:
    if col in df.columns:
        label_col = col
        break

if label_col is None:
    raise KeyError(f"데이터에서 감정 라벨 컬럼({candidates})을 찾을 수 없습니다.\n현재 컬럼: {list(df.columns)}")

print(f"-> 감정 라벨 컬럼으로 '{label_col}'을 사용합니다.")


def get_emotion_name(row):
    # 1. Confidence Check (컬럼이 있을 경우에만)
    if 'pred_score' in row and pd.notnull(row['pred_score']) and row['pred_score'] <= 0.3:
        return 'neutral'

    # 2. 라벨 파싱
    val = row[label_col]

    # NaN 값 처리
    if pd.isna(val):
        return 'neutral'

    try:
        # "LABEL_0" 형태 처리
        if isinstance(val, str) and "LABEL_" in val:
            label_id = int(val.split("_")[-1])
        else:
            # 이미 숫자거나, 숫자로 된 문자열인 경우
            label_id = int(float(val))  # 1.0 같은 경우 대비

        return id2label.get(label_id, "neutral")
    except Exception as e:
        # 변환 실패 시 (디버깅용 로그는 생략하고 neutral 리턴)
        return "neutral"


print("감정 라벨 변환 중...")
df['emotion_final'] = df.apply(get_emotion_name, axis=1)


# =========================================================
# 3. 이벤트별 감정 비율 계산 함수
# =========================================================
def calculate_proportions(data, title):
    if len(data) == 0:
        return None

    # 감정별 개수 세기
    counts = data['emotion_final'].value_counts()

    # 전체 개수로 나누어 비율 계산
    props = counts / counts.sum()

    # 보기 좋게 데이터프레임 변환 (빠진 감정은 0으로 채움)
    props_df = pd.DataFrame(props).reindex(EMOTIONS).fillna(0)
    props_df.columns = [title]  # 컬럼명을 이벤트 이름으로
    return props_df


# =========================================================
# 4. 분석 실행
# =========================================================
print("이벤트별 감정 비율 계산 중...")

results = []

# (1) 전체 평균 (Baseline) - 이벤트가 없는 경우
# event_marker 컬럼이 없으면 생성 (ev_ 컬럼들 이용)
if 'event_marker' not in df.columns:
    event_cols = [c for c in ['ev_unexp', 'ev_resp', 'ev_out'] if c in df.columns]
    if event_cols:
        df['event_marker'] = df[event_cols].notna().any(axis=1).astype(int)
    else:
        df['event_marker'] = 0

df_no_event = df[df['event_marker'] == 0]
results.append(calculate_proportions(df_no_event, "No_Event (Baseline)"))

# (2) 각 이벤트가 1일 때
event_types = ['ev_unexp', 'ev_resp', 'ev_out']

for ev_col in event_types:
    if ev_col not in df.columns:
        print(f"[Skip] '{ev_col}' 컬럼이 데이터에 없습니다.")
        continue

    # 해당 이벤트가 발생한(1) 데이터 필터링
    subset = df[df[ev_col] == 1]

    col_name = f"Event: {ev_col}"
    props = calculate_proportions(subset, col_name)

    if props is not None:
        results.append(props)
        print(f"- {col_name}: 샘플 {len(subset)}개")
    else:
        print(f"- {col_name}: 샘플 없음 (0개)")

# =========================================================
# 5. 결과 통합 및 저장
# =========================================================
if results:
    # 옆으로 합치기 (Column Bind)
    final_df = pd.concat(results, axis=1)

    print("\n[분석 결과 요약 (비율 0~1)]")
    print(final_df)

    # 엑셀 저장
    final_df.to_excel(output_path)
    print(f"\n결과 파일이 저장되었습니다: {output_path}")
else:
    print("분석할 결과가 없습니다.")