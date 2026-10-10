#!/usr/bin/env python3
"""
NEPHELE Task 3 - Pricing Algorithms
Multiple algorithms for dynamic pricing:
  1. Linear Regression (baseline)
  2. Gradient Boosting (XGBoost/LightGBM)
  3. Neural Network (TensorFlow/Keras)
  4. Seasonal Time-Series Pricing
  5. Ensemble Method
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False


class PricingAlgorithm:
    """Base class for pricing algorithms"""
    
    def __init__(self, name):
        self.name = name
        self.model = None
        self.scaler = StandardScaler()
        self.encoders = {}
        self.feature_names = []
        self.is_trained = False
    
    def train(self, X_train, y_train):
        """Train the model"""
        raise NotImplementedError
    
    def predict(self, X):
        """Make predictions"""
        raise NotImplementedError
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        predictions = self.predict(X_test)
        
        mae = mean_absolute_error(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, predictions)
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        
        return {
            'MAE': mae,
            'MSE': mse,
            'RMSE': rmse,
            'R²': r2,
            'MAPE': mape
        }
    
    def save(self, path):
        """Save model to disk"""
        joblib.dump(self.model, path)
        print(f"  ✓ Model saved: {path}")
    
    def load(self, path):
        """Load model from disk"""
        self.model = joblib.load(path)
        self.is_trained = True
        print(f"  ✓ Model loaded: {path}")


class LinearRegressionPricer(PricingAlgorithm):
    """Linear Regression baseline model"""
    
    def __init__(self):
        super().__init__("Linear Regression")
        self.model = LinearRegression()
    
    def train(self, X_train, y_train):
        """Train linear regression model"""
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_train)
        self.is_trained = True
        print(f"  ✓ {self.name} trained")
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)


class GradientBoostingPricer(PricingAlgorithm):
    """Gradient Boosting (LightGBM backend or SkLearn)"""
    
    def __init__(self, use_xgboost=HAS_XGBOOST):
        super().__init__("Gradient Boosting")
        
        if use_xgboost and HAS_XGBOOST:
            self.model = xgb.XGBRegressor(
                max_depth=5,
                learning_rate=0.1,
                n_estimators=100,
                random_state=42
            )
            self.use_xgboost = True
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.use_xgboost = False
    
    def train(self, X_train, y_train):
        """Train gradient boosting model"""
        if not self.use_xgboost:
            X_train = self.scaler.fit_transform(X_train)
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        print(f"  ✓ {self.name} trained")
    
    def predict(self, X):
        """Make predictions"""
        if not self.use_xgboost:
            X = self.scaler.transform(X)
        return self.model.predict(X)


class NeuralNetworkPricer(PricingAlgorithm):
    """Deep Neural Network pricing model"""
    
    def __init__(self):
        super().__init__("Neural Network")
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required for Neural Network pricing")
        self.model = None
    
    def _build_model(self, input_dim):
        """Build neural network architecture"""
        model = keras.Sequential([
            layers.Dense(128, activation='relu', input_dim=input_dim),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.1),
            layers.Dense(1)  # Output layer
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train(self, X_train, y_train, epochs=30, batch_size=32):
        """Train neural network"""
        X_train = self.scaler.fit_transform(X_train)
        
        self.model = self._build_model(X_train.shape[1])
        
        # Train with validation split
        self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=0
        )
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained")
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled, verbose=0).flatten()


class SeasonalPricer(PricingAlgorithm):
    """Seasonal time-series based pricing"""
    
    def __init__(self):
        super().__init__("Seasonal Pricing")
        self.season_multipliers = {}
        self.base_price = 0
        self.room_type_multipliers = {}
    
    def train(self, X_train, y_train):
        """Learn seasonal and room-type multipliers"""
        
        # Create a temporary dataframe for analysis
        temp_df = pd.DataFrame(X_train)
        temp_df['price'] = y_train
        
        # Calculate base price (annual average)
        self.base_price = temp_df['price'].mean()
        
        # Calculate seasonal multipliers if 'season' column exists
        if 'season' in temp_df.columns:
            season_avg = temp_df.groupby('season')['price'].mean()
            self.season_multipliers = (season_avg / self.base_price).to_dict()
        else:
            self.season_multipliers = {'winter': 0.85, 'spring': 1.0, 'summer': 1.4, 'fall': 1.0}
        
        # Calculate room type multipliers if 'room_type' column exists
        if 'room_type' in temp_df.columns:
            room_avg = temp_df.groupby('room_type')['price'].mean()
            self.room_type_multipliers = (room_avg / self.base_price).to_dict()
        else:
            self.room_type_multipliers = {}
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained")
    
    def predict(self, X):
        """Predict prices using seasonal adjustments"""
        predictions = []
        
        for i in range(len(X)):
            price = self.base_price
            
            # Apply seasonal multiplier
            if 'season' in X.columns:
                season = X.iloc[i]['season']
                if season in self.season_multipliers:
                    price *= self.season_multipliers[season]
            
            # Apply room type multiplier
            if 'room_type' in X.columns:
                room_type = X.iloc[i]['room_type']
                if room_type in self.room_type_multipliers:
                    price *= self.room_type_multipliers[room_type]
            
            # Adjust for accommodates
            if 'accommodates' in X.columns:
                accommodates = X.iloc[i]['accommodates']
                price *= (1 + (accommodates - 2) * 0.15)
            
            # Adjust for rating
            if 'review_scores_rating' in X.columns:
                rating = X.iloc[i]['review_scores_rating']
                if rating >= 4.8:
                    price *= 1.15
                elif rating < 4.0:
                    price *= 0.85
            
            predictions.append(max(20, price))  # Minimum price floor
        
        return np.array(predictions)


class EnsemblePricer(PricingAlgorithm):
    """Ensemble of multiple pricing algorithms"""
    
    def __init__(self):
        super().__init__("Ensemble Pricer")
        self.models = {}
        
        # Create ensemble components
        self.models['linear'] = LinearRegressionPricer()
        self.models['gbm'] = GradientBoostingPricer(use_xgboost=False)
        self.models['seasonal'] = SeasonalPricer()
        
        # Try to add neural network if available
        if HAS_TENSORFLOW:
            try:
                self.models['nn'] = NeuralNetworkPricer()
            except:
                pass
    
    def train(self, X_train, y_train):
        """Train all ensemble models"""
        print(f"  Training {len(self.models)} ensemble models...")
        
        for name, model in self.models.items():
            try:
                model.train(X_train, y_train)
            except Exception as e:
                print(f"    ⚠️  {name} failed: {str(e)}")
        
        self.is_trained = True
        print(f"  ✓ Ensemble with {len([m for m in self.models.values() if m.is_trained])} models trained")
    
    def predict(self, X):
        """Predict using ensemble (average of all models)"""
        predictions = []
        
        for model in self.models.values():
            if model.is_trained:
                try:
                    pred = model.predict(X)
                    predictions.append(pred)
                except:
                    pass
        
        if not predictions:
            raise ValueError("No models in ensemble are trained")
        
        # Return average of all predictions
        return np.mean(predictions, axis=0)


def compare_pricing_algorithms(X_train, X_test, y_train, y_test):
    """Train and compare all pricing algorithms"""
    
    print("\n" + "=" * 80)
    print("🎯 TRAINING PRICING ALGORITHMS")
    print("=" * 80)
    
    algorithms = {
        'Linear Regression': LinearRegressionPricer(),
        'Gradient Boosting': GradientBoostingPricer(),
        'Seasonal Pricing': SeasonalPricer(),
    }
    
    # Add neural network if available
    if HAS_TENSORFLOW:
        algorithms['Neural Network'] = NeuralNetworkPricer()
    
    # Add ensemble last
    algorithms['Ensemble'] = EnsemblePricer()
    
    results = {}
    
    for name, algo in algorithms.items():
        print(f"\n🔹 {name}")
        try:
            if name == 'Neural Network' and HAS_TENSORFLOW:
                algo.train(X_train, y_train, epochs=20)
            elif name == 'Ensemble':
                algo.train(X_train, y_train)
            else:
                algo.train(X_train, y_train)
            
            metrics = algo.evaluate(X_test, y_test)
            results[name] = metrics
            
            print(f"  MAE: ${metrics['MAE']:.2f}")
            print(f"  RMSE: ${metrics['RMSE']:.2f}")
            print(f"  R²: {metrics['R²']:.4f}")
            print(f"  MAPE: {metrics['MAPE']:.2f}%")
        
        except Exception as e:
            print(f"  ⚠️  Error: {str(e)}")
    
    print("\n" + "=" * 80)
    
    return algorithms, results


if __name__ == "__main__":
    # Test with dummy data
    from sklearn.datasets import make_regression
    
    X, y = make_regression(n_samples=1000, n_features=10, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    algorithms, results = compare_pricing_algorithms(X_train, X_test, y_train, y_test)
