import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
import joblib
import os
from .models import Booking

FEATURES = ["occupancy_rate", "competitor_price", "demand_index", "day_of_week", "season"]
MODEL_PATH = "dynamic_pricing_model.pkl"
MODEL_META_PATH = "dynamic_pricing_model_meta.txt"


def get_season(date):
    """Map a date to a numeric season index (0=Winter … 3=Autumn)."""
    month = pd.to_datetime(date).month
    if month in [12, 1, 2]:
        return 0  # Winter
    elif month in [3, 4, 5]:
        return 1  # Spring
    elif month in [6, 7, 8]:
        return 2  # Summer
    return 3  # Autumn


def train_dynamic_pricing_model():
    """
    Train LightGBM and XGBoost on historical booking data, compare RMSE on a
    held-out test set, and persist the better model together with a metadata
    file that records which algorithm won.

    Returns a summary dict with RMSE figures and the winning model name.
    """
    bookings = Booking.objects.all().values()
    df = pd.DataFrame(list(bookings))

    if df.empty:
        return {"error": "No booking data available for training."}

    # Feature engineering
    df["day_of_week"] = pd.to_datetime(df["check_in_date"]).dt.dayofweek
    df["season"] = df["check_in_date"].apply(get_season)

    # Drop rows missing any required feature
    required = FEATURES + ["competitor_price"]
    df = df.dropna(subset=required)
    if df.empty:
        return {"error": "Insufficient data after dropping rows with missing features."}

    X = df[FEATURES]
    # Target: a 10 % premium on the competitor price
    y = df["competitor_price"] * 1.1

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # --- LightGBM ---
    lgb_model = LGBMRegressor(n_estimators=500, learning_rate=0.05, max_depth=5, random_state=42, verbose=-1)
    lgb_model.fit(X_train, y_train)
    lgb_rmse = float(np.sqrt(mean_squared_error(y_test, lgb_model.predict(X_test))))

    # --- XGBoost ---
    xgb_model = XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=5, random_state=42, verbosity=0)
    xgb_model.fit(X_train, y_train)
    xgb_rmse = float(np.sqrt(mean_squared_error(y_test, xgb_model.predict(X_test))))

    # Choose the model with lower RMSE
    if xgb_rmse < lgb_rmse:
        winner_name = "XGBoost"
        winner_model = xgb_model
    else:
        winner_name = "LightGBM"
        winner_model = lgb_model

    joblib.dump(winner_model, MODEL_PATH)

    with open(MODEL_META_PATH, "w") as f:
        f.write(f"algorithm={winner_name}\n")
        f.write(f"lgb_rmse={lgb_rmse:.4f}\n")
        f.write(f"xgb_rmse={xgb_rmse:.4f}\n")
        f.write(f"training_rows={len(X_train)}\n")
        f.write(f"test_rows={len(X_test)}\n")

    return {
        "winner": winner_name,
        "lgb_rmse": round(lgb_rmse, 4),
        "xgb_rmse": round(xgb_rmse, 4),
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "message": f"Model saved ({winner_name}, RMSE={min(lgb_rmse, xgb_rmse):.4f})",
    }


def load_pricing_model():
    """
    Load the saved pricing model from disk.
    Returns (model, algorithm_name) or (None, None) if no model is saved yet.
    """
    if not os.path.exists(MODEL_PATH):
        return None, None

    model = joblib.load(MODEL_PATH)
    algorithm = "unknown"
    if os.path.exists(MODEL_META_PATH):
        with open(MODEL_META_PATH) as f:
            for line in f:
                if line.startswith("algorithm="):
                    algorithm = line.strip().split("=", 1)[1]
                    break
    return model, algorithm


def predict_price(features_dict):
    """
    Predict a room price given a features dict with keys matching FEATURES.
    Returns the predicted price (float) or None if no model is available.
    """
    model, _ = load_pricing_model()
    if model is None:
        return None

    try:
        row = pd.DataFrame([{f: features_dict.get(f, 0) for f in FEATURES}])
        return float(model.predict(row)[0])
    except Exception:
        return None
