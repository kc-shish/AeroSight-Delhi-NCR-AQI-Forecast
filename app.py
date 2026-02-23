"""
app.py
──────
Project structure:
    app.py          ← you are here (run this)
    config.py       ← paths, station registry, feature list
    api.py          ← WAQI fetch + persistent lag store
    prediction.py   ← feature engineering + model inference
    ui.py           ← all Streamlit rendering / CSS
    artifacts/
        aqi_model.joblib
        scaler.joblib
    lag_history.json  ← auto-created on first fetch

Run:
    streamlit run app.py
"""

import datetime
import streamlit as st

from config     import STATIONS
from api        import fetch_waqi, station_names_match, load_lag_store, push_reading, save_lag_store
from prediction import load_model, build_feature_row, predict_aqi
from ui         import (apply_styles, render_sidebar, render_status_row,
                         render_live_readings, render_forecast_result, render_lag_table)

# ── Page config & CSS ──────────────────────────────────────────────────────
apply_styles()

# ── Load model (cached) ────────────────────────────────────────────────────
@st.cache_resource
def get_model():
    return load_model()

try:
    model, scaler, cols_to_scale = get_model()
    model_ok = True
except Exception as e:
    model_ok  = False
    model_err = str(e)

# ── Sidebar ────────────────────────────────────────────────────────────────
station_name, api_key, fetch_btn = render_sidebar()
lat, lon, station_int, city_name = STATIONS[station_name]

# ── Main header ────────────────────────────────────────────────────────────
st.markdown("# 🌍 AeroSight — Delhi NCR AQI Forecast")
st.markdown("Live geo-lookup → lag buffer → XGBoost → **next 6-hour AQI prediction**")
st.markdown("---")

if not model_ok:
    st.error(
        f"❌ Could not load model: {model_err}\n\n"
        "Ensure `artifacts/aqi_model.joblib` and `artifacts/scaler.joblib` "
        "are in the same folder as `app.py`."
    )
    st.stop()

# ── Load lag store & status ────────────────────────────────────────────────
lag_store       = load_lag_store()
station_key     = station_name
station_history = lag_store.get(station_key, [])

render_status_row(station_name, station_history)

# ── Fetch + Predict ────────────────────────────────────────────────────────
if fetch_btn:
    if not api_key:
        st.error("⚠️ Enter your WAQI API key in the sidebar. Free key at waqi.info/api/")
        st.stop()

    # 1. Fetch live data from WAQI
    with st.spinner(f"Fetching data for {lat:.4f}°N, {lon:.4f}°E …"):
        reading, err = fetch_waqi(lat, lon, api_key)

    if err:
        st.error(f"❌ WAQI API error: {err}")
        st.stop()

    # 2. Show which station WAQI resolved to
    api_station = reading.pop("_api_station", "unknown")
    if station_names_match(station_name, api_station):
        st.success(f"✅ Live data from: **{api_station}**")
    else:
        st.markdown(
            f'<div class="warnbar">⚠️ WAQI resolved to a nearby station: <b>{api_station}</b><br>'
            f'No exact match for <b>{station_name}</b> — using nearest available monitoring point.</div>',
            unsafe_allow_html=True
        )

    # 3. Debug expander — raw API values
    with st.expander("🔍 Raw API values (debug)", expanded=False):
        st.markdown(f"**Geo lookup:** `geo:{lat};{lon}` → resolved to `{api_station}`")
        dcols = st.columns(4)
        for i, k in enumerate(["aqi","pm25","pm10","no2","so2","co","o3","temperature","humidity","wind_speed"]):
            with dcols[i % 4]:
                st.metric(k, reading.get(k, "—"))

    # 4. Save reading to persistent lag buffer
    lag_store       = push_reading(lag_store, station_key, reading)
    station_history = lag_store[station_key]
    st.info(f"💾 Saved to lag buffer · {len(station_history)}/6 readings stored")

    # 5. Show live readings
    render_live_readings(reading)

    # 6. Build feature row & predict
    feature_df   = build_feature_row(reading, station_history, lat, lon, station_int, city_name)
    pred          = predict_aqi(model, scaler, cols_to_scale, feature_df)
    forecast_time = datetime.datetime.now() + datetime.timedelta(hours=6)

    # 7. Render forecast result
    render_forecast_result(pred, reading, station_name, lat, lon, forecast_time)

    # 8. Buffer fill warning
    if len(station_history) < 6:
        st.warning(
            f"⚠️ Buffer has {len(station_history)}/6 readings. "
            f"Fetch {6 - len(station_history)} more time(s) for full lag accuracy. "
            f"Missing lags use nearest available value as fallback."
        )

# ── Lag Buffer Table ───────────────────────────────────────────────────────
render_lag_table(station_name, station_history, lag_store, save_lag_store, station_key)
