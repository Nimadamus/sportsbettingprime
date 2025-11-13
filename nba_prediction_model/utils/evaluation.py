"""
Model Evaluation and Backtesting Framework
Evaluates prediction accuracy and simulates betting performance
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json


class ModelEvaluator:
    """Evaluate prediction model performance"""

    def __init__(self):
        self.results = []
        self.betting_results = []

    def evaluate_win_predictions(self, predictions, actuals):
        """
        Evaluate win/loss prediction accuracy

        Args:
            predictions: List of predicted winners ('home' or 'away')
            actuals: List of actual winners ('home' or 'away')

        Returns:
            Dictionary with evaluation metrics
        """
        correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
        total = len(predictions)
        accuracy = correct / total if total > 0 else 0

        metrics = {
            'total_games': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'win_rate': accuracy
        }

        return metrics

    def evaluate_spread_predictions(self, predicted_spreads, actual_spreads, threshold=3.0):
        """
        Evaluate point spread prediction accuracy

        Args:
            predicted_spreads: List of predicted point spreads
            actual_spreads: List of actual point spreads
            threshold: Points within this threshold are considered accurate

        Returns:
            Dictionary with evaluation metrics
        """
        predicted = np.array(predicted_spreads)
        actual = np.array(actual_spreads)

        mae = np.mean(np.abs(predicted - actual))
        rmse = np.sqrt(np.mean((predicted - actual) ** 2))

        # Accuracy within threshold
        within_threshold = np.sum(np.abs(predicted - actual) <= threshold)
        accuracy_rate = within_threshold / len(predicted) if len(predicted) > 0 else 0

        # Correlation
        correlation = np.corrcoef(predicted, actual)[0, 1] if len(predicted) > 1 else 0

        metrics = {
            'mae': mae,
            'rmse': rmse,
            'within_threshold': within_threshold,
            'accuracy_rate': accuracy_rate,
            'threshold': threshold,
            'correlation': correlation
        }

        return metrics

    def evaluate_total_predictions(self, predicted_totals, actual_totals, threshold=5.0):
        """
        Evaluate total points prediction accuracy

        Args:
            predicted_totals: List of predicted totals
            actual_totals: List of actual totals
            threshold: Points within this threshold are considered accurate

        Returns:
            Dictionary with evaluation metrics
        """
        predicted = np.array(predicted_totals)
        actual = np.array(actual_totals)

        mae = np.mean(np.abs(predicted - actual))
        rmse = np.sqrt(np.mean((predicted - actual) ** 2))

        # Accuracy within threshold
        within_threshold = np.sum(np.abs(predicted - actual) <= threshold)
        accuracy_rate = within_threshold / len(predicted) if len(predicted) > 0 else 0

        # Over/Under accuracy
        over_under_correct = np.sum((predicted > np.mean(actual)) == (actual > np.mean(actual)))
        over_under_accuracy = over_under_correct / len(predicted) if len(predicted) > 0 else 0

        metrics = {
            'mae': mae,
            'rmse': rmse,
            'within_threshold': within_threshold,
            'accuracy_rate': accuracy_rate,
            'threshold': threshold,
            'over_under_accuracy': over_under_accuracy
        }

        return metrics

    def simulate_betting(self, predictions_df, results_df, unit_size=100, kelly_fraction=0.25):
        """
        Simulate betting performance using predictions

        Args:
            predictions_df: DataFrame with predictions (home_win_prob, predicted_spread, etc.)
            results_df: DataFrame with actual results (home_score, away_score, etc.)
            unit_size: Base betting unit in dollars
            kelly_fraction: Fraction of Kelly criterion to use (0.25 = quarter Kelly)

        Returns:
            Dictionary with betting performance metrics
        """
        bankroll = 10000  # Starting bankroll
        initial_bankroll = bankroll
        bets_placed = []

        for idx, (pred, result) in enumerate(zip(predictions_df.iterrows(), results_df.iterrows())):
            pred_row = pred[1]
            result_row = result[1]

            # Skip if insufficient data
            if pd.isna(pred_row.get('home_win_prob')):
                continue

            # Determine bet based on confidence
            home_win_prob = pred_row['home_win_prob']
            confidence = abs(home_win_prob - 0.5)

            # Only bet if confidence is high enough (>60% or <40%)
            if home_win_prob > 0.60:
                # Bet on home team
                pick = 'home'
                prob = home_win_prob
            elif home_win_prob < 0.40:
                # Bet on away team
                pick = 'away'
                prob = 1 - home_win_prob
            else:
                # Skip low confidence games
                continue

            # Calculate bet size using modified Kelly criterion
            # Assuming -110 odds (1.909 decimal)
            implied_odds = 1.909
            kelly = (prob * implied_odds - 1) / (implied_odds - 1)
            bet_size = max(unit_size, min(bankroll * kelly * kelly_fraction, bankroll * 0.05))

            # Determine actual winner
            actual_winner = 'home' if result_row.get('home_win', 1) == 1 else 'away'

            # Calculate profit/loss
            if pick == actual_winner:
                profit = bet_size * 0.909  # Win at -110 odds
                bankroll += profit
                outcome = 'WIN'
            else:
                profit = -bet_size
                bankroll += profit
                outcome = 'LOSS'

            bet_record = {
                'game_num': idx + 1,
                'pick': pick,
                'confidence': prob,
                'bet_size': bet_size,
                'outcome': outcome,
                'profit': profit,
                'bankroll': bankroll
            }

            bets_placed.append(bet_record)

        # Calculate metrics
        if len(bets_placed) == 0:
            return {'error': 'No bets placed'}

        bets_df = pd.DataFrame(bets_placed)

        wins = len(bets_df[bets_df['outcome'] == 'WIN'])
        losses = len(bets_df[bets_df['outcome'] == 'LOSS'])
        win_rate = wins / len(bets_df) if len(bets_df) > 0 else 0

        total_profit = bankroll - initial_bankroll
        roi = (total_profit / initial_bankroll) * 100

        # Calculate max drawdown
        bets_df['peak'] = bets_df['bankroll'].cummax()
        bets_df['drawdown'] = (bets_df['peak'] - bets_df['bankroll']) / bets_df['peak']
        max_drawdown = bets_df['drawdown'].max() * 100

        metrics = {
            'total_bets': len(bets_df),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'initial_bankroll': initial_bankroll,
            'final_bankroll': bankroll,
            'total_profit': total_profit,
            'roi': roi,
            'max_drawdown': max_drawdown,
            'avg_bet_size': bets_df['bet_size'].mean(),
            'total_wagered': bets_df['bet_size'].sum()
        }

        self.betting_results = bets_df.to_dict('records')

        return metrics

    def analyze_by_spread(self, predictions_df, results_df):
        """
        Analyze performance by spread ranges

        Args:
            predictions_df: DataFrame with predictions
            results_df: DataFrame with actual results

        Returns:
            DataFrame with performance by spread range
        """
        df = predictions_df.copy()
        df['actual_spread'] = results_df['point_differential']

        # Create spread bins
        df['spread_category'] = pd.cut(
            df['predicted_spread'].abs(),
            bins=[0, 3, 7, 10, 100],
            labels=['Pick\'em (0-3)', 'Small (3-7)', 'Medium (7-10)', 'Large (10+)']
        )

        # Calculate accuracy by category
        df['spread_correct'] = (
            (df['predicted_spread'] > 0) == (df['actual_spread'] > 0)
        ).astype(int)

        analysis = df.groupby('spread_category').agg({
            'spread_correct': ['sum', 'count', 'mean']
        }).round(3)

        return analysis

    def generate_report(self, predictions_df, results_df, output_file='evaluation_report.json'):
        """
        Generate comprehensive evaluation report

        Args:
            predictions_df: DataFrame with predictions
            results_df: DataFrame with actual results
            output_file: Path to save report

        Returns:
            Dictionary with complete evaluation
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_games': len(predictions_df)
        }

        # Win predictions
        if 'predicted_winner' in predictions_df.columns and 'actual_winner' in results_df.columns:
            win_metrics = self.evaluate_win_predictions(
                predictions_df['predicted_winner'],
                results_df['actual_winner']
            )
            report['win_predictions'] = win_metrics

        # Spread predictions
        if 'predicted_spread' in predictions_df.columns and 'actual_spread' in results_df.columns:
            spread_metrics = self.evaluate_spread_predictions(
                predictions_df['predicted_spread'],
                results_df['actual_spread']
            )
            report['spread_predictions'] = spread_metrics

        # Total predictions
        if 'predicted_total' in predictions_df.columns and 'actual_total' in results_df.columns:
            total_metrics = self.evaluate_total_predictions(
                predictions_df['predicted_total'],
                results_df['actual_total']
            )
            report['total_predictions'] = total_metrics

        # Betting simulation
        betting_metrics = self.simulate_betting(predictions_df, results_df)
        report['betting_simulation'] = betting_metrics

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Evaluation report saved to {output_file}")

        return report

    def print_summary(self, report):
        """Print evaluation summary"""
        print("\n" + "=" * 60)
        print("MODEL EVALUATION SUMMARY")
        print("=" * 60)

        if 'win_predictions' in report:
            print("\nWin Prediction Performance:")
            print(f"  Accuracy: {report['win_predictions']['accuracy']:.1%}")
            print(f"  Correct: {report['win_predictions']['correct_predictions']}/{report['win_predictions']['total_games']}")

        if 'spread_predictions' in report:
            print("\nSpread Prediction Performance:")
            print(f"  MAE: {report['spread_predictions']['mae']:.2f} points")
            print(f"  RMSE: {report['spread_predictions']['rmse']:.2f} points")
            print(f"  Within 3 pts: {report['spread_predictions']['accuracy_rate']:.1%}")

        if 'total_predictions' in report:
            print("\nTotal Points Prediction Performance:")
            print(f"  MAE: {report['total_predictions']['mae']:.2f} points")
            print(f"  Over/Under Accuracy: {report['total_predictions']['over_under_accuracy']:.1%}")

        if 'betting_simulation' in report and 'error' not in report['betting_simulation']:
            print("\nBetting Simulation Results:")
            print(f"  Win Rate: {report['betting_simulation']['win_rate']:.1%}")
            print(f"  Total Bets: {report['betting_simulation']['total_bets']}")
            print(f"  ROI: {report['betting_simulation']['roi']:.2f}%")
            print(f"  Profit: ${report['betting_simulation']['total_profit']:.2f}")
            print(f"  Max Drawdown: {report['betting_simulation']['max_drawdown']:.2f}%")

        print("=" * 60)


if __name__ == "__main__":
    # Test evaluation with sample data
    print("Model Evaluation Test")

    # Create sample data
    n_games = 100

    predictions = pd.DataFrame({
        'predicted_winner': np.random.choice(['home', 'away'], n_games),
        'home_win_prob': np.random.uniform(0.3, 0.7, n_games),
        'predicted_spread': np.random.uniform(-10, 10, n_games),
        'predicted_total': np.random.uniform(210, 230, n_games)
    })

    results = pd.DataFrame({
        'actual_winner': np.random.choice(['home', 'away'], n_games),
        'home_win': np.random.choice([0, 1], n_games),
        'actual_spread': predictions['predicted_spread'] + np.random.normal(0, 5, n_games),
        'actual_total': predictions['predicted_total'] + np.random.normal(0, 10, n_games),
        'point_differential': predictions['predicted_spread'] + np.random.normal(0, 5, n_games)
    })

    # Evaluate
    evaluator = ModelEvaluator()
    report = evaluator.generate_report(predictions, results, 'outputs/test_evaluation.json')
    evaluator.print_summary(report)
