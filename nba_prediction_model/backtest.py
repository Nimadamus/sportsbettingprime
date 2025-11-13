"""
Comprehensive Backtesting Framework
Walk-forward validation with realistic betting simulation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from models.predictor import NBAPredictor
from sklearn.metrics import mean_absolute_error


class BacktestEngine:
    """
    Walk-forward backtesting engine for NBA predictions
    Simulates real betting conditions day-by-day
    """

    def __init__(self, data_file='nba_prediction_model/data/outputs/historical_training_data.csv'):
        """Initialize backtest engine"""
        self.data_file = data_file
        self.df = None
        self.predictor = NBAPredictor(model_type='xgboost')
        self.results = []
        self.bankroll_history = []

    def load_data(self):
        """Load historical game data"""
        self.df = pd.read_csv(self.data_file)
        self.df['game_date'] = pd.to_datetime(self.df['game_date'])
        self.df = self.df.sort_values('game_date').reset_index(drop=True)
        print(f"Loaded {len(self.df)} games")
        print(f"Date range: {self.df['game_date'].min()} to {self.df['game_date'].max()}")
        return self.df

    def simulate_vegas_lines(self, actual_spread, actual_total):
        """
        Simulate realistic Vegas lines based on actual results
        Vegas is typically accurate within 3-4 points

        Args:
            actual_spread: Actual point differential
            actual_total: Actual total points

        Returns:
            Dictionary with simulated Vegas lines
        """
        # Vegas line is correlated with actual but not perfect
        # Add noise to simulate Vegas pricing
        vegas_spread = actual_spread + np.random.normal(0, 3.5)
        vegas_total = actual_total + np.random.normal(0, 6.0)

        return {
            'vegas_spread': round(vegas_spread * 2) / 2,  # Round to nearest 0.5
            'vegas_total': round(vegas_total * 2) / 2
        }

    def get_feature_columns(self):
        """Get feature columns for model"""
        return [
            'home_last_5_win_pct', 'home_last_5_avg_score', 'home_last_5_avg_opp_score', 'home_last_5_point_diff',
            'home_last_10_win_pct', 'home_last_10_avg_score', 'home_last_10_avg_opp_score', 'home_last_10_point_diff',
            'away_last_5_win_pct', 'away_last_5_avg_score', 'away_last_5_avg_opp_score', 'away_last_5_point_diff',
            'away_last_10_win_pct', 'away_last_10_avg_score', 'away_last_10_avg_opp_score', 'away_last_10_point_diff',
            'win_pct_diff_5', 'win_pct_diff_10', 'point_diff_diff',
            'home_rest_days', 'away_rest_days', 'rest_advantage',
            'home_back_to_back', 'away_back_to_back',
            'home_court_advantage'
        ]

    def walk_forward_backtest(self, initial_train_size=500, retrain_frequency=50):
        """
        Walk-forward validation: train on past data, predict future games

        Args:
            initial_train_size: Number of games to use for initial training
            retrain_frequency: Retrain model every N games

        Returns:
            DataFrame with all predictions and results
        """
        print("\n" + "="*60)
        print("WALK-FORWARD BACKTESTING")
        print("="*60)
        print(f"Initial training size: {initial_train_size} games")
        print(f"Retrain frequency: every {retrain_frequency} games")
        print()

        feature_cols = self.get_feature_columns()
        predictions = []
        games_since_retrain = 0

        for idx in range(initial_train_size, len(self.df)):
            # Get training data (all games before this one)
            train_df = self.df.iloc[:idx]

            # Retrain model periodically
            if games_since_retrain == 0 or games_since_retrain >= retrain_frequency:
                if idx % 100 == 0:
                    print(f"Processing game {idx}/{len(self.df)} (retraining)...")

                X_train = train_df[feature_cols]
                y_spread_train = train_df['point_differential']
                y_total_train = train_df['total_points']
                y_win_train = train_df['home_win']

                # Train models (suppress output)
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Quick training without verbose output
                    self.predictor.win_model = self.predictor.build_win_model()
                    self.predictor.spread_model = self.predictor.build_spread_model()
                    self.predictor.total_model = self.predictor.build_total_model()

                    X_train_scaled = self.predictor.scaler.fit_transform(X_train)
                    self.predictor.win_model.fit(X_train_scaled, y_win_train)
                    self.predictor.spread_model.fit(X_train_scaled, y_spread_train)
                    self.predictor.total_model.fit(X_train_scaled, y_total_train)

                games_since_retrain = 0

            # Get test game
            test_game = self.df.iloc[idx]
            X_test = test_game[feature_cols]

            # Make prediction
            pred = self.predictor.predict_game(X_test)

            # Simulate Vegas lines
            vegas_lines = self.simulate_vegas_lines(
                test_game['point_differential'],
                test_game['total_points']
            )

            # Record prediction and actual
            result = {
                'game_date': test_game['game_date'],
                'home_team': test_game['home_team'],
                'away_team': test_game['away_team'],
                'predicted_spread': pred['predicted_spread'],
                'actual_spread': test_game['point_differential'],
                'vegas_spread': vegas_lines['vegas_spread'],
                'predicted_total': pred['predicted_total'],
                'actual_total': test_game['total_points'],
                'vegas_total': vegas_lines['vegas_total'],
                'home_win_prob': pred.get('home_win_prob', 0.5),
                'actual_home_win': test_game['home_win']
            }

            predictions.append(result)
            games_since_retrain += 1

        results_df = pd.DataFrame(predictions)
        print(f"\nBacktest complete: {len(results_df)} predictions made")

        return results_df

    def calculate_betting_results(self, predictions_df, unit_size=100, min_edge=0.5, kelly_fraction=0.25):
        """
        Simulate betting with bankroll management

        Args:
            predictions_df: DataFrame with predictions and Vegas lines
            unit_size: Base bet size in dollars
            min_edge: Minimum edge (points) to place bet
            kelly_fraction: Fraction of Kelly criterion to use

        Returns:
            DataFrame with bet-by-bet results
        """
        print("\n" + "="*60)
        print("SIMULATING BETTING PERFORMANCE")
        print("="*60)
        print(f"Starting bankroll: ${unit_size * 100:,.0f}")
        print(f"Unit size: ${unit_size}")
        print(f"Minimum edge: {min_edge} points")
        print(f"Kelly fraction: {kelly_fraction}")
        print()

        bankroll = unit_size * 100  # Start with 100 units
        initial_bankroll = bankroll
        bets = []

        for idx, row in predictions_df.iterrows():
            # Calculate edge (difference between our prediction and Vegas)
            spread_edge = abs(row['predicted_spread'] - row['vegas_spread'])
            total_edge = abs(row['predicted_total'] - row['vegas_total'])

            # Spread betting
            if spread_edge >= min_edge:
                # Determine which side to bet
                if row['predicted_spread'] < row['vegas_spread']:
                    # Model likes home team more than Vegas
                    pick = 'home'
                    bet_spread = row['vegas_spread']
                    won = (row['actual_spread'] + row['vegas_spread']) > 0
                else:
                    # Model likes away team more than Vegas
                    pick = 'away'
                    bet_spread = row['vegas_spread']
                    won = (row['actual_spread'] + row['vegas_spread']) < 0

                # Bet sizing (Kelly criterion based on edge)
                confidence = min(spread_edge / 10, 0.1)  # Cap at 10%
                bet_size = min(bankroll * confidence * kelly_fraction, bankroll * 0.05)
                bet_size = max(bet_size, unit_size)  # Minimum 1 unit

                # Calculate profit/loss
                if won:
                    profit = bet_size * 0.909  # Win at -110 odds
                    outcome = 'WIN'
                else:
                    profit = -bet_size
                    outcome = 'LOSS'

                bankroll += profit

                bets.append({
                    'game_date': row['game_date'],
                    'matchup': f"{row['away_team']} @ {row['home_team']}",
                    'bet_type': 'spread',
                    'pick': pick,
                    'bet_line': bet_spread,
                    'edge': spread_edge,
                    'bet_size': bet_size,
                    'outcome': outcome,
                    'profit': profit,
                    'bankroll': bankroll,
                    'predicted': row['predicted_spread'],
                    'vegas': row['vegas_spread'],
                    'actual': row['actual_spread']
                })

            # Total betting
            if total_edge >= min_edge * 1.5:  # Higher threshold for totals
                # Determine over/under
                if row['predicted_total'] > row['vegas_total']:
                    pick = 'over'
                    won = row['actual_total'] > row['vegas_total']
                else:
                    pick = 'under'
                    won = row['actual_total'] < row['vegas_total']

                # Bet sizing
                confidence = min(total_edge / 15, 0.08)
                bet_size = min(bankroll * confidence * kelly_fraction, bankroll * 0.04)
                bet_size = max(bet_size, unit_size)

                # Calculate profit/loss
                if won:
                    profit = bet_size * 0.909
                    outcome = 'WIN'
                else:
                    profit = -bet_size
                    outcome = 'LOSS'

                bankroll += profit

                bets.append({
                    'game_date': row['game_date'],
                    'matchup': f"{row['away_team']} @ {row['home_team']}",
                    'bet_type': 'total',
                    'pick': pick,
                    'bet_line': row['vegas_total'],
                    'edge': total_edge,
                    'bet_size': bet_size,
                    'outcome': outcome,
                    'profit': profit,
                    'bankroll': bankroll,
                    'predicted': row['predicted_total'],
                    'vegas': row['vegas_total'],
                    'actual': row['actual_total']
                })

        bets_df = pd.DataFrame(bets)

        if len(bets_df) > 0:
            # Calculate metrics
            wins = len(bets_df[bets_df['outcome'] == 'WIN'])
            losses = len(bets_df[bets_df['outcome'] == 'LOSS'])
            win_rate = wins / len(bets_df)
            total_profit = bankroll - initial_bankroll
            roi = (total_profit / initial_bankroll) * 100

            # Calculate max drawdown
            bets_df['peak'] = bets_df['bankroll'].cummax()
            bets_df['drawdown'] = (bets_df['peak'] - bets_df['bankroll']) / bets_df['peak'] * 100
            max_drawdown = bets_df['drawdown'].max()

            print(f"Total bets placed: {len(bets_df)}")
            print(f"  Spread bets: {len(bets_df[bets_df['bet_type']=='spread'])}")
            print(f"  Total bets: {len(bets_df[bets_df['bet_type']=='total'])}")
            print(f"\nWin rate: {win_rate:.1%} ({wins}W-{losses}L)")
            print(f"Final bankroll: ${bankroll:,.2f}")
            print(f"Total profit: ${total_profit:,.2f}")
            print(f"ROI: {roi:.2f}%")
            print(f"Max drawdown: {max_drawdown:.2f}%")
        else:
            print("No bets placed (insufficient edge)")

        return bets_df

    def generate_backtest_report(self, predictions_df, bets_df, output_file='backtest_report.json'):
        """Generate comprehensive backtest report"""

        # Prediction accuracy
        spread_mae = mean_absolute_error(predictions_df['actual_spread'], predictions_df['predicted_spread'])
        total_mae = mean_absolute_error(predictions_df['actual_total'], predictions_df['predicted_total'])

        # Spread direction accuracy
        predictions_df['spread_correct'] = (
            (predictions_df['predicted_spread'] > 0) == (predictions_df['actual_spread'] > 0)
        )
        spread_direction_acc = predictions_df['spread_correct'].mean()

        # ATS vs Vegas
        predictions_df['beat_vegas_spread'] = np.abs(
            predictions_df['predicted_spread'] - predictions_df['actual_spread']
        ) < np.abs(
            predictions_df['vegas_spread'] - predictions_df['actual_spread']
        )
        beat_vegas_rate = predictions_df['beat_vegas_spread'].mean()

        report = {
            'backtest_date': datetime.now().isoformat(),
            'total_games': len(predictions_df),
            'date_range': {
                'start': predictions_df['game_date'].min().isoformat(),
                'end': predictions_df['game_date'].max().isoformat()
            },
            'prediction_accuracy': {
                'spread_mae': float(spread_mae),
                'total_mae': float(total_mae),
                'spread_direction_accuracy': float(spread_direction_acc),
                'beat_vegas_rate': float(beat_vegas_rate)
            }
        }

        if len(bets_df) > 0:
            wins = len(bets_df[bets_df['outcome'] == 'WIN'])
            losses = len(bets_df[bets_df['outcome'] == 'LOSS'])
            win_rate = wins / len(bets_df)
            initial_bankroll = 10000
            final_bankroll = bets_df.iloc[-1]['bankroll']
            total_profit = final_bankroll - initial_bankroll
            roi = (total_profit / initial_bankroll) * 100

            bets_df['peak'] = bets_df['bankroll'].cummax()
            bets_df['drawdown'] = (bets_df['peak'] - bets_df['bankroll']) / bets_df['peak'] * 100
            max_drawdown = bets_df['drawdown'].max()

            report['betting_performance'] = {
                'total_bets': len(bets_df),
                'wins': wins,
                'losses': losses,
                'win_rate': float(win_rate),
                'initial_bankroll': initial_bankroll,
                'final_bankroll': float(final_bankroll),
                'total_profit': float(total_profit),
                'roi_percent': float(roi),
                'max_drawdown_percent': float(max_drawdown),
                'profitable': total_profit > 0
            }

            # Performance by bet type
            for bet_type in ['spread', 'total']:
                type_bets = bets_df[bets_df['bet_type'] == bet_type]
                if len(type_bets) > 0:
                    type_wins = len(type_bets[type_bets['outcome'] == 'WIN'])
                    type_win_rate = type_wins / len(type_bets)
                    type_profit = type_bets['profit'].sum()

                    report['betting_performance'][f'{bet_type}_bets'] = {
                        'count': len(type_bets),
                        'win_rate': float(type_win_rate),
                        'profit': float(type_profit)
                    }

        # Save report
        output_path = f'nba_prediction_model/data/outputs/{output_file}'
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nBacktest report saved: {output_path}")

        return report


def main():
    """Run comprehensive backtest"""
    print("\n" + "="*60)
    print("NBA PREDICTION MODEL - COMPREHENSIVE BACKTEST")
    print("="*60)

    # Initialize engine
    engine = BacktestEngine()

    # Load data
    engine.load_data()

    # Walk-forward backtest
    predictions_df = engine.walk_forward_backtest(
        initial_train_size=500,
        retrain_frequency=50
    )

    # Save predictions
    predictions_df.to_csv(
        'nba_prediction_model/data/outputs/backtest_predictions.csv',
        index=False
    )
    print(f"Predictions saved: nba_prediction_model/data/outputs/backtest_predictions.csv")

    # Simulate betting
    bets_df = engine.calculate_betting_results(
        predictions_df,
        unit_size=100,
        min_edge=1.0,
        kelly_fraction=0.25
    )

    if len(bets_df) > 0:
        # Save bets
        bets_df.to_csv(
            'nba_prediction_model/data/outputs/backtest_bets.csv',
            index=False
        )
        print(f"Betting results saved: nba_prediction_model/data/outputs/backtest_bets.csv")

    # Generate report
    report = engine.generate_backtest_report(predictions_df, bets_df)

    # Print summary
    print("\n" + "="*60)
    print("BACKTEST SUMMARY")
    print("="*60)
    print(f"\nPrediction Accuracy:")
    print(f"  Spread MAE: {report['prediction_accuracy']['spread_mae']:.2f} points")
    print(f"  Total MAE: {report['prediction_accuracy']['total_mae']:.2f} points")
    print(f"  Beat Vegas: {report['prediction_accuracy']['beat_vegas_rate']:.1%}")

    if 'betting_performance' in report:
        print(f"\nBetting Performance:")
        print(f"  Total Bets: {report['betting_performance']['total_bets']}")
        print(f"  Win Rate: {report['betting_performance']['win_rate']:.1%}")
        print(f"  ROI: {report['betting_performance']['roi_percent']:.2f}%")
        print(f"  Final Profit: ${report['betting_performance']['total_profit']:,.2f}")
        print(f"  Status: {'PROFITABLE ✅' if report['betting_performance']['profitable'] else 'NOT PROFITABLE ❌'}")

    print("="*60)


if __name__ == "__main__":
    main()
