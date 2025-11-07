#!/usr/bin/env python3
"""
Covers Contest Selenium Scraper - Uses Selenium to handle JavaScript-rendered content.
This version can scrape dynamically loaded picks and consensus data.
"""

import json
import time
import re
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional
import argparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not installed. Run: pip install selenium")


class CoversSeleniumScraper:
    """Selenium-based scraper for Covers.com Streak Survivor."""

    BASE_URL = "https://contests.covers.com"
    LEADERBOARD_URL = f"{BASE_URL}/survivor/currentleaderboard"
    SURVIVOR_URL = f"{BASE_URL}/survivor"

    def __init__(self, headless: bool = True, debug: bool = False):
        """
        Initialize the Selenium scraper.

        Args:
            headless: Run browser in headless mode
            debug: Enable debug output
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required. Install with: pip install selenium")

        self.headless = headless
        self.debug = debug
        self.driver = None

    def _init_driver(self):
        """Initialize the Selenium WebDriver."""
        if self.driver:
            return

        print("Initializing browser...")

        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Browser initialized")
        except Exception as e:
            print(f"Error initializing Chrome: {e}")
            print("\nTroubleshooting:")
            print("1. Install Chrome/Chromium browser")
            print("2. Install ChromeDriver: https://chromedriver.chromium.org/")
            print("3. Or run: apt-get install chromium-chromedriver (Linux)")
            raise

    def get_consensus_picks(self) -> List[Dict]:
        """
        Scrape consensus picks from the main Survivor page.

        Returns:
            List of consensus pick dictionaries
        """
        self._init_driver()

        print(f"\nFetching consensus picks from {self.SURVIVOR_URL}...")

        try:
            self.driver.get(self.SURVIVOR_URL)

            # Wait for page to load
            time.sleep(3)

            # Try to wait for consensus data to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass

            picks = []

            # Look for consensus percentages in the page
            page_source = self.driver.page_source

            # Pattern: team names with percentages
            # Common patterns: "Team at 75%", "Team: 75%", "Team - 75%"
            patterns = [
                r'([A-Z][A-Za-z\s]+?)\s+(?:at|:|-)\s+(\d+)%',
                r'>([^<]+?)\s*</.*?>.*?(\d+)%',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                for team, percentage in matches:
                    team = team.strip()
                    # Filter out non-team text
                    if len(team) > 3 and len(team) < 50:
                        picks.append({
                            'team': team,
                            'consensus_percentage': float(percentage),
                            'source': 'selenium'
                        })

            # Deduplicate picks
            seen = {}
            unique_picks = []
            for pick in picks:
                key = pick['team'].lower()
                if key not in seen or pick['consensus_percentage'] > seen[key]['consensus_percentage']:
                    seen[key] = pick
                    if pick not in unique_picks:
                        unique_picks.append(pick)

            # Get unique picks
            unique_picks = list(seen.values())

            print(f"✓ Found {len(unique_picks)} consensus picks")

            return sorted(unique_picks, key=lambda x: x['consensus_percentage'], reverse=True)

        except Exception as e:
            print(f"Error fetching consensus: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return []

    def get_leaderboard(self, top_n: int = 20) -> List[Dict]:
        """
        Scrape the leaderboard to get top contestants.

        Args:
            top_n: Number of top contestants to get

        Returns:
            List of contestant dictionaries
        """
        self._init_driver()

        print(f"\nFetching leaderboard from {self.LEADERBOARD_URL}...")

        try:
            self.driver.get(self.LEADERBOARD_URL)

            # Wait for table to load
            time.sleep(2)

            contestants = []

            # Find table rows
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")

                for i, row in enumerate(rows[1:top_n+1]):  # Skip header
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")

                        if len(cells) < 2:
                            continue

                        # Try to find username link
                        try:
                            link = row.find_element(By.TAG_NAME, "a")
                            username = link.text.strip()
                            profile_url = link.get_attribute('href')
                        except:
                            username = cells[1].text.strip()
                            profile_url = ""

                        streak = cells[2].text.strip() if len(cells) > 2 else "0"
                        best = cells[3].text.strip() if len(cells) > 3 else "0"

                        if username:
                            contestants.append({
                                'rank': i + 1,
                                'username': username,
                                'streak': streak,
                                'best': best,
                                'profile_url': profile_url
                            })

                            print(f"  #{i+1}: {username} (Streak: {streak})")

                    except Exception as e:
                        if self.debug:
                            print(f"  Debug: Error parsing row: {e}")
                        continue

            except Exception as e:
                print(f"Error finding table: {e}")

            print(f"✓ Found {len(contestants)} contestants")
            return contestants

        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            return []

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def run(self, top_n: int = 20, output_file: str = 'covers_consensus.json'):
        """
        Run the full scraping process.

        Args:
            top_n: Number of top contestants to scrape
            output_file: Path to save the consensus JSON
        """
        print("="*60)
        print("Covers Contest Selenium Scraper")
        print("="*60)
        print(f"Target: Top {top_n} contestants + Consensus picks")
        print(f"Output: {output_file}")
        print("="*60)

        try:
            # Get consensus picks
            consensus_picks = self.get_consensus_picks()

            # Get leaderboard
            leaderboard = self.get_leaderboard(top_n=top_n)

            # Create output data
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'consensus_picks': consensus_picks[:20],  # Top 20
                'leaderboard': leaderboard,
                'total_consensus_picks': len(consensus_picks),
                'total_contestants': len(leaderboard)
            }

            # Save to file
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)

            print(f"\n✓ Data saved to {output_file}")

            # Print summary
            print("\n" + "="*60)
            print("CONSENSUS SUMMARY")
            print("="*60)

            for i, pick in enumerate(consensus_picks[:10], 1):
                print(f"{i}. {pick['team']}")
                print(f"   Consensus: {pick['consensus_percentage']}%")
                print()

        finally:
            self.close()


def main():
    """Main entry point for the scraper."""
    if not SELENIUM_AVAILABLE:
        print("\nError: Selenium is not installed.")
        print("\nTo use this scraper, install Selenium:")
        print("  pip install selenium")
        print("\nYou also need Chrome/Chromium and ChromeDriver installed.")
        return

    parser = argparse.ArgumentParser(
        description='Scrape Covers.com Streak Survivor using Selenium (handles JavaScript)'
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
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    scraper = CoversSeleniumScraper(headless=not args.no_headless, debug=args.debug)
    scraper.run(top_n=args.top_n, output_file=args.output)


if __name__ == '__main__':
    main()
