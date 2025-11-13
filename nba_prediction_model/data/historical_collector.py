"""
Historical NBA Game Data Collector
Fetches multiple seasons of game data with team stats at game-time
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2, teamdashboardbygeneralsplits
from nba_api.stats.static import teams
import time
import json
import os


class HistoricalGameCollector:
    """Collect historical NBA games with detailed stats"""

    def __init__(self, seasons=['2021-22', '2022-23', '2023-24', '2024-25']):
        """
        Initialize collector for multiple seasons

        Args:
            seasons: List of season strings in format 'YYYY-YY'
        """
        self.seasons = seasons
        self.teams_data = teams.get_teams()
        self.team_id_map = {team['id']: team for team in self.teams_data}
        self.all_games = []

    def fetch_season_games(self, season):
        """
        Fetch all games for a specific season

        Args:
            season: Season string like '2023-24'

        Returns:
            DataFrame with all games
        """
        print(f"\nFetching games for {season} season...")

        try:
            time.sleep(0.6)  # Rate limiting

            # Get all games for the season
            game_finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                season_type_nullable='Regular Season'
            )

            games = game_finder.get_data_frames()[0]

            # Each game appears twice (once for each team), so deduplicate
            games = games.sort_values('GAME_DATE')
            games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])

            # Create unique game identifiers
            games_unique = []
            seen_games = set()

            for idx, row in games.iterrows():
                game_id = row['GAME_ID']

                if game_id not in seen_games:
                    seen_games.add(game_id)

                    # Find both teams in this game
                    game_rows = games[games['GAME_ID'] == game_id]

                    if len(game_rows) == 2:
                        # Determine home and away
                        team1 = game_rows.iloc[0]
                        team2 = game_rows.iloc[1]

                        # Home team typically appears second in the data
                        if '@' in team1['MATCHUP']:
                            away_row = team1
                            home_row = team2
                        else:
                            home_row = team1
                            away_row = team2

                        game_data = {
                            'game_id': game_id,
                            'game_date': home_row['GAME_DATE'],
                            'season': season,
                            'home_team_id': home_row['TEAM_ID'],
                            'away_team_id': away_row['TEAM_ID'],
                            'home_team': home_row['TEAM_ABBREVIATION'],
                            'away_team': away_row['TEAM_ABBREVIATION'],
                            'home_score': home_row['PTS'],
                            'away_score': away_row['PTS'],
                            'home_win': 1 if home_row['WL'] == 'W' else 0,
                            'total_points': home_row['PTS'] + away_row['PTS'],
                            'point_differential': home_row['PTS'] - away_row['PTS']
                        }

                        games_unique.append(game_data)

            df = pd.DataFrame(games_unique)
            print(f"  Found {len(df)} unique games")

            return df

        except Exception as e:
            print(f"Error fetching {season}: {e}")
            return None

    def calculate_rolling_stats(self, team_id, date, all_games, window=10):
        """
        Calculate team's rolling average stats leading up to a specific date

        Args:
            team_id: NBA team ID
            date: Date of the game
            all_games: DataFrame with all games sorted by date
            window: Number of previous games to average

        Returns:
            Dictionary with rolling stats
        """
        # Get games before this date involving this team
        prior_games = all_games[all_games['game_date'] < date]

        # Get games where team was home or away
        team_home = prior_games[prior_games['home_team_id'] == team_id].copy()
        team_away = prior_games[prior_games['away_team_id'] == team_id].copy()

        # Combine and get last N games
        team_home['team_score'] = team_home['home_score']
        team_home['opp_score'] = team_home['away_score']
        team_home['won'] = team_home['home_win']
        team_home['is_home'] = 1

        team_away['team_score'] = team_away['away_score']
        team_away['opp_score'] = team_away['home_score']
        team_away['won'] = 1 - team_away['home_win']
        team_away['is_home'] = 0

        all_team_games = pd.concat([team_home, team_away]).sort_values('game_date')
        recent_games = all_team_games.tail(window)

        if len(recent_games) == 0:
            # No prior games (season start)
            return {
                'games_played': 0,
                'win_pct': 0.500,
                'avg_score': 110,
                'avg_opp_score': 110,
                'avg_point_diff': 0,
                'home_games': 0,
                'away_games': 0
            }

        stats = {
            'games_played': len(recent_games),
            'win_pct': recent_games['won'].mean(),
            'avg_score': recent_games['team_score'].mean(),
            'avg_opp_score': recent_games['opp_score'].mean(),
            'avg_point_diff': (recent_games['team_score'] - recent_games['opp_score']).mean(),
            'home_games': recent_games['is_home'].sum(),
            'away_games': len(recent_games) - recent_games['is_home'].sum()
        }

        return stats

    def calculate_rest_days(self, team_id, date, all_games):
        """
        Calculate days of rest before this game

        Args:
            team_id: NBA team ID
            date: Date of current game
            all_games: DataFrame with all games

        Returns:
            Number of rest days
        """
        prior_games = all_games[all_games['game_date'] < date]

        team_games = prior_games[
            (prior_games['home_team_id'] == team_id) |
            (prior_games['away_team_id'] == team_id)
        ].sort_values('game_date')

        if len(team_games) == 0:
            return 7  # Start of season, assume week of rest

        last_game_date = team_games.iloc[-1]['game_date']
        rest_days = (date - last_game_date).days

        return rest_days

    def build_training_dataset(self):
        """
        Build complete training dataset with features for each game

        Returns:
            DataFrame ready for ML training
        """
        print("\n" + "="*60)
        print("BUILDING HISTORICAL TRAINING DATASET")
        print("="*60)

        # Fetch all seasons
        all_games = []
        for season in self.seasons:
            season_games = self.fetch_season_games(season)
            if season_games is not None:
                all_games.append(season_games)
                time.sleep(1)  # Be nice to API

        if not all_games:
            print("ERROR: No game data collected")
            return None

        # Combine all seasons
        df = pd.concat(all_games, ignore_index=True)
        df = df.sort_values('game_date').reset_index(drop=True)

        print(f"\nTotal games collected: {len(df)}")
        print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

        # Calculate features for each game
        print("\nCalculating rolling stats and features for each game...")
        print("(This will take several minutes...)")

        training_data = []

        for idx, game in df.iterrows():
            if idx % 100 == 0:
                print(f"  Processing game {idx}/{len(df)}...")

            # Calculate stats for both teams entering this game
            home_stats_5 = self.calculate_rolling_stats(
                game['home_team_id'], game['game_date'], df, window=5
            )
            home_stats_10 = self.calculate_rolling_stats(
                game['home_team_id'], game['game_date'], df, window=10
            )

            away_stats_5 = self.calculate_rolling_stats(
                game['away_team_id'], game['game_date'], df, window=5
            )
            away_stats_10 = self.calculate_rolling_stats(
                game['away_team_id'], game['game_date'], df, window=10
            )

            # Calculate rest
            home_rest = self.calculate_rest_days(
                game['home_team_id'], game['game_date'], df
            )
            away_rest = self.calculate_rest_days(
                game['away_team_id'], game['game_date'], df
            )

            # Build feature row
            features = {
                # Game identifiers
                'game_id': game['game_id'],
                'game_date': game['game_date'],
                'season': game['season'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],

                # Home team recent form (last 5 games)
                'home_last_5_win_pct': home_stats_5['win_pct'],
                'home_last_5_avg_score': home_stats_5['avg_score'],
                'home_last_5_avg_opp_score': home_stats_5['avg_opp_score'],
                'home_last_5_point_diff': home_stats_5['avg_point_diff'],

                # Home team recent form (last 10 games)
                'home_last_10_win_pct': home_stats_10['win_pct'],
                'home_last_10_avg_score': home_stats_10['avg_score'],
                'home_last_10_avg_opp_score': home_stats_10['avg_opp_score'],
                'home_last_10_point_diff': home_stats_10['avg_point_diff'],

                # Away team recent form (last 5 games)
                'away_last_5_win_pct': away_stats_5['win_pct'],
                'away_last_5_avg_score': away_stats_5['avg_score'],
                'away_last_5_avg_opp_score': away_stats_5['avg_opp_score'],
                'away_last_5_point_diff': away_stats_5['avg_point_diff'],

                # Away team recent form (last 10 games)
                'away_last_10_win_pct': away_stats_10['win_pct'],
                'away_last_10_avg_score': away_stats_10['avg_score'],
                'away_last_10_avg_opp_score': away_stats_10['avg_opp_score'],
                'away_last_10_point_diff': away_stats_10['avg_point_diff'],

                # Differential features
                'win_pct_diff_5': home_stats_5['win_pct'] - away_stats_5['win_pct'],
                'win_pct_diff_10': home_stats_10['win_pct'] - away_stats_10['win_pct'],
                'point_diff_diff': home_stats_10['avg_point_diff'] - away_stats_10['avg_point_diff'],

                # Rest and schedule
                'home_rest_days': home_rest,
                'away_rest_days': away_rest,
                'rest_advantage': home_rest - away_rest,
                'home_back_to_back': 1 if home_rest <= 1 else 0,
                'away_back_to_back': 1 if away_rest <= 1 else 0,

                # Home court
                'home_court_advantage': 1,

                # Games played (for data quality)
                'home_games_played': home_stats_10['games_played'],
                'away_games_played': away_stats_10['games_played'],

                # TARGET VARIABLES
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'home_win': game['home_win'],
                'total_points': game['total_points'],
                'point_differential': game['point_differential']
            }

            training_data.append(features)

        training_df = pd.DataFrame(training_data)

        # Filter out games at start of season with insufficient data
        print("\nFiltering games with insufficient prior data...")
        initial_count = len(training_df)
        training_df = training_df[
            (training_df['home_games_played'] >= 5) &
            (training_df['away_games_played'] >= 5)
        ]
        print(f"  Removed {initial_count - len(training_df)} games (both teams need 5+ prior games)")
        print(f"  Final training set: {len(training_df)} games")

        return training_df

    def save_dataset(self, df, filename='historical_training_data.csv'):
        """Save training dataset to CSV"""
        output_dir = 'nba_prediction_model/data/outputs'
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)

        print(f"\n{'='*60}")
        print(f"Dataset saved to: {filepath}")
        print(f"{'='*60}")
        print(f"\nDataset Summary:")
        print(f"  Total games: {len(df)}")
        print(f"  Seasons: {df['season'].unique()}")
        print(f"  Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print(f"  Features: {len(df.columns)} columns")
        print(f"\nTarget variable distributions:")
        print(f"  Home win rate: {df['home_win'].mean():.3f}")
        print(f"  Avg point differential: {df['point_differential'].mean():.2f}")
        print(f"  Avg total points: {df['total_points'].mean():.2f}")

        return filepath


def main():
    """Main execution - collect historical data"""

    print("\n" + "="*60)
    print("NBA HISTORICAL DATA COLLECTION")
    print("="*60)
    print("\nThis will collect 3-4 seasons of NBA games (~3,500 games)")
    print("Estimated time: 10-15 minutes due to API rate limiting")
    print("="*60)

    # Initialize collector for recent seasons
    seasons = ['2021-22', '2022-23', '2023-24', '2024-25']
    collector = HistoricalGameCollector(seasons=seasons)

    # Build complete training dataset
    training_data = collector.build_training_dataset()

    if training_data is not None:
        # Save to CSV
        filepath = collector.save_dataset(training_data)

        print("\n" + "="*60)
        print("SUCCESS - Historical data collection complete!")
        print("="*60)
        print(f"\nNext steps:")
        print(f"1. Examine the data: pandas.read_csv('{filepath}')")
        print(f"2. Run model training: python train_model.py --use-real-data")
        print(f"3. Evaluate performance: Check MAE on spread/total predictions")
        print("="*60)
    else:
        print("\nERROR: Data collection failed")


if __name__ == "__main__":
    main()
