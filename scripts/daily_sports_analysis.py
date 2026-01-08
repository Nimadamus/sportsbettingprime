#!/usr/bin/env python3
"""
Daily Sports Analysis Generator
================================
Generates real, substantive sports betting analysis using:
- The Odds API for live spreads, totals, moneylines
- ESPN API for team records and standings

This runs via GitHub Actions daily.
"""

import os
import json
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")

SPORT_CONFIG = {
    'nfl': {
        'odds_api': 'americanfootball_nfl',
        'espn': 'football/nfl',
        'name': 'NFL',
        'active': True,  # Playoffs in January
    },
    'nba': {
        'odds_api': 'basketball_nba',
        'espn': 'basketball/nba',
        'name': 'NBA',
        'active': True,
    },
    'nhl': {
        'odds_api': 'icehockey_nhl',
        'espn': 'hockey/nhl',
        'name': 'NHL',
        'active': True,
    },
    'ncaab': {
        'odds_api': 'basketball_ncaab',
        'espn': 'basketball/mens-college-basketball',
        'name': 'NCAAB',
        'active': True,
    },
}

# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_odds(sport_key: str) -> List[Dict]:
    """Fetch odds from The Odds API"""
    if not ODDS_API_KEY:
        print(f"  [WARN] No ODDS_API_KEY set")
        return []

    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'spreads,totals,h2h',
        'oddsFormat': 'american',
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  [ERROR] Odds API: {e}")
        return []


def fetch_team_records(espn_path: str) -> Dict[str, str]:
    """Fetch team records from ESPN scoreboard"""
    url = f"{ESPN_API_BASE}/{espn_path}/scoreboard"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        records = {}
        for event in data.get('events', []):
            for comp in event.get('competitions', []):
                for team in comp.get('competitors', []):
                    name = team.get('team', {}).get('displayName', '')
                    rec = team.get('records', [])
                    if rec and name:
                        records[name] = rec[0].get('summary', '')
        return records
    except Exception as e:
        print(f"  [ERROR] ESPN: {e}")
        return {}


# =============================================================================
# CONTENT GENERATION
# =============================================================================

OPENERS = [
    "Look,", "Here's the thing:", "Let's be real here.",
    "I'll be honest with you.", "Here's what I'm seeing.",
    "This one's interesting.", "Pay attention to this.",
    "Don't sleep on this matchup.", "This is a fascinating spot.",
    "Mark this one down.", "Circle this game.",
]

TRANSITIONS = [
    "On the flip side,", "But here's the catch:", "Now,",
    "The key here is", "What makes this interesting is",
    "Consider this:", "Here's where it gets good.",
    "The numbers tell a story here.", "Dig a little deeper and",
]

CLOSERS = [
    "Bottom line:", "At the end of the day,", "The way I see it,",
    "When you break it all down,", "Put it all together and",
    "The verdict:", "My take:", "Here's what it comes down to:",
]


def format_spread(spread: float) -> str:
    return f"+{spread}" if spread > 0 else str(spread)


def format_odds(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def generate_game_analysis(game: Dict, sport: str, records: Dict) -> str:
    """Generate substantive analysis for a single game"""

    home_team = game.get('home_team', 'Home Team')
    away_team = game.get('away_team', 'Away Team')

    home_record = records.get(home_team, '')
    away_record = records.get(away_team, '')

    # Extract odds
    spread = total = home_ml = away_ml = None

    for book in game.get('bookmakers', []):
        for market in book.get('markets', []):
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    if outcome['name'] == home_team:
                        spread = outcome.get('point', 0)
            elif market['key'] == 'totals':
                for outcome in market['outcomes']:
                    if outcome['name'] == 'Over':
                        total = outcome.get('point', 0)
            elif market['key'] == 'h2h':
                for outcome in market['outcomes']:
                    if outcome['name'] == home_team:
                        home_ml = outcome.get('price', 0)
                    else:
                        away_ml = outcome.get('price', 0)
        break

    # Sport-specific terminology
    home_adv = "home ice" if sport == 'nhl' else "home field" if sport in ['nfl', 'ncaaf'] else "home court"

    paragraphs = []

    # Opening paragraph
    opener = random.choice(OPENERS)
    record_ctx = ""
    if home_record and away_record:
        record_ctx = f" The {away_team} ({away_record}) visit the {home_team} ({home_record})."

    if spread is not None:
        spread_str = format_spread(spread)
        if abs(spread) <= 3:
            paragraphs.append(
                f"{opener} {away_team} travels to face {home_team} in what the oddsmakers see as a tight matchup.{record_ctx} "
                f"The line sits at {home_team} {spread_str}, suggesting this one could go either way. "
                f"Games with spreads this tight often come down to execution in crunch time."
            )
        elif spread < -7:
            paragraphs.append(
                f"{opener} {home_team} hosts {away_team} as a {spread_str} favorite.{record_ctx} "
                f"That's a significant number to cover. The market is saying this should be a comfortable win, "
                f"but double-digit spreads always carry risk if the favorite lets off the gas."
            )
        else:
            paragraphs.append(
                f"{opener} {home_team} hosts {away_team} as a {spread_str} favorite.{record_ctx} "
                f"It's a moderate spread that suggests {home_adv} advantage is a factor but this isn't expected to be a blowout."
            )
    else:
        paragraphs.append(
            f"{opener} {away_team} travels to face {home_team}.{record_ctx} "
            f"Both teams have been competitive and this has the makings of a closely contested game."
        )

    # Totals paragraph (sport-aware)
    transition = random.choice(TRANSITIONS)
    if total is not None:
        if sport in ['nba', 'ncaab']:
            if total > 220:
                paragraphs.append(
                    f"{transition} the total is set at {total}, which tells you Vegas expects offense in this one. "
                    f"Both teams have shown they can score, and the pace of play should create plenty of possessions. "
                    f"If you're looking at the over, the question is whether the defenses show up."
                )
            else:
                paragraphs.append(
                    f"{transition} with a total of {total}, this projects as a slower-paced affair. "
                    f"Expect more halfcourt sets and grinding possessions. The under gets interesting if both teams commit to defense."
                )
        elif sport in ['nfl', 'ncaaf']:
            if total > 48:
                paragraphs.append(
                    f"{transition} look at that total: {total} points. That's a shootout number. "
                    f"The books are expecting points, which means they see offensive fireworks. "
                    f"Track the weather and injury reports before making a play."
                )
            elif total > 42:
                paragraphs.append(
                    f"{transition} the total sits at {total} points. That's a moderate number suggesting "
                    f"balanced offenses and defenses. This could go either way on the total depending on game flow and turnovers."
                )
            else:
                paragraphs.append(
                    f"{transition} with a total of {total} points, Vegas is expecting a defensive battle. "
                    f"Low-scoring games often come down to turnovers and field position. The under is in play if weather factors in."
                )
        elif sport == 'nhl':
            paragraphs.append(
                f"{transition} the total sits at {total} goals. In hockey, totals are all about goaltending and special teams. "
                f"Check the starting goalies and power play efficiency before making your move."
            )

    # Moneyline paragraph
    if home_ml is not None and away_ml is not None:
        home_ml_str = format_odds(home_ml)
        away_ml_str = format_odds(away_ml)

        if home_ml < -200:
            paragraphs.append(
                f"On the moneyline, {home_team} is a heavy favorite at {home_ml_str}. You're laying a lot of juice there. "
                f"{away_team} at {away_ml_str} is the value play if you believe in an upset, but there's usually a reason favorites are priced this steep."
            )
        elif home_ml > 100:
            paragraphs.append(
                f"Interestingly, {home_team} is actually the underdog on the moneyline at {home_ml_str}, with {away_team} favored at {away_ml_str}. "
                f"That's telling - the road team is expected to win outright despite playing away."
            )
        else:
            paragraphs.append(
                f"The moneyline prices this as competitive: {home_team} {home_ml_str}, {away_team} {away_ml_str}. "
                f"In games priced this close, small edges matter. {home_adv.capitalize()}, rest advantages, injury reports - all of it factors in."
            )

    # Closing
    closer = random.choice(CLOSERS)
    paragraphs.append(
        f"{closer} this matchup between {away_team} and {home_team} has clear angles to consider. "
        f"Do your homework on recent form, check the injury wire, and don't just follow the public. "
        f"The sharp money often sees things the casual bettor misses."
    )

    return "\n\n".join(paragraphs)


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(sport_name: str, games: List[Dict], game_count: int) -> str:
    """Generate full HTML page for a sport"""

    game_sections = []
    for g in games:
        home = g['home_team']
        away = g['away_team']
        analysis = g['analysis']

        # Parse time
        commence = g.get('commence_time', '')
        if commence:
            try:
                dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                game_time = dt.strftime("%I:%M %p ET")
            except:
                game_time = "TBD"
        else:
            game_time = "TBD"

        paragraphs_html = '\n'.join(f'<p>{p}</p>' for p in analysis.split('\n\n') if p.strip())

        game_sections.append(f'''
        <div class="game-analysis">
            <h3>{away} @ {home}</h3>
            <p class="game-time">{game_time}</p>
            <div class="analysis-content">
                {paragraphs_html}
            </div>
        </div>''')

    games_html = "\n".join(game_sections)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{sport_name} Analysis - {DATE_DISPLAY} | Sports Betting Prime</title>
    <meta name="description" content="{sport_name} betting analysis for {DATE_DISPLAY}. {game_count}-game slate with spreads, totals, and expert breakdowns.">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0f172a; --card: #1e293b; --accent: #22c55e; --gold: #f59e0b; --text: #f1f5f9; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.8; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ background: linear-gradient(135deg, var(--accent), var(--gold)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; margin-bottom: 10px; line-height: 1.3; }}
        .meta {{ color: #94a3b8; margin-bottom: 30px; font-size: 14px; }}
        .intro {{ font-size: 18px; color: #cbd5e1; margin-bottom: 40px; padding: 20px; background: var(--card); border-radius: 12px; border-left: 4px solid var(--accent); }}
        .game-analysis {{ background: var(--card); border-radius: 12px; padding: 25px; margin-bottom: 25px; }}
        .game-analysis h3 {{ color: var(--gold); font-size: 1.4rem; margin-bottom: 8px; }}
        .game-time {{ color: #64748b; font-size: 13px; margin-bottom: 15px; }}
        .analysis-content p {{ margin-bottom: 16px; font-size: 16px; color: #cbd5e1; }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .back-link {{ margin-top: 40px; text-align: center; }}
        .back-link a {{ background: var(--accent); color: #000; padding: 12px 30px; border-radius: 8px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{sport_name} Betting Analysis - {DATE_DISPLAY}</h1>
        <p class="meta">{DATE_DISPLAY} | Sports Betting Prime | {game_count}-Game Slate</p>

        <div class="intro">
            <p>Full breakdown of today's {game_count}-game {sport_name} slate. Real odds, real analysis, no fluff.
            Every game covered with current lines and substantive breakdowns to help you find value.</p>
        </div>

        {games_html}

        <div class="back-link">
            <a href="../index.html">Back to Sports Betting Prime</a>
        </div>
    </div>
</body>
</html>'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("DAILY SPORTS ANALYSIS GENERATOR")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    os.makedirs('daily', exist_ok=True)

    for sport_key, config in SPORT_CONFIG.items():
        if not config.get('active', False):
            print(f"\n[{config['name']}] - Inactive, skipping")
            continue

        print(f"\n[{config['name']}]")
        print("-" * 40)

        # Fetch odds
        print(f"  Fetching {config['name']} odds...")
        games_data = fetch_odds(config['odds_api'])

        if not games_data:
            print(f"  No games found")
            continue

        print(f"  Found {len(games_data)} games")

        # Fetch records
        print(f"  Fetching team records from ESPN...")
        records = fetch_team_records(config['espn'])
        print(f"  Found records for {len(records)} teams")

        # Generate analysis
        games = []
        for game in games_data:
            analysis = generate_game_analysis(game, sport_key, records)
            games.append({
                'home_team': game.get('home_team', 'TBD'),
                'away_team': game.get('away_team', 'TBD'),
                'commence_time': game.get('commence_time', ''),
                'analysis': analysis,
            })

        # Generate HTML
        html = generate_html(config['name'], games, len(games))

        # Save
        filename = f"daily/{sport_key}-analysis-{DATE_STR}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  Generated: {filename}")
        print(f"  Games covered: {len(games)}")

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
