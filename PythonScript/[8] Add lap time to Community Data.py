import pandas as pd
import numpy as np
import os
import pytz

# --- 📌 사용자 정의 변수 및 경로 ---
GRAND_PRIX = 'Abu_Dhabi'
YEAR = 2024
BASE_DIR = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/GlobalLapTimeData'
COMMUNITY_FILE = f'/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/CommunityData/Community_{GRAND_PRIX}.csv'

# 입력 랩타임 파일 (썸머타임/시차 조정된 파일 사용)
LAP_AVG_FILE = os.path.join(
    BASE_DIR,
    f'{YEAR}_{GRAND_PRIX}_Lapwise_Average_Lap_Times_KST_Shifted.csv'
)

# 출력 파일 (원래 커뮤니티 파일에 LapNumber 컬럼을 추가)
OUTPUT_FILE = f'/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/CommunityData/Community_{GRAND_PRIX}_With_LapNumber.csv'
# ------------------------------------

# 1. 파일 로드 및 시간대 정의
KST = pytz.timezone('Asia/Seoul')
TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

try:
    # 랩 평균 데이터 로드 (Lap Time Interval의 경계)
    df_lap = pd.read_csv(LAP_AVG_FILE)

    # 커뮤니티 데이터 로드
    df_community = pd.read_csv(COMMUNITY_FILE)

    print(f"✅ 파일 로드 성공: {os.path.basename(LAP_AVG_FILE)}, {os.path.basename(COMMUNITY_FILE)}")

except Exception as e:
    print(f"❌ 파일 로드 오류: 경로를 다시 확인해 주세요. 오류: {e}")
    exit()

# 2. 시간 컬럼을 KST Timezone-aware datetime 객체로 변환
KST = pytz.timezone('Asia/Seoul')
TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

try:
    # 랩 데이터 시간 변환: Naive Datetime 생성 후 tz_localize
    df_lap['Avg_LapStartTime_KST_DT'] = pd.to_datetime(df_lap['Avg_LapStartTime_KST'],
                                                       format=TIME_FORMAT).dt.tz_localize(KST)
    df_lap['Avg_LapFinishTime_KST_DT'] = pd.to_datetime(df_lap['Avg_LapFinishTime_KST'],
                                                        format=TIME_FORMAT).dt.tz_localize(KST)

    # 🌟 커뮤니티 데이터 수정: Naive Datetime 생성 시 errors='coerce' 사용
    community_time_naive = pd.to_datetime(df_community['post_timestamp'], errors='coerce')

    # 🌟 tz_localize 호출 시 errors 인자 완전히 제거
    df_community['Comment_Time_DT'] = community_time_naive.dt.tz_localize(KST)

    # KST 시간으로 변환되지 않은 댓글(NaT)은 분석에서 제외
    df_community.dropna(subset=['Comment_Time_DT'], inplace=True)

except KeyError:
    print("\n❌ 오류: 커뮤니티 데이터에 'Timestamp' 컬럼이 없습니다.")
    exit()
except Exception as e:
    print(f"\n❌ 시간 변환 오류: {e}")
    exit()

# 3. LapTime 구간 설정 (Time Interval)

# 구간 경계 정의: Lap 1 Start부터 마지막 Lap Finish까지의 모든 시작 시간 + 마지막 종료 시간
lap_start_times = df_lap['Avg_LapStartTime_KST_DT'].tolist()
last_lap_finish_time = df_lap['Avg_LapFinishTime_KST_DT'].iloc[-1]
base_borders = lap_start_times + [last_lap_finish_time]  # N + 1 개의 경계

# 외부 경계 정의 (Before/After Lap 레이블 처리를 위해)
min_border = lap_start_times[0] - pd.Timedelta(hours=1)
max_border = last_lap_finish_time + pd.Timedelta(hours=1)

# 최종 구간 경계 리스트: [min_border, L1_Start, L2_Start, ..., LN_Finish, max_border]
final_borders = [min_border] + base_borders + [max_border]

# 구간 레이블 설정: 1 (Before) + N (Laps) + 1 (After) => N + 2 개
lap_labels = ['Before Lap'] + df_lap['LapNumber'].astype(int).astype(str).tolist() + ['After Lap']

# 4. Pandas.cut을 사용하여 댓글에 랩 레이블 지정
df_community['Lap_Label'] = pd.cut(
    df_community['Comment_Time_DT'],
    bins=final_borders,
    labels=lap_labels,
    include_lowest=True,
    right=False  # [Lap N Start, Lap N+1 Start) 구간으로 설정
)

# 5. 최종 LapNumber 컬럼 추가 (정수형)
# Lap_Label에서 'Before Lap'/'After Lap'을 제외한 순수 숫자만 추출
df_community['LapNumber'] = pd.to_numeric(df_community['Lap_Label'], errors='coerce', downcast='integer')


# 6. 최종 CSV 파일로 저장
df_community.drop(columns=['Comment_Time_DT'], inplace=True)
df_community.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

print("\n--- 결과 요약 ---")
print(f"✅ 커뮤니티 데이터에 랩 번호 추가 저장 성공!")
print(f"생성된 파일명: **{os.path.basename(OUTPUT_FILE)}**")