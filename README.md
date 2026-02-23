## AeroSight-Delhi-NCR-AQI-Forecast


Here’s a clean, professional **README context section** you can directly paste into your repository. It clearly explains the **purpose of each file** and the **working of the app**.

---

## 🌍 AeroSight - NCR AQI Forecast

Delhi’s air quality can change rapidly — and real decisions depend on what it will be, not just what it is now.

**AeroSight** is a Machine Learning–powered AQI forecasting system that predicts **Air Quality Index (AQI) 6 hours ahead (t+6)** using live data from **23 official monitoring stations across 5 NCR cities**.

Unlike typical AQI apps that show current readings, this system forecasts near-future air quality to support smarter daily planning.

---

# 🚀 How the App Works

The system operates in two stages:

## 1️⃣ Model Training Phase (Offline)

* Historical hourly data (2020–2025)
* Trained on 20,000+ records
* 23 monitoring stations
* Pollutants: PM2.5, PM10, NO₂, SO₂, CO, O₃
* Weather + temporal features
* 6 lag values per pollutant

### Process:

1. Data cleaning & preprocessing
2. Feature engineering (lag generation + time features)
3. Train-test split using **TimeSeriesSplit**
4. Multiple model benchmarking
5. Final model selection → Tuned **XGBoost Regressor**
6. Model + scaler saved using `joblib`

**Test Performance**

* R² = 0.972
* MAE = 21.49

---

## 2️⃣ Live Forecast Phase (Production)

When a user selects a station:

1. Live AQI data is fetched via **WAQI API**
2. Latest pollutant values are added to a persistent JSON lag buffer
3. Feature vector is generated with:

   * Current readings
   * 6 previous lag values
   * Temporal features
4. Data is scaled
5. XGBoost model predicts AQI at t+6
6. Forecast + delta indicator displayed in Streamlit UI

The lag buffer survives restarts — no database required.

---

# 📂 Project Structure & File Purpose

```
AeroSight-Delhi-NCR-AQI-Forecast/
│
├── Source_Code/
├── artifacts/
├── api.py
├── app.py
├── config.py
├── prediction.py
├── ui.py
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 📁 `Source_Code/`

Contains model training notebooks/scripts:

* Data preprocessing
* Feature engineering
* Model experimentation
* Hyperparameter tuning
* Final model export

Used for development and retraining.

---

## 📁 `artifacts/`

Stores production assets:

* Trained XGBoost model (`.pkl`)
* Scaler object
* Feature metadata
* Persistent lag buffer (JSON)

This ensures inference uses the exact same feature structure as training.

---

## 📄 `api.py`

Handles:

* WAQI API requests
* Station-level data retrieval
* Error handling for API failures
* Parsing pollutant values

Acts as the external data interface layer.

---

## 📄 `config.py`

Central configuration file:

* API endpoint templates
* Feature lists
* Model paths
* Lag settings
* Constants used across modules

Keeps the system modular and maintainable.

---

## 📄 `prediction.py`

Core inference engine:

* Loads model & scaler
* Maintains lag buffer
* Generates feature vector
* Applies scaling
* Produces 6-hour AQI forecast

Ensures strict feature parity between training and production.

---

## 📄 `ui.py`

Contains Streamlit UI components:

* Station selection dropdown
* Live AQI display
* Forecast visualization
* Delta indicator logic
* User messages & layout

Handles frontend presentation logic.

---

## 📄 `app.py`

Main application entry point.

* Integrates API layer
* Calls prediction engine
* Connects UI components
* Runs Streamlit app

This is the file executed when launching the app.

---

## 📄 `requirements.txt`

Lists all Python dependencies required to run the project:

* streamlit
* xgboost
* scikit-learn
* pandas
* numpy
* requests
* joblib
* etc.

---

## 🧠 System Design Highlights

✔ Strict feature consistency between training & inference
✔ Time-series aware cross-validation
✔ Persistent lag architecture without database
✔ Modular production-ready structure
✔ Real-time API-based forecasting

---

# ⚙️ Running the App Locally

```bash
# Clone the repository
git clone https://github.com/kc-shish/AeroSight-Delhi-NCR-AQI-Forecast.git

# Navigate to project directory
cd AeroSight-Delhi-NCR-AQI-Forecast

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

To use live data:

* Generate a free API key from World Air Quality Index (WAQI)
* Add it to your configuration

---

# 💡 Key Engineering Insight

The most critical production challenge was not model tuning.

It was ensuring:

> Training features = Inference features (exact order, encoding, scaling)

Even a single mismatch can invalidate predictions.

This project emphasizes:

* Production-grade ML engineering
* Time-series forecasting
* Feature pipeline discipline
* Real-world deployment beyond notebooks

---

If you're exploring time-series ML, environmental forecasting, or production ML systems — contributions and discussions are welcome.
