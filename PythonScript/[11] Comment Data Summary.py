import pandas as pd
import numpy as np

# 1. 파일 경로 설정
analysis_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_race_lap_analysis.xlsx'
event_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/EventLogData/F1 Event Data.xlsx'

# 2. 데이터 로드
print("데이터 로드 중...")
df_analysis = pd.read_excel(analysis_path)
df_event = pd.read_excel(event_path)


# =========================================================
# 핵심 수정: 공통 키(Key) 생성 함수 정의
# =========================================================

def make_common_lap_key(val):
    """
    어떤 입력값(1, '1', '1.0', 'Lap 1', 'Finish')이 들어와도
    통일된 포맷('Lap 1', 'After Lap')으로 변환하는 함수
    """
    s = str(val).strip().lower()  # 소문자로 통일해서 처리

    # 1. Finish 처리
    if s == 'finish':
        return 'After Lap'

    # 2. 이미 포맷이 완성된 경우 ('after lap')
    if s == 'after lap':
        return 'After Lap'

    # 3. 숫자만 있는 경우 or '1.0' 같은 실수형 문자열 (-> "Lap 1"로 변환)
    # 숫자 제거하고 남은게 없거나 점(.) 하나라면 숫자로 간주
    clean_s = s.replace('lap', '').strip()  # 'lap 1' -> '1'

    try:
        # float으로 먼저 변환 후 int로 바꿔서 소수점(.0) 제거
        num = int(float(clean_s))
        return f"Lap {num}"
    except:
        # 변환 실패 시 원본 그대로 반환 (혹시 모를 텍스트 데이터)
        # 예: 'Start' 등은 원본 유지하거나 필요시 규칙 추가
        return str(val).strip()


# =========================================================
# 적용: 양쪽 데이터프레임에 "똑같은 함수" 적용
# =========================================================

print("\n[매칭 키 생성 중...]")

# 1. Race 이름 공백 제거
df_analysis['race'] = df_analysis['race'].astype(str).str.strip()
df_event['race'] = df_event['race'].astype(str).str.strip()

# 2. Lap 컬럼 통일 (Analysis)
df_analysis['join_lap'] = df_analysis['lap'].apply(make_common_lap_key)

# 3. Lap 컬럼 통일 (Event)
# Event 데이터의 컬럼명 자동 탐색
event_lap_col = 'Lap'
for col in df_event.columns:
    if 'lap' in col.lower():
        event_lap_col = col
        break
df_event['join_lap'] = df_event[event_lap_col].apply(make_common_lap_key)

# =========================================================
# 디버깅: 매칭이 잘 될지 눈으로 확인 (중요!)
# =========================================================
print("\n--- 키 포맷 확인 (상위 5개) ---")
print(f"Analysis 쪽 키: {df_analysis['join_lap'].unique()[:5]}")
print(f"Event 쪽 키   : {df_event['join_lap'].unique()[:5]}")

# 교집합 확인
common_keys = set(df_analysis['join_lap']).intersection(set(df_event['join_lap']))
print(f"\n매칭 가능한 공통 Lap 개수: {len(common_keys)} 종류")
if len(common_keys) == 0:
    print("WARNING: 매칭되는 Lap이 하나도 없습니다! 포맷을 다시 확인하세요.")

# =========================================================
# 병합 (Merge) & 마커 생성
# =========================================================

# 1. 병합할 컬럼 선택
cols_to_use = ['race', 'join_lap', 'ev_unexp', 'ev_resp', 'ev_out']

# 2. Left Join 수행
merged_df = pd.merge(df_analysis, df_event[cols_to_use],
                     on=['race', 'join_lap'],
                     how='left')

# 3. event_marker 생성
merged_df['event_marker'] = np.where(
    merged_df[['ev_unexp', 'ev_resp', 'ev_out']].notna().any(axis=1),
    1,
    0
)

# 4. NaN 처리
merged_df['ev_unexp'] = merged_df['ev_unexp'].fillna(0)
merged_df['ev_resp'] = merged_df['ev_resp'].fillna(0)
merged_df['ev_out'] = merged_df['ev_out'].fillna(0)

# 불필요한 join_lap 제거
merged_df = merged_df.drop(columns=['join_lap'])

# =========================================================
# 저장 및 결과 확인
# =========================================================
output_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_race_lap_analysis_with_event.xlsx'
merged_df.to_excel(output_path, index=False)

print("-" * 30)
print("작업 완료!")
print(f"총 데이터 개수: {len(merged_df)}")
print(f"이벤트 매칭 성공(marker=1) 개수: {merged_df['event_marker'].sum()}")

# 어떤 이벤트들이 매칭되었는지 살짝 보여주기
if merged_df['event_marker'].sum() > 0:
    print("\n[매칭된 이벤트 예시]")
    print(merged_df[merged_df['event_marker'] == 1][['race', 'lap', 'ev_unexp']].head())
else:
    print("\n[주의] 여전히 매칭된 이벤트가 0개입니다. Race 이름이 서로 다른지 확인해보세요.")