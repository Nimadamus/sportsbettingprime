"""
NBA Data Collector
Fetches team and player statistics from NBA API and other sources
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    teamgamelog,
    leaguestandings,
    playergamelogs,
    teamdashboardbygeneralsplits
)
from nba_api.stats.static import teams
import time
import json


class NBADataCollector:
    """Collects and processes NBA team and game data"""

    def __init__(self, season='2024-25'):
        """
        Initialize the NBA data collector

        Args:
            season: NBA season in format 'YYYY-YY' (e.g., '2024-25')
        """
        self.season = season
        self.teams_data = teams.get_teams()
        self.team_id_map = {team['id']: team for team in self.teams_data}
        self.team_abbr_map = {team['abbreviation']: team for team in self.teams_data}

    def get_team_stats(self, measure_type='Advanced', per_mode='PerGame'):
        """
        Fetch current season team statistics

        Args:
            measure_type: 'Base', 'Advanced', 'Misc', 'Four Factors', 'Scoring', 'Opponent', 'Defense'
            per_mode: 'Totals', 'PerGame', 'Per36', 'Per100Possessions'

        Returns:
            DataFrame with team statistics
        """
        try:
            time.sleep(0.6)  # Rate limiting
            team_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=self.season,
                measure_type_detailed_defense=measure_type,
                per_mode_detailed=per_mode
            )
            df = team_stats.get_data_frames()[0]
            return df
        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return None

    def get_team_game_log(self, team_id, season=None):
        """
        Get game log for a specific team

        Args:
            team_id: NBA team ID
            season: Season in format 'YYYY-YY', defaults to self.season

        Returns:
            DataFrame with team's game log
        """
        if season is None:
            season = self.season

        try:
            time.sleep(0.6)  # Rate limiting
            game_log = teamgamelog.TeamGameLog(
                team_id=team_id,
                season=season
            )
            df = game_log.get_data_frames()[0]
            return df
        except Exception as e:
            print(f"Error fetching game log for team {team_id}: {e}")
            return None

    def get_team_splits(self, team_id, measure_type='Advanced'):
        """
        Get team performance splits (home/away, etc.)

        Args:
            team_id: NBA team ID
            measure_type: Type of stats to retrieve

        Returns:
            DataFrame with team splits
        """
        try:
            time.sleep(0.6)  # Rate limiting
            splits = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
                team_id=team_id,
                season=self.season,
                measure_type_detailed_defense=measure_type
            )
            df = splits.get_data_frames()[0]
            return df
        except Exception as e:
            print(f"Error fetching splits for team {team_id}: {e}")
            return None

    def get_league_standings(self):
        """
        Get current league standings

        Returns:
            DataFrame with standings
        """
        try:
            time.sleep(0.6)  # Rate limiting
            standings = leaguestandings.LeagueStandings(
                season=self.season
            )
            df = standings.get_data_frames()[0]
            return df
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return None

    def get_recent_form(self, team_id, last_n_games=10):
        """
        Calculate team's recent form (win %, point differential, etc.)

        Args:
            team_id: NBA team ID
            last_n_games: Number of recent games to analyze

        Returns:
            Dictionary with recent form metrics
        """
        game_log = self.get_team_game_log(team_id)

        if game_log is None or len(game_log) == 0:
            return None

        # Get last N games
        recent_games = game_log.head(last_n_games)

        # Calculate metrics
        wins = (recent_games['WL'] == 'W').sum()
        win_pct = wins / len(recent_games)

        avg_pts = recent_games['PTS'].mean()
        avg_pts_allowed = recent_games['PTS'].mean() - recent_games['PLUS_MINUS'].mean()
        point_diff = recent_games['PLUS_MINUS'].mean()

        avg_fg_pct = recent_games['FG_PCT'].mean()
        avg_fg3_pct = recent_games['FG3_PCT'].mean()
        avg_ft_pct = recent_games['FT_PCT'].mean()

        return {
            'team_id': team_id,
            f'last_{last_n_games}_wins': wins,
            f'last_{last_n_games}_win_pct': win_pct,
            f'last_{last_n_games}_avg_pts': avg_pts,
            f'last_{last_n_games}_avg_pts_allowed': avg_pts_allowed,
            f'last_{last_n_games}_point_diff': point_diff,
            f'last_{last_n_games}_fg_pct': avg_fg_pct,
            f'last_{last_n_games}_fg3_pct': avg_fg3_pct,
            f'last_{last_n_games}_ft_pct': avg_ft_pct
        }

    def get_team_by_abbreviation(self, abbr):
        """Get team info by abbreviation"""
        return self.team_abbr_map.get(abbr)

    def get_team_by_id(self, team_id):
        """Get team info by ID"""
        return self.team_id_map.get(team_id)

    def build_comprehensive_dataset(self):
        """
        Build a comprehensive dataset with all team statistics

        Returns:
            DataFrame with comprehensive team data
        """
        print("Fetching team statistics...")

        # Get various stat types
        base_stats = self.get_team_stats(measure_type='Base')
        advanced_stats = self.get_team_stats(measure_type='Advanced')
        four_factors = self.get_team_stats(measure_type='Four Factors')

        if base_stats is None or advanced_stats is None:
            print("Failed to fetch basic statistics")
            return None

        # Merge datasets
        df = base_stats.merge(
            advanced_stats[['TEAM_ID', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'PACE',
                           'PIE', 'TS_PCT', 'EFG_PCT']],
            on='TEAM_ID',
            how='left'
        )

        if four_factors is not None:
            df = df.merge(
                four_factors[['TEAM_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT',
                             'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']],
                on='TEAM_ID',
                how='left',
                suffixes=('', '_ff')
            )

        # Get recent form for each team
        print("Calculating recent form metrics...")
        recent_forms = []
        for team_id in df['TEAM_ID'].unique():
            form_5 = self.get_recent_form(team_id, last_n_games=5)
            form_10 = self.get_recent_form(team_id, last_n_games=10)

            if form_5 and form_10:
                combined_form = {**form_5, **form_10}
                recent_forms.append(combined_form)

        if recent_forms:
            form_df = pd.DataFrame(recent_forms)
            df = df.merge(form_df, left_on='TEAM_ID', right_on='team_id', how='left')

        # Add standings
        standings = self.get_league_standings()
        if standings is not None:
            df = df.merge(
                standings[['TeamID', 'PlayoffRank', 'ConferenceRecord', 'DivisionRank']],
                left_on='TEAM_ID',
                right_on='TeamID',
                how='left'
            )

        return df

    def save_dataset(self, df, filename='nba_team_data.csv'):
        """Save dataset to CSV"""
        filepath = f"data/outputs/{filename}"
        df.to_csv(filepath, index=False)
        print(f"Dataset saved to {filepath}")
        return filepath


if __name__ == "__main__":
    # Test the data collector
    collector = NBADataCollector(season='2024-25')

    # Build comprehensive dataset
    dataset = collector.build_comprehensive_dataset()

    if dataset is not None:
        print(f"\nDataset shape: {dataset.shape}")
        print(f"Columns: {list(dataset.columns)}")
        print("\nSample data:")
        print(dataset[['TEAM_NAME', 'W', 'L', 'W_PCT', 'OFF_RATING', 'DEF_RATING', 'NET_RATING']].head())

        # Save dataset
        collector.save_dataset(dataset)
