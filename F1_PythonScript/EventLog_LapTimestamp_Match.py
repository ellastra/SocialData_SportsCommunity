# -*- coding: utf-8 -*-
"""
Round1_Bahrain_Event.csv + bahrain_2024_laps_kst.csv 병합 스크립트
Lap 번호를 기준으로 각 이벤트에 해당 Lap의 시작/종료 시각(KST)을 추가합니다.
"""

import pandas as pd
from pathlib import Path

# --- 경로 설정 ---
BASE = Path("/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_EventLog")
EVENT_CSV = BASE / "Round1_Bahrain_Event.csv"
LAPTIME_CSV = BASE / "bahrain_2024_laps_kst.csv"
OUTPUT_CSV = BASE / "Round1_Bahrain_Event_with_timewindow.csv"

# --- 1️⃣ 파일 불러오기 ---
print(f"[INFO] Loading {EVENT_CSV.name} and {LAPTIME_CSV.name}...")
events = pd.read_csv(EVENT_CSV, encoding="utf-8-sig")
laps = pd.read_csv(LAPTIME_CSV, encoding="utf-8-sig")

# Lap 컬럼명 표준화
if "lap_number" in laps.columns:
    laps.rename(columns={"lap_number": "lap"}, inplace=True)

# --- 2️⃣ Lap 기반 병합 ---
merged = pd.merge(events, laps, on="lap", how="left")

# --- 3️⃣ 시간 형식 통일 (문자열로 변환) ---
merged["lap_start_kst"] = pd.to_datetime(merged["lap_start_kst"]).dt.strftime("%Y-%m-%d %H:%M:%S")
merged["lap_end_kst"] = pd.to_datetime(merged["lap_end_kst"]).dt.strftime("%Y-%m-%d %H:%M:%S")

# --- 4️⃣ 결과 저장 ---
merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"[DONE] 병합 완료 → {OUTPUT_CSV}")
print(f"[INFO] 총 {len(merged)}개의 이벤트에 Lap별 시간대 추가됨.")