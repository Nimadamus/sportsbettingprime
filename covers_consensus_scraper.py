#!/usr/bin/env python3
"""
Covers Consensus Scraper - Alternative scraper that gets consensus picks
directly from the Covers.com Streak Survivor main page.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import List, Dict
import argparse


class CoversConsensusScraper:
    """Scraper for Covers.com Streak Survivor consensus picks."""

    BASE_URL = "https://contests.covers.com"
    SURVIVOR_URL = f"{BASE_URL}/survivor"
    CONSENSUS_URL = f"{BASE_URL}/consensus"

    def __init__(self, debug: bool = False):
        """
        Initialize the scraper.

        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_consensus_picks(self, sport: str = 'ALL') -> List[Dict]:
        """
        Scrape consensus picks from the main Survivor page.

        Args:
            sport: Sport filter (ALL, NFL, NBA, NHL, NCF, NCB)

        Returns:
            List of consensus pick dictionaries
        """
        print(f"Fetching consensus picks for {sport}...")

        try:
            response = self.session.get(self.SURVIVOR_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            picks = []

            # Look for consensus data in the page
            # The consensus is often in a table or list structure
            consensus_section = soup.find('div', class_='consensus') or soup.find('section', class_='consensus')

            if consensus_section:
                if self.debug:
                    print("Debug: Found consensus section")

                # Look for team picks with percentages
                pick_items = consensus_section.find_all(['div', 'tr'], class_=re.compile('pick|matchup|game'))

                for item in pick_items:
                    pick = self._extract_consensus_pick(item)
                    if pick:
                        picks.append(pick)

            # Alternative: Look for tables with consensus data
            if not picks:
                tables = soup.find_all('table')

                for table in tables:
                    # Check if this table has percentage data
                    if '%' in table.get_text():
                        rows = table.find_all('tr')

                        for row in rows[1:]:  # Skip header
                            cells = row.find_all(['td', 'th'])

                            if len(cells) >= 2:
                                team_text = cells[0].get_text(strip=True)
                                percentage_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

                                # Look for percentage
                                percentage_match = re.search(r'(\d+(?:\.\d+)?)%', percentage_text)

                                if percentage_match:
                                    picks.append({
                                        'team': team_text,
                                        'consensus_percentage': float(percentage_match.group(1)),
                                        'source': 'consensus_table'
                                    })

            # Also try to extract from any text containing percentages
            if not picks:
                text_content = soup.get_text()

                # Look for patterns like "Team Name at 75%"
                pattern = r'([A-Z][A-Za-z\s]+?)\s+at\s+(\d+)%'
                matches = re.findall(pattern, text_content)

                for team, percentage in matches[:20]:  # Limit to 20
                    picks.append({
                        'team': team.strip(),
                        'consensus_percentage': float(percentage),
                        'source': 'text_extraction'
                    })

            print(f"Found {len(picks)} consensus picks")

            return picks

        except Exception as e:
            print(f"Error fetching consensus: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return []

    def _extract_consensus_pick(self, element) -> Dict:
        """
        Extract consensus pick data from an element.

        Args:
            element: BeautifulSoup element

        Returns:
            Dictionary with pick data or None
        """
        try:
            pick = {}

            # Try to find team name
            team_elem = element.find(class_=re.compile('team|pick'))
            if team_elem:
                pick['team'] = team_elem.get_text(strip=True)

            # Try to find percentage
            percentage_elem = element.find(class_=re.compile('percentage|consensus'))
            if not percentage_elem:
                # Look in any text
                text = element.get_text()
                percentage_match = re.search(r'(\d+(?:\.\d+)?)%', text)
                if percentage_match:
                    pick['consensus_percentage'] = float(percentage_match.group(1))
            else:
                percentage_text = percentage_elem.get_text(strip=True)
                percentage_match = re.search(r'(\d+(?:\.\d+)?)%', percentage_text)
                if percentage_match:
                    pick['consensus_percentage'] = float(percentage_match.group(1))

            # Try to find matchup info
            matchup_elem = element.find(class_=re.compile('matchup|game'))
            if matchup_elem:
                pick['matchup'] = matchup_elem.get_text(strip=True)

            # Try to find sport
            sport_elem = element.find(class_=re.compile('sport|league'))
            if sport_elem:
                pick['sport'] = sport_elem.get_text(strip=True)

            if 'team' in pick or 'matchup' in pick:
                return pick

            return None

        except Exception as e:
            if self.debug:
                print(f"Debug: Error extracting pick: {e}")
            return None

    def get_available_matchups(self) -> List[Dict]:
        """
        Get all available matchups for picking.

        Returns:
            List of matchup dictionaries
        """
        print("Fetching available matchups...")

        try:
            response = self.session.get(self.SURVIVOR_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            matchups = []

            # Look for matchup listings
            matchup_sections = soup.find_all(['div', 'section'], class_=re.compile('matchup|game|pick-option'))

            for section in matchup_sections:
                matchup = {}

                # Extract teams
                teams = section.find_all(class_=re.compile('team'))
                if len(teams) >= 2:
                    matchup['away_team'] = teams[0].get_text(strip=True)
                    matchup['home_team'] = teams[1].get_text(strip=True)

                # Extract time
                time_elem = section.find(class_=re.compile('time|start'))
                if time_elem:
                    matchup['game_time'] = time_elem.get_text(strip=True)

                # Extract sport
                sport_elem = section.find(class_=re.compile('sport|league'))
                if sport_elem:
                    matchup['sport'] = sport_elem.get_text(strip=True)

                if matchup:
                    matchups.append(matchup)

            print(f"Found {len(matchups)} available matchups")
            return matchups

        except Exception as e:
            print(f"Error fetching matchups: {e}")
            return []

    def run(self, output_file: str = 'covers_consensus.json'):
        """
        Run the full scraping process.

        Args:
            output_file: Path to save the consensus JSON
        """
        print("="*60)
        print("Covers Consensus Scraper")
        print("="*60)
        print(f"Output: {output_file}")
        print("="*60)
        print()

        # Get consensus picks
        consensus_picks = self.get_consensus_picks()

        # Get available matchups
        matchups = self.get_available_matchups()

        # Create output data
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'consensus_picks': sorted(consensus_picks, key=lambda x: x.get('consensus_percentage', 0), reverse=True),
            'available_matchups': matchups,
            'total_consensus_picks': len(consensus_picks),
            'total_matchups': len(matchups)
        }

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Consensus saved to {output_file}")

        # Print summary
        print("\n" + "="*60)
        print("CONSENSUS SUMMARY")
        print("="*60)

        for i, pick in enumerate(output_data['consensus_picks'][:15], 1):
            team = pick.get('team', pick.get('matchup', 'Unknown'))
            percentage = pick.get('consensus_percentage', 0)
            print(f"{i}. {team}")
            print(f"   Consensus: {percentage}%")
            print()


def main():
    """Main entry point for the scraper."""
    parser = argparse.ArgumentParser(
        description='Scrape Covers.com Streak Survivor consensus picks'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='covers_consensus.json',
        help='Output file path (default: covers_consensus.json)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    scraper = CoversConsensusScraper(debug=args.debug)
    scraper.run(output_file=args.output)


if __name__ == '__main__':
    main()
