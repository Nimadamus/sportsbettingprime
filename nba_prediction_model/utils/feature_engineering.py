"""
Feature Engineering for NBA Predictions
Transforms raw NBA data into features for machine learning models
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class NBAFeatureEngineer:
    """Create features for NBA game predictions"""

    def __init__(self):
        self.feature_columns = []

    def create_matchup_features(self, home_team_stats, away_team_stats):
        """
        Create features for a specific matchup

        Args:
            home_team_stats: DataFrame row with home team statistics
            away_team_stats: DataFrame row with away team statistics

        Returns:
            Dictionary with matchup features
        """
        features = {}

        # Basic win percentages
        features['home_win_pct'] = home_team_stats.get('W_PCT', 0.5)
        features['away_win_pct'] = away_team_stats.get('W_PCT', 0.5)
        features['win_pct_diff'] = features['home_win_pct'] - features['away_win_pct']

        # Offensive and defensive ratings
        features['home_off_rating'] = home_team_stats.get('OFF_RATING', 110)
        features['away_off_rating'] = away_team_stats.get('OFF_RATING', 110)
        features['home_def_rating'] = home_team_stats.get('DEF_RATING', 110)
        features['away_def_rating'] = away_team_stats.get('DEF_RATING', 110)

        # Net ratings
        features['home_net_rating'] = home_team_stats.get('NET_RATING', 0)
        features['away_net_rating'] = away_team_stats.get('NET_RATING', 0)
        features['net_rating_diff'] = features['home_net_rating'] - features['away_net_rating']

        # Pace
        features['home_pace'] = home_team_stats.get('PACE', 100)
        features['away_pace'] = away_team_stats.get('PACE', 100)
        features['avg_pace'] = (features['home_pace'] + features['away_pace']) / 2
        features['pace_diff'] = features['home_pace'] - features['away_pace']

        # Shooting efficiency
        features['home_ts_pct'] = home_team_stats.get('TS_PCT', 0.55)
        features['away_ts_pct'] = away_team_stats.get('TS_PCT', 0.55)
        features['home_efg_pct'] = home_team_stats.get('EFG_PCT', 0.52)
        features['away_efg_pct'] = away_team_stats.get('EFG_PCT', 0.52)

        # Four Factors - Offense
        features['home_efg'] = home_team_stats.get('EFG_PCT', 0.52)
        features['away_efg'] = away_team_stats.get('EFG_PCT', 0.52)
        features['home_tov_pct'] = home_team_stats.get('TM_TOV_PCT', 0.14)
        features['away_tov_pct'] = away_team_stats.get('TM_TOV_PCT', 0.14)
        features['home_oreb_pct'] = home_team_stats.get('OREB_PCT', 0.25)
        features['away_oreb_pct'] = away_team_stats.get('OREB_PCT', 0.25)
        features['home_fta_rate'] = home_team_stats.get('FTA_RATE', 0.25)
        features['away_fta_rate'] = away_team_stats.get('FTA_RATE', 0.25)

        # Four Factors - Defense
        features['home_opp_efg'] = home_team_stats.get('OPP_EFG_PCT', 0.52)
        features['away_opp_efg'] = away_team_stats.get('OPP_EFG_PCT', 0.52)
        features['home_opp_tov_pct'] = home_team_stats.get('OPP_TOV_PCT', 0.14)
        features['away_opp_tov_pct'] = away_team_stats.get('OPP_TOV_PCT', 0.14)

        # Recent form (last 5 games)
        features['home_last_5_win_pct'] = home_team_stats.get('last_5_win_pct', 0.5)
        features['away_last_5_win_pct'] = away_team_stats.get('last_5_win_pct', 0.5)
        features['home_last_5_point_diff'] = home_team_stats.get('last_5_point_diff', 0)
        features['away_last_5_point_diff'] = away_team_stats.get('last_5_point_diff', 0)

        # Recent form (last 10 games)
        features['home_last_10_win_pct'] = home_team_stats.get('last_10_win_pct', 0.5)
        features['away_last_10_win_pct'] = away_team_stats.get('last_10_win_pct', 0.5)
        features['home_last_10_point_diff'] = home_team_stats.get('last_10_point_diff', 0)
        features['away_last_10_point_diff'] = away_team_stats.get('last_10_point_diff', 0)

        # Momentum features
        features['home_momentum'] = features['home_last_5_win_pct'] - features['home_last_10_win_pct']
        features['away_momentum'] = features['away_last_5_win_pct'] - features['away_last_10_win_pct']

        # Expected points (based on off rating and pace)
        features['home_expected_pts'] = (features['home_off_rating'] * features['avg_pace']) / 100
        features['away_expected_pts'] = (features['away_off_rating'] * features['avg_pace']) / 100

        # Matchup advantages
        features['off_vs_def_home'] = features['home_off_rating'] - features['away_def_rating']
        features['off_vs_def_away'] = features['away_off_rating'] - features['home_def_rating']

        # Scoring and assists
        features['home_pts_per_game'] = home_team_stats.get('PTS', 110)
        features['away_pts_per_game'] = away_team_stats.get('PTS', 110)
        features['home_ast_per_game'] = home_team_stats.get('AST', 25)
        features['away_ast_per_game'] = away_team_stats.get('AST', 25)

        # Rebounding
        features['home_reb_per_game'] = home_team_stats.get('REB', 45)
        features['away_reb_per_game'] = away_team_stats.get('REB', 45)

        # Three-point shooting
        features['home_fg3_pct'] = home_team_stats.get('FG3_PCT', 0.35)
        features['away_fg3_pct'] = away_team_stats.get('FG3_PCT', 0.35)
        features['home_fg3a_per_game'] = home_team_stats.get('FG3A', 35)
        features['away_fg3a_per_game'] = away_team_stats.get('FG3A', 35)

        # PIE (Player Impact Estimate)
        features['home_pie'] = home_team_stats.get('PIE', 0.5)
        features['away_pie'] = away_team_stats.get('PIE', 0.5)

        return features

    def create_situational_features(self, home_team, away_team, game_date=None,
                                   is_back_to_back_home=False, is_back_to_back_away=False,
                                   days_rest_home=1, days_rest_away=1):
        """
        Create situational features (rest, schedule, etc.)

        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            game_date: Date of the game
            is_back_to_back_home: Whether home team is on back-to-back
            is_back_to_back_away: Whether away team is on back-to-back
            days_rest_home: Days of rest for home team
            days_rest_away: Days of rest for away team

        Returns:
            Dictionary with situational features
        """
        features = {}

        # Rest advantage
        features['rest_advantage'] = days_rest_home - days_rest_away
        features['home_days_rest'] = days_rest_home
        features['away_days_rest'] = days_rest_away

        # Back-to-back situations
        features['home_back_to_back'] = 1 if is_back_to_back_home else 0
        features['away_back_to_back'] = 1 if is_back_to_back_away else 0
        features['back_to_back_disadvantage'] = features['home_back_to_back'] - features['away_back_to_back']

        # Home court advantage (baseline)
        features['home_court_advantage'] = 1  # Binary indicator

        # Day of week features (if date provided)
        if game_date:
            if isinstance(game_date, str):
                game_date = datetime.strptime(game_date, '%Y-%m-%d')

            features['day_of_week'] = game_date.weekday()
            features['is_weekend'] = 1 if game_date.weekday() in [4, 5, 6] else 0
            features['month'] = game_date.month

        return features

    def create_feature_dataframe(self, matchups_data):
        """
        Create a complete feature dataframe for multiple matchups

        Args:
            matchups_data: List of dictionaries with matchup information
                Each dict should contain:
                - home_team_stats: DataFrame row or dict
                - away_team_stats: DataFrame row or dict
                - situational_data: Dict with rest/schedule info (optional)

        Returns:
            DataFrame with all features
        """
        all_features = []

        for matchup in matchups_data:
            # Create matchup features
            features = self.create_matchup_features(
                matchup['home_team_stats'],
                matchup['away_team_stats']
            )

            # Add situational features if provided
            if 'situational_data' in matchup:
                sit_features = self.create_situational_features(**matchup['situational_data'])
                features.update(sit_features)

            # Add identifiers
            features['home_team'] = matchup.get('home_team', 'UNK')
            features['away_team'] = matchup.get('away_team', 'UNK')
            features['game_date'] = matchup.get('game_date', '')

            all_features.append(features)

        df = pd.DataFrame(all_features)
        self.feature_columns = [col for col in df.columns if col not in ['home_team', 'away_team', 'game_date']]

        return df

    def get_prediction_features(self, feature_df):
        """
        Get only the features needed for prediction (exclude identifiers)

        Args:
            feature_df: DataFrame with all features

        Returns:
            DataFrame with only prediction features
        """
        return feature_df[self.feature_columns]

    def add_target_variable(self, feature_df, results):
        """
        Add target variables for training

        Args:
            feature_df: DataFrame with features
            results: List of dictionaries with game results
                - home_score: Home team score
                - away_score: Away team score
                - home_win: 1 if home won, 0 otherwise

        Returns:
            DataFrame with target variables added
        """
        df = feature_df.copy()

        results_df = pd.DataFrame(results)

        if 'home_win' in results_df.columns:
            df['home_win'] = results_df['home_win']

        if 'home_score' in results_df.columns and 'away_score' in results_df.columns:
            df['home_score'] = results_df['home_score']
            df['away_score'] = results_df['away_score']
            df['point_differential'] = results_df['home_score'] - results_df['away_score']
            df['total_points'] = results_df['home_score'] + results_df['away_score']

        return df

    def calculate_expected_spread(self, features):
        """
        Calculate expected point spread using a simple model

        Args:
            features: Dictionary or Series with matchup features

        Returns:
            Expected point spread (positive = home favored)
        """
        # Simple baseline model
        home_court = 3.5  # Average home court advantage

        # Net rating differential
        net_rating_component = features.get('net_rating_diff', 0) * 0.4

        # Recent form
        form_component = (features.get('home_last_10_point_diff', 0) -
                         features.get('away_last_10_point_diff', 0)) * 0.2

        # Rest advantage
        rest_component = features.get('rest_advantage', 0) * 0.5

        expected_spread = home_court + net_rating_component + form_component + rest_component

        return round(expected_spread, 1)

    def calculate_expected_total(self, features):
        """
        Calculate expected total points

        Args:
            features: Dictionary or Series with matchup features

        Returns:
            Expected total points
        """
        # Use pace and offensive/defensive ratings
        avg_pace = features.get('avg_pace', 100)
        home_off = features.get('home_off_rating', 110)
        away_off = features.get('away_off_rating', 110)
        home_def = features.get('home_def_rating', 110)
        away_def = features.get('away_def_rating', 110)

        # Expected points
        home_pts = ((home_off + away_def) / 2) * (avg_pace / 100)
        away_pts = ((away_off + home_def) / 2) * (avg_pace / 100)

        expected_total = home_pts + away_pts

        return round(expected_total, 1)


if __name__ == "__main__":
    # Test feature engineering
    engineer = NBAFeatureEngineer()

    # Sample team stats
    home_stats = {
        'W_PCT': 0.650,
        'OFF_RATING': 118.5,
        'DEF_RATING': 112.0,
        'NET_RATING': 6.5,
        'PACE': 102.3,
        'TS_PCT': 0.580,
        'EFG_PCT': 0.545,
        'last_5_win_pct': 0.800,
        'last_10_win_pct': 0.700,
        'last_5_point_diff': 8.2,
        'last_10_point_diff': 5.5,
        'PTS': 116.5,
        'AST': 27.2,
        'REB': 46.8,
        'FG3_PCT': 0.382,
        'PIE': 0.535
    }

    away_stats = {
        'W_PCT': 0.450,
        'OFF_RATING': 113.2,
        'DEF_RATING': 115.8,
        'NET_RATING': -2.6,
        'PACE': 98.7,
        'TS_PCT': 0.560,
        'EFG_PCT': 0.525,
        'last_5_win_pct': 0.400,
        'last_10_win_pct': 0.500,
        'last_5_point_diff': -2.4,
        'last_10_point_diff': -1.8,
        'PTS': 111.2,
        'AST': 24.5,
        'REB': 43.2,
        'FG3_PCT': 0.355,
        'PIE': 0.465
    }

    # Create features
    features = engineer.create_matchup_features(home_stats, away_stats)

    print("Matchup Features:")
    for key, value in features.items():
        print(f"  {key}: {value}")

    # Calculate predictions
    spread = engineer.calculate_expected_spread(features)
    total = engineer.calculate_expected_total(features)

    print(f"\nExpected Spread: {spread} (Home team favored)" if spread > 0 else f"\nExpected Spread: {abs(spread)} (Away team favored)")
    print(f"Expected Total: {total}")
