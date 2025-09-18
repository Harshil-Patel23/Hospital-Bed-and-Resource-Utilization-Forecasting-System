import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import xgboost as xgb
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
warnings.filterwarnings('ignore')

class HospitalAdmissionForecaster:
    def __init__(self, data):
        """Initialize forecaster with preprocessed data"""
        self.data = data
        self.daily_data = None
        self.models = {}
        self.predictions = {}
        self.metrics = {}
        
    def prepare_time_series_data(self):
        """Prepare daily aggregated data for time series forecasting"""
        # Aggregate daily admissions
        self.daily_data = self.data.groupby('admission_date').agg({
            'admission_count': 'sum',
            'readmission_count': 'sum',
            'emergency_visit_count': 'sum',
            'length_of_stay_avg': 'mean',
            'severity_level': lambda x: (x == 'Critical').sum(),  # Count critical cases
            'seasonal_indicator': 'first',
            'is_weekend': 'first'
        }).reset_index()
        
        # Sort by date
        self.daily_data = self.daily_data.sort_values('admission_date').reset_index(drop=True)
        
        # Add time-based features
        self.daily_data['day_of_week'] = self.daily_data['admission_date'].dt.dayofweek
        self.daily_data['month'] = self.daily_data['admission_date'].dt.month
        self.daily_data['year'] = self.daily_data['admission_date'].dt.year
        self.daily_data['day_of_year'] = self.daily_data['admission_date'].dt.dayofyear
        
        # Add lagged features
        for lag in [1, 7, 14, 30]:
            self.daily_data[f'admission_lag_{lag}'] = self.daily_data['admission_count'].shift(lag)
        
        # Add rolling averages
        for window in [7, 14, 30]:
            self.daily_data[f'admission_rolling_{window}'] = self.daily_data['admission_count'].rolling(window=window).mean()
        
        # Fill NaN values created by lags and rolling averages
        self.daily_data.fillna(method='bfill', inplace=True)
        self.daily_data.fillna(method='ffill', inplace=True)
        
        print(f"Time series data prepared: {len(self.daily_data)} days")
        return self.daily_data
    
    def calculate_metrics(self, y_true, y_pred, model_name):
        """Calculate evaluation metrics"""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        r2 = r2_score(y_true, y_pred)
        
        self.metrics[model_name] = {
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'R2': r2
        }
        
        print(f"\n{model_name} Metrics:")
        print(f"MAE: {mae:.2f}")
        print(f"RMSE: {rmse:.2f}")
        print(f"MAPE: {mape:.2f}%")
        print(f"R²: {r2:.4f}")
        
        return self.metrics[model_name]
    
    def arima_forecast(self, forecast_days=30):
        """ARIMA time series forecasting"""
        print("Training ARIMA model...")
        
        if self.daily_data is None:
            self.prepare_time_series_data()
        
        # Prepare time series
        ts_data = self.daily_data.set_index('admission_date')['admission_count']
        
        # Split data
        train_size = int(len(ts_data) * 0.8)
        train_data = ts_data[:train_size]
        test_data = ts_data[train_size:]
        
        # Fit ARIMA model (using auto-selected parameters)
        # For simplicity, using ARIMA(1,1,1) - you might want to use auto_arima for optimal parameters
        try:
            model = ARIMA(train_data, order=(1, 1, 1))
            fitted_model = model.fit()
            self.models['ARIMA'] = fitted_model
            
            # Forecast on test data
            test_predictions = fitted_model.forecast(steps=len(test_data))
            
            # Future forecast
            future_forecast = fitted_model.forecast(steps=forecast_days)
            
            # Calculate metrics
            self.calculate_metrics(test_data.values, test_predictions, 'ARIMA')
            
            # Store predictions
            self.predictions['ARIMA'] = {
                'test_pred': test_predictions,
                'test_actual': test_data.values,
                'future_forecast': future_forecast,
                'train_data': train_data,
                'test_data': test_data
            }
            
            print(f"ARIMA model trained successfully. Forecast for next {forecast_days} days generated.")
            
        except Exception as e:
            print(f"ARIMA model failed: {e}")
            return None
    
    def random_forest_forecast(self, forecast_days=30):
        """Random Forest forecasting"""
        print("Training Random Forest model...")
        
        if self.daily_data is None:
            self.prepare_time_series_data()
        
        # Prepare features
        feature_cols = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'readmission_count', 'emergency_visit_count', 'length_of_stay_avg',
            'admission_lag_1', 'admission_lag_7', 'admission_lag_14', 'admission_lag_30',
            'admission_rolling_7', 'admission_rolling_14', 'admission_rolling_30'
        ]
        
        # Encode categorical variables
        le_seasonal = LabelEncoder()
        self.daily_data['seasonal_encoded'] = le_seasonal.fit_transform(self.daily_data['seasonal_indicator'])
        feature_cols.append('seasonal_encoded')
        
        X = self.daily_data[feature_cols].values
        y = self.daily_data['admission_count'].values
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=5)
        train_idx, test_idx = list(tscv.split(X))[-1]
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train Random Forest
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        self.models['RandomForest'] = (rf_model, scaler, le_seasonal)
        
        # Predictions
        y_pred = rf_model.predict(X_test_scaled)
        
        # Calculate metrics
        self.calculate_metrics(y_test, y_pred, 'RandomForest')
        
        # Generate future forecasts
        future_forecasts = self._generate_future_forecasts_rf(forecast_days, rf_model, scaler)
        
        # Store predictions
        self.predictions['RandomForest'] = {
            'test_pred': y_pred,
            'test_actual': y_test,
            'future_forecast': future_forecasts,
            'test_dates': self.daily_data.iloc[test_idx]['admission_date'].values
        }
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("Top 5 most important features:")
        print(feature_importance.head())
        
        print(f"Random Forest model trained successfully.")
    
    def xgboost_forecast(self, forecast_days=30):
        """XGBoost forecasting"""
        print("Training XGBoost model...")
        
        if self.daily_data is None:
            self.prepare_time_series_data()
        
        # Use same features as Random Forest
        feature_cols = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'readmission_count', 'emergency_visit_count', 'length_of_stay_avg',
            'admission_lag_1', 'admission_lag_7', 'admission_lag_14', 'admission_lag_30',
            'admission_rolling_7', 'admission_rolling_14', 'admission_rolling_30'
        ]
        
        # Encode seasonal indicator if not already done
        if 'seasonal_encoded' not in self.daily_data.columns:
            le_seasonal = LabelEncoder()
            self.daily_data['seasonal_encoded'] = le_seasonal.fit_transform(self.daily_data['seasonal_indicator'])
        else:
            le_seasonal = None
            
        feature_cols.append('seasonal_encoded')
        
        X = self.daily_data[feature_cols].values
        y = self.daily_data['admission_count'].values
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=5)
        train_idx, test_idx = list(tscv.split(X))[-1]
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train XGBoost
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        self.models['XGBoost'] = (xgb_model, le_seasonal)
        
        # Predictions
        y_pred = xgb_model.predict(X_test)
        
        # Calculate metrics
        self.calculate_metrics(y_test, y_pred, 'XGBoost')
        
        # Generate future forecasts
        future_forecasts = self._generate_future_forecasts_xgb(forecast_days, xgb_model)
        
        # Store predictions
        self.predictions['XGBoost'] = {
            'test_pred': y_pred,
            'test_actual': y_test,
            'future_forecast': future_forecasts,
            'test_dates': self.daily_data.iloc[test_idx]['admission_date'].values
        }
        
        print(f"XGBoost model trained successfully.")
    
    def _generate_future_forecasts_rf(self, forecast_days, model, scaler):
        """Generate future forecasts using Random Forest"""
        last_data = self.daily_data.iloc[-1:].copy()
        forecasts = []
        
        feature_cols = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'readmission_count', 'emergency_visit_count', 'length_of_stay_avg',
            'admission_lag_1', 'admission_lag_7', 'admission_lag_14', 'admission_lag_30',
            'admission_rolling_7', 'admission_rolling_14', 'admission_rolling_30',
            'seasonal_encoded'
        ]
        
        for i in range(forecast_days):
            # Create future date
            future_date = last_data['admission_date'].iloc[-1] + pd.Timedelta(days=1)
            
            # Update time-based features
            last_data.loc[last_data.index[-1], 'admission_date'] = future_date
            last_data.loc[last_data.index[-1], 'day_of_week'] = future_date.dayofweek
            last_data.loc[last_data.index[-1], 'month'] = future_date.month
            last_data.loc[last_data.index[-1], 'day_of_year'] = future_date.dayofyear
            last_data.loc[last_data.index[-1], 'is_weekend'] = future_date.dayofweek >= 5
            
            # Prepare features
            X_future = last_data[feature_cols].values
            X_future_scaled = scaler.transform(X_future)
            
            # Make prediction
            pred = model.predict(X_future_scaled)[0]
            forecasts.append(pred)
            
            # Update lag features for next iteration
            if i == 0:
                last_data.loc[last_data.index[-1], 'admission_lag_1'] = self.daily_data['admission_count'].iloc[-1]
            else:
                last_data.loc[last_data.index[-1], 'admission_lag_1'] = forecasts[-1]
        
        return np.array(forecasts)
    
    def _generate_future_forecasts_xgb(self, forecast_days, model):
        """Generate future forecasts using XGBoost"""
        last_data = self.daily_data.iloc[-1:].copy()
        forecasts = []
        
        feature_cols = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'readmission_count', 'emergency_visit_count', 'length_of_stay_avg',
            'admission_lag_1', 'admission_lag_7', 'admission_lag_14', 'admission_lag_30',
            'admission_rolling_7', 'admission_rolling_14', 'admission_rolling_30',
            'seasonal_encoded'
        ]
        
        for i in range(forecast_days):
            # Create future date
            future_date = last_data['admission_date'].iloc[-1] + pd.Timedelta(days=1)
            
            # Update time-based features
            last_data.loc[last_data.index[-1], 'admission_date'] = future_date
            last_data.loc[last_data.index[-1], 'day_of_week'] = future_date.dayofweek
            last_data.loc[last_data.index[-1], 'month'] = future_date.month
            last_data.loc[last_data.index[-1], 'day_of_year'] = future_date.dayofyear
            last_data.loc[last_data.index[-1], 'is_weekend'] = future_date.dayofweek >= 5
            
            # Prepare features
            X_future = last_data[feature_cols].values
            
            # Make prediction
            pred = model.predict(X_future)[0]
            forecasts.append(pred)
            
            # Update lag features for next iteration
            if i == 0:
                last_data.loc[last_data.index[-1], 'admission_lag_1'] = self.daily_data['admission_count'].iloc[-1]
            else:
                last_data.loc[last_data.index[-1], 'admission_lag_1'] = forecasts[-1]
        
        return np.array(forecasts)
    
    def plot_forecasting_results(self):
        """Plot forecasting results for all models"""
        n_models = len(self.predictions)
        if n_models == 0:
            print("No trained models to plot.")
            return
        
        fig, axes = plt.subplots(n_models, 2, figsize=(20, 6*n_models))
        if n_models == 1:
            axes = axes.reshape(1, -1)
        
        colors = ['blue', 'red', 'green', 'orange']
        
        for idx, (model_name, pred_data) in enumerate(self.predictions.items()):
            color = colors[idx % len(colors)]
            
            # Plot 1: Test predictions vs actual
            if model_name == 'ARIMA':
                test_dates = pred_data['test_data'].index
                axes[idx, 0].plot(test_dates, pred_data['test_actual'], 
                                label='Actual', color='black', linewidth=2)
                axes[idx, 0].plot(test_dates, pred_data['test_pred'], 
                                label='Predicted', color=color, linewidth=2, alpha=0.8)
            else:
                test_dates = pred_data['test_dates']
                axes[idx, 0].plot(test_dates, pred_data['test_actual'], 
                                label='Actual', color='black', linewidth=2)
                axes[idx, 0].plot(test_dates, pred_data['test_pred'], 
                                label='Predicted', color=color, linewidth=2, alpha=0.8)
            
            axes[idx, 0].set_title(f'{model_name} - Test Set Predictions')
            axes[idx, 0].set_xlabel('Date')
            axes[idx, 0].set_ylabel('Daily Admissions')
            axes[idx, 0].legend()
            axes[idx, 0].grid(True, alpha=0.3)
            
            # Plot 2: Future forecasts
            if model_name == 'ARIMA':
                last_date = pred_data['test_data'].index[-1]
            else:
                last_date = pd.to_datetime(pred_data['test_dates'][-1])
            
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                                       periods=len(pred_data['future_forecast']), freq='D')
            
            # Show last 30 days of actual data for context
            if model_name == 'ARIMA':
                recent_data = pred_data['test_data'].tail(30)
                axes[idx, 1].plot(recent_data.index, recent_data.values, 
                                color='black', linewidth=2, label='Recent Actual')
            else:
                recent_dates = pd.to_datetime(pred_data['test_dates'][-30:])
                recent_actual = pred_data['test_actual'][-30:]
                axes[idx, 1].plot(recent_dates, recent_actual, 
                                color='black', linewidth=2, label='Recent Actual')
            
            axes[idx, 1].plot(future_dates, pred_data['future_forecast'], 
                            color=color, linewidth=2, alpha=0.8, label='Forecast')
            axes[idx, 1].axvline(x=last_date, color='red', linestyle='--', alpha=0.7, label='Forecast Start')
            
            axes[idx, 1].set_title(f'{model_name} - Future Forecast (30 days)')
            axes[idx, 1].set_xlabel('Date')
            axes[idx, 1].set_ylabel('Daily Admissions')
            axes[idx, 1].legend()
            axes[idx, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def compare_models(self):
        """Compare model performance"""
        if not self.metrics:
            print("No models trained yet.")
            return
        
        metrics_df = pd.DataFrame(self.metrics).T
        print("\nModel Comparison:")
        print("="*50)
        print(metrics_df.round(4))
        
        # Plot comparison
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Model Performance Comparison', fontsize=16, fontweight='bold')
        
        metrics_to_plot = ['MAE', 'RMSE', 'MAPE', 'R2']
        
        for idx, metric in enumerate(metrics_to_plot):
            ax = axes[idx//2, idx%2]
            values = [self.metrics[model][metric] for model in self.metrics.keys()]
            models = list(self.metrics.keys())
            
            bars = ax.bar(models, values, alpha=0.7)
            ax.set_title(f'{metric} Comparison')
            ax.set_ylabel(metric)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                       f'{value:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
        
        # Determine best model
        best_model_mae = min(self.metrics.keys(), key=lambda x: self.metrics[x]['MAE'])
        best_model_rmse = min(self.metrics.keys(), key=lambda x: self.metrics[x]['RMSE'])
        best_model_mape = min(self.metrics.keys(), key=lambda x: self.metrics[x]['MAPE'])
        best_model_r2 = max(self.metrics.keys(), key=lambda x: self.metrics[x]['R2'])
        
        print(f"\nBest Models by Metric:")
        print(f"MAE: {best_model_mae} ({self.metrics[best_model_mae]['MAE']:.2f})")
        print(f"RMSE: {best_model_rmse} ({self.metrics[best_model_rmse]['RMSE']:.2f})")
        print(f"MAPE: {best_model_mape} ({self.metrics[best_model_mape]['MAPE']:.2f}%)")
        print(f"R²: {best_model_r2} ({self.metrics[best_model_r2]['R2']:.4f})")
    
    def get_forecast_summary(self, days=7):
        """Get forecast summary for next N days"""
        if not self.predictions:
            print("No forecasts available.")
            return None
        
        summary = {}
        for model_name, pred_data in self.predictions.items():
            forecast = pred_data['future_forecast'][:days]
            summary[model_name] = {
                'total_forecast': forecast.sum(),
                'daily_average': forecast.mean(),
                'peak_day': forecast.argmax() + 1,
                'peak_admissions': forecast.max(),
                'daily_forecast': forecast.tolist()
            }
        
        print(f"\nForecast Summary for Next {days} Days:")
        print("="*60)
        
        for model_name, data in summary.items():
            print(f"\n{model_name}:")
            print(f"  Total Admissions: {data['total_forecast']:.0f}")
            print(f"  Daily Average: {data['daily_average']:.1f}")
            print(f"  Peak Day: Day {data['peak_day']} ({data['peak_admissions']:.0f} admissions)")
        
        return summary
    
    def save_models(self, filepath='models'):
        """Save trained models to a directory"""
        import pickle
        import os
        
        # Create directory if it doesn't exist
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        
        for model_name, model_data in self.models.items():
            filename = os.path.join(filepath, f"{model_name.lower()}.pkl")
            with open(filename, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"Saved {model_name} model to {filename}")
        
        # Save predictions and metrics
        results = {
            'predictions': self.predictions,
            'metrics': self.metrics,
            'daily_data': self.daily_data
        }
        results_filename = os.path.join(filepath, "results.pkl")
        with open(results_filename, 'wb') as f:
            pickle.dump(results, f)
        print(f"Saved results to {results_filename}")


# Example usage and model training
def train_all_models(data):
    """Train all forecasting models"""
    forecaster = HospitalAdmissionForecaster(data)
    
    # Prepare time series data
    forecaster.prepare_time_series_data()
    
    print("Training all forecasting models...")
    print("="*50)
    
    # Train ARIMA model
    forecaster.arima_forecast(forecast_days=30)
    
    # Train Random Forest model
    forecaster.random_forest_forecast(forecast_days=30)
    
    # Train XGBoost model
    forecaster.xgboost_forecast(forecast_days=30)
    
    # Compare models
    forecaster.compare_models()
    
    # Plot results
    forecaster.plot_forecasting_results()
     
    # Get forecast summary
    forecaster.get_forecast_summary(days=7)
    
    # Save models
    forecaster.save_models()
    
    return forecaster

if __name__ == "__main__":
    df = pd.read_csv('processed_hospital_data.csv')
    df['admission_date'] = pd.to_datetime(df['admission_date'])

    # This would be run after data preprocessing
    print("Forecasting models script ready.")
    print("To use: forecaster = train_all_models(processed_data)")
    forecaster = train_all_models(df)
    