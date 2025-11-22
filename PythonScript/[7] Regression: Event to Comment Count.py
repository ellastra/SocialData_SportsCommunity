import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# --- 📌 파일 경로 정의 (생략) ---
YEAR = 2024
GRAND_PRIX = 'Japan'
BASE_DIR_COMMUNITY = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/CommunityData'
COMMENT_COUNT_FILE = os.path.join(BASE_DIR_COMMUNITY, f'{GRAND_PRIX}_Lapwise_Comment_Count.csv')
EVENT_CHAR_FILE = f'/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/EventLogData/Event_{GRAND_PRIX}.csv'
# ------------------------------------

# 1. 데이터 로드
try:
    df_comments = pd.read_csv(COMMENT_COUNT_FILE)
    df_events = pd.read_csv(EVENT_CHAR_FILE)
    print("✅ 데이터 로드 성공.")
except Exception as e:
    print(f"❌ 데이터 로드 오류: {e}")
    exit()

# 2. 데이터 정리 및 컬럼명 표준화

# 2-a. 댓글 데이터 정리 (댓글 수와 랩 번호)
df_comments['LapNumber'] = pd.to_numeric(df_comments['Lap_Label'], errors='coerce')
df_comments_race = df_comments.dropna(subset=['LapNumber']).copy()
df_comments_race['LapNumber'] = df_comments_race['LapNumber'].astype(int) # LapNumber -> int64

# 2-b. 이벤트 데이터 정리 (Category 및 LapNumber 통일)
columns_to_rename = {}

# 🌟 수정: 사용자 피드백 반영 ('lap' -> 'LapNumber')
if 'lap' in df_events.columns:
    columns_to_rename['lap'] = 'LapNumber'
elif 'Start_Lap' in df_events.columns: # 이전 단계의 백업
     columns_to_rename['Start_Lap'] = 'LapNumber'

# Category 컬럼명 통일 (가장 자주 발생하는 문제였으므로, 유연하게 처리)
CATEGORY_CANDIDATES = ['Category', 'category', 'Domain']
found_category_col = next((col for col in CATEGORY_CANDIDATES if col in df_events.columns), None)
if found_category_col and found_category_col != 'Category':
    columns_to_rename[found_category_col] = 'Category'
elif 'Category' not in df_events.columns and len(df_events.columns) > 1:
    # 비상: 두 번째 컬럼을 Category로 가정
    df_events.rename(columns={df_events.columns[1]: 'Category'}, inplace=True)


if columns_to_rename:
    df_events.rename(columns=columns_to_rename, inplace=True)

# 3. 🌟 타입 변환 (루트 오류 해결)
# df_events의 LapNumber를 정수형(int)으로 강제 변환하여 병합 오류 해결
df_events['LapNumber'] = pd.to_numeric(df_events['LapNumber'], errors='coerce').fillna(0).astype(int)

# LapNumber와 Category를 포함하는 유니크한 이벤트 목록 생성
df_events_unique = df_events[['LapNumber', 'Category', 'unexpectedness', 'outcome_relevance']].drop_duplicates()

# 4. 데이터 통합 (Merge)
df_analysis = pd.merge(
    df_comments_race,
    df_events_unique,
    on='LapNumber',
    how='left'
)

# 🌟 이벤트 유무 플래그 생성
df_analysis['Has_Event'] = df_analysis['Category'].notna().astype(int)

# Unexpected 또는 Outcome_Relevance 중 하나라도 1이면 Major Event
df_analysis['Major_Event'] = (
    (df_analysis['unexpectedness'] == 1) |
    (df_analysis['outcome_relevance'] == 1)
).astype(int)

# 5. 📊 통계적 분석 2: 주요 이벤트 범주별 평균 댓글 수 비교
# Normal Lap을 제외하고, 주요 범주 (최소 2회 이상 발생한 범주)만 비교
df_events_only = df_analysis[df_analysis['Has_Event'] == 1].copy()
category_counts = df_events_only['Category'].value_counts()
major_categories = category_counts[category_counts >= 2].index.tolist()

avg_by_category = df_events_only[df_events_only['Category'].isin(major_categories)].groupby('Category')['Comment_Count'].mean().sort_values(ascending=False)

print("\n--- 2. 주요 이벤트 범주별 평균 댓글 수 (Top Categories) ---")
print(avg_by_category.to_markdown(numalign="left", stralign="left", floatfmt=".2f"))

# 6. 📈 시각화: 댓글 수와 이벤트 발생 지점
plt.figure(figsize=(16, 7))
plt.plot(df_analysis['LapNumber'], df_analysis['Comment_Count'], label='Comment Count', color='gray', linestyle='-', alpha=0.6)

# 이벤트 발생 지점에 마커 표시
event_laps = df_analysis[df_analysis['Has_Event'] == 1]
# Major Event (빨간색)
major = event_laps[event_laps['Major_Event'] == 1]
plt.scatter(
    major['LapNumber'],
    major['Comment_Count'],
    c='red',
    marker='o',
    s=80,
    label='Major Event'
)

# Minor Event (파란색)
minor = event_laps[event_laps['Major_Event'] == 0]
plt.scatter(
    minor['LapNumber'],
    minor['Comment_Count'],
    c='blue',
    marker='o',
    s=50,
    label='Minor Event'
)


plt.xlabel("Lap Number", fontsize=12)
plt.ylabel("Comment Count", fontsize=12)
plt.title(f"{GRAND_PRIX} {YEAR} - Comment Count by Event", fontsize=14)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)

# 7. 파일 저장
plot_file = f'{YEAR}_{GRAND_PRIX}_Event_Reaction_Analysis.png'
plt.savefig(plot_file)

print(f"\n✅ 시각화 파일 저장 성공: {plot_file}")