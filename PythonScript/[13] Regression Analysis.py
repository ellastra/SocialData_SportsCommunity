import pandas as pd
import numpy as np
import os

# =========================================================
# 1. 파일 경로 설정
# =========================================================
base_dir = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity'

# (1) Race-Lap 기본 분석 데이터 (댓글 수, 간격 등)
analysis_path = os.path.join(base_dir, 'AnalysisResults/f1_race_lap_analysis.xlsx')
# (2) 이벤트 데이터
event_path = os.path.join(base_dir, 'EventLogData/F1 Event Data.xlsx')
# (3) 감정 분석 결과 (개별 댓글 단위)
emotion_path = os.path.join(base_dir, 'EmotionAnalysis/f1_community_prediction_result.csv')

# 결과 저장 경로
output_path = os.path.join(base_dir, 'AnalysisResults/f1_race_lap_full_dataset.xlsx')

# =========================================================
# 2. 데이터 로드
# =========================================================
print("데이터 로드 중...")
df_analysis = pd.read_excel(analysis_path)
df_event = pd.read_excel(event_path)
df_emotion = pd.read_csv(emotion_path)

# 컬럼명 공백 제거
df_analysis.columns = df_analysis.columns.str.strip()
df_event.columns = df_event.columns.str.strip()
df_emotion.columns = df_emotion.columns.str.strip()


# =========================================================
# 3. 공통 키(Key) 생성 함수 (모든 데이터프레임에 적용)
# =========================================================
def make_common_lap_key(val):
    """모든 랩 표기를 'Lap N' 또는 'After Lap'으로 통일"""
    s = str(val).strip().lower()

    if s in ['finish', 'after lap']:
        return 'After Lap'

    clean_s = s.replace('lap', '').strip()
    try:
        num = int(float(clean_s))
        return f"Lap {num}"
    except:
        return str(val).strip()


print("\n[매칭 키 생성 중...]")

# (1) Analysis 데이터 키 적용
df_analysis['race'] = df_analysis['race'].astype(str).str.strip()
df_analysis['join_lap'] = df_analysis['lap'].apply(make_common_lap_key)

# (2) Event 데이터 키 적용
df_event['race'] = df_event['race'].astype(str).str.strip()
# Event 데이터의 Lap 컬럼 찾기
event_lap_col = next((c for c in df_event.columns if 'lap' in c.lower()), 'Lap')
df_event['join_lap'] = df_event[event_lap_col].apply(make_common_lap_key)

# (3) Emotion 데이터 키 적용 (집계를 위해 필요)
df_emotion['race'] = df_emotion['race'].astype(str).str.strip()
# Emotion 데이터의 Lap 컬럼 찾기
emo_lap_col = next((c for c in ['lap', 'LapNumber', 'Lap_Number', 'Lap'] if c in df_emotion.columns), None)
if emo_lap_col:
    df_emotion['join_lap'] = df_emotion[emo_lap_col].apply(make_common_lap_key)
else:
    raise ValueError("Emotion 데이터에서 Lap 컬럼을 찾을 수 없습니다.")

# =========================================================
# 4. 감정 데이터 집계 (Aggregation): 댓글 단위 -> 랩 단위
# =========================================================
print("감정 데이터 랩별 집계 중...")

# 4-1. 감정 라벨링 (ID -> Name)
id2label = {0: "anger", 1: "disgust", 2: "fear", 3: "happiness", 4: "sadness", 5: "surprise"}


def get_emotion(row):
    if 'pred_score' in row and pd.notnull(row['pred_score']) and row['pred_score'] <= 0.0:
        return 'neutral'

    # Label Parsing
    label_col = next((c for c in ['pred_label', 'pred_label_id', 'label'] if c in row.index), None)
    val = row[label_col]

    try:
        if isinstance(val, str) and "LABEL_" in val:
            lid = int(val.split("_")[-1])
        else:
            lid = int(float(val))
        return id2label.get(lid, 'neutral')
    except:
        return 'neutral'


df_emotion['emotion_final'] = df_emotion.apply(get_emotion, axis=1)

# 4-2. 랩별 감정 비율 계산
# pivot_table을 사용하여 Race-Lap별 각 감정의 개수를 셉니다.
emo_counts = df_emotion.pivot_table(
    index=['race', 'join_lap'],
    columns='emotion_final',
    aggfunc='size',
    fill_value=0
)

# 비율(Proportion)로 변환
emo_props = emo_counts.div(emo_counts.sum(axis=1), axis=0)
# 컬럼명 변경 (prop_anger, prop_happiness 등)
emo_props.columns = [f'prop_{col}' for col in emo_props.columns]
emo_props = emo_props.reset_index()

print(f"- 집계된 감정 데이터: {len(emo_props)}개 행")

# =========================================================
# 5. 데이터 병합 (Merge All)
# =========================================================
print("\n데이터 병합 중...")

# 1단계: Analysis(통계) + Event(이벤트)
cols_event = ['race', 'join_lap', 'ev_unexp', 'ev_resp', 'ev_out']
merged_1 = pd.merge(df_analysis, df_event[cols_event], on=['race', 'join_lap'], how='left')

# 이벤트 마커 생성
merged_1['event_marker'] = np.where(merged_1[['ev_unexp', 'ev_resp', 'ev_out']].notna().any(axis=1), 1, 0)
merged_1[['ev_unexp', 'ev_resp', 'ev_out']] = merged_1[['ev_unexp', 'ev_resp', 'ev_out']].fillna(0)

# 2단계: Merged_1 + Emotion(감정 비율)
merged_final = pd.merge(merged_1, emo_props, on=['race', 'join_lap'], how='left')

# 감정 비율 NaN 처리 (해당 랩에 댓글이 없거나 매칭 안 된 경우 0으로)
prop_cols = [c for c in merged_final.columns if c.startswith('prop_')]
merged_final[prop_cols] = merged_final[prop_cols].fillna(0)

# join_lap 제거 및 정리
merged_final = merged_final.drop(columns=['join_lap'])

# =========================================================
# 6. 저장
# =========================================================
merged_final.to_excel(output_path, index=False)

print("-" * 30)
print("작업 완료!")
print(f"최종 데이터 개수: {len(merged_final)}")
print(f"저장 경로: {output_path}")
print("\n[생성된 컬럼 목록]")
print(list(merged_final.columns))