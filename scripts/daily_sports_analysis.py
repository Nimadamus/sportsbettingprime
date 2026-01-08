#!/usr/bin/env python3
"""
Daily Sports Analysis Generator
================================
Generates REAL, HUMAN-SOUNDING, CONVERSATIONAL sports betting analysis using:
- The Odds API for live spreads, totals, moneylines
- ESPN API for team records, standings, team stats, and recent form

This runs via GitHub Actions daily.

ENHANCED: January 2026 - More varied content, player mentions, deeper analysis
"""

import os
import json
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONFIGURATION
# =============================================================================

ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
MONTH_DAY = TODAY.strftime("%B %d")

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


def fetch_team_data(espn_path: str) -> Tuple[Dict[str, str], Dict[str, Dict]]:
    """Fetch team records AND additional stats from ESPN scoreboard"""
    url = f"{ESPN_API_BASE}/{espn_path}/scoreboard"

    records = {}
    team_stats = {}

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        for event in data.get('events', []):
            for comp in event.get('competitions', []):
                for team in comp.get('competitors', []):
                    name = team.get('team', {}).get('displayName', '')
                    abbrev = team.get('team', {}).get('abbreviation', '')
                    rec = team.get('records', [])

                    if name:
                        # Basic record
                        if rec:
                            records[name] = rec[0].get('summary', '')

                        # Extended stats if available
                        stats_data = {}
                        for stat in team.get('statistics', []):
                            stat_name = stat.get('name', '')
                            stat_val = stat.get('displayValue', '')
                            if stat_name and stat_val:
                                stats_data[stat_name] = stat_val

                        # Leaders if available
                        leaders = team.get('leaders', [])
                        if leaders:
                            stats_data['leaders'] = leaders

                        team_stats[name] = {
                            'abbrev': abbrev,
                            'home_away': team.get('homeAway', ''),
                            'stats': stats_data
                        }

        return records, team_stats
    except Exception as e:
        print(f"  [ERROR] ESPN: {e}")
        return {}, {}


def fetch_team_records(espn_path: str) -> Dict[str, str]:
    """Fetch team records from ESPN scoreboard (backward compatible)"""
    records, _ = fetch_team_data(espn_path)
    return records


# =============================================================================
# CONTENT GENERATION
# =============================================================================

OPENERS = [
    "Look,", "Here's the thing:", "Let's be real here.",
    "I'll be honest with you.", "Here's what I'm seeing.",
    "This one's interesting.", "Pay attention to this.",
    "Don't sleep on this matchup.", "This is a fascinating spot.",
    "Mark this one down.", "Circle this game.",
    "This has trap game written all over it.",
    "The market might be sleeping on this one.",
    "There's value hiding in plain sight here.",
]

TRANSITIONS = [
    "On the flip side,", "But here's the catch:", "Now,",
    "The key here is", "What makes this interesting is",
    "Consider this:", "Here's where it gets good.",
    "The numbers tell a story here.", "Dig a little deeper and",
    "But wait—", "Here's where it gets tricky:",
    "The flip side of this coin:", "Diving deeper,",
]

# MANY varied closing angles - each game gets a UNIQUE closer
CLOSING_ANGLES = [
    # Value-focused
    "If you're hunting value, the {} line deserves a hard look. The market may be overreacting to recent results.",
    "Smart money knows that lines like these don't come around often. The {} situation here is worth a close look.",
    "There's an argument for both sides here, but the {} number is where I'd focus my attention.",

    # Trend-focused
    "Recent trends favor {}, but trends don't win games—execution does. Watch the first quarter closely.",
    "The {} pattern here is hard to ignore. Sometimes the simplest analysis is the best.",
    "History says {} has an edge in spots like this. The question is whether this game follows the script.",

    # Matchup-focused
    "This comes down to the {} matchup. That's where games like this are won or lost.",
    "Whoever controls the {} will likely cover. It's that simple in this type of game.",
    "The key matchup to watch is {} vs their counterpart. That battle could swing the outcome.",

    # Situational
    "Situational spot for {} here. Fatigue, travel, and schedule all factor in when making your pick.",
    "The schedule makers did {} no favors with this spot. Factor that into your analysis.",
    "This is a classic letdown/lookahead spot for {}. The market doesn't always account for human nature.",

    # Analytical
    "When you strip away the noise, this is a {} game. Don't overthink it.",
    "The numbers point one direction, the eye test points another. In spots like these, I trust {}.",
    "Advanced metrics favor {}, but this is where context matters more than spreadsheets.",

    # Contrarian
    "The public will be heavy on {} here. That alone makes the other side interesting.",
    "Everyone's talking about {}, which makes me want to look the other way.",
    "The sharps have been fading {} in spots like this. There's a reason for that.",

    # Game-specific insights
    "This has the makings of a {} game. Position yourself accordingly.",
    "If this turns into a {} affair, the edge shifts considerably.",
    "The game script will determine everything. If {} controls pace, adjust your expectations.",
]

def get_unique_closer(game_num: int, home: str, away: str, sport: str) -> str:
    """Get a unique closing paragraph for each game"""
    # Use game number to ensure variety
    angle = CLOSING_ANGLES[game_num % len(CLOSING_ANGLES)]

    # Sport-specific fill words
    if sport == 'nba':
        fills = ['spread', 'total', 'pace', 'rebounding', 'three-point shooting', 'defensive',
                 'tempo', 'back-to-back', 'home court', 'offensive efficiency']
    elif sport == 'nhl':
        fills = ['puck line', 'total', 'goaltending', 'special teams', 'home ice',
                 'power play', 'defensive structure', 'back-to-back', 'travel', 'physical']
    elif sport in ['nfl', 'ncaaf']:
        fills = ['spread', 'total', 'rushing', 'turnover', 'red zone', 'third down',
                 'time of possession', 'weather', 'home field', 'defensive front']
    else:
        fills = ['spread', 'total', home, away, 'underdog', 'favorite']

    # Pick a contextual fill based on game number
    fill = fills[game_num % len(fills)]

    return angle.format(fill)


def format_spread(spread: float) -> str:
    return f"+{spread}" if spread > 0 else str(spread)


def format_odds(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def generate_game_analysis(game: Dict, sport: str, records: Dict, game_num: int = 0) -> str:
    """Generate substantive, human-sounding analysis for a single game"""

    home_team = game.get('home_team', 'Home Team')
    away_team = game.get('away_team', 'Away Team')

    home_record = records.get(home_team, '')
    away_record = records.get(away_team, '')

    # Parse records for W-L analysis
    home_wins = home_losses = away_wins = away_losses = 0
    if home_record and '-' in home_record:
        try:
            parts = home_record.split('-')
            home_wins, home_losses = int(parts[0]), int(parts[1])
        except:
            pass
    if away_record and '-' in away_record:
        try:
            parts = away_record.split('-')
            away_wins, away_losses = int(parts[0]), int(parts[1])
        except:
            pass

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

    # Opening paragraph - with record context woven in naturally
    opener = OPENERS[game_num % len(OPENERS)]

    # Build a more analytical opening based on records
    if home_record and away_record:
        # Analyze the matchup based on records
        if home_wins > 0 and away_wins > 0:
            home_pct = home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0
            away_pct = away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0

            if home_pct > 0.6 and away_pct < 0.4:
                # Dominant home team vs struggling visitor
                if spread is not None:
                    spread_str = format_spread(spread)
                    paragraphs.append(
                        f"{opener} {home_team} ({home_record}) has been rolling, and they host a {away_team} squad ({away_record}) "
                        f"that's been searching for answers. The {spread_str} spread reflects that disparity, but sometimes the market "
                        f"overreacts to recent form. {away_team} has nothing to lose here, which can make them dangerous."
                    )
                else:
                    paragraphs.append(
                        f"{opener} {home_team} ({home_record}) has been one of the better teams we've seen, hosting {away_team} ({away_record}) "
                        f"who has been scuffling. The question isn't whether {home_team} is better—they clearly are. "
                        f"It's whether the line properly accounts for just how much better."
                    )
            elif away_pct > 0.6 and home_pct < 0.4:
                # Strong road team at a weak home team
                if spread is not None:
                    spread_str = format_spread(spread)
                    paragraphs.append(
                        f"{opener} {away_team} ({away_record}) travels to face a struggling {home_team} ({home_record}). "
                        f"The {spread_str} line suggests the books know what's coming. Road favorites can be tricky to back, "
                        f"but {away_team}'s form makes them hard to fade right now."
                    )
                else:
                    paragraphs.append(
                        f"{opener} {away_team} ({away_record}) brings their strong record on the road against {home_team} ({home_record}). "
                        f"The visitors are clearly the better team on paper. The {home_adv} factor is real, but is it enough to overcome this talent gap?"
                    )
            elif abs(home_pct - away_pct) < 0.1:
                # Evenly matched teams
                if spread is not None and abs(spread) <= 4:
                    spread_str = format_spread(spread)
                    paragraphs.append(
                        f"{opener} Two similarly matched teams square off here. {away_team} ({away_record}) visits {home_team} ({home_record}) "
                        f"in what should be a coin-flip game. The {spread_str} line suggests {home_adv} is the difference-maker. "
                        f"In games this close, execution and momentum swings decide everything."
                    )
                else:
                    paragraphs.append(
                        f"{opener} {away_team} ({away_record}) and {home_team} ({home_record}) have had nearly identical seasons. "
                        f"This is the type of game that comes down to who wants it more on that particular night. "
                        f"Don't expect either team to run away with this one."
                    )
            else:
                # Default with spread context
                if spread is not None:
                    spread_str = format_spread(spread)
                    paragraphs.append(
                        f"{opener} {away_team} ({away_record}) travels to face {home_team} ({home_record}). "
                        f"The line sits at {home_team} {spread_str}. Both teams have had their moments this season, "
                        f"and this matchup has more intrigue than the records might suggest."
                    )
                else:
                    paragraphs.append(
                        f"{opener} {away_team} ({away_record}) visits {home_team} ({home_record}) in an intriguing matchup. "
                        f"The records tell one story, but the eye test often tells another. This is a game worth watching closely."
                    )
        else:
            # Fallback if we can't parse records
            if spread is not None:
                spread_str = format_spread(spread)
                paragraphs.append(
                    f"{opener} {away_team} travels to face {home_team}. The {spread_str} spread sets the stage for what should be "
                    f"a competitive matchup. Both teams have shown flashes this season, and this game could go either way."
                )
            else:
                paragraphs.append(
                    f"{opener} {away_team} visits {home_team} in what should be an interesting contest. "
                    f"Both squads are looking to build momentum heading into the next stretch of games."
                )
    else:
        # No records available - simpler opening
        if spread is not None:
            spread_str = format_spread(spread)
            paragraphs.append(
                f"{opener} {away_team} travels to {home_team}, where the home team is a {spread_str} favorite. "
                f"The market has spoken, but markets can be wrong. Let's dig into what makes this matchup tick."
            )
        else:
            paragraphs.append(
                f"{opener} {away_team} heads to {home_team} for this {MONTH_DAY} clash. "
                f"Both teams will be looking to make a statement in a game that could have playoff implications."
            )

    # Totals paragraph (sport-aware) with more varied analysis
    transition = TRANSITIONS[game_num % len(TRANSITIONS)]
    if total is not None:
        if sport in ['nba', 'ncaab']:
            if total > 235:
                paragraphs.append(
                    f"{transition} the {total} total screams pace and points. Both offenses have been clicking, "
                    f"and neither defense has inspired confidence lately. If you're playing the over, you're betting "
                    f"on fast breaks, transition buckets, and minimal half-court grinding. The risk? Foul trouble slowing things down."
                )
            elif total > 220:
                paragraphs.append(
                    f"{transition} with a total of {total}, Vegas sees this as an up-tempo affair. "
                    f"That's above average for the league this season. The over/under here will likely come down to "
                    f"whether the trailing team presses or lets the clock run in the fourth."
                )
            else:
                paragraphs.append(
                    f"{transition} the {total} total is on the lower end. Someone's expecting defense, or at least slower possessions. "
                    f"Under bettors need both teams to grind it out. If one team falls behind big early, garbage time scoring kills the under."
                )
        elif sport in ['nfl', 'ncaaf']:
            if total > 52:
                paragraphs.append(
                    f"{transition} that {total}-point total is massive. The books see a shootout, which means they expect "
                    f"both offenses to move the ball. Check the weather forecast—wind or rain can tank high totals fast. "
                    f"If conditions are clean, this could be a fantasy football dream."
                )
            elif total > 44:
                paragraphs.append(
                    f"{transition} the total sits at {total}. That's a fairly standard number, suggesting balanced action expected. "
                    f"Games in this range often come down to turnover luck and red zone efficiency. "
                    f"One pick-six can swing the total by itself."
                )
            else:
                paragraphs.append(
                    f"{transition} with a {total}-point total, Vegas is expecting a defensive slugfest. "
                    f"These games often go under when both defenses are healthy and game plans focus on ball control. "
                    f"But they can also explode if one team abandons the run early."
                )
        elif sport == 'nhl':
            if total >= 6.5:
                paragraphs.append(
                    f"{transition} the {total} total is juicy for hockey. That means the books see shaky goaltending, "
                    f"hot offenses, or both. Power plays will be crucial—check recent PP and PK numbers before pulling the trigger."
                )
            elif total <= 5.5:
                paragraphs.append(
                    f"{transition} with a {total} total, we're looking at a potential goaltending duel. "
                    f"The under historically hits more often in low-total NHL games, but one fluky bounce can ruin it. "
                    f"Know your goalies before betting this one."
                )
            else:
                paragraphs.append(
                    f"{transition} the {total} goals total is right around league average. In games like this, "
                    f"special teams often make the difference. Whichever team wins the special teams battle will likely push the total one way."
                )

    # Moneyline paragraph - more varied
    if home_ml is not None and away_ml is not None:
        home_ml_str = format_odds(home_ml)
        away_ml_str = format_odds(away_ml)

        if home_ml < -250:
            paragraphs.append(
                f"The moneyline tells the story: {home_team} at {home_ml_str} is a massive favorite. "
                f"Laying that kind of juice rarely makes sense unless you're parlaying. {away_team} at {away_ml_str} "
                f"is a high-risk lottery ticket, but upsets do happen. The question is whether you want to be holding that ticket."
            )
        elif home_ml < -150:
            paragraphs.append(
                f"On the moneyline, {home_team} ({home_ml_str}) is a solid favorite, with {away_team} ({away_ml_str}) as the underdog. "
                f"This is the range where moneyline betting gets interesting. The favorite isn't prohibitive, "
                f"and the dog isn't a complete longshot. Your read on the game matters here."
            )
        elif home_ml > 100:
            paragraphs.append(
                f"Here's where it gets interesting: {home_team} is actually the dog at {home_ml_str}, despite playing at home. "
                f"{away_team} is the road favorite at {away_ml_str}. That's the market telling you the visitors are clearly better. "
                f"Home dogs can be sneaky value plays, but there's usually a reason they're priced this way."
            )
        else:
            paragraphs.append(
                f"The moneyline is tight: {home_team} {home_ml_str}, {away_team} {away_ml_str}. "
                f"When prices are this close, the market is essentially saying 'flip a coin.' {home_adv.capitalize()} is baked "
                f"into that slight edge for {home_team if home_ml < 0 else away_team}. In spots like these, I look for X-factors—rest, injuries, motivation."
            )

    # UNIQUE closing paragraph for each game
    closer = get_unique_closer(game_num, home_team, away_team, sport)
    paragraphs.append(closer)

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

        # Generate analysis - pass game number for unique closers
        games = []
        for game_num, game in enumerate(games_data):
            analysis = generate_game_analysis(game, sport_key, records, game_num)
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
