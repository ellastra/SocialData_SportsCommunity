import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
import os

# =========================================================
# 1. 설정 및 데이터 로드
# =========================================================
# 방금 만든 통합 데이터셋 경로
base_dir = '/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity'
input_path = os.path.join(base_dir, 'AnalysisResults/f1_race_lap_full_dataset.xlsx')
output_txt_path = os.path.join(base_dir, 'AnalysisResults/f1_final_regression_report.txt')

print(f"데이터 로드 중: {input_path}")
df = pd.read_excel(input_path)

# 컬럼명 공백 제거 (오류 방지)
df.columns = df.columns.str.strip()

# 데이터 확인
print(f"총 데이터 개수: {len(df)}개 (Race-Lap 단위)")
print(f"컬럼 목록: {list(df.columns)}")

# =========================================================
# 2. 회귀분석 함수 정의
# =========================================================
results_summary = []


def run_regression(target_col, title):
    print(f"\n--- Analyzing: {target_col} ({title}) ---")

    # 1. 데이터 유효성 검사
    if target_col not in df.columns:
        print(f"[Skip] 컬럼 '{target_col}'이 데이터에 없습니다.")
        return

    # 2. 회귀식 정의 (Target ~ X1 + X2 + X3 + Control)
    # 독립변수: ev_unexp(예상밖), ev_resp(책임), ev_out(리타이어)
    # 통제변수: comment_count (댓글이 많을수록 감정이 격해질 수 있으므로 통제)
    formula = f"{target_col} ~ ev_unexp + ev_resp + ev_out + comment_count"

    # 3. 모델 적합 (OLS)
    try:
        model = ols(formula, data=df).fit()

        # 4. 결과 저장
        summary_text = f"\n{'=' * 60}\n[Model] {title}\nFormula: {formula}\n{'=' * 60}\n"
        summary_text += model.summary().as_text() + "\n\n"
        results_summary.append(summary_text)

        # 5. 핵심 결과 콘솔 출력 (유의한 변수만)
        print(f"R-squared: {model.rsquared:.3f}")
        for term in ['ev_unexp', 'ev_resp', 'ev_out']:
            coef = model.params.get(term, 0)
            pval = model.pvalues.get(term, 1)
            star = "*" if pval < 0.05 else ""
            print(f" - {term}: Coef = {coef:.4f} (P = {pval:.4f}) {star}")

    except Exception as e:
        print(f"회귀분석 중 오류 발생: {e}")


# =========================================================
# 3. 분석 실행
# =========================================================

# (1) 댓글 간격 (화력/Speed) 예측
# -> 간격이 줄어들수록(- Coef) 화력이 센 것임
run_regression('avg_time_gap', 'Impact on Comment Speed (Time Gap)')

# (2) 주요 감정 비율 예측
# 어떤 이벤트가 어떤 감정을 자극하는지 확인
run_regression('prop_anger', 'Impact on Anger Proportion')
run_regression('prop_happiness', 'Impact on Happiness Proportion')
run_regression('prop_surprise', 'Impact on Surprise Proportion')
run_regression('prop_sadness', 'Impact on Sadness Proportion')
run_regression('prop_fear', 'Impact on Fear Proportion')
run_regression('prop_disgust', 'Impact on Disgust Proportion')

# =========================================================
# 4. 결과 파일 저장
# =========================================================
if results_summary:
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.writelines(results_summary)

    print("-" * 30)
    print(f"전체 분석 리포트가 저장되었습니다: {output_txt_path}")
    print("팁: P-value(P>|t|)가 0.05보다 작은 항목의 Coef(계수)를 확인하세요.")
    print("    (양수면 증가, 음수면 감소)")
else:
    print("분석 결과가 없습니다.")