"""
ui.py
─────
All Streamlit UI logic: page config, CSS injection, sidebar,
status cards, live readings display, forecast result card,
lag buffer table, and reusable render helpers.

Functions:
  apply_styles()           → inject CSS into Streamlit page
  render_sidebar()         → draws sidebar, returns (station_name, api_key, fetch_btn)
  render_status_row()      → station / buffer / last-fetch cards
  render_live_readings()   → weather + pollutant metric cards
  render_forecast_result() → big AQI result box + current vs forecast comparison
  render_lag_table()       → lag buffer dataframe + clear button
  aqi_meta()               → returns (category_label, fg_color, bg_color)
  fmt()                    → safe format for display
"""

import streamlit as st
import pandas as pd

from config import STATIONS


# ── AQI Category Metadata ──────────────────────────────────────────────────
def aqi_meta(aqi: float):
    """
    Returns category for a given AQI.
    Follows Indian AQI scale (CPCB).
    """
    a = int(aqi)
    if a <= 50:  return "Good",         "#00e676", "#001a0d"
    if a <= 100: return "Satisfactory", "#ffea00", "#1a1700"
    if a <= 200: return "Moderate",     "#ff9100", "#1a0e00"
    if a <= 300: return "Poor",         "#ff1744", "#1a0005"
    if a <= 400: return "Very Poor",    "#d500f9", "#18001f"
    return              "Severe",       "#b0bec5", "#12151c"


def fmt(v, d: int = 1):
    """Safely format a value for display. Returns '—' for NaN/None."""
    try:
        fv = float(v)
        return "—" if (fv != fv) else (int(fv) if d == 0 else round(fv, d))
    except (TypeError, ValueError):
        return "—"


# ── Page Config & CSS ──────────────────────────────────────────────────────
def apply_styles():
    """Configure Streamlit page and inject custom dark-theme CSS."""
    st.set_page_config(
        page_title="🌪️️AeroSight",
        page_icon="📈",
        layout="wide"
    )
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

    html,body,[class*="css"]  { font-family:'Syne',sans-serif; }
    .stApp                    { background:#080c18; color:#dde2f0; }
    .block-container          { padding:2rem 2.5rem 4rem; }
    h1,h2,h3,h4              { font-family:'Syne',sans-serif; font-weight:800; color:#dde2f0; }

    section[data-testid="stSidebar"]       { background:#0c1022; border-right:1px solid #1a2040; }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span { color:#8898c0 !important; }

    div[data-testid="stSelectbox"] > div > div,
    div[data-testid="stTextInput"] > div > div > input {
        background:#111828 !important; border:1px solid #1e2c50 !important;
        color:#dde2f0 !important; border-radius:8px !important;
    }
    .stButton > button {
        background:linear-gradient(135deg,#2563eb,#7c3aed);
        color:#fff; border:none; border-radius:10px;
        font-family:'Space Mono',monospace; font-size:13px; font-weight:700;
        letter-spacing:1.5px; padding:14px; width:100%; transition:opacity .2s;
    }
    .stButton > button:hover { opacity:.82; }

    .card {
        background:#111828; border:1px solid #1a2545;
        border-radius:14px; padding:20px 22px; margin-bottom:12px;
    }
    .clabel {
        font-family:'Space Mono',monospace; font-size:10px;
        letter-spacing:2.5px; color:#445070; text-transform:uppercase; margin-bottom:6px;
    }
    .cval { font-family:'Space Mono',monospace; font-size:26px; font-weight:700; color:#dde2f0; }

    .aqi-box { border-radius:20px; padding:44px 40px; text-align:center; margin:18px 0; }
    .aqi-num { font-family:'Space Mono',monospace; font-size:100px; font-weight:700; line-height:1; }
    .aqi-cat { font-family:'Syne',sans-serif; font-size:22px; font-weight:700; letter-spacing:3px; margin-top:8px; }
    .aqi-sub { font-family:'Space Mono',monospace; font-size:11px; letter-spacing:2px; opacity:.55; margin-top:10px; }

    .infobar {
        background:#111828; border-left:3px solid #2563eb;
        border-radius:0 10px 10px 0; padding:10px 16px;
        font-family:'Space Mono',monospace; font-size:11px;
        color:#6070a0; margin-bottom:14px; line-height:1.7;
    }
    .warnbar {
        background:#1a1200; border-left:3px solid #ff9100;
        border-radius:0 10px 10px 0; padding:10px 16px;
        font-family:'Space Mono',monospace; font-size:11px;
        color:#cc7700; margin-bottom:14px; line-height:1.7;
    }
    hr { border-color:#1a2040; margin:20px 0; }
    </style>
    """, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
def render_sidebar():
    """
    Draw the sidebar: station selector, coordinates info, API key input, fetch button.
    Returns: (station_name, api_key, fetch_clicked)
    """
    with st.sidebar:
        st.markdown("### 🌥️ AeroSight")
        st.markdown(
            '<div class="infobar">Select station → Fetch live data<br>→ 6-hour ahead prediction</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        station_name = st.selectbox("Station", list(STATIONS.keys()))
        lat, lon, station_int, city_name = STATIONS[station_name]

        st.markdown(
            f'<div class="infobar">'
            f'📍 {lat:.4f}°N, {lon:.4f}°E<br>'
            f'🏙️ City: <b>{city_name}</b><br>'
            f'🔢 Station code: <b>{station_int}</b><br>'
            f'🌐 Lookup: <code>geo:{lat};{lon}</code>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        api_key = st.text_input(
            "WAQI API Key", type="password",
            placeholder="Get free key → waqi.info/api/"
        ).strip()

        st.markdown("---")
        fetch_btn = st.button("⚡ FETCH & FORECAST", use_container_width=True)
        st.markdown(
            '<p style="font-family:\'Space Mono\',monospace;font-size:10px;'
            'color:#2a3560;margin-top:10px;">'
            'Model: XGBoost (tuned)<br>Target: aqi_future<br>Test R² 0.9720 · MAE 21.49</p>',
            unsafe_allow_html=True
        )

    return station_name, api_key, fetch_btn


# ── Status Row ─────────────────────────────────────────────────────────────
def render_status_row(station_name: str, station_history: list):
    """Three info cards: selected station, buffer fill, last fetch time."""
    s1, s2, s3 = st.columns(3)
    buf_color = "#00e676" if len(station_history) == 6 \
           else ("#ff9100" if station_history else "#ff1744")

    with s1:
        st.markdown(
            f'<div class="card"><div class="clabel">Station</div>'
            f'<div class="cval" style="font-size:13px;line-height:1.5;">{station_name}</div></div>',
            unsafe_allow_html=True
        )
    with s2:
        st.markdown(
            f'<div class="card"><div class="clabel">Lag Buffer</div>'
            f'<div class="cval" style="color:{buf_color};">{len(station_history)}'
            f'<span style="font-size:14px;color:#445070;"> / 6</span></div></div>',
            unsafe_allow_html=True
        )
    with s3:
        last_ts = (station_history[0]["timestamp"][:16].replace("T", " ")
                   if station_history else "No data yet")
        st.markdown(
            f'<div class="card"><div class="clabel">Last Fetch</div>'
            f'<div class="cval" style="font-size:14px;">{last_ts}</div></div>',
            unsafe_allow_html=True
        )


# ── Live Readings ──────────────────────────────────────────────────────────
def render_live_readings(reading: dict):
    """Weather row (4 cols) + pollutants row (5 cols)."""
    st.markdown("### 📡 Current Live Readings")

    r1, r2, r3, r4 = st.columns(4)
    for col, lbl, val in zip(
        [r1, r2, r3, r4],
        ["Current AQI", "Temperature (°C)", "Humidity (%)", "Wind Speed (m/s)"],
        [fmt(reading["aqi"], 0), fmt(reading["temperature"]),
         fmt(reading["humidity"]), fmt(reading["wind_speed"])],
    ):
        with col:
            st.markdown(
                f'<div class="card"><div class="clabel">{lbl}</div>'
                f'<div class="cval">{val}</div></div>',
                unsafe_allow_html=True
            )

    p1, p2, p3, p4, p5 = st.columns(5)
    for col, lbl, val in zip(
        [p1, p2, p3, p4, p5],
        ["PM2.5 µg/m³", "PM10 µg/m³", "NO₂ µg/m³", "SO₂ µg/m³", "CO mg/m³"],
        [fmt(reading["pm25"]), fmt(reading["pm10"]),
         fmt(reading["no2"]),  fmt(reading["so2"]), fmt(reading["co"], 2)],
    ):
        with col:
            st.markdown(
                f'<div class="card"><div class="clabel">{lbl}</div>'
                f'<div class="cval" style="font-size:20px;">{val}</div></div>',
                unsafe_allow_html=True
            )


# ── Forecast Result ────────────────────────────────────────────────────────
def render_forecast_result(
    pred_aqi:     float,
    reading:      dict,
    station_name: str,
    lat:          float,
    lon:          float,
    forecast_dt,
):
    """
    Big AQI result card + current vs forecast comparison side-by-side.
    """
    import datetime
    cat, fg, bg = aqi_meta(pred_aqi)

    st.markdown("---")
    st.markdown("### 🔮 Forecasted AQI")

    st.markdown(f"""
    <div class="aqi-box" style="background:{bg}; border:2px solid {fg}44;">
        <div class="aqi-sub">FORECAST · {forecast_dt.strftime('%d %b %Y · %H:%M')}</div>
        <div class="aqi-num" style="color:{fg};">{int(pred_aqi)}</div>
        <div class="aqi-cat" style="color:{fg};">{cat}</div>
        <div class="aqi-sub" style="margin-top:18px;">
            {station_name} &nbsp;·&nbsp; {lat:.4f}°N {lon:.4f}°E
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Current vs Forecast side-by-side
    curr_raw   = reading["aqi"]
    curr_valid = not (curr_raw is None or curr_raw != curr_raw)
    curr_int   = int(float(curr_raw)) if curr_valid else None
    curr_cat, curr_fg, curr_bg = aqi_meta(curr_int) if curr_valid else ("—", "#aaa", "#111828")

    ca, cb = st.columns(2)
    with ca:
        st.markdown(
            f'<div class="card" style="text-align:center;background:{curr_bg};border-color:{curr_fg}33;">'
            f'<div class="clabel">Current AQI — Now</div>'
            f'<div class="cval" style="font-size:52px;color:{curr_fg};">{curr_int if curr_valid else "—"}</div>'
            f'<div style="font-family:\'Space Mono\',monospace;font-size:12px;color:{curr_fg};'
            f'opacity:.7;margin-top:6px;">{curr_cat}</div></div>',
            unsafe_allow_html=True
        )
    with cb:
        if curr_valid:
            delta   = pred_aqi - float(curr_raw)
            arrow   = "▲" if delta > 5 else ("▼" if delta < -5 else "●")
            dcol    = "#ff1744" if delta > 5 else ("#00e676" if delta < -5 else "#8898c0")
            delta_s = f"{arrow} {abs(round(delta, 1))} pts"
        else:
            delta_s, dcol = "—", "#8898c0"

        st.markdown(
            f'<div class="card" style="text-align:center;background:{bg};border-color:{fg}33;">'
            f'<div class="clabel">Forecast AQI — +6 Hours</div>'
            f'<div class="cval" style="font-size:52px;color:{fg};">{int(pred_aqi)}</div>'
            f'<div style="font-family:\'Space Mono\',monospace;font-size:12px;color:{dcol};'
            f'margin-top:6px;">{delta_s} · {cat}</div></div>',
            unsafe_allow_html=True
        )


# ── Lag Buffer Table ───────────────────────────────────────────────────────
def render_lag_table(station_name: str, station_history: list,
                     lag_store: dict, save_fn, clear_key: str):
    """
    Show stored lag readings in a table with a clear button.
    """
    st.markdown("---")
    st.markdown("### 🗂️ Lag Buffer")
    st.markdown(
        f'<div class="infobar">Saved in <code>lag_history.json</code> — persists across restarts.<br>'
        f'Station: <b>{station_name}</b> · {len(station_history)}/6 readings stored.</div>',
        unsafe_allow_html=True
    )

    if station_history:
        lag_df = pd.DataFrame(station_history)
        lag_df.insert(0, "Lag", [
            "lag1 ← latest" if i == 0 else f"lag{i+1}"
            for i in range(len(lag_df))
        ])
        lag_df["timestamp"] = lag_df["timestamp"].astype(str).str[:16].str.replace("T", " ")
        disp = ["Lag", "timestamp", "aqi", "pm25", "pm10", "no2",
                "so2", "co", "o3", "temperature", "humidity", "wind_speed"]
        disp = [c for c in disp if c in lag_df.columns]

        st.dataframe(
            lag_df[disp].rename(columns={
                "timestamp": "Time",  "aqi": "AQI",   "pm25": "PM2.5",
                "pm10": "PM10",       "no2": "NO₂",   "so2": "SO₂",
                "co": "CO",           "o3": "O₃",
                "temperature": "Temp °C", "humidity": "Hum %", "wind_speed": "Wind m/s"
            }),
            use_container_width=True, hide_index=True
        )

        if st.button("🗑️ Clear buffer for this station"):
            lag_store.pop(clear_key, None)
            save_fn(lag_store)
            st.rerun()
    else:
        st.markdown(
            '<div class="infobar">No readings yet. Press ⚡ FETCH &amp; FORECAST to begin.</div>',
            unsafe_allow_html=True
        )
