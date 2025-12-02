#!/usr/bin/env python3
"""
SPORTSBETTINGPRIME SHARP CONSENSUS UPDATE - GitHub Actions Version
===================================================================
Runs on GitHub's servers to update the Sharp Consensus page daily.

WHAT THIS SCRIPT DOES:
1. Scrapes top contestants from Covers.com King of Covers
2. Aggregates their pending picks
3. Creates a dated archive page
4. Updates the main sharp-consensus.html with new data
(Git commit/push handled by GitHub Actions workflow)
"""

import os
import re
import json
import shutil
from datetime import datetime, timedelta
from collections import Counter
import time

import requests
from bs4 import BeautifulSoup

# Configuration
REPO = os.getcwd()
CONSENSUS_DIR = os.path.join(REPO, "consensus_library")
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
DATE_FULL = TODAY.strftime("%A, %B %d, %Y")


class CoversConsensusScraper:
    """Scrape Covers.com King of Covers contests"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        self.sports = {
            'nfl': 'NFL',
            'nba': 'NBA',
            'nhl': 'NHL',
            'ncaab': 'College Basketball',
            'ncaaf': 'College Football',
        }

        self.all_picks = []
        self.pick_counter = Counter()

    def get_leaderboard(self, sport_code, pages=2):
        """Fetch top contestants from leaderboard"""
        print(f"\n  Fetching {self.sports.get(sport_code, sport_code)} leaderboard...")
        contestants = []

        for page in range(1, pages + 1):
            try:
                url = f"https://contests.covers.com/consensus/pickleaders/{sport_code}?page={page}"
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                table = soup.find('table')
                if not table:
                    continue

                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    link = cells[1].find('a')
                    if not link:
                        continue

                    name = link.text.strip()
                    profile_url = link.get('href', '')
                    if not profile_url.startswith('http'):
                        profile_url = 'https://contests.covers.com' + profile_url

                    units = cells[2].text.strip()
                    record = cells[3].text.strip()

                    try:
                        units_value = float(units.replace('+', '').replace(',', ''))
                    except:
                        units_value = 0.0

                    contestants.append({
                        'name': name,
                        'profile_url': profile_url,
                        'units': units,
                        'units_value': units_value,
                        'record': record,
                        'sport': self.sports.get(sport_code, sport_code)
                    })

                time.sleep(0.5)

            except Exception as e:
                print(f"    Error fetching page {page}: {e}")

        # Sort by units and dedupe
        seen = set()
        unique = []
        for c in sorted(contestants, key=lambda x: -x['units_value']):
            if c['profile_url'] not in seen:
                seen.add(c['profile_url'])
                unique.append(c)

        print(f"    Found {len(unique)} contestants")
        return unique[:100]

    def get_contestant_picks(self, contestant, sport):
        """Get pending picks for a contestant"""
        try:
            response = self.session.get(contestant['profile_url'], timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            picks = []
            pending_table = soup.find('table', class_='cmg_contests_pendingpicks')

            if not pending_table:
                return []

            for row in pending_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue

                # Skip finished games
                if len(cells) > 1:
                    score = cells[1].text.strip()
                    if score and any(c.isdigit() for c in score):
                        continue

                # Extract teams
                teams_text = cells[0].text.strip().split('\n')
                teams = [t.strip() for t in teams_text if t.strip()]
                away = teams[0] if teams else ''
                home = teams[1] if len(teams) > 1 else ''

                # Extract picks
                picks_cell = cells[3] if len(cells) > 3 else None
                if not picks_cell:
                    continue

                for div in picks_cell.find_all('div'):
                    pick_text = div.text.strip()
                    if not pick_text or len(pick_text) < 3:
                        continue

                    pick_lower = pick_text.lower()
                    if 'over' in pick_lower:
                        pick_type = 'Total (Over)'
                    elif 'under' in pick_lower:
                        pick_type = 'Total (Under)'
                    elif '+' in pick_text or '-' in pick_text:
                        pick_type = 'Spread (ATS)'
                    else:
                        pick_type = 'Moneyline'

                    picks.append({
                        'sport': sport,
                        'matchup': f"{away} @ {home}",
                        'pick_type': pick_type,
                        'pick_text': pick_text
                    })

            return picks

        except Exception as e:
            return []

    def scrape_all(self):
        """Scrape all sports"""
        print("\n" + "=" * 60)
        print("SCRAPING COVERS.COM CONSENSUS DATA")
        print("=" * 60)

        for sport_code, sport_name in self.sports.items():
            print(f"\n[{sport_name}]")
            contestants = self.get_leaderboard(sport_code)

            picks_found = 0
            for i, contestant in enumerate(contestants[:50], 1):
                picks = self.get_contestant_picks(contestant, sport_name)

                if picks:
                    picks_found += len(picks)
                    self.all_picks.extend(picks)

                    for pick in picks:
                        key = f"{pick['sport']}|{pick['matchup']}|{pick['pick_type']}|{pick['pick_text']}"
                        self.pick_counter[key] += 1

                time.sleep(0.3)

            print(f"    Total picks found: {picks_found}")

        return self.aggregate_picks()

    def aggregate_picks(self):
        """Aggregate and filter picks"""
        aggregated = []

        for pick_key, count in self.pick_counter.most_common():
            if count < 2:
                continue

            parts = pick_key.split('|')
            if len(parts) == 4:
                sport, matchup, pick_type, pick_text = parts
                aggregated.append({
                    'count': count,
                    'sport': sport,
                    'matchup': matchup,
                    'pickType': pick_type,
                    'pick': pick_text
                })

        aggregated.sort(key=lambda x: -x['count'])
        print(f"\n[OK] Aggregated {len(aggregated)} consensus picks")
        return aggregated[:100]


def update_sharp_consensus(picks):
    """Update the sharp-consensus.html with new data"""
    main_file = os.path.join(CONSENSUS_DIR, "sharp-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] Main file not found: {main_file}")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Generate JavaScript data
    js_data = json.dumps(picks, indent=8)

    # Replace consensusData
    pattern = r'const consensusData = \[[\s\S]*?\];'
    replacement = f'const consensusData = {js_data};'
    html = re.sub(pattern, replacement, html)

    # Update title and meta
    html = re.sub(
        r'<title>[^<]*</title>',
        f'<title>Sharp Consensus Picks Today - {DATE_DISPLAY} | NFL NBA NHL Expert Picks</title>',
        html
    )

    # Update date in header
    html = re.sub(
        r'December \d{2}, 2025',
        DATE_DISPLAY,
        html
    )

    # Update canonical URL
    html = re.sub(
        r'sharp-consensus-\d{4}-\d{2}-\d{2}\.html',
        f'sharp-consensus-{DATE_STR}.html',
        html
    )

    # Update stats
    max_consensus = max(p['count'] for p in picks) if picks else 0
    sports_covered = len(set(p['sport'] for p in picks))

    html = re.sub(
        r'<div class="stat-number" id="topConsensus">\d+</div>',
        f'<div class="stat-number" id="topConsensus">{max_consensus}</div>',
        html
    )
    html = re.sub(
        r'<div class="stat-number" id="sportCount">\d+</div>',
        f'<div class="stat-number" id="sportCount">{sports_covered}</div>',
        html
    )

    # Save main file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated sharp-consensus.html with {len(picks)} picks")

    # Create dated archive
    archive_file = os.path.join(CONSENSUS_DIR, f"sharp-consensus-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Created archive: sharp-consensus-{DATE_STR}.html")

    return True


def update_index_html():
    """Update index.html to point to new consensus page"""
    index_file = os.path.join(REPO, "index.html")

    if not os.path.exists(index_file):
        return

    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update link to sharp consensus
    content = re.sub(
        r'href="consensus_library/sharp-consensus-\d{4}-\d{2}-\d{2}\.html[^"]*"',
        f'href="consensus_library/sharp-consensus-{DATE_STR}.html?v={DATE_STR.replace("-", "")}"',
        content
    )

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Updated index.html")


def main():
    print("=" * 60)
    print("SPORTSBETTINGPRIME SHARP CONSENSUS UPDATE")
    print(f"Date: {DATE_FULL}")
    print(f"Running from: {REPO}")
    print("=" * 60)

    # Check if consensus_library exists
    if not os.path.exists(CONSENSUS_DIR):
        print(f"[ERROR] Consensus library not found: {CONSENSUS_DIR}")
        return 1

    # 1. Scrape data
    print("\n[1] Scraping Covers.com...")
    scraper = CoversConsensusScraper()
    picks = scraper.scrape_all()

    if not picks:
        print("\n[ERROR] No picks found - skipping update")
        return 1

    # 2. Update sharp-consensus.html
    print("\n[2] Updating sharp-consensus.html...")
    if not update_sharp_consensus(picks):
        return 1

    # 3. Update index.html
    print("\n[3] Updating index.html...")
    update_index_html()

    print("\n" + "=" * 60)
    print("SHARP CONSENSUS UPDATE COMPLETE!")
    print(f"  - {len(picks)} consensus picks")
    print(f"  - Highest consensus: {max(p['count'] for p in picks)}x")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
