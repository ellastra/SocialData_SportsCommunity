import pandas as pd
import numpy as np
import os
import pytz

# --- 📌 사용자 정의 변수 및 경로 ---
GRAND_PRIX = 'Las_Vegas'
YEAR = 2024
# 랩타임 데이터의 경로 (사용자 제공)
LAP_AVG_FILE = f'/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/GlobalLapTimeData/{YEAR}_{GRAND_PRIX}_Lapwise_Average_Lap_Times_KST_Shifted.csv'
# 커뮤니티 데이터 파일명 (업로드된 파일)
COMMUNITY_FILE = f'/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/CommunityData/Community_{GRAND_PRIX}.csv'
# 출력 파일명
OUTPUT_FILE = f'/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/CommunityData/{GRAND_PRIX}_Lapwise_Comment_Count.csv'

# ------------------------------------

# 1. 파일 로드 및 시간대 정의
KST = pytz.timezone('Asia/Seoul')
TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

try:
    # 랩 평균 데이터 로드
    df_lap = pd.read_csv(LAP_AVG_FILE)

    # 커뮤니티 데이터 로드 (댓글 시간을 'Timestamp' 컬럼으로 가정)
    df_community = pd.read_csv(COMMUNITY_FILE)

    print(f"✅ 파일 로드 성공: {os.path.basename(LAP_AVG_FILE)}, {COMMUNITY_FILE}")

except Exception as e:
    print(f"❌ 파일 로드 오류: 경로를 다시 확인해 주세요. 오류: {e}")
    exit()

# 2. 시간 컬럼을 KST Timezone-aware datetime 객체로 변환
try:
    # 랩 데이터 시간 변환
    df_lap['Avg_LapStartTime_KST_DT'] = pd.to_datetime(df_lap['Avg_LapStartTime_KST'],
                                                       format=TIME_FORMAT).dt.tz_localize(KST)
    df_lap['Avg_LapFinishTime_KST_DT'] = pd.to_datetime(df_lap['Avg_LapFinishTime_KST'],
                                                        format=TIME_FORMAT).dt.tz_localize(KST)

    df_community['Comment_Time_DT'] = pd.to_datetime(df_community['post_timestamp']).dt.tz_localize(KST)

except Exception as e:
    print(f"\n❌ 시간 변환 오류: 시간 문자열 포맷을 확인해주세요. 오류: {e}")
    exit()

# 3. LapTime 구간 설정 (Time Interval)

# 구간 경계 정의: Lap 1 Start부터 마지막 Lap Finish까지의 모든 시작 시간 + 마지막 종료 시간
lap_start_times = df_lap['Avg_LapStartTime_KST_DT'].tolist()  # N 개의 랩 시작 시각
last_lap_finish_time = df_lap['Avg_LapFinishTime_KST_DT'].iloc[-1]
base_borders = lap_start_times + [last_lap_finish_time]  # N + 1 개의 경계

# 외부 경계 정의 (Before/After Lap 레이블 처리를 위해)
min_border = lap_start_times[0] - pd.Timedelta(hours=1)
max_border = last_lap_finish_time + pd.Timedelta(hours=1)

# 🌟 수정된 부분: 최종 구간 경계(final_borders)에는 min_border와 max_border를 포함합니다.
# [min_border, L1_Start, L2_Start, ..., LN_Finish, max_border] => N + 3 개
final_borders = [min_border] + base_borders + [max_border]

# 구간 레이블 설정: 1 (Before) + N (Laps) + 1 (After) => N + 2 개
lap_labels = ['Before Lap'] + df_lap['LapNumber'].astype(str).tolist() + ['After Lap']

# 4. Pandas.cut을 사용하여 댓글에 랩 레이블 지정
# bins 개수(N+3)와 labels 개수(N+2)가 일치하므로 오류가 해결됩니다.
df_community['Lap_Label'] = pd.cut(
    df_community['Comment_Time_DT'],
    bins=final_borders,
    labels=lap_labels,
    include_lowest=True,
    right=False  # 왼쪽 경계(시작 시각)를 포함하도록 설정: [Lap N Start, Lap N+1 Start)
)

# 5. 랩별 댓글 수 그룹화 및 카운트
comment_counts = df_community.groupby('Lap_Label')['Comment_Time_DT'].count().reset_index()
comment_counts.rename(columns={'Comment_Time_DT': 'Comment_Count'}, inplace=True)

# 6. 최종 CSV 파일로 저장
comment_counts.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

print("\n--- 결과 요약 ---")
print(f"✅ 랩별 댓글 수 데이터 저장 성공!")
print(f"생성된 파일명: **{OUTPUT_FILE}**")
print("저장된 데이터 미리보기 (Lap별 댓글 수):")
print(comment_counts.head())