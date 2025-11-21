# -*- coding: utf-8 -*-
import os
import fastf1
import pandas as pd


# ---------------------------
# CONFIGURATION
# ---------------------------
YEAR = 2024
EVENT = "Abu Dhabi"          # e.g. "Abu Dhabi", "Monza", "Bahrain"
SESSION = "R"                 # R = Race, Q = Qualifying, FP1/FP2/FP3
DRIVER = "55"                 # Driver number as STRING ("55", "1", "44", etc.)

# Output CSV path
OUTPUT_CSV = (
    "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/"
    "SocialData_SportsCommunity/F1_RawData/uae_2024_laps.csv"
)

# Cache folder (must exist or we create it)
CACHE_DIR = (
    "/Users/chohyunseo/Desktop/SocialData_SportsAnalysis/"
    "SocialData_SportsCommunity/fastf1_cache"
)


# ---------------------------
# MAIN SCRIPT
# ---------------------------
def main():

    # Ensure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Enable FastF1 cache
    fastf1.Cache.enable_cache(CACHE_DIR)

    print(f"[INFO] Loading {YEAR} {EVENT} ({SESSION}) via FastF1...")

    # Load session
    session = fastf1.get_session(YEAR, EVENT, SESSION)
    session.load()

    print("[INFO] Session loaded successfully!")

    # Filter laps for chosen driver
    laps = session.laps.pick_driver(DRIVER)

    if laps.empty:
        print(f"[ERROR] No laps found for driver {DRIVER}")
        return

    print(f"[INFO] Found {len(laps)} laps for driver #{DRIVER}")

    # Build DataFrame
    df = pd.DataFrame({
        "lap_number": laps["LapNumber"],
        "lap_time_seconds": laps["LapTime"].dt.total_seconds(),
        "sector1_seconds": laps["Sector1Time"].dt.total_seconds(),
        "sector2_seconds": laps["Sector2Time"].dt.total_seconds(),
        "sector3_seconds": laps["Sector3Time"].dt.total_seconds(),
        "compound": laps["Compound"],
        "fresh_tyre": laps["FreshTyre"],
        "is_pit_out_lap": laps["PitOutLap"],
        "is_pit_in_lap": laps["PitInLap"],
        "is_valid_lap": laps["IsValid"],
    })

    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n✅ CSV saved successfully!")
    print(f"➡ Path: {OUTPUT_CSV}\n")

    # Print first rows
    print(df.head(10))


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    main()