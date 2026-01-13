#!/usr/bin/env python3
"""
SPORTSBETTINGPRIME SHARP CONSENSUS UPDATE - GitHub Actions Version
===================================================================
Runs on GitHub's servers to update the Sharp Consensus page daily.

WHAT THIS SCRIPT DOES:
1. Scrapes top contestants from Covers.com King of Covers
2. Aggregates their pending picks
3. Groups picks by game (card layout)
4. Updates both sharp-consensus.html and covers-consensus.html
(Git commit/push handled by GitHub Actions workflow)
"""

import os
import re
import json
import shutil
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import time

import requests
from bs4 import BeautifulSoup

# Configuration - auto-detect repo root (works on both Windows local and GitHub Actions)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPT_DIR)  # Go up one level from scripts/ to repo root
# Fallback to Windows path if running outside repo structure
if not os.path.exists(os.path.join(REPO, "covers-consensus.html")):
    REPO = r"C:\Users\Nima\sportsbettingprime"
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
                url = f"https://contests.covers.com/consensus/pickleaders/{sport_code}?totalPicks=1&orderPickBy=Overall&orderBy=Units&pageNum={page}"
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

        print(f"    Found {len(unique)} unique contestants (from {len(contestants)} total)")
        return unique[:100]  # Return top 100 (sharper picks)

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

                    # Determine pick type with better logic
                    if 'over' in pick_lower:
                        pick_type = 'Total (Over)'
                    elif 'under' in pick_lower:
                        pick_type = 'Total (Under)'
                    elif '+ml' in pick_lower or '-ml' in pick_lower or 'ml' in pick_lower:
                        # Explicit moneyline notation
                        pick_type = 'Moneyline'
                    else:
                        # Check for moneyline odds (3-digit numbers like +104, -150)
                        import re as pick_re
                        ml_pattern = pick_re.search(r'[+-]\d{3,}', pick_text)
                        spread_pattern = pick_re.search(r'[+-]\d+\.5', pick_text)

                        if ml_pattern and not spread_pattern:
                            # Has 3+ digit odds = moneyline
                            pick_type = 'Moneyline'
                        elif spread_pattern:
                            # Has .5 = spread
                            pick_type = 'Spread (ATS)'
                        elif '+' in pick_text or '-' in pick_text:
                            # Small numbers without .5 - check if looks like ML odds
                            num_match = pick_re.search(r'[+-](\d+)', pick_text)
                            if num_match:
                                num = int(num_match.group(1))
                                if num >= 100:
                                    # 3-digit number = moneyline
                                    pick_type = 'Moneyline'
                                else:
                                    # Small number = spread
                                    pick_type = 'Spread (ATS)'
                            else:
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
            contestants = self.get_leaderboard(sport_code, pages=2)  # 2 pages = 100 contestants

            picks_found = 0
            for i, contestant in enumerate(contestants[:100], 1):  # Process top 100
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
        """Aggregate picks - return ALL picks with 2+ experts"""
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
        return aggregated  # Return ALL, not limited


def group_picks_by_game(picks):
    """Group picks by matchup, sorted by highest consensus"""
    games = defaultdict(list)

    for pick in picks:
        key = (pick['sport'], pick['matchup'])
        games[key].append(pick)

    # Sort picks within each game by count
    for key in games:
        games[key].sort(key=lambda x: -x['count'])

    # Convert to list and sort by highest consensus pick per game
    game_list = []
    for (sport, matchup), game_picks in games.items():
        top_consensus = max(p['count'] for p in game_picks)
        game_list.append({
            'sport': sport,
            'matchup': matchup,
            'top_consensus': top_consensus,
            'picks': game_picks
        })

    # Sort games by top consensus (highest first)
    game_list.sort(key=lambda x: -x['top_consensus'])

    return game_list


def get_consensus_class(count):
    """Get CSS class based on consensus count"""
    if count >= 10:
        return 'consensus-high'
    elif count >= 5:
        return 'consensus-medium'
    return 'consensus-low'


def get_pick_class(pick_type):
    """Get CSS class based on pick type"""
    if 'Over' in pick_type:
        return 'pick-total-over'
    elif 'Under' in pick_type:
        return 'pick-total-under'
    elif 'Spread' in pick_type:
        return 'pick-spread'
    return 'pick-moneyline'


def get_sport_class(sport):
    """Get CSS class for sport tag"""
    return {
        'NFL': 'sport-nfl',
        'NBA': 'sport-nba',
        'NHL': 'sport-nhl',
        'College Basketball': 'sport-ncaab',
        'College Football': 'sport-ncaaf'
    }.get(sport, 'sport-nfl')


def get_sport_abbrev(sport):
    """Get sport abbreviation"""
    return {
        'College Basketball': 'NCAAB',
        'College Football': 'NCAAF'
    }.get(sport, sport)


def generate_game_cards_html(games):
    """Generate HTML for game cards"""
    cards_html = []

    for game in games:
        picks_html = []
        for pick in game['picks']:
            pick_row = f'''                            <div class="pick-row">
                                <span class="consensus-badge {get_consensus_class(pick['count'])}">{pick['count']}x</span>
                                <span class="pick-type-badge {get_pick_class(pick['pickType'])}">{pick['pickType']}</span>
                                <span class="pick-value">{pick['pick']}</span>
                            </div>'''
            picks_html.append(pick_row)

        card = f'''                <div class="game-card" data-sport="{game['sport']}">
                    <div class="game-header">
                        <span class="sport-tag {get_sport_class(game['sport'])}">{get_sport_abbrev(game['sport'])}</span>
                        <span class="game-matchup">{game['matchup']}</span>
                        <span class="game-top-consensus">{game['top_consensus']}x TOP</span>
                    </div>
                    <div class="game-picks">
{chr(10).join(picks_html)}
                    </div>
                </div>'''
        cards_html.append(card)

    return '\n'.join(cards_html)


def update_covers_consensus(picks):
    """Update covers-consensus.html with game card layout"""
    main_file = os.path.join(REPO, "covers-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] covers-consensus.html not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Group picks by game
    games = group_picks_by_game(picks)

    # Generate game cards HTML
    cards_html = generate_game_cards_html(games)

    # Calculate stats
    total_picks = sum(p['count'] for p in picks)
    num_games = len(games)
    num_sports = len(set(p['sport'] for p in picks))
    top_consensus = max(p['count'] for p in picks) if picks else 0

    # Update date
    html = re.sub(
        r'<div class="update-date">[^<]+</div>',
        f'<div class="update-date">{DATE_FULL}</div>',
        html
    )

    # Update stats
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Total Picks)',
        f'\\g<1>{len(picks)}\\2',
        html
    )
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Games)',
        f'\\g<1>{num_games}\\2',
        html
    )
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Sports)',
        f'\\g<1>{num_sports}\\2',
        html
    )
    html = re.sub(
        r'(<div class="stat-value">)\d+x(</div>\s*<div class="stat-label">Top Consensus)',
        f'\\g<1>{top_consensus}x\\2',
        html
    )

    # Replace games container content
    games_start = html.find('<div class="games-container">')
    if games_start == -1:
        print("  [ERROR] Could not find games-container")
        return False

    # Find the closing div for games-container
    # Count nested divs to find the right closing tag
    pos = games_start + len('<div class="games-container">')
    depth = 1
    while depth > 0 and pos < len(html):
        if html[pos:pos+4] == '<div':
            depth += 1
        elif html[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                break
        pos += 1

    games_end = pos

    # Replace content
    new_games_section = f'''<div class="games-container">
{cards_html}
            </div>'''

    html = html[:games_start] + new_games_section + html[games_end + 6:]

    # Update timestamp
    timestamp = TODAY.strftime('%B %d, %Y at %I:%M %p ET')
    html = re.sub(
        r'<strong>Last Updated:</strong>[^<]+',
        f'<strong>Last Updated:</strong> {timestamp}',
        html
    )

    # Update archive section with current date and recent archives
    current_date_short = TODAY.strftime('%b %d').replace(' 0', ' ').replace('Dec 0', 'Dec ')
    # Generate last 4 days for archive links
    archive_links = []
    for i in range(1, 5):
        prev_date = TODAY - timedelta(days=i)
        date_str = prev_date.strftime('%Y-%m-%d')
        date_short = prev_date.strftime('%b %d').replace(' 0', ' ')
        archive_file = f"covers-consensus-{date_str}.html"
        if os.path.exists(os.path.join(REPO, archive_file)):
            archive_links.append(f'<a href="{archive_file}">{date_short}</a>')

    archive_section = f'''<!-- Archive -->
        <div class="archive-section">
            <h3>Previous Days</h3>
            <div class="archive-links">
                <span class="current">{current_date_short} (Current)</span>
                {chr(10).join('                ' + link for link in archive_links)}
            </div>
        </div>'''

    # Replace existing archive section
    html = re.sub(
        r'<!-- Archive -->.*?</div>\s*</div>\s*</div>\s*<script>',
        archive_section + '\n    </div>\n\n    <script>',
        html,
        flags=re.DOTALL
    )

    # Save updated file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated covers-consensus.html with {len(games)} games, {len(picks)} picks")

    # Create dated archive
    archive_file = os.path.join(REPO, f"covers-consensus-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Created archive: covers-consensus-{DATE_STR}.html")

    return True


def update_sharp_consensus(picks):
    """Update sharp-consensus.html in consensus_library"""
    main_file = os.path.join(CONSENSUS_DIR, "sharp-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] sharp-consensus.html not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Generate JavaScript data
    js_data = json.dumps(picks[:100], indent=8)  # Top 100 for this view

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

    # Update date displays
    html = re.sub(
        r'(December|January|February|March|April|May|June|July|August|September|October|November) \d{2}, 2025',
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

    print(f"  Updated sharp-consensus.html with {min(len(picks), 100)} picks")

    # Create dated archive
    archive_file = os.path.join(CONSENSUS_DIR, f"sharp-consensus-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Created archive: sharp-consensus-{DATE_STR}.html")

    return True


def update_index_html():
    """Update index.html links"""
    index_file = os.path.join(REPO, "index.html")

    if not os.path.exists(index_file):
        return

    # No changes needed - links already point to consensus pages
    print(f"  index.html OK")


def main():
    print("=" * 60)
    print("SPORTSBETTINGPRIME CONSENSUS UPDATE")
    print(f"Date: {DATE_FULL}")
    print(f"Running from: {REPO}")
    print("=" * 60)

    # 1. Scrape data
    print("\n[1] Scraping Covers.com...")
    scraper = CoversConsensusScraper()
    picks = scraper.scrape_all()

    if not picks:
        print("\n[ERROR] No picks found - skipping update")
        return 1

    # 2. Update covers-consensus.html (game cards layout)
    print("\n[2] Updating covers-consensus.html (game cards)...")
    update_covers_consensus(picks)

    # 3. Update sharp-consensus.html (list layout)
    print("\n[3] Updating sharp-consensus.html...")
    if os.path.exists(CONSENSUS_DIR):
        update_sharp_consensus(picks)
    else:
        print(f"  Skipping - consensus_library not found")

    # 4. Update index.html
    print("\n[4] Checking index.html...")
    update_index_html()

    print("\n" + "=" * 60)
    print("CONSENSUS UPDATE COMPLETE!")
    print(f"  - {len(picks)} total consensus picks")
    print(f"  - {len(group_picks_by_game(picks))} games")
    print(f"  - Highest consensus: {max(p['count'] for p in picks)}x")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
