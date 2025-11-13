"""
Collect Historical Vegas Lines
Sources: The Odds API, Sports Reference, or manual data entry
"""

import pandas as pd
import requests
import json
from datetime import datetime
import time


class VegasLineCollector:
    """
    Collect historical Vegas betting lines
    """

    def __init__(self, api_key=None):
        """
        Initialize collector

        Args:
            api_key: The Odds API key (get free key at the-odds-api.com)
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

    def fetch_historical_odds(self, sport='basketball_nba', date=None):
        """
        Fetch historical odds from The Odds API

        Note: Free tier has limited historical data
        Premium required for full historical access

        Args:
            sport: Sport key
            date: ISO date string

        Returns:
            List of games with odds
        """
        if not self.api_key:
            print("ERROR: No API key provided")
            print("\nTo get historical Vegas lines:")
            print("1. Sign up at https://the-odds-api.com")
            print("2. Get API key (free tier available)")
            print("3. Pass key to VegasLineCollector(api_key='your_key')")
            return None

        endpoint = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'spreads,totals',
            'oddsFormat': 'american'
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            print(f"Fetched odds for {len(data)} games")

            return self.parse_odds_response(data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching odds: {e}")
            return None

    def parse_odds_response(self, data):
        """Parse odds API response into structured format"""
        games = []

        for game in data:
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            commence_time = game.get('commence_time')

            # Get best odds across books
            spread_odds = []
            total_odds = []

            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                spread_odds.append({
                                    'book': bookmaker['title'],
                                    'spread': outcome['point'],
                                    'price': outcome['price']
                                })
                    elif market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            total_odds.append({
                                'book': bookmaker['title'],
                                'total': outcome['point'],
                                'type': outcome['name'],
                                'price': outcome['price']
                            })

            if spread_odds:
                # Use consensus spread (average)
                avg_spread = sum(o['spread'] for o in spread_odds) / len(spread_odds)
            else:
                avg_spread = None

            if total_odds:
                avg_total = sum(o['total'] for o in total_odds) / len(total_odds)
            else:
                avg_total = None

            games.append({
                'commence_time': commence_time,
                'home_team': home_team,
                'away_team': away_team,
                'vegas_spread': avg_spread,
                'vegas_total': avg_total,
                'num_books': len(game.get('bookmakers', []))
            })

        return pd.DataFrame(games)

    def load_manual_lines(self, csv_file):
        """
        Load manually collected Vegas lines from CSV

        CSV format:
        game_date,home_team,away_team,vegas_spread,vegas_total

        Args:
            csv_file: Path to CSV with historical lines

        Returns:
            DataFrame with Vegas lines
        """
        try:
            df = pd.read_csv(csv_file)
            df['game_date'] = pd.to_datetime(df['game_date'])
            print(f"Loaded {len(df)} historical lines from {csv_file}")
            return df
        except FileNotFoundError:
            print(f"File not found: {csv_file}")
            return None

    def create_sample_lines_template(self, output_file='vegas_lines_template.csv'):
        """Create a template CSV for manual entry of Vegas lines"""
        template = pd.DataFrame({
            'game_date': ['2024-01-15', '2024-01-15'],
            'home_team': ['LAL', 'BOS'],
            'away_team': ['GSW', 'MIA'],
            'vegas_spread': [-5.5, -7.0],
            'vegas_total': [225.5, 218.0],
            'source': ['Draftkings', 'FanDuel']
        })

        template.to_csv(output_file, index=False)
        print(f"Template created: {output_file}")
        print("\nFill in with historical Vegas lines, then load with:")
        print(f"  collector.load_manual_lines('{output_file}')")

        return output_file


def merge_with_predictions(predictions_df, vegas_lines_df):
    """
    Merge model predictions with actual Vegas lines

    Args:
        predictions_df: DataFrame with model predictions
        vegas_lines_df: DataFrame with Vegas lines

    Returns:
        Merged DataFrame ready for backtesting
    """
    # Normalize team names for matching
    predictions_df['game_date'] = pd.to_datetime(predictions_df['game_date'])
    vegas_lines_df['game_date'] = pd.to_datetime(vegas_lines_df['game_date'])

    # Merge on date and teams
    merged = predictions_df.merge(
        vegas_lines_df[['game_date', 'home_team', 'away_team', 'vegas_spread', 'vegas_total']],
        on=['game_date', 'home_team', 'away_team'],
        how='left',
        suffixes=('_model', '_vegas')
    )

    print(f"\nMerge Results:")
    print(f"  Total predictions: {len(predictions_df)}")
    print(f"  Matched with Vegas lines: {merged['vegas_spread'].notna().sum()}")
    print(f"  Missing Vegas lines: {merged['vegas_spread'].isna().sum()}")

    return merged


def main():
    """
    Main execution - collect Vegas lines
    """
    print("="*60)
    print("VEGAS LINE COLLECTION")
    print("="*60)

    collector = VegasLineCollector()

    print("\nOPTIONS FOR GETTING HISTORICAL VEGAS LINES:")
    print("\n1. The Odds API (Recommended)")
    print("   - Sign up: https://the-odds-api.com")
    print("   - Free tier: 500 requests/month")
    print("   - Historical data requires premium")
    print("   - Cost: ~$100/month for full historical")

    print("\n2. Sports Reference / Basketball Reference")
    print("   - Manual scraping possible")
    print("   - Historical lines available for recent seasons")
    print("   - Free but requires scraping")

    print("\n3. Manual Entry")
    print("   - Create CSV template")
    print("   - Fill in historical lines")
    print("   - Good for validation/testing")

    print("\n4. Paid Data Providers")
    print("   - SportsDataIO: $500-1000/month")
    print("   - SportRadar: Enterprise pricing")
    print("   - Most comprehensive historical data")

    print("\n" + "="*60)
    print("CREATING MANUAL ENTRY TEMPLATE")
    print("="*60)

    collector.create_sample_lines_template()

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Get API key from the-odds-api.com OR")
    print("2. Fill in vegas_lines_template.csv manually OR")
    print("3. Scrape Basketball Reference for historical lines")
    print("\nOnce you have Vegas lines, run:")
    print("  python backtest.py --vegas-lines vegas_lines.csv")


if __name__ == "__main__":
    main()
