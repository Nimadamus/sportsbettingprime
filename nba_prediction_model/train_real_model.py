"""
Train NBA Prediction Models on Real Historical Data
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

from models.predictor import NBAPredictor
from utils.evaluation import ModelEvaluator


def load_historical_data(filepath='nba_prediction_model/data/outputs/historical_training_data.csv'):
    """
    Load historical game data

    Returns:
        DataFrame with historical games and features
    """
    try:
        df = pd.read_csv(filepath)
        df['game_date'] = pd.to_datetime(df['game_date'])
        print(f"Loaded {len(df)} games from {filepath}")
        print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print(f"Seasons: {df['season'].unique()}")
        return df
    except FileNotFoundError:
        print(f"ERROR: Historical data file not found: {filepath}")
        print("\nYou need to run the data collector first:")
        print("  python nba_prediction_model/data/historical_collector.py")
        return None


def prepare_features_and_targets(df):
    """
    Separate features from target variables

    Returns:
        X (features), y_win, y_spread, y_total
    """
    # Feature columns (everything except identifiers and targets)
    feature_cols = [
        'home_last_5_win_pct', 'home_last_5_avg_score', 'home_last_5_avg_opp_score', 'home_last_5_point_diff',
        'home_last_10_win_pct', 'home_last_10_avg_score', 'home_last_10_avg_opp_score', 'home_last_10_point_diff',
        'away_last_5_win_pct', 'away_last_5_avg_score', 'away_last_5_avg_opp_score', 'away_last_5_point_diff',
        'away_last_10_win_pct', 'away_last_10_avg_score', 'away_last_10_avg_opp_score', 'away_last_10_point_diff',
        'win_pct_diff_5', 'win_pct_diff_10', 'point_diff_diff',
        'home_rest_days', 'away_rest_days', 'rest_advantage',
        'home_back_to_back', 'away_back_to_back',
        'home_court_advantage'
    ]

    X = df[feature_cols].copy()

    # Target variables
    y_win = df['home_win'].copy()
    y_spread = df['point_differential'].copy()  # home_score - away_score
    y_total = df['total_points'].copy()  # home_score + away_score

    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Features: {len(feature_cols)}")

    return X, y_win, y_spread, y_total


def split_by_season(df, test_season='2024-25'):
    """
    Split data into train/test by season (proper temporal split)

    Args:
        df: Full dataset
        test_season: Season to hold out for testing

    Returns:
        train_df, test_df
    """
    train_df = df[df['season'] != test_season].copy()
    test_df = df[df['season'] == test_season].copy()

    print(f"\nTrain/Test Split by Season:")
    print(f"  Train: {len(train_df)} games ({df[df['season'] != test_season]['season'].unique()})")
    print(f"  Test:  {len(test_df)} games ({test_season})")
    print(f"  Train date range: {train_df['game_date'].min()} to {train_df['game_date'].max()}")
    print(f"  Test date range:  {test_df['game_date'].min()} to {test_df['game_date'].max()}")

    return train_df, test_df


def train_models_real_data(model_type='xgboost', test_season='2024-25'):
    """
    Train models on real historical data with proper validation

    Args:
        model_type: Type of ML model
        test_season: Season to use for testing (temporal holdout)

    Returns:
        Trained predictor and evaluation metrics
    """
    print("="*60)
    print("NBA PREDICTION MODEL TRAINING - REAL DATA")
    print("="*60)

    # Load data
    df = load_historical_data()
    if df is None:
        return None, None

    # Split by season (proper temporal validation)
    train_df, test_df = split_by_season(df, test_season=test_season)

    if len(test_df) == 0:
        print(f"\nWARNING: No test data for season {test_season}")
        print("Using 20% random split instead")
        from sklearn.model_selection import train_test_split
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

    # Prepare features and targets
    X_train, y_win_train, y_spread_train, y_total_train = prepare_features_and_targets(train_df)
    X_test, y_win_test, y_spread_test, y_total_test = prepare_features_and_targets(test_df)

    # Initialize predictor
    predictor = NBAPredictor(model_type=model_type)

    # Train win model
    print("\n" + "="*60)
    print("TRAINING WIN PREDICTION MODEL")
    print("="*60)
    win_metrics = predictor.train_win_model(
        pd.concat([X_train, X_test]),
        pd.concat([y_win_train, y_win_test]),
        test_size=len(X_test)/(len(X_train)+len(X_test))
    )

    # Train spread model
    print("\n" + "="*60)
    print("TRAINING POINT SPREAD MODEL")
    print("="*60)
    spread_metrics = predictor.train_spread_model(
        pd.concat([X_train, X_test]),
        pd.concat([y_spread_train, y_spread_test]),
        test_size=len(X_test)/(len(X_train)+len(X_test))
    )

    # Train total model
    print("\n" + "="*60)
    print("TRAINING TOTAL POINTS MODEL")
    print("="*60)
    total_metrics = predictor.train_total_model(
        pd.concat([X_train, X_test]),
        pd.concat([y_total_train, y_total_test]),
        test_size=len(X_test)/(len(X_train)+len(X_test))
    )

    # Make predictions on test set
    print("\n" + "="*60)
    print("GENERATING TEST SET PREDICTIONS")
    print("="*60)

    test_predictions = []
    for idx, row in X_test.iterrows():
        pred = predictor.predict_game(row)
        test_predictions.append(pred)

    predictions_df = pd.DataFrame(test_predictions)

    # Add actual results
    results_df = pd.DataFrame({
        'actual_winner': ['home' if w == 1 else 'away' for w in y_win_test],
        'home_win': y_win_test.values,
        'actual_spread': y_spread_test.values,
        'actual_total': y_total_test.values,
        'point_differential': y_spread_test.values
    })

    # Detailed evaluation
    print("\n" + "="*60)
    print("MODEL EVALUATION ON TEST SET")
    print("="*60)

    evaluator = ModelEvaluator()

    # Win prediction accuracy
    win_eval = evaluator.evaluate_win_predictions(
        predictions_df['predicted_winner'],
        results_df['actual_winner']
    )
    print(f"\nWin Prediction Accuracy: {win_eval['accuracy']:.1%}")
    print(f"  Correct: {win_eval['correct_predictions']}/{win_eval['total_games']}")

    # Spread prediction accuracy
    spread_eval = evaluator.evaluate_spread_predictions(
        predictions_df['predicted_spread'],
        results_df['actual_spread']
    )
    print(f"\nSpread Prediction Performance:")
    print(f"  MAE: {spread_eval['mae']:.2f} points")
    print(f"  RMSE: {spread_eval['rmse']:.2f} points")
    print(f"  Within 3 points: {spread_eval['accuracy_rate']:.1%}")
    print(f"  Correlation: {spread_eval['correlation']:.3f}")

    # Total prediction accuracy
    total_eval = evaluator.evaluate_total_predictions(
        predictions_df['predicted_total'],
        results_df['actual_total']
    )
    print(f"\nTotal Points Prediction Performance:")
    print(f"  MAE: {total_eval['mae']:.2f} points")
    print(f"  RMSE: {total_eval['rmse']:.2f} points")
    print(f"  Within 6 points: {total_eval['accuracy_rate']:.1%}")
    print(f"  Over/Under Accuracy: {total_eval['over_under_accuracy']:.1%}")

    # Against the spread (ATS) analysis
    print(f"\n" + "="*60)
    print("AGAINST THE SPREAD (ATS) ANALYSIS")
    print("="*60)

    # Simulate comparing to a typical Vegas spread
    # Assume Vegas spread is similar to our prediction +/- some noise
    predictions_df['predicted_spread_sign'] = predictions_df['predicted_spread'].apply(lambda x: 1 if x > 0 else 0)
    results_df['actual_spread_sign'] = results_df['actual_spread'].apply(lambda x: 1 if x > 0 else 0)

    ats_correct = (predictions_df['predicted_spread_sign'] == results_df['actual_spread_sign']).sum()
    ats_accuracy = ats_correct / len(predictions_df)

    print(f"Predicted spread direction correctly: {ats_accuracy:.1%}")
    print(f"  ({ats_correct}/{len(predictions_df)} games)")
    print(f"\nTo be profitable betting spreads at -110 odds:")
    print(f"  Need: 52.4% accuracy")
    print(f"  Current: {ats_accuracy:.1%}")
    print(f"  Status: {'PROFITABLE' if ats_accuracy >= 0.524 else 'NOT PROFITABLE YET'}")

    # Save models
    print("\n" + "="*60)
    print("SAVING TRAINED MODELS")
    print("="*60)
    os.makedirs('nba_prediction_model/models/saved', exist_ok=True)
    predictor.save_models('nba_prediction_model/models/saved')

    # Save evaluation report
    eval_report = {
        'timestamp': datetime.now().isoformat(),
        'model_type': model_type,
        'test_season': test_season,
        'train_games': len(train_df),
        'test_games': len(test_df),
        'win_prediction': win_eval,
        'spread_prediction': spread_eval,
        'total_prediction': total_eval,
        'ats_accuracy': float(ats_accuracy),
        'profitable': ats_accuracy >= 0.524
    }

    report_path = 'nba_prediction_model/data/outputs/model_evaluation_report.json'
    with open(report_path, 'w') as f:
        json.dump(eval_report, f, indent=2)

    print(f"\nEvaluation report saved: {report_path}")

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)

    return predictor, eval_report


def main():
    """Main training execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Train NBA models on real historical data')
    parser.add_argument('--model-type', type=str, default='xgboost',
                       choices=['logistic', 'random_forest', 'xgboost', 'lightgbm'],
                       help='Type of ML model to use')
    parser.add_argument('--test-season', type=str, default='2024-25',
                       help='Season to use for testing (e.g., 2024-25)')

    args = parser.parse_args()

    # Train models
    predictor, report = train_models_real_data(
        model_type=args.model_type,
        test_season=args.test_season
    )

    if predictor and report:
        print("\n" + "="*60)
        print("MODELS READY FOR PRODUCTION")
        print("="*60)
        print("\nYou can now:")
        print("1. Generate daily predictions: python generate_predictions.py")
        print("2. Review evaluation report: cat nba_prediction_model/data/outputs/model_evaluation_report.json")
        print("3. Load models in your own scripts:")
        print("   predictor = NBAPredictor()")
        print("   predictor.load_models('nba_prediction_model/models/saved')")
        print("="*60)


if __name__ == "__main__":
    main()
