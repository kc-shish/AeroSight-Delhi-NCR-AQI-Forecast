"""
prediction.py
─────────────
Handles everything between raw API data and final AQI forecast:
  - Loading the trained XGBoost model + scaler from disk
  - Feature engineering (encodings, lag assembly, datetime features)
  - Running inference and returning the predicted AQI

Functions:
  load_model()         → returns (model, scaler, cols_to_scale)
  build_feature_row()  → assembles the exact input DataFrame the model expects
  predict_aqi()        → scales + predicts, returns clipped float
"""

import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")  # UTC+5:30

def now_ist():
    """Current time in Indian Standard Time (IST = UTC+5:30)."""
    return datetime.datetime.now(IST).replace(tzinfo=None)
import numpy as np
import pandas as pd
from joblib import load

from config import ARTIFACTS_DIR, FEATURE_COLS

# ARTIFACTS_DIR is resolved in config.py via Path(__file__).resolve().parent


# ── Model Loading ──────────────────────────────────────────────────────────
def load_model():
    """
    Load XGBoost model and StandardScaler from artifacts/.
    Returns: (model, scaler, cols_to_scale)
    Raises:  FileNotFoundError if artifacts are missing.
    """
    model       = load(ARTIFACTS_DIR / "aqi_model.joblib")
    scaler_data = load(ARTIFACTS_DIR / "scaler.joblib")
    return model, scaler_data["scaler"], scaler_data["cols_to_scale"]


# ── Encoding Helpers ───────────────────────────────────────────────────────
def city_enc(city: str) -> dict:
    """
    One-hot encode city column.
    Delhi is the drop_first baseline → all zeros.
    Matches pd.get_dummies(drop_first=True) used in training notebook.
    """
    return {
        'city_Faridabad': int(city == 'Faridabad'),
        'city_Ghaziabad': int(city == 'Ghaziabad'),
        'city_Gurugram':  int(city == 'Gurugram'),
        'city_Noida':     int(city == 'Noida'),
    }


def season_enc(month: int) -> dict:
    """
    One-hot encode season column.
    Monsoon is the drop_first baseline → all zeros.
    Matches pd.get_dummies(drop_first=True) used in training notebook.
    """
    if month in (12, 1, 2):  s = 'winter'
    elif month in (3, 4, 5): s = 'summer'
    elif month in (10, 11):  s = 'post_monsoon'
    else:                    s = 'monsoon'
    return {
        'season_post_monsoon': int(s == 'post_monsoon'),
        'season_summer':       int(s == 'summer'),
        'season_winter':       int(s == 'winter'),
    }


def dow_enc(dt: datetime.datetime) -> int:
    """
    Day-of-week encoding matching notebook cell 35:
    Monday=1, Tuesday=2, ... Sunday=7
    (Python's weekday() is 0-based, so we add 1)
    """
    return dt.weekday() + 1


def safe_f(v, default: float = 0.0) -> float:
    """Safely cast to float, returning default on NaN/None/error."""
    try:
        fv = float(v)
        return default if (fv != fv) else fv   # fv != fv → NaN check
    except (TypeError, ValueError):
        return default


# ── Feature Assembly ───────────────────────────────────────────────────────
def build_feature_row(
    reading:         dict,
    station_history: list,
    lat:             float,
    lon:             float,
    station_int:     int,
    city_name:       str,
) -> pd.DataFrame:
    """
    Build a single-row DataFrame in the exact column order the model expects.

    Args:
        reading:         live data dict from fetch_waqi()
        station_history: list of past readings (index 0 = most recent = lag1)
        lat, lon:        station coordinates
        station_int:     encoded station integer (from notebook cell 35)
        city_name:       city string for one-hot encoding

    Returns:
        pd.DataFrame with shape (1, len(FEATURE_COLS))
    """
    # Forecast timestamp = now + 6 hours (model predicts next reading)
    forecast = now_ist() + datetime.timedelta(hours=6)

    def lag_val(field: str, lag_idx: int) -> float:
        """
        Pull a pollutant value from history.
        lag_idx 0 → lag1 (most recent), lag_idx 5 → lag6 (oldest).
        Falls back to the nearest available value if buffer is incomplete.
        """
        if lag_idx < len(station_history):
            return safe_f(station_history[lag_idx].get(field), 0.0)
        # Buffer not full yet — repeat the oldest available value
        for h in station_history:
            v = safe_f(h.get(field), None)
            if v is not None:
                return v
        return 0.0

    row = {
        # ── Datetime features ──────────────────────────────────────────
        'year':        forecast.year,
        'month':       forecast.month,
        'day':         forecast.day,
        'hour':        forecast.hour,
        'day_of_week': dow_enc(forecast),           # Mon=1 … Sun=7
        'is_weekend':  int(forecast.weekday() >= 5),

        # ── Station ────────────────────────────────────────────────────
        'station':    station_int,

        # ── Coordinates ────────────────────────────────────────────────
        'latitude':   lat,
        'longitude':  lon,

        # ── Weather (from live API, sensible defaults if missing) ──────
        'temperature': safe_f(reading["temperature"], 25.0),
        'humidity':    safe_f(reading["humidity"],    60.0),
        'wind_speed':  safe_f(reading["wind_speed"],  5.0),
        'visibility':  4.0,    # WAQI doesn't provide; use mid-range default

        # ── Season one-hot (monsoon = baseline) ────────────────────────
        **season_enc(forecast.month),

        # ── City one-hot (Delhi = baseline) ────────────────────────────
        **city_enc(city_name),
    }

    # ── Lag features (lag1 = most recent, lag6 = oldest) ──────────────
    for pollutant in ["pm25", "pm10", "no2", "so2", "co", "o3", "aqi"]:
        for i in range(1, 7):
            row[f"{pollutant}_lag{i}"] = lag_val(pollutant, i - 1)

    # Return in exact FEATURE_COLS order
    return pd.DataFrame([row])[FEATURE_COLS]


# ── Inference ──────────────────────────────────────────────────────────────
def predict_aqi(
    model,
    scaler,
    cols_to_scale: list,
    feature_df:    pd.DataFrame,
) -> float:
    """
    Scale the feature DataFrame and run model inference.

    Args:
        model:         trained XGBoost model
        scaler:        fitted StandardScaler
        cols_to_scale: list of column names to scale (from scaler artifact)
        feature_df:    output of build_feature_row()

    Returns:
        Predicted AQI clipped to [0, 500]
    """
    scaled_df = feature_df.copy()
    cols_present = [c for c in cols_to_scale if c in scaled_df.columns]
    scaled_df[cols_present] = scaler.transform(scaled_df[cols_present])

    raw = float(model.predict(scaled_df)[0])
    return round(max(0.0, min(500.0, raw)), 1)
