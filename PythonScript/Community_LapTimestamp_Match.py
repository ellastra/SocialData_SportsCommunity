# -*- coding: utf-8 -*-
"""
Match each post (Round1_Bahrain.csv) to Verstappen's nearest lap midpoint
from bahrain_2024_laps_kst.csv.
"""

import pandas as pd
from pathlib import Path

BASE = Path("/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/SocialData_SportsCommunity/F1_RawData")

LAP_FILE = BASE / "uae_2024_laps_kst.csv"
POST_FILE = BASE / "Round24_AbuDhabi.csv"
OUT_FILE = BASE / "Round24_UnitedArabEmirates_with_lap.csv"

def ensure_kst(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    # Localize or convert everything to KST tz-aware
    if getattr(dt.dt, "tz", None) is None:
        return dt.dt.tz_localize("Asia/Seoul")
    else:
        return dt.dt.tz_convert("Asia/Seoul")

def main():
    # --- Load lap times ---
    laps = pd.read_csv(LAP_FILE, encoding="utf-8-sig")
    laps["lap_start_kst"] = ensure_kst(laps["lap_start_kst"])
    laps["lap_end_kst"]   = ensure_kst(laps["lap_end_kst"])
    laps["lap_mid_kst"]   = laps["lap_start_kst"] + (laps["lap_end_kst"] - laps["lap_start_kst"]) / 2
    ver_mid = laps[["lap_number", "lap_mid_kst"]].copy().rename(columns={"lap_number": "lap"})

    # --- Load posts ---
    posts = pd.read_csv(POST_FILE, encoding="utf-8-sig")
    posts["post_timestamp"] = ensure_kst(posts["post_timestamp"])

    # --- Find nearest lap midpoint ---
    posts["_key"] = 1
    ver_mid["_key"] = 1
    combo = posts.merge(ver_mid, on="_key", how="left")
    combo["abs_diff"] = (combo["post_timestamp"] - combo["lap_mid_kst"]).abs()

    nearest = (
        combo.sort_values(["post_timestamp", "abs_diff"])
             .groupby("post_timestamp", as_index=False)
             .first()[["post_timestamp", "lap", "lap_mid_kst", "abs_diff"]]
    )

    # --- Merge back to posts ---
    result = posts.merge(nearest, on="post_timestamp", how="left")
    result["lap_mid_kst"] = result["lap_mid_kst"].dt.strftime("%Y-%m-%d %H:%M:%S")
    result["post_timestamp"] = result["post_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # --- Save ---
    result.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[DONE] Matched {len(result)} posts to nearest Verstappen lap midpoint → {OUT_FILE}")
    print("Columns added: lap, lap_mid_kst, abs_diff (timedelta)")

if __name__ == "__main__":
    main()