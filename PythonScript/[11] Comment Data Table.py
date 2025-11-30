import pandas as pd

# 1. 파일 경로 설정 (앞서 병합된 최종 파일)
file_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_race_lap_analysis_with_event.xlsx'

# 2. 데이터 로드
print("데이터 로드 중...")
df = pd.read_excel(file_path)

# 분석할 이벤트 변수들과 커뮤니티 지표 설정
# comment_count: 댓글 수
# avg_text_len: 평균 댓글 길이
# avg_time_gap: 평균 댓글 간격 (초 단위, 낮을수록 화력이 셈)
event_vars = ['ev_unexp', 'ev_resp', 'ev_out']
metrics = ['comment_count', 'avg_text_len', 'avg_time_gap']

# 결과 담을 리스트
summary_list = []

print("\n[이벤트별 영향력 분석 결과]")
print("=" * 60)

for event in event_vars:
    # 해당 이벤트 컬럼이 데이터에 있는지 확인
    if event in df.columns:
        # 0(미발생)과 1(발생)로 그룹화하여 평균 계산
        grouped = df.groupby(event)[metrics].mean()

        # 보기 좋게 출력
        print(f"\n>> {event} (0: 미발생, 1: 발생) 에 따른 평균값:")
        print(grouped)

        # 결과를 데이터프레임 형태로 정리해서 저장용 리스트에 추가
        diff_df = grouped.copy()
        diff_df['Event_Type'] = event
        summary_list.append(diff_df)
    else:
        print(f"\n[Warning] '{event}' 컬럼이 데이터에 없습니다.")

print("\n" + "=" * 60)

# 3. 통합 요약표 만들기 (엑셀 저장용)
if summary_list:
    # 깔끔하게 다시 정리
    export_df = pd.DataFrame()

    for event in event_vars:
        if event in df.columns:
            # 그룹화 및 인덱스 리셋
            temp = df.groupby(event)[metrics].mean().reset_index()

            # 컬럼명 통일 (ev_unexp, ev_resp -> Is_Occurred)
            temp.rename(columns={event: 'Is_Occurred'}, inplace=True)

            # 이벤트 타입 명시
            temp['Event_Type'] = event

            # 통합 데이터프레임에 추가
            export_df = pd.concat([export_df, temp])

    # 컬럼 순서 재배치 (avg_time_gap 포함)
    export_df = export_df[['Event_Type', 'Is_Occurred', 'comment_count', 'avg_text_len', 'avg_time_gap']]

    # 저장
    save_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_event_impact_summary.xlsx'
    export_df.to_excel(save_path, index=False)
    print(f"\n요약 결과가 저장되었습니다: {save_path}")
    print(export_df)