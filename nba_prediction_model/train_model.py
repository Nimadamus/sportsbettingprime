"""
Model Training Script
Train NBA prediction models using historical data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import json

from data.nba_data_collector import NBADataCollector
from utils.feature_engineering import NBAFeatureEngineer
from models.predictor import NBAPredictor
from utils.evaluation import ModelEvaluator


def load_historical_games(csv_file='data/historical_games.csv'):
    """
    Load historical game data from CSV

    CSV should have columns:
    - game_date
    - home_team
    - away_team
    - home_score
    - away_score

    Returns:
        DataFrame with historical games
    """
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} historical games from {csv_file}")
        return df
    except FileNotFoundError:
        print(f"Historical games file not found: {csv_file}")
        print("\nYou need to create a CSV file with historical NBA games.")
        print("Required columns: game_date, home_team, away_team, home_score, away_score")
        return None


def create_synthetic_training_data(n_samples=1000):
    """
    Create synthetic training data for testing purposes

    Args:
        n_samples: Number of synthetic games to generate

    Returns:
        Tuple of (features_df, targets_df)
    """
    print(f"Generating {n_samples} synthetic training samples...")

    np.random.seed(42)

    # Generate features
    features = {
        'home_win_pct': np.random.uniform(0.3, 0.7, n_samples),
        'away_win_pct': np.random.uniform(0.3, 0.7, n_samples),
        'win_pct_diff': np.random.uniform(-0.4, 0.4, n_samples),
        'home_off_rating': np.random.uniform(105, 120, n_samples),
        'away_off_rating': np.random.uniform(105, 120, n_samples),
        'home_def_rating': np.random.uniform(105, 120, n_samples),
        'away_def_rating': np.random.uniform(105, 120, n_samples),
        'home_net_rating': np.random.uniform(-8, 10, n_samples),
        'away_net_rating': np.random.uniform(-8, 10, n_samples),
        'net_rating_diff': np.random.uniform(-15, 15, n_samples),
        'home_pace': np.random.uniform(95, 105, n_samples),
        'away_pace': np.random.uniform(95, 105, n_samples),
        'avg_pace': np.random.uniform(95, 105, n_samples),
        'pace_diff': np.random.uniform(-10, 10, n_samples),
        'home_ts_pct': np.random.uniform(0.52, 0.60, n_samples),
        'away_ts_pct': np.random.uniform(0.52, 0.60, n_samples),
        'home_efg_pct': np.random.uniform(0.48, 0.56, n_samples),
        'away_efg_pct': np.random.uniform(0.48, 0.56, n_samples),
        'home_efg': np.random.uniform(0.48, 0.56, n_samples),
        'away_efg': np.random.uniform(0.48, 0.56, n_samples),
        'home_tov_pct': np.random.uniform(0.10, 0.18, n_samples),
        'away_tov_pct': np.random.uniform(0.10, 0.18, n_samples),
        'home_oreb_pct': np.random.uniform(0.20, 0.30, n_samples),
        'away_oreb_pct': np.random.uniform(0.20, 0.30, n_samples),
        'home_fta_rate': np.random.uniform(0.20, 0.30, n_samples),
        'away_fta_rate': np.random.uniform(0.20, 0.30, n_samples),
        'home_opp_efg': np.random.uniform(0.48, 0.56, n_samples),
        'away_opp_efg': np.random.uniform(0.48, 0.56, n_samples),
        'home_opp_tov_pct': np.random.uniform(0.10, 0.18, n_samples),
        'away_opp_tov_pct': np.random.uniform(0.10, 0.18, n_samples),
        'home_last_5_win_pct': np.random.uniform(0.2, 0.8, n_samples),
        'away_last_5_win_pct': np.random.uniform(0.2, 0.8, n_samples),
        'home_last_5_point_diff': np.random.uniform(-10, 10, n_samples),
        'away_last_5_point_diff': np.random.uniform(-10, 10, n_samples),
        'home_last_10_win_pct': np.random.uniform(0.2, 0.8, n_samples),
        'away_last_10_win_pct': np.random.uniform(0.2, 0.8, n_samples),
        'home_last_10_point_diff': np.random.uniform(-10, 10, n_samples),
        'away_last_10_point_diff': np.random.uniform(-10, 10, n_samples),
        'home_momentum': np.random.uniform(-0.4, 0.4, n_samples),
        'away_momentum': np.random.uniform(-0.4, 0.4, n_samples),
        'home_expected_pts': np.random.uniform(105, 120, n_samples),
        'away_expected_pts': np.random.uniform(105, 120, n_samples),
        'off_vs_def_home': np.random.uniform(-10, 10, n_samples),
        'off_vs_def_away': np.random.uniform(-10, 10, n_samples),
        'home_pts_per_game': np.random.uniform(105, 120, n_samples),
        'away_pts_per_game': np.random.uniform(105, 120, n_samples),
        'home_ast_per_game': np.random.uniform(20, 30, n_samples),
        'away_ast_per_game': np.random.uniform(20, 30, n_samples),
        'home_reb_per_game': np.random.uniform(40, 50, n_samples),
        'away_reb_per_game': np.random.uniform(40, 50, n_samples),
        'home_fg3_pct': np.random.uniform(0.32, 0.40, n_samples),
        'away_fg3_pct': np.random.uniform(0.32, 0.40, n_samples),
        'home_fg3a_per_game': np.random.uniform(25, 45, n_samples),
        'away_fg3a_per_game': np.random.uniform(25, 45, n_samples),
        'home_pie': np.random.uniform(0.45, 0.55, n_samples),
        'away_pie': np.random.uniform(0.45, 0.55, n_samples),
        'rest_advantage': np.random.randint(-2, 3, n_samples),
        'home_days_rest': np.random.randint(0, 4, n_samples),
        'away_days_rest': np.random.randint(0, 4, n_samples),
        'home_back_to_back': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'away_back_to_back': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'back_to_back_disadvantage': np.random.choice([-1, 0, 1], n_samples, p=[0.1, 0.8, 0.1]),
        'home_court_advantage': np.ones(n_samples)
    }

    features_df = pd.DataFrame(features)

    # Generate realistic targets
    # Home win probability increases with net rating diff and home court advantage
    win_logit = (
        3.5 +  # Home court advantage
        features_df['net_rating_diff'] * 0.15 +
        features_df['home_last_5_point_diff'] * 0.1 +
        features_df['rest_advantage'] * 0.3 +
        np.random.normal(0, 1.5, n_samples)
    )

    targets = {
        'home_win': (win_logit > 0).astype(int),
        'point_differential': win_logit + np.random.normal(0, 3, n_samples),
        'total_points': (
            (features_df['home_expected_pts'] + features_df['away_expected_pts']) / 2 +
            (features_df['avg_pace'] - 100) * 2.5 +
            np.random.normal(0, 8, n_samples)
        )
    }

    targets_df = pd.DataFrame(targets)

    return features_df, targets_df


def train_models(model_type='xgboost', use_synthetic=True):
    """
    Train all prediction models

    Args:
        model_type: Type of ML model to use
        use_synthetic: Whether to use synthetic data for training

    Returns:
        Trained predictor object
    """
    print("NBA Model Training Pipeline")
    print("=" * 60)
    print(f"Model Type: {model_type}")
    print(f"Using Synthetic Data: {use_synthetic}")
    print()

    # Load or generate training data
    if use_synthetic:
        X, y_df = create_synthetic_training_data(n_samples=2000)
        print(f"Training data shape: {X.shape}")
    else:
        # Load historical data
        historical_games = load_historical_games()
        if historical_games is None:
            print("No historical data available. Using synthetic data instead.")
            X, y_df = create_synthetic_training_data(n_samples=2000)
        else:
            # Process historical games into features
            # This would require implementing feature extraction from game logs
            print("Historical data processing not yet implemented")
            print("Using synthetic data for now")
            X, y_df = create_synthetic_training_data(n_samples=2000)

    # Initialize predictor
    predictor = NBAPredictor(model_type=model_type)

    # Train win model
    print("\n" + "=" * 60)
    predictor.train_win_model(X, y_df['home_win'])

    # Train spread model
    print("\n" + "=" * 60)
    predictor.train_spread_model(X, y_df['point_differential'])

    # Train total model
    print("\n" + "=" * 60)
    predictor.train_total_model(X, y_df['total_points'])

    # Save models
    print("\n" + "=" * 60)
    print("Saving models...")
    os.makedirs('models/saved', exist_ok=True)
    predictor.save_models('models/saved')

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)

    return predictor


def evaluate_models(predictor, X_test, y_test_df):
    """
    Evaluate trained models

    Args:
        predictor: Trained predictor object
        X_test: Test features
        y_test_df: Test targets

    Returns:
        Evaluation report
    """
    print("\nEvaluating Models...")
    print("=" * 60)

    # Generate predictions
    predictions = []
    for idx, row in X_test.iterrows():
        pred = predictor.predict_game(row)
        predictions.append(pred)

    predictions_df = pd.DataFrame(predictions)

    # Prepare results dataframe
    results_df = pd.DataFrame({
        'actual_winner': ['home' if w == 1 else 'away' for w in y_test_df['home_win']],
        'home_win': y_test_df['home_win'],
        'actual_spread': y_test_df['point_differential'],
        'actual_total': y_test_df['total_points'],
        'point_differential': y_test_df['point_differential']
    })

    # Evaluate
    evaluator = ModelEvaluator()
    report = evaluator.generate_report(
        predictions_df,
        results_df,
        'outputs/training_evaluation.json'
    )

    evaluator.print_summary(report)

    return report


def main():
    """Main training execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Train NBA prediction models')
    parser.add_argument('--model-type', type=str, default='xgboost',
                       choices=['logistic', 'random_forest', 'xgboost', 'lightgbm', 'ensemble'],
                       help='Type of ML model to use')
    parser.add_argument('--use-real-data', action='store_true',
                       help='Use real historical data instead of synthetic')
    parser.add_argument('--evaluate', action='store_true',
                       help='Evaluate models on test set after training')

    args = parser.parse_args()

    # Train models
    predictor = train_models(
        model_type=args.model_type,
        use_synthetic=not args.use_real_data
    )

    # Evaluate if requested
    if args.evaluate:
        # Generate test data
        X_test, y_test = create_synthetic_training_data(n_samples=500)
        evaluate_models(predictor, X_test, y_test)

    print("\n" + "=" * 60)
    print("Models are now ready for making predictions!")
    print("Run: python generate_predictions.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
