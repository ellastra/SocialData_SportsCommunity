# -*- coding: utf-8 -*-
"""
OpenF1 API를 이용해 2024 Bahrain Grand Prix (Race)의 랩별 시작/종료 시각을 가져옵니다.
기준 드라이버: Max Verstappen (driver_number=1)
"""

import requests
import pandas as pd
from datetime import timedelta

# --- 설정 ---
YEAR = 2024
COUNTRY = "United Arab Emirates"
SESSION_NAME = "Race"
DRIVER_NUMBER = 55  # Max Verstappen
BASE_URL = "https://api.openf1.org/v1"


def get_session_key(year, country, session_name):
    url = f"{BASE_URL}/sessions"
    params = {"year": year, "country_name": country, "session_name": session_name}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise RuntimeError(f"Session not found for {year} {country} {session_name}")
    session_key = data[0]["session_key"]
    print(f"[INFO] Session key: {session_key}")
    return session_key


def get_laps(session_key, driver_number):
    url = f"{BASE_URL}/laps"
    params = {"session_key": session_key, "driver_number": driver_number}
    r = requests.get(url, params=params)
    r.raise_for_status()
    laps = pd.DataFrame(r.json())
    if laps.empty:
        raise RuntimeError("No lap data found for this driver.")
    return laps


def main():
    print(f"[INFO] Loading {YEAR} {COUNTRY} {SESSION_NAME} lap data from OpenF1...")

    session_key = get_session_key(YEAR, COUNTRY, SESSION_NAME)
    laps = get_laps(session_key, DRIVER_NUMBER)

    # 필요한 컬럼만 추출
    df = laps[["lap_number", "date_start", "lap_duration"]].copy()
    df["date_start"] = pd.to_datetime(df["date_start"], utc=True)
    df["lap_duration"] = pd.to_timedelta(df["lap_duration"], unit="s")
    df["date_end"] = df["date_start"] + df["lap_duration"]

    # KST 변환
    df["lap_start_kst"] = df["date_start"].dt.tz_convert("Asia/Seoul")
    df["lap_end_kst"] = df["date_end"].dt.tz_convert("Asia/Seoul")

    # 정리
    out = df[["lap_number", "lap_start_kst", "lap_end_kst"]].sort_values("lap_number")
    print(out.to_string(index=False))

    # CSV로 저장
    out.to_csv("/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_RawData/uae_2024_laps_kst.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ Saved ({len(out)} laps)")

if __name__ == "__main__":
    main()