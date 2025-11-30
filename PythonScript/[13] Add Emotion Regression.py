import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

# =========================================================
# 1. 설정 및 데이터 로드
# =========================================================
# 댓글 단위 데이터 (Event 정보가 병합된 파일)
csv_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_emotion_with_event.csv'
output_txt_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_logistic_regression_report.txt'
output_xlsx_path = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/AnalysisResults/f1_odds_ratios.xlsx'

print(f"데이터 로드 중: {csv_path}")
df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip()

# =========================================================
# 2. 전처리: 감정 레이블 변환 & 기준 범주 설정
# =========================================================
id2label = {
    0: "anger", 1: "disgust", 2: "fear", 3: "happiness",
    4: "sadness", 5: "surprise"
}

# 라벨 컬럼 찾기
label_col = next((c for c in ['pred_label', 'pred_label_id', 'label', 'Label'] if c in df.columns), None)
if not label_col:
    raise ValueError("Label 컬럼을 찾을 수 없습니다.")


def get_emotion_name(row):
    # Confidence 0.5 이하는 neutral (선택사항)
    if 'pred_score' in row and pd.notnull(row['pred_score']) and row['pred_score'] <= 0.5:
        return 'neutral'

    val = row[label_col]
    if pd.isna(val): return 'neutral'
    try:
        if isinstance(val, str) and "LABEL_" in val:
            lid = int(val.split("_")[-1])
        else:
            lid = int(float(val))
        return id2label.get(lid, 'neutral')
    except:
        return 'neutral'


df['emotion_final'] = df.apply(get_emotion_name, axis=1)

# [중요] 기준 범주(Reference Category) 설정
available_emotions = df['emotion_final'].unique()
print(f"분석 대상 감정: {available_emotions}")

if 'neutral' not in available_emotions:
    ref_cat = df['emotion_final'].mode()[0]
    print(f"주의: neutral이 없어 '{ref_cat}'을 기준 범주로 설정합니다.")
else:
    ref_cat = 'neutral'

# [Fix] 문자열 라벨을 숫자형으로 매핑 (Patsy 오류 방지)
# ref_cat을 0으로 설정하여 mnlogit의 기준 범주로 사용되게 함
categories = sorted(list(available_emotions))
emotion_map = {ref_cat: 0}
counter = 1
for cat in categories:
    if cat != ref_cat:
        emotion_map[cat] = counter
        counter += 1

# 역매핑 (결과 해석용)
int_to_emotion = {v: k for k, v in emotion_map.items()}

# 숫자형 타겟 생성
df['emotion_target'] = df['emotion_final'].map(emotion_map)
print(f"감정 매핑 테이블: {emotion_map}")

# =========================================================
# 3. 다항 로지스틱 회귀분석 (Multinomial Logistic Regression)
# =========================================================
print(f"\n로지스틱 회귀분석 시작 (기준 범주: {ref_cat})...")

# Formula: 감정(숫자) ~ 예상밖 + 책임 + 리타이어
formula = "emotion_target ~ ev_unexp + ev_resp + ev_out"

try:
    # 모델 적합
    model = smf.mnlogit(formula, data=df).fit()

    # 결과 요약
    print(model.summary())

    # 4. 오즈비(Odds Ratio) 계산
    odds_ratios = np.exp(model.params)
    p_values = model.pvalues

    # 결과 정리 (Odds Ratio + P-value)
    results_list = []

    # model.params.columns는 숫자형 코드(1, 2...)임 (0번은 기준이므로 없음)
    for emotion_code in model.params.columns:
        # 숫자 코드를 다시 감정 이름으로 변환
        emotion_name = int_to_emotion.get(emotion_code, f"Unknown_{emotion_code}")

        for var in model.params.index:
            if var == 'Intercept': continue

            or_val = odds_ratios.loc[var, emotion_code]
            pval = p_values.loc[var, emotion_code]

            results_list.append({
                'Target_Emotion': emotion_name,
                'Event_Variable': var,
                'Odds_Ratio': or_val,
                'P_value': pval,
                'Interpretation': 'Significant' if pval < 0.05 else 'Not Significant'
            })

    results_df = pd.DataFrame(results_list)

    # 보기 좋게 정렬 (유의한 것 위주로)
    results_df = results_df.sort_values(by=['P_value', 'Odds_Ratio'], ascending=[True, False])

    # =========================================================
    # 5. 저장
    # =========================================================
    # (1) 전체 리포트 (통계적 상세)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(model.summary().as_text())

    # (2) 오즈비 엑셀 (해석용)
    results_df.to_excel(output_xlsx_path, index=False)

    print("-" * 30)
    print("분석 완료!")
    print(f"상세 통계 리포트: {output_txt_path}")
    print(f"오즈비(Odds Ratio) 결과: {output_xlsx_path}")

    print("\n[핵심 결과 미리보기 (P < 0.05)]")
    sig_results = results_df[results_df['P_value'] < 0.05]
    if not sig_results.empty:
        print(sig_results)
    else:
        print("통계적으로 유의미한(P < 0.05) 결과가 발견되지 않았습니다.")

except Exception as e:
    print(f"회귀분석 중 오류 발생: {e}")
    print("Tip: 데이터 샘플 수가 너무 적거나, 특정 감정의 빈도가 0이면 수렴하지 않을 수 있습니다.")