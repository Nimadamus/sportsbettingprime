#!/usr/bin/env python3
"""
Claude API Content Generator
=============================
Generates REAL human-written sports analysis by sending game data to Claude API.
Claude writes the actual content - not templates, not fill-in-the-blank.

This produces the same quality as when a human asks Claude to write analysis manually.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")

SPORT_CONFIG = {
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
    'nfl': {
        'odds_api': 'americanfootball_nfl',
        'espn': 'football/nfl',
        'name': 'NFL',
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


def format_game_data(game: Dict, records: Dict) -> Dict:
    """Format game data for Claude prompt"""
    home_team = game.get('home_team', 'Home Team')
    away_team = game.get('away_team', 'Away Team')

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

    return {
        'home_team': home_team,
        'away_team': away_team,
        'home_record': records.get(home_team, 'N/A'),
        'away_record': records.get(away_team, 'N/A'),
        'spread': spread,
        'total': total,
        'home_ml': home_ml,
        'away_ml': away_ml,
        'commence_time': game.get('commence_time', ''),
    }


# =============================================================================
# CLAUDE API CONTENT GENERATION
# =============================================================================

def call_claude_api(prompt: str, max_tokens: int = 4000) -> str:
    """Call Claude API to generate content"""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data['content'][0]['text']
    except Exception as e:
        print(f"  [ERROR] Claude API: {e}")
        raise


def generate_sport_analysis(sport_name: str, games_data: List[Dict]) -> str:
    """Generate full analysis for a sport using Claude API"""

    # Build the prompt with all game data
    games_info = ""
    for i, game in enumerate(games_data, 1):
        spread_str = f"{game['spread']:+.1f}" if game['spread'] else "N/A"
        home_ml_str = f"{game['home_ml']:+d}" if game['home_ml'] else "N/A"
        away_ml_str = f"{game['away_ml']:+d}" if game['away_ml'] else "N/A"

        games_info += f"""
Game {i}: {game['away_team']} @ {game['home_team']}
- Away Record: {game['away_record']}
- Home Record: {game['home_record']}
- Spread: {game['home_team']} {spread_str}
- Total: {game['total']}
- Moneyline: {game['home_team']} {home_ml_str}, {game['away_team']} {away_ml_str}
"""

    prompt = f"""You are a veteran sports betting analyst writing for Sports Betting Prime. Today is {DATE_DISPLAY}.

Write analysis for today's {sport_name} slate. Here are the games and betting lines:

{games_info}

REQUIREMENTS:
1. Write 3-4 paragraphs of UNIQUE analysis for EACH game
2. Be conversational and human - use contractions, casual language, strong opinions
3. Reference the ACTUAL spreads, totals, and moneylines provided
4. Reference the ACTUAL team records provided
5. Each game's analysis must be DIFFERENT - vary your angles, don't repeat the same structure
6. Include specific insights: pace, matchup advantages, situational factors, public vs sharp money angles
7. End each game with a unique angle or key factor to watch (NOT the same closing for every game)
8. Write like you're talking to a fellow bettor, not writing a formal report
9. NO placeholder text, NO "coming soon", NO generic filler
10. Be opinionated - take stances on value, traps, and sharp angles

Format your response as HTML with each game in this structure:
<div class="game-analysis">
    <h3>[Away Team] @ [Home Team]</h3>
    <p class="game-time">[Time from data] ET</p>
    <div class="analysis-content">
        <p>[Paragraph 1]</p>
        <p>[Paragraph 2]</p>
        <p>[Paragraph 3]</p>
        <p>[Paragraph 4 - unique closing angle]</p>
    </div>
</div>

Write the analysis now. Remember: this should read like a human expert wrote it, not an AI."""

    return call_claude_api(prompt)


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_full_html(sport_name: str, analysis_html: str, game_count: int) -> str:
    """Wrap Claude's analysis in full HTML page"""

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

        {analysis_html}

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
    print("CLAUDE API CONTENT GENERATOR")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("\n[ERROR] ANTHROPIC_API_KEY not set. Cannot generate content.")
        print("Please add ANTHROPIC_API_KEY to GitHub secrets.")
        return

    os.makedirs('daily', exist_ok=True)

    for sport_key, config in SPORT_CONFIG.items():
        if not config.get('active', False):
            print(f"\n[{config['name']}] - Inactive, skipping")
            continue

        print(f"\n[{config['name']}]")
        print("-" * 40)

        # Fetch odds
        print(f"  Fetching {config['name']} odds...")
        games_raw = fetch_odds(config['odds_api'])

        if not games_raw:
            print(f"  No games found")
            continue

        print(f"  Found {len(games_raw)} games")

        # Fetch records
        print(f"  Fetching team records from ESPN...")
        records = fetch_team_records(config['espn'])
        print(f"  Found records for {len(records)} teams")

        # Format game data
        games_data = [format_game_data(g, records) for g in games_raw]

        # Generate content via Claude API
        print(f"  Calling Claude API to generate analysis...")
        try:
            analysis_html = generate_sport_analysis(config['name'], games_data)
            print(f"  Claude generated {len(analysis_html)} characters of analysis")
        except Exception as e:
            print(f"  [ERROR] Failed to generate: {e}")
            continue

        # Generate full HTML
        html = generate_full_html(config['name'], analysis_html, len(games_data))

        # Save
        filename = f"daily/{sport_key}-analysis-{DATE_STR}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  Generated: {filename}")
        print(f"  Games covered: {len(games_data)}")

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
