import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor
import joblib
from .models import Booking

def train_dynamic_pricing_model():
    """Train a dynamic pricing model based on historical booking data."""
    
    # Load Booking Data from Django Model
    bookings = Booking.objects.all().values()
    df = pd.DataFrame(list(bookings))

    # Feature Engineering
    df["day_of_week"] = pd.to_datetime(df["check_in_date"]).dt.dayofweek
    df["season"] = df["check_in_date"].apply(lambda x: get_season(x))  # Helper function

    # Select Features
    X = df[["occupancy_rate", "competitor_price", "demand_index", "day_of_week", "season"]]
    y = df["competitor_price"] * 1.1  # Set target as adjusted competitor price

    # Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Model (LightGBM)
    model = LGBMRegressor(n_estimators=500, learning_rate=0.05, max_depth=5)
    model.fit(X_train, y_train)

    # Save Model
    joblib.dump(model, "dynamic_pricing_model.pkl")
    return "Model training complete!"

def get_season(date):
    """Helper function to categorize seasons."""
    month = pd.to_datetime(date).month
    if month in [12, 1, 2]: return 0  # Winter
    elif month in [3, 4, 5]: return 1  # Spring
    elif month in [6, 7, 8]: return 2  # Summer
    else: return 3  # Autumn
