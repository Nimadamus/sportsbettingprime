"""
Daily NBA Prediction Generator
Generates predictions for today's NBA games using trained models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from data.nba_data_collector import NBADataCollector
from utils.feature_engineering import NBAFeatureEngineer
from models.predictor import NBAPredictor


class DailyPredictionGenerator:
    """Generate daily NBA game predictions"""

    def __init__(self, season='2024-25'):
        self.season = season
        self.collector = NBADataCollector(season=season)
        self.engineer = NBAFeatureEngineer()
        self.predictor = NBAPredictor(model_type='xgboost')
        self.predictions = []

    def get_todays_games(self, date=None):
        """
        Get list of games scheduled for today

        Args:
            date: Date string in format 'YYYY-MM-DD', defaults to today

        Returns:
            List of game dictionaries
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # For now, return sample games
        # In production, this would fetch from NBA API or schedule
        sample_games = [
            {
                'date': date,
                'home_team': 'LAL',
                'away_team': 'BOS',
                'game_time': '19:00'
            },
            {
                'date': date,
                'home_team': 'GSW',
                'away_team': 'PHX',
                'game_time': '22:00'
            }
        ]

        return sample_games

    def prepare_game_features(self, home_team, away_team, team_stats_df):
        """
        Prepare features for a specific matchup

        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            team_stats_df: DataFrame with team statistics

        Returns:
            Dictionary with game features
        """
        # Get team IDs
        home_info = self.collector.get_team_by_abbreviation(home_team)
        away_info = self.collector.get_team_by_abbreviation(away_team)

        if not home_info or not away_info:
            print(f"Warning: Could not find team info for {home_team} or {away_team}")
            return None

        # Get team stats from dataframe
        home_stats = team_stats_df[team_stats_df['TEAM_ID'] == home_info['id']]
        away_stats = team_stats_df[team_stats_df['TEAM_ID'] == away_info['id']]

        if home_stats.empty or away_stats.empty:
            print(f"Warning: No stats found for {home_team} or {away_team}")
            return None

        home_stats = home_stats.iloc[0].to_dict()
        away_stats = away_stats.iloc[0].to_dict()

        # Create matchup features
        features = self.engineer.create_matchup_features(home_stats, away_stats)

        # Add situational features (default values for now)
        situational = self.engineer.create_situational_features(
            home_team=home_team,
            away_team=away_team,
            game_date=datetime.now().strftime('%Y-%m-%d'),
            is_back_to_back_home=False,
            is_back_to_back_away=False,
            days_rest_home=1,
            days_rest_away=1
        )

        features.update(situational)

        return features

    def generate_daily_predictions(self, date=None):
        """
        Generate predictions for all games on a given date

        Args:
            date: Date string in format 'YYYY-MM-DD', defaults to today

        Returns:
            DataFrame with predictions
        """
        print("Generating Daily NBA Predictions")
        print("=" * 60)

        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        print(f"Date: {date}")
        print()

        # Get team statistics
        print("Fetching team statistics...")
        team_stats = self.collector.build_comprehensive_dataset()

        if team_stats is None:
            print("Error: Could not fetch team statistics")
            return None

        # Get today's games
        print("Fetching today's games...")
        games = self.get_todays_games(date)
        print(f"Found {len(games)} games scheduled")
        print()

        # Generate predictions for each game
        all_predictions = []

        for game in games:
            home_team = game['home_team']
            away_team = game['away_team']

            print(f"Analyzing: {away_team} @ {home_team}")

            # Prepare features
            features = self.prepare_game_features(home_team, away_team, team_stats)

            if features is None:
                print(f"  Skipping due to missing data")
                continue

            # Generate prediction
            prediction = self.predictor.predict_game(features)

            # Add game info
            prediction['game_date'] = game['date']
            prediction['game_time'] = game['game_time']
            prediction['home_team'] = home_team
            prediction['away_team'] = away_team
            prediction['matchup'] = f"{away_team} @ {home_team}"

            # Calculate expected scores
            if 'predicted_total' in prediction and 'predicted_spread' in prediction:
                total = prediction['predicted_total']
                spread = prediction['predicted_spread']
                prediction['home_expected_score'] = round((total + spread) / 2, 1)
                prediction['away_expected_score'] = round((total - spread) / 2, 1)

            # Add baseline predictions from feature engineer
            prediction['baseline_spread'] = self.engineer.calculate_expected_spread(features)
            prediction['baseline_total'] = self.engineer.calculate_expected_total(features)

            all_predictions.append(prediction)

            # Print prediction summary
            self._print_game_prediction(prediction)
            print()

        # Create predictions dataframe
        if all_predictions:
            predictions_df = pd.DataFrame(all_predictions)
            self.predictions = all_predictions
            return predictions_df
        else:
            print("No predictions generated")
            return None

    def _print_game_prediction(self, prediction):
        """Print formatted prediction for a game"""
        print(f"  Predicted Winner: {prediction['predicted_winner'].upper()}")
        print(f"  Win Probability: {prediction.get('home_win_prob', 0):.1%} (Home) | {prediction.get('away_win_prob', 0):.1%} (Away)")

        if 'predicted_spread' in prediction:
            spread = prediction['predicted_spread']
            if spread > 0:
                print(f"  Predicted Spread: {prediction['home_team']} -{abs(spread)}")
            else:
                print(f"  Predicted Spread: {prediction['away_team']} -{abs(spread)}")

        if 'predicted_total' in prediction:
            print(f"  Predicted Total: {prediction['predicted_total']:.1f}")

        if 'home_expected_score' in prediction:
            print(f"  Expected Score: {prediction['home_team']} {prediction['home_expected_score']} - {prediction['away_team']} {prediction['away_expected_score']}")

    def save_predictions(self, predictions_df, filename=None):
        """
        Save predictions to file

        Args:
            predictions_df: DataFrame with predictions
            filename: Output filename (defaults to date-based name)

        Returns:
            Path to saved file
        """
        if filename is None:
            date = datetime.now().strftime('%Y-%m-%d')
            filename = f"outputs/nba_predictions_{date}.json"

        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)

        # Save as JSON
        predictions_dict = predictions_df.to_dict('records')

        output = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'total_games': len(predictions_dict),
            'predictions': predictions_dict
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Predictions saved to {filename}")
        return filename

    def generate_top_picks(self, predictions_df, min_confidence=0.65):
        """
        Generate top picks based on confidence

        Args:
            predictions_df: DataFrame with predictions
            min_confidence: Minimum confidence threshold

        Returns:
            DataFrame with top picks
        """
        # Filter by confidence
        high_confidence = predictions_df[
            (predictions_df['home_win_prob'] >= min_confidence) |
            (predictions_df['away_win_prob'] >= min_confidence)
        ].copy()

        # Calculate confidence level
        high_confidence['confidence'] = high_confidence.apply(
            lambda row: max(row['home_win_prob'], row['away_win_prob']),
            axis=1
        )

        # Sort by confidence
        high_confidence = high_confidence.sort_values('confidence', ascending=False)

        # Add pick recommendations
        high_confidence['pick'] = high_confidence.apply(
            lambda row: f"{row['home_team']} ML" if row['home_win_prob'] > row['away_win_prob']
            else f"{row['away_team']} ML",
            axis=1
        )

        return high_confidence

    def generate_consensus_integration(self, predictions_df, consensus_file='consensus_library/picks_database.json'):
        """
        Compare model predictions with consensus picks

        Args:
            predictions_df: DataFrame with model predictions
            consensus_file: Path to consensus picks database

        Returns:
            DataFrame with integrated analysis
        """
        # Load consensus data
        try:
            with open(consensus_file, 'r') as f:
                consensus_data = json.load(f)
        except:
            print(f"Could not load consensus data from {consensus_file}")
            return predictions_df

        # Get today's consensus picks
        today = datetime.now().strftime('%Y-%m-%d')
        today_picks = []

        if 'picks_by_date' in consensus_data and today in consensus_data['picks_by_date']:
            today_picks = consensus_data['picks_by_date'][today]

        # Filter NBA picks
        nba_picks = [p for p in today_picks if p.get('sport') == 'NBA']

        # Add consensus info to predictions
        for idx, pred in predictions_df.iterrows():
            matchup = f"{pred['away_team']} @ {pred['home_team']}"

            # Find matching consensus picks
            matching_picks = [p for p in nba_picks if matchup in p.get('matchup', '')]

            if matching_picks:
                predictions_df.at[idx, 'consensus_picks'] = len(matching_picks)
                predictions_df.at[idx, 'consensus_details'] = str(matching_picks)
            else:
                predictions_df.at[idx, 'consensus_picks'] = 0

        return predictions_df


def main():
    """Main execution function"""
    # Initialize generator
    generator = DailyPredictionGenerator(season='2024-25')

    # Note: Before running predictions, you need to train the models
    # For now, we'll show the structure
    print("NBA Daily Prediction Generator")
    print("=" * 60)
    print("\nIMPORTANT: Before generating predictions, you must:")
    print("1. Collect historical game data")
    print("2. Train the prediction models")
    print("3. Save the trained models")
    print("\nAfter training, you can run this script daily to generate predictions.")
    print("\nTo train models, run: python train_model.py")
    print()

    # Example: Generate predictions (requires trained models)
    # predictions = generator.generate_daily_predictions()
    # if predictions is not None:
    #     generator.save_predictions(predictions)
    #     top_picks = generator.generate_top_picks(predictions)
    #     print("\nTop Picks:")
    #     print(top_picks[['matchup', 'pick', 'confidence']])


if __name__ == "__main__":
    main()
