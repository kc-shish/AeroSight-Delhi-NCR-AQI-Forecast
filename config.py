"""
config.py
─────────
Central place for all constants: paths, station registry,
model feature list, and encoding maps.

"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
LAG_FILE      = BASE_DIR / "lag_history.json"   # persists across restarts

# ── Exact feature order the model was trained on ───────────────────────────
FEATURE_COLS = [
    'year', 'month', 'day', 'hour', 'day_of_week', 'is_weekend', 'station',
    'latitude', 'longitude',
    'temperature', 'humidity', 'wind_speed', 'visibility',
    'season_post_monsoon', 'season_summer', 'season_winter',
    'city_Faridabad', 'city_Ghaziabad', 'city_Gurugram', 'city_Noida',
    'pm25_lag1', 'pm25_lag2', 'pm25_lag3', 'pm25_lag4', 'pm25_lag5', 'pm25_lag6',
    'pm10_lag1', 'pm10_lag2', 'pm10_lag3', 'pm10_lag4', 'pm10_lag5', 'pm10_lag6',
    'no2_lag1',  'no2_lag2',  'no2_lag3',  'no2_lag4',  'no2_lag5',  'no2_lag6',
    'so2_lag1',  'so2_lag2',  'so2_lag3',  'so2_lag4',  'so2_lag5',  'so2_lag6',
    'co_lag1',   'co_lag2',   'co_lag3',   'co_lag4',   'co_lag5',   'co_lag6',
    'o3_lag1',   'o3_lag2',   'o3_lag3',   'o3_lag4',   'o3_lag5',   'o3_lag6',
    'aqi_lag1',  'aqi_lag2',  'aqi_lag3',  'aqi_lag4',  'aqi_lag5',  'aqi_lag6',
]

# ── Station registry ────────────────────────────────────────────────────────
# Format: 'Display Name': (latitude, longitude, station_int, city_name)
#
# station_int → exact encoding used in training notebook (cell 35)
# city_name   → used to build city_* one-hot encoded columns

STATIONS= {

    # ---------------- DELHI ----------------
    'Anand Vihar, Delhi':   (28.6469, 77.3152,  1, 'Delhi'),
    'Bawana, Delhi':        (28.7710, 77.0350,  2, 'Delhi'),
    'Dwarka Sec 8, Delhi':  (28.5921, 77.0460,  3, 'Delhi'),
    'ITO, Delhi':           (28.6289, 77.2409, 11, 'Delhi'),
    'Jahangirpuri, Delhi':  (28.7274, 77.1628, 12, 'Delhi'),
    'Mandir Marg, Delhi':   (28.6380, 77.1990, 13, 'Delhi'),
    'NSIT Dwarka, Delhi':   (28.6080, 77.0290, 14, 'Delhi'),
    'Okhla Phase 2, Delhi': (28.5330, 77.2710, 17, 'Delhi'),
    'Punjabi Bagh, Delhi':  (28.6663, 77.1317, 18, 'Delhi'),
    'RK Puram, Delhi':      (28.5640, 77.1858, 19, 'Delhi'),
    'Rohini, Delhi':        (28.7350, 77.1170, 20, 'Delhi'),
    'Shadipur, Delhi':      (28.6520, 77.1480, 21, 'Delhi'),
    'Siri Fort, Delhi':     (28.5490, 77.2190, 22, 'Delhi'),
    'Wazirpur, Delhi':      (28.6910, 77.1640, 23, 'Delhi'),

    # ---------------- FARIDABAD ----------------
    'Faridabad New Town':   (28.3940, 77.3200,  4, 'Faridabad'),
    'Faridabad Sec 16A':    (28.4082, 77.3098,  5, 'Faridabad'),

    # ---------------- GHAZIABAD ----------------
    'Ghaziabad Loni':       (28.7480, 77.2890,  6, 'Ghaziabad'),
    'Ghaziabad Vasundhara': (28.6600, 77.3540,  7, 'Ghaziabad'),

    # ---------------- NOIDA ----------------
    'Greater Noida':        (28.4744, 77.5040,  8, 'Noida'),
    'Noida Sec 125':        (28.5443, 77.3200, 15, 'Noida'),
    'Noida Sec 62':         (28.6270, 77.3800, 16, 'Noida'),

    # ---------------- GURUGRAM ----------------
    'Gurugram Sec 51':      (28.4456, 77.0510,  9, 'Gurugram'),
    'Gurugram Vikas Sadan': (28.4700, 77.0270, 10, 'Gurugram'),

}
