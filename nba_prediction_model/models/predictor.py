"""
NBA Game Prediction Models
Implements multiple ML models for predicting NBA game outcomes
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import joblib
import json
from datetime import datetime


class NBAPredictor:
    """Main prediction class for NBA games"""

    def __init__(self, model_type='ensemble'):
        """
        Initialize NBA predictor

        Args:
            model_type: 'logistic', 'random_forest', 'xgboost', 'lightgbm', 'ensemble'
        """
        self.model_type = model_type
        self.win_model = None
        self.spread_model = None
        self.total_model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.training_metrics = {}

    def build_win_model(self):
        """Build model for predicting game winner"""
        if self.model_type == 'logistic':
            return LogisticRegression(max_iter=1000, random_state=42)
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        elif self.model_type == 'xgboost':
            return xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                     random_state=42, n_jobs=-1)
        elif self.model_type == 'lightgbm':
            return lgb.LGBMClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                     random_state=42, n_jobs=-1)
        elif self.model_type == 'ensemble':
            # Use XGBoost as default for ensemble
            return xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                     random_state=42, n_jobs=-1)

    def build_spread_model(self):
        """Build model for predicting point spread"""
        if self.model_type == 'random_forest':
            return RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        elif self.model_type == 'xgboost':
            return xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                   random_state=42, n_jobs=-1)
        elif self.model_type == 'lightgbm':
            return lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                    random_state=42, n_jobs=-1)
        else:
            # Default to Gradient Boosting
            return GradientBoostingRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                            random_state=42)

    def build_total_model(self):
        """Build model for predicting total points"""
        if self.model_type == 'random_forest':
            return RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        elif self.model_type == 'xgboost':
            return xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                   random_state=42, n_jobs=-1)
        elif self.model_type == 'lightgbm':
            return lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                    random_state=42, n_jobs=-1)
        else:
            return GradientBoostingRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                            random_state=42)

    def train_win_model(self, X, y, test_size=0.2):
        """
        Train model to predict game winner

        Args:
            X: Feature dataframe
            y: Target variable (1 = home win, 0 = away win)
            test_size: Proportion of data for testing

        Returns:
            Dictionary with training metrics
        """
        print("Training win prediction model...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.win_model = self.build_win_model()
        self.win_model.fit(X_train_scaled, y_train)

        # Predictions
        y_pred_train = self.win_model.predict(X_train_scaled)
        y_pred_test = self.win_model.predict(X_test_scaled)

        # Metrics
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)

        # Cross-validation
        cv_scores = cross_val_score(self.win_model, X_train_scaled, y_train, cv=5)

        metrics = {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'cv_mean_accuracy': cv_scores.mean(),
            'cv_std_accuracy': cv_scores.std()
        }

        self.training_metrics['win_model'] = metrics

        print(f"Train Accuracy: {train_acc:.4f}")
        print(f"Test Accuracy: {test_acc:.4f}")
        print(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Feature importance
        if hasattr(self.win_model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': X.columns,
                'importance': self.win_model.feature_importances_
            }).sort_values('importance', ascending=False)
            self.feature_importance['win_model'] = importance.to_dict('records')
            print("\nTop 10 Most Important Features:")
            print(importance.head(10))

        return metrics

    def train_spread_model(self, X, y, test_size=0.2):
        """
        Train model to predict point spread

        Args:
            X: Feature dataframe
            y: Target variable (point differential: home_score - away_score)
            test_size: Proportion of data for testing

        Returns:
            Dictionary with training metrics
        """
        print("\nTraining point spread prediction model...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        # Use same scaler as win model
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.spread_model = self.build_spread_model()
        self.spread_model.fit(X_train_scaled, y_train)

        # Predictions
        y_pred_train = self.spread_model.predict(X_train_scaled)
        y_pred_test = self.spread_model.predict(X_test_scaled)

        # Metrics
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2 = r2_score(y_test, y_pred_test)

        metrics = {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'r2_score': r2
        }

        self.training_metrics['spread_model'] = metrics

        print(f"Train MAE: {train_mae:.2f} points")
        print(f"Test MAE: {test_mae:.2f} points")
        print(f"Test RMSE: {test_rmse:.2f} points")
        print(f"R² Score: {r2:.4f}")

        # Feature importance
        if hasattr(self.spread_model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': X.columns,
                'importance': self.spread_model.feature_importances_
            }).sort_values('importance', ascending=False)
            self.feature_importance['spread_model'] = importance.to_dict('records')
            print("\nTop 10 Most Important Features for Spread:")
            print(importance.head(10))

        return metrics

    def train_total_model(self, X, y, test_size=0.2):
        """
        Train model to predict total points

        Args:
            X: Feature dataframe
            y: Target variable (total_points: home_score + away_score)
            test_size: Proportion of data for testing

        Returns:
            Dictionary with training metrics
        """
        print("\nTraining total points prediction model...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        # Use same scaler as win model
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.total_model = self.build_total_model()
        self.total_model.fit(X_train_scaled, y_train)

        # Predictions
        y_pred_train = self.total_model.predict(X_train_scaled)
        y_pred_test = self.total_model.predict(X_test_scaled)

        # Metrics
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2 = r2_score(y_test, y_pred_test)

        metrics = {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'r2_score': r2
        }

        self.training_metrics['total_model'] = metrics

        print(f"Train MAE: {train_mae:.2f} points")
        print(f"Test MAE: {test_mae:.2f} points")
        print(f"Test RMSE: {test_rmse:.2f} points")
        print(f"R² Score: {r2:.4f}")

        # Feature importance
        if hasattr(self.total_model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': X.columns,
                'importance': self.total_model.feature_importances_
            }).sort_values('importance', ascending=False)
            self.feature_importance['total_model'] = importance.to_dict('records')
            print("\nTop 10 Most Important Features for Total:")
            print(importance.head(10))

        return metrics

    def predict_game(self, features):
        """
        Predict outcome for a single game

        Args:
            features: DataFrame or dict with game features

        Returns:
            Dictionary with predictions
        """
        if isinstance(features, dict):
            features = pd.DataFrame([features])

        # Scale features
        features_scaled = self.scaler.transform(features)

        predictions = {}

        # Win prediction
        if self.win_model:
            win_prob = self.win_model.predict_proba(features_scaled)[0]
            predictions['home_win_prob'] = float(win_prob[1])
            predictions['away_win_prob'] = float(win_prob[0])
            predictions['predicted_winner'] = 'home' if win_prob[1] > 0.5 else 'away'

        # Spread prediction
        if self.spread_model:
            spread = self.spread_model.predict(features_scaled)[0]
            predictions['predicted_spread'] = float(round(spread, 1))
            predictions['spread_confidence'] = 'high' if abs(spread) > 7 else 'medium' if abs(spread) > 3 else 'low'

        # Total prediction
        if self.total_model:
            total = self.total_model.predict(features_scaled)[0]
            predictions['predicted_total'] = float(round(total, 1))

        return predictions

    def predict_games(self, features_df):
        """
        Predict outcomes for multiple games

        Args:
            features_df: DataFrame with features for multiple games

        Returns:
            DataFrame with predictions
        """
        predictions = []

        for idx, row in features_df.iterrows():
            game_pred = self.predict_game(row)
            game_pred['home_team'] = row.get('home_team', '')
            game_pred['away_team'] = row.get('away_team', '')
            predictions.append(game_pred)

        return pd.DataFrame(predictions)

    def save_models(self, directory='models/saved'):
        """Save trained models to disk"""
        import os
        os.makedirs(directory, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if self.win_model:
            joblib.dump(self.win_model, f'{directory}/win_model_{timestamp}.pkl')
            print(f"Win model saved to {directory}/win_model_{timestamp}.pkl")

        if self.spread_model:
            joblib.dump(self.spread_model, f'{directory}/spread_model_{timestamp}.pkl')
            print(f"Spread model saved to {directory}/spread_model_{timestamp}.pkl")

        if self.total_model:
            joblib.dump(self.total_model, f'{directory}/total_model_{timestamp}.pkl')
            print(f"Total model saved to {directory}/total_model_{timestamp}.pkl")

        # Save scaler
        joblib.dump(self.scaler, f'{directory}/scaler_{timestamp}.pkl')

        # Save metrics and feature importance
        metadata = {
            'timestamp': timestamp,
            'model_type': self.model_type,
            'training_metrics': self.training_metrics,
            'feature_importance': self.feature_importance
        }

        with open(f'{directory}/model_metadata_{timestamp}.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Model metadata saved to {directory}/model_metadata_{timestamp}.json")

    def load_models(self, directory='models/saved', timestamp=None):
        """Load trained models from disk"""
        if timestamp is None:
            # Load most recent models
            import os
            files = os.listdir(directory)
            timestamps = [f.split('_')[-1].replace('.pkl', '') for f in files if 'win_model' in f]
            if not timestamps:
                print("No saved models found")
                return
            timestamp = max(timestamps)

        self.win_model = joblib.load(f'{directory}/win_model_{timestamp}.pkl')
        self.spread_model = joblib.load(f'{directory}/spread_model_{timestamp}.pkl')
        self.total_model = joblib.load(f'{directory}/total_model_{timestamp}.pkl')
        self.scaler = joblib.load(f'{directory}/scaler_{timestamp}.pkl')

        # Load metadata
        with open(f'{directory}/model_metadata_{timestamp}.json', 'r') as f:
            metadata = json.load(f)
            self.model_type = metadata['model_type']
            self.training_metrics = metadata['training_metrics']
            self.feature_importance = metadata['feature_importance']

        print(f"Models loaded from timestamp: {timestamp}")


if __name__ == "__main__":
    # Test predictor with sample data
    print("NBA Predictor Test")
    print("=" * 50)

    # Create sample training data
    np.random.seed(42)
    n_samples = 1000

    # Generate synthetic features
    X = pd.DataFrame({
        'home_win_pct': np.random.uniform(0.3, 0.7, n_samples),
        'away_win_pct': np.random.uniform(0.3, 0.7, n_samples),
        'home_net_rating': np.random.uniform(-5, 10, n_samples),
        'away_net_rating': np.random.uniform(-5, 10, n_samples),
        'home_pace': np.random.uniform(95, 105, n_samples),
        'away_pace': np.random.uniform(95, 105, n_samples),
        'rest_advantage': np.random.randint(-2, 3, n_samples)
    })

    # Generate synthetic targets
    y_win = (X['home_net_rating'] - X['away_net_rating'] + np.random.normal(0, 3, n_samples) + 3.5 > 0).astype(int)
    y_spread = X['home_net_rating'] - X['away_net_rating'] + np.random.normal(0, 5, n_samples) + 3.5
    y_total = 110 + (X['home_pace'] + X['away_pace']) / 2 - 100 + np.random.normal(0, 10, n_samples)

    # Train models
    predictor = NBAPredictor(model_type='xgboost')
    predictor.train_win_model(X, y_win)
    predictor.train_spread_model(X, y_spread)
    predictor.train_total_model(X, y_total)

    # Make a prediction
    print("\n" + "=" * 50)
    print("Sample Prediction:")
    sample_features = {
        'home_win_pct': 0.600,
        'away_win_pct': 0.450,
        'home_net_rating': 5.2,
        'away_net_rating': -1.8,
        'home_pace': 102.0,
        'away_pace': 98.5,
        'rest_advantage': 1
    }

    prediction = predictor.predict_game(sample_features)
    print(json.dumps(prediction, indent=2))
