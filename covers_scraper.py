#!/usr/bin/env python3
"""
Covers Contest Scraper - Scrapes top contestants' picks from Covers.com Streak Survivor
and generates a consensus report.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional
import argparse


class CoversContestScraper:
    """Scraper for Covers.com Streak Survivor contest."""

    BASE_URL = "https://contests.covers.com"
    LEADERBOARD_URL = f"{BASE_URL}/survivor/currentleaderboard"

    def __init__(self, top_n: int = 20, delay: float = 1.0, debug: bool = False):
        """
        Initialize the scraper.

        Args:
            top_n: Number of top contestants to scrape
            delay: Delay between requests in seconds (be respectful!)
            debug: Enable debug output
        """
        self.top_n = top_n
        self.delay = delay
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_leaderboard(self) -> List[Dict]:
        """
        Scrape the current leaderboard to get top contestants.

        Returns:
            List of contestant dictionaries with rank, username, streak, and profile URL
        """
        print(f"Fetching leaderboard from {self.LEADERBOARD_URL}...")

        try:
            response = self.session.get(self.LEADERBOARD_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            contestants = []

            # Find the leaderboard table - try multiple approaches
            table = soup.find('table', class_='table') or soup.find('table', class_='leaderboard') or soup.find('table')

            if not table:
                if self.debug:
                    print("Debug: Could not find table. Looking for any tables...")
                    all_tables = soup.find_all('table')
                    print(f"Debug: Found {len(all_tables)} tables total")
                print("Warning: Could not find leaderboard table")
                return contestants

            rows = table.find_all('tr')

            if self.debug:
                print(f"Debug: Found {len(rows)} rows in table")

            # Skip header row (first row)
            data_rows = rows[1:] if len(rows) > 1 else rows

            for i, row in enumerate(data_rows[:self.top_n]):
                cells = row.find_all('td')

                if self.debug and i == 0:
                    print(f"Debug: First row has {len(cells)} cells")

                if len(cells) < 2:
                    continue

                # Try to find username and profile link
                # Look for any link in the row that might be a profile
                all_links = row.find_all('a')

                username = ""
                profile_url = ""

                for link in all_links:
                    href = link.get('href', '')
                    if '/contestant/' in href.lower() or '/survivor/contestant' in href.lower():
                        username = link.text.strip()
                        profile_url = href
                        break

                # If no profile link found, try to get any text that looks like a username
                if not username:
                    # Try second cell (usually where member name is)
                    if len(cells) > 1:
                        username = cells[1].text.strip()
                        # Look for link in this cell
                        member_link = cells[1].find('a')
                        if member_link:
                            profile_url = member_link.get('href', '')

                # Make profile URL absolute
                if profile_url and not profile_url.startswith('http'):
                    profile_url = f"{self.BASE_URL}{profile_url}"

                # Extract streak info (usually in 3rd cell)
                streak = cells[2].text.strip() if len(cells) > 2 else "0"
                best = cells[3].text.strip() if len(cells) > 3 else "0"

                if username or profile_url:
                    contestant = {
                        'rank': i + 1,
                        'username': username if username else f"Contestant_{i+1}",
                        'streak': streak,
                        'best': best,
                        'profile_url': profile_url
                    }

                    contestants.append(contestant)
                    print(f"  #{contestant['rank']}: {contestant['username']} (Streak: {contestant['streak']})")

            print(f"\nFound {len(contestants)} contestants")
            return contestants

        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            return []

    def get_contestant_picks(self, contestant: Dict) -> Dict:
        """
        Scrape picks from a contestant's profile page.

        Args:
            contestant: Contestant dictionary with profile_url

        Returns:
            Dictionary with contestant info and their picks
        """
        profile_url = contestant['profile_url']

        if not profile_url:
            return {'contestant': contestant, 'picks': []}

        print(f"Fetching picks for {contestant['username']}...")

        try:
            time.sleep(self.delay)  # Be respectful

            response = self.session.get(profile_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            picks = []

            # Look for pending picks section
            pending_section = soup.find('div', id='SurvivorPendingPicks') or soup.find('div', class_='pending-picks')

            if pending_section:
                pick_items = pending_section.find_all('div', class_='pick-item') or pending_section.find_all('tr')

                if self.debug:
                    print(f"  Debug: Found {len(pick_items)} pending pick items")

                for item in pick_items:
                    pick_data = self._extract_pick_data(item)
                    if pick_data:
                        picks.append(pick_data)

            # Also check for completed picks section to get recent picks
            completed_section = soup.find('div', id='SurvivorCompletedPicks') or soup.find('div', class_='completed-picks')

            if completed_section:
                pick_items = completed_section.find_all('div', class_='pick-item') or completed_section.find_all('tr')

                if self.debug:
                    print(f"  Debug: Found {len(pick_items)} completed pick items")

                # Get most recent completed picks if no pending picks
                max_completed = 3 if len(picks) == 0 else 1

                for item in pick_items[:max_completed]:
                    pick_data = self._extract_pick_data(item)
                    if pick_data:
                        pick_data['status'] = 'completed'
                        picks.append(pick_data)

            if self.debug and len(picks) > 0:
                print(f"  Debug: Extracted {len(picks)} total picks")

            return {
                'contestant': contestant,
                'picks': picks
            }

        except Exception as e:
            print(f"  Error fetching picks for {contestant['username']}: {e}")
            return {'contestant': contestant, 'picks': []}

    def _extract_pick_data(self, element) -> Optional[Dict]:
        """
        Extract pick data from a pick element.

        Args:
            element: BeautifulSoup element containing pick data

        Returns:
            Dictionary with pick details or None
        """
        try:
            pick = {}

            # Try to extract team name
            team_elem = element.find(class_='team-name') or element.find('strong') or element.find(class_='pick-team')
            if team_elem:
                pick['team'] = team_elem.text.strip()

            # Try to extract matchup info
            matchup_elem = element.find(class_='matchup') or element.find(class_='game-info')
            if matchup_elem:
                pick['matchup'] = matchup_elem.text.strip()

            # Try to extract game time
            time_elem = element.find(class_='game-time') or element.find('time')
            if time_elem:
                pick['game_time'] = time_elem.text.strip()

            # Try to extract sport/league
            league_elem = element.find(class_='league') or element.find(class_='sport')
            if league_elem:
                pick['league'] = league_elem.text.strip()

            # Try to extract pick type (spread, moneyline, etc)
            pick_type_elem = element.find(class_='pick-type') or element.find(class_='bet-type')
            if pick_type_elem:
                pick['pick_type'] = pick_type_elem.text.strip()

            # If we got at least a team name, return the pick
            if 'team' in pick:
                pick['status'] = 'pending'
                return pick

            # Fallback: try to extract any text content
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                pick['raw_text'] = text
                return pick

            return None

        except Exception as e:
            print(f"  Error extracting pick data: {e}")
            return None

    def create_consensus(self, all_picks: List[Dict]) -> Dict:
        """
        Create consensus from all contestants' picks.

        Args:
            all_picks: List of contestant pick dictionaries

        Returns:
            Dictionary with consensus data
        """
        print("\nGenerating consensus...")

        # Count picks by team
        team_counts = defaultdict(int)
        team_details = defaultdict(list)

        total_contestants = len(all_picks)
        contestants_with_picks = 0

        for contestant_data in all_picks:
            contestant = contestant_data['contestant']
            picks = contestant_data['picks']

            if picks:
                contestants_with_picks += 1

                for pick in picks:
                    team = pick.get('team', pick.get('raw_text', 'Unknown'))
                    team_counts[team] += 1

                    team_details[team].append({
                        'contestant': contestant['username'],
                        'rank': contestant['rank'],
                        'streak': contestant['streak'],
                        'pick_info': pick
                    })

        # Create consensus list sorted by popularity
        consensus = []
        for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / contestants_with_picks * 100) if contestants_with_picks > 0 else 0

            consensus.append({
                'team': team,
                'pick_count': count,
                'percentage': round(percentage, 1),
                'picked_by': team_details[team]
            })

        return {
            'timestamp': datetime.now().isoformat(),
            'total_contestants_scraped': total_contestants,
            'contestants_with_picks': contestants_with_picks,
            'consensus': consensus
        }

    def run(self, output_file: str = 'covers_consensus.json'):
        """
        Run the full scraping process.

        Args:
            output_file: Path to save the consensus JSON
        """
        print("="*60)
        print("Covers Contest Scraper")
        print("="*60)
        print(f"Target: Top {self.top_n} contestants")
        print(f"Output: {output_file}")
        print("="*60)
        print()

        # Step 1: Get leaderboard
        contestants = self.get_leaderboard()

        if not contestants:
            print("No contestants found. Exiting.")
            return

        print()
        print("-"*60)

        # Step 2: Get picks from each contestant
        all_picks = []
        for contestant in contestants:
            picks_data = self.get_contestant_picks(contestant)
            all_picks.append(picks_data)

        print()
        print("-"*60)

        # Step 3: Create consensus
        consensus_data = self.create_consensus(all_picks)

        # Step 4: Save to file
        with open(output_file, 'w') as f:
            json.dump(consensus_data, f, indent=2)

        print(f"\n✓ Consensus saved to {output_file}")

        # Print summary
        print("\n" + "="*60)
        print("CONSENSUS SUMMARY")
        print("="*60)

        for i, item in enumerate(consensus_data['consensus'][:10], 1):
            print(f"{i}. {item['team']}")
            print(f"   Picked by: {item['pick_count']}/{consensus_data['contestants_with_picks']} ({item['percentage']}%)")
            print()


def main():
    """Main entry point for the scraper."""
    parser = argparse.ArgumentParser(
        description='Scrape Covers.com Streak Survivor contest and generate pick consensus'
    )
    parser.add_argument(
        '-n', '--top-n',
        type=int,
        default=20,
        help='Number of top contestants to scrape (default: 20)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='covers_consensus.json',
        help='Output file path (default: covers_consensus.json)'
    )
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    scraper = CoversContestScraper(top_n=args.top_n, delay=args.delay, debug=args.debug)
    scraper.run(output_file=args.output)


if __name__ == '__main__':
    main()
