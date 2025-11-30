import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# =========================================================
# 1. 설정 및 데이터 로드
# =========================================================
csv_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_emotion_with_event.csv'
output_excel_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_event_emotion_proportions.xlsx'
output_img_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_event_emotion_pie_charts.png'

print(f"데이터 로드 중: {csv_path}")
df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip()

# =========================================================
# 2. 감정 라벨 매핑 및 전처리
# =========================================================
id2label = {
    0: "anger", 1: "disgust", 2: "fear", 3: "happiness",
    4: "sadness", 5: "surprise"
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
    raise KeyError(f"감정 라벨 컬럼을 찾을 수 없습니다. (후보: {candidates})")


def get_emotion_name(row):
    # Confidence Check
    if 'pred_score' in row and pd.notnull(row['pred_score']) and row['pred_score'] <= 0.3:
        return 'neutral'

    val = row[label_col]
    if pd.isna(val): return 'neutral'

    try:
        if isinstance(val, str) and "LABEL_" in val:
            label_id = int(val.split("_")[-1])
        else:
            label_id = int(float(val))
        return id2label.get(label_id, "neutral")
    except:
        return "neutral"


print("감정 라벨 변환 중...")
df['emotion_final'] = df.apply(get_emotion_name, axis=1)


# =========================================================
# 3. 비율 계산 함수
# =========================================================
def calculate_proportions(data, title):
    if len(data) == 0:
        return None
    counts = data['emotion_final'].value_counts()
    props = counts / counts.sum()
    props_df = pd.DataFrame(props).reindex(EMOTIONS).fillna(0)
    props_df.columns = [title]
    return props_df


# =========================================================
# 4. 분석 실행 및 데이터프레임 생성
# =========================================================
print("이벤트별 비율 계산 중...")
results = []
col_names = []  # 그래프 제목용

# (1) Baseline
if 'event_marker' not in df.columns:
    event_cols = [c for c in ['ev_unexp', 'ev_resp', 'ev_out'] if c in df.columns]
    if event_cols:
        df['event_marker'] = df[event_cols].notna().any(axis=1).astype(int)
    else:
        df['event_marker'] = 0

df_no_event = df[df['event_marker'] == 0]
results.append(calculate_proportions(df_no_event, "Baseline"))
col_names.append(f"Baseline (No Event)\n(N={len(df_no_event)})")

# (2) Events
event_types = ['ev_unexp', 'ev_resp', 'ev_out']
event_labels = {
    'ev_unexp': 'Unexpectedness',
    'ev_resp': 'Responsibility',
    'ev_out': 'Outcome Relevance'
}

for ev_col in event_types:
    if ev_col in df.columns:
        subset = df[df[ev_col] == 1]
        props = calculate_proportions(subset, ev_col)

        if props is not None:
            results.append(props)
            col_names.append(f"{event_labels.get(ev_col, ev_col)}\n(N={len(subset)})")

# 결과 통합
if results:
    final_df = pd.concat(results, axis=1)
    final_df.to_excel(output_excel_path)
    print(f"엑셀 저장 완료: {output_excel_path}")

    # =========================================================
    # 5. 원그래프(Pie Chart) 시각화
    # =========================================================
    print("원그래프 생성 중...")

    # 색상 설정 (직관적인 색상 매핑)
    color_map = {
        "neutral": "#D3D3D3",  # LightGray
        "anger": "#FF4500",  # OrangeRed (강렬함)
        "happiness": "#FFD700",  # Gold
        "sadness": "#4169E1",  # RoyalBlue
        "surprise": "#9370DB",  # MediumPurple
        "fear": "#2F4F4F",  # DarkSlateGray (어두움)
        "disgust": "#228B22",  # ForestGreen
    }
    colors = [color_map[emo] for emo in final_df.index]

    # 그래프 레이아웃 (2x2 그리드 추천)
    num_charts = len(final_df.columns)
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))  # 가로로 길게 배치 (1x4)
    # 만약 2x2로 보고 싶다면 아래 주석 해제 후 위 줄 주석 처리
    # fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    # axes = axes.flatten()

    if num_charts == 1:
        axes = [axes]

    for i, col in enumerate(final_df.columns):
        ax = axes[i]
        data = final_df[col]


        # 0%인 데이터는 라벨 겹침 방지를 위해 숨김 처리할 수도 있으나,
        # 여기서는 autopct 함수로 2% 이상만 숫자 표시
        def my_autopct(pct):
            return f'{pct:.1f}%' if pct > 2 else ''


        wedges, texts, autotexts = ax.pie(
            data,
            labels=None,  # 범례가 있으므로 라벨은 생략하거나 선택
            autopct=my_autopct,
            startangle=90,
            colors=colors,
            counterclock=False,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )

        # 제목 설정
        ax.set_title(col_names[i], fontsize=12, fontweight='bold')

        # 텍스트 스타일 조정
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)

    # 범례 추가 (오른쪽 바깥에 하나만)
    fig.legend(final_df.index, title="Emotion", loc="center right", bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout(rect=[0, 0, 0.9, 1])  # 범례 공간 확보

    # 저장
    plt.savefig(output_img_path, dpi=150)
    print(f"그래프 저장 완료: {output_img_path}")
    # plt.show() # 로컬 환경에 따라 주석 해제

else:
    print("분석할 결과가 없어 그래프를 그리지 못했습니다.")