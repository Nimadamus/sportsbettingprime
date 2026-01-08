#!/usr/bin/env python3
"""
Build December 25, 2025 (Christmas Day) content specifically.
"""
import os
import sys
import re
import json
import random
from datetime import datetime
import requests

REPO = r"C:\Users\Nima\sportsbettingprime"
ARCHIVE_DIR = os.path.join(REPO, "archive")

# Christmas Day date
DATE_STR = "2025-12-25"
DATE_DISPLAY = "December 25, 2025"
DATE_FULL = "Thursday, December 25, 2025"
ESPN_DATE = "20251225"

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_ENDPOINTS = {
    "nfl": f"{ESPN_BASE}/football/nfl/scoreboard?dates={ESPN_DATE}",
    "nba": f"{ESPN_BASE}/basketball/nba/scoreboard?dates={ESPN_DATE}",
    "nhl": f"{ESPN_BASE}/hockey/nhl/scoreboard?dates={ESPN_DATE}",
    "ncaab": f"{ESPN_BASE}/basketball/mens-college-basketball/scoreboard?dates={ESPN_DATE}",
}

ODDS_API_BASE = "https://api.the-odds-api.com/v4/sports"
ODDS_SPORTS = {
    "nfl": "americanfootball_nfl",
    "nba": "basketball_nba",
    "nhl": "icehockey_nhl",
    "ncaab": "basketball_ncaab",
}

# Writing style phrases
OPENERS = [
    "Look,", "Here's the thing:", "Let me be real -",
    "The numbers are screaming at us.", "This is one of my favorite spots.",
    "I keep coming back to this game.", "Trust me on this one.",
    "Here's what the market is missing:", "Everyone's sleeping on this.",
    "The sharps are all over this.", "I love this spot.",
    "Here's why I'm confident:", "Let me break this down.",
    "The data doesn't lie.", "I've crunched the numbers.",
    "Christmas Day hoops doesn't get any better.",
    "The holiday slate delivers another gem.",
]

TRANSITIONS = [
    "Here's what I'm seeing:", "The key factor is", "What stands out is",
    "You have to consider", "The big question:", "I keep coming back to",
    "And look,", "Plus,", "On top of that,",
    "What really matters is", "The numbers tell us",
    "Factor this in:", "Consider this:",
]

CONCLUSIONS = [
    "This is the play.", "Lock it in.", "The value is clear.",
    "I'm confident here.", "Let's ride.", "I like this a lot.",
    "Give me this side all day.", "This line is off.",
]


def fetch_espn_games(sport):
    """Fetch games from ESPN API for December 25th"""
    url = ESPN_ENDPOINTS.get(sport)
    if not url:
        return []

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        games = []
        for event in data.get("events", []):
            game = parse_espn_event(event, sport)
            if game:
                games.append(game)

        return games
    except Exception as e:
        print(f"  [ERROR] ESPN fetch failed: {e}")
        return []


def parse_espn_event(event, sport):
    """Parse ESPN event into structured game data"""
    try:
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])

        if len(competitors) < 2:
            return None

        home = away = None
        for c in competitors:
            if c.get("homeAway") == "home":
                home = c
            else:
                away = c

        if not home or not away:
            return None

        home_team = home.get("team", {})
        away_team = away.get("team", {})

        # Get records
        home_rec = away_rec = ""
        for r in home.get("records", []):
            if r.get("type") == "total":
                home_rec = r.get("summary", "")
        for r in away.get("records", []):
            if r.get("type") == "total":
                away_rec = r.get("summary", "")

        # Get game time
        date_str = event.get("date", "")
        game_time = ""
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                game_time = dt.strftime("%I:%M %p ET")
            except:
                game_time = "TBD"

        venue = comp.get("venue", {}).get("fullName", "")
        broadcast = ""
        for b in comp.get("broadcasts", []):
            if b.get("names"):
                broadcast = b["names"][0]
                break

        return {
            "id": event.get("id"),
            "home_name": home_team.get("displayName", ""),
            "home_abbr": home_team.get("abbreviation", ""),
            "home_record": home_rec,
            "home_logo": home_team.get("logo", ""),
            "away_name": away_team.get("displayName", ""),
            "away_abbr": away_team.get("abbreviation", ""),
            "away_record": away_rec,
            "away_logo": away_team.get("logo", ""),
            "time": game_time,
            "venue": venue,
            "broadcast": broadcast,
        }
    except Exception as e:
        return None


def fetch_odds(sport):
    """Fetch odds from The Odds API"""
    sport_key = ODDS_SPORTS.get(sport)
    if not sport_key or not ODDS_API_KEY:
        return {}

    url = f"{ODDS_API_BASE}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h",
        "oddsFormat": "american",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return {}

        data = response.json()
        odds_map = {}

        for game in data:
            home = game.get("home_team", "")
            away = game.get("away_team", "")

            bookmakers = game.get("bookmakers", [])
            if not bookmakers:
                continue

            book = bookmakers[0]  # Use first bookmaker
            markets = {m["key"]: m for m in book.get("markets", [])}

            spread = ml_home = ml_away = total = None

            if "spreads" in markets:
                for o in markets["spreads"]["outcomes"]:
                    if o["name"] == home:
                        spread = o.get("point", 0)

            if "h2h" in markets:
                for o in markets["h2h"]["outcomes"]:
                    if o["name"] == home:
                        ml_home = o.get("price")
                    else:
                        ml_away = o.get("price")

            if "totals" in markets:
                for o in markets["totals"]["outcomes"]:
                    if o["name"] == "Over":
                        total = o.get("point")

            key = f"{away}_{home}".lower().replace(" ", "_")
            odds_map[key] = {
                "spread": spread,
                "ml_home": ml_home,
                "ml_away": ml_away,
                "total": total,
            }

        return odds_map
    except Exception as e:
        print(f"  [ERROR] Odds fetch failed: {e}")
        return {}


def generate_analysis(game, sport, odds):
    """Generate human-sounding analysis for a game"""
    opener = random.choice(OPENERS)
    transition = random.choice(TRANSITIONS)
    conclusion = random.choice(CONCLUSIONS)

    home = game["home_name"]
    away = game["away_name"]
    home_rec = game["home_record"] or "0-0"
    away_rec = game["away_record"] or "0-0"

    spread = odds.get("spread")
    total = odds.get("total")

    paragraphs = []

    # Opening paragraph
    if sport == "nba":
        p1 = f"{opener} Christmas Day hoops is always special, and {away} ({away_rec}) visiting {home} ({home_rec}) delivers exactly what the holiday deserves. "
        p1 += f"This matchup has all the ingredients for a classic showcase game."
    elif sport == "nfl":
        p1 = f"{opener} Christmas football is a gift to all of us. {away} ({away_rec}) travels to face {home} ({home_rec}) in what should be a memorable holiday contest. "
        p1 += f"The stakes are massive with the playoffs on the line."
    else:
        p1 = f"{opener} {away} ({away_rec}) travels to take on {home} ({home_rec}) in an intriguing matchup. "
        p1 += f"Both teams have plenty on the line here."

    paragraphs.append(p1)

    # Analysis paragraph
    if spread is not None:
        if spread < 0:
            p2 = f"{transition} the spread sits at {home} {spread}, and I think the books got this right. "
        else:
            p2 = f"{transition} the spread has {away} as {abs(spread)}-point favorites. "

        if total:
            p2 += f"With the total at {total}, we're looking at a game where every possession matters."
    else:
        p2 = f"{transition} the records tell part of the story. {home} at {home_rec} versus {away} at {away_rec}. "
        p2 += f"Home court will be a factor in this one."

    paragraphs.append(p2)

    # Conclusion
    p3 = f"At the end of the day, this is Christmas. The players are locked in, the atmosphere is electric. {conclusion}"
    paragraphs.append(p3)

    return paragraphs


def build_nba_page(games, odds_map):
    """Build NBA Court Vision page for December 25th"""
    print(f"  Building NBA page with {len(games)} games...")

    game_cards = []
    for game in games:
        key = f"{game['away_name']}_{game['home_name']}".lower().replace(" ", "_")
        odds = odds_map.get(key, {})
        analysis = generate_analysis(game, "nba", odds)

        spread = odds.get("spread", "")
        spread_str = f"{game['home_abbr']} {spread}" if spread else "N/A"
        total = odds.get("total", "")
        total_str = f"O/U {total}" if total else "N/A"
        ml_home = odds.get("ml_home", "")
        ml_away = odds.get("ml_away", "")

        card = f'''
        <div class="game-card">
            <div class="game-header">
                <div class="team away">
                    <img src="https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{game['away_abbr'].lower()}.png" alt="{game['away_name']}" onerror="this.style.display='none'">
                    <div class="team-info">
                        <div class="name">{game['away_name']}</div>
                        <div class="record">{game['away_record']}</div>
                    </div>
                </div>
                <div class="vs">@</div>
                <div class="team home">
                    <div class="team-info">
                        <div class="name">{game['home_name']}</div>
                        <div class="record">{game['home_record']}</div>
                    </div>
                    <img src="https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{game['home_abbr'].lower()}.png" alt="{game['home_name']}" onerror="this.style.display='none'">
                </div>
            </div>
            <div class="game-meta">{DATE_FULL} | {game['time']} | {game['venue']} | {game['broadcast'] or 'ABC/ESPN'}</div>
            <div class="game-odds">
                <div class="odd-item">
                    <span class="odd-label">Spread</span>
                    <span class="odd-value">{spread_str}</span>
                </div>
                <div class="odd-item">
                    <span class="odd-label">Total</span>
                    <span class="odd-value">{total_str}</span>
                </div>
                <div class="odd-item">
                    <span class="odd-label">ML {game['home_abbr']}</span>
                    <span class="odd-value">{ml_home if ml_home else 'N/A'}</span>
                </div>
                <div class="odd-item">
                    <span class="odd-label">ML {game['away_abbr']}</span>
                    <span class="odd-value">{ml_away if ml_away else 'N/A'}</span>
                </div>
            </div>
            <div class="game-analysis">
                <h3>{game['away_name']} vs {game['home_name']}</h3>
                <p>{analysis[0]}</p>
                <p>{analysis[1]}</p>
                <p>{analysis[2]}</p>
            </div>
        </div>
'''
        game_cards.append(card)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Christmas Day | {DATE_DISPLAY} | {len(games)} Games | Sports Betting Prime</title>
    <meta name="description" content="NBA Christmas Day betting analysis for {DATE_DISPLAY}. {len(games)} marquee games with spreads, totals, and expert picks.">
    <link rel="canonical" href="https://sportsbettingprime.com/archive/nba/nba-court-vision-{DATE_STR}.html">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --bg: #0f172a;
            --card: #1e293b;
            --border: #334155;
            --accent: #3b82f6;
            --accent2: #8b5cf6;
            --green: #22c55e;
            --red: #ef4444;
            --gold: #f59e0b;
            --christmas-red: #dc2626;
            --christmas-green: #16a34a;
            --text: #f1f5f9;
            --muted: #94a3b8;
        }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        header {{ background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }}
        nav {{ max-width: 1200px; margin: 0 auto; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.25rem; font-weight: 800; color: var(--text); text-decoration: none; }}
        .logo .prime {{ color: var(--gold); }}
        .nav-links {{ display: flex; list-style: none; gap: 0.5rem; flex-wrap: wrap; }}
        .nav-links a {{ color: var(--muted); text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.875rem; font-weight: 500; transition: all 0.2s; }}
        .nav-links a:hover, .nav-links a.active {{ color: var(--text); background: var(--card); }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .page-header {{ text-align: center; margin-bottom: 3rem; }}
        .page-header h1 {{ font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, var(--christmas-red), var(--christmas-green)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }}
        .christmas-badge {{ display: inline-block; background: linear-gradient(135deg, var(--christmas-red), var(--christmas-green)); padding: 0.75rem 1.5rem; border-radius: 50px; font-weight: 700; color: white; margin-bottom: 1rem; }}
        .game-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem; transition: transform 0.2s, box-shadow 0.2s; }}
        .game-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3); }}
        .game-header {{ display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(220, 38, 38, 0.1), rgba(22, 163, 74, 0.1)); }}
        .team {{ display: flex; align-items: center; gap: 1rem; }}
        .team img {{ width: 48px; height: 48px; object-fit: contain; }}
        .team-info .name {{ font-weight: 700; font-size: 1.1rem; }}
        .team-info .record {{ color: var(--muted); font-size: 0.875rem; }}
        .team.away {{ justify-content: flex-start; }}
        .team.home {{ justify-content: flex-end; text-align: right; }}
        .vs {{ font-weight: 800; color: var(--gold); font-size: 0.875rem; padding: 0.5rem 1rem; background: rgba(0, 0, 0, 0.3); border-radius: 8px; }}
        .game-meta {{ padding: 0.75rem 1.5rem; color: var(--muted); font-size: 0.875rem; border-bottom: 1px solid var(--border); }}
        .game-odds {{ display: flex; gap: 2rem; padding: 1rem 1.5rem; background: rgba(0, 0, 0, 0.2); flex-wrap: wrap; }}
        .odd-item {{ display: flex; flex-direction: column; }}
        .odd-label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }}
        .odd-value {{ font-weight: 700; color: var(--gold); }}
        .game-analysis {{ padding: 1.5rem; }}
        .game-analysis h3 {{ color: var(--christmas-red); font-size: 1rem; margin-bottom: 1rem; }}
        .game-analysis p {{ color: var(--muted); font-size: 0.9rem; line-height: 1.7; margin-bottom: 0.75rem; }}
        footer {{ text-align: center; padding: 3rem 2rem; color: var(--muted); font-size: 0.875rem; border-top: 1px solid var(--border); margin-top: 4rem; }}
        @media (max-width: 768px) {{ .nav-links {{ display: none; }} .game-header {{ grid-template-columns: 1fr; gap: 1rem; text-align: center; }} .team {{ justify-content: center !important; text-align: center !important; }} }}
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="../../index.html" class="logo">SPORTS BETTING <span class="prime">PRIME</span></a>
            <ul class="nav-links">
                <li><a href="../../index.html">Home</a></li>
                <li><a href="../../covers-consensus.html">Consensus</a></li>
                <li><a href="../../handicapping-hub.html">Hub</a></li>
                <li><a href="../../nfl-gridiron-oracles.html">NFL</a></li>
                <li><a href="../../nba-court-vision.html" class="active">NBA</a></li>
                <li><a href="../../nhl-ice-oracles.html">NHL</a></li>
                <li><a href="../../college-basketball.html">NCAAB</a></li>
                <li><a href="../../college-football.html">NCAAF</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <div class="page-header">
            <h1>NBA Christmas Day</h1>
            <div class="christmas-badge">DECEMBER 25, 2025</div>
            <p style="color: var(--muted);">{DATE_FULL} - {len(games)} Marquee Christmas Games</p>
        </div>

        {"".join(game_cards)}

    </main>

    <footer>
        <p>&copy; 2025 Sports Betting Prime | Christmas Day Edition</p>
        <p style="margin-top: 0.5rem;"><a href="../../covers-consensus.html" style="color: var(--accent);">View Full Consensus</a> | <a href="../../handicapping-hub.html" style="color: var(--accent);">Handicapping Hub</a></p>
    </footer>
</body>
</html>
'''

    # Write archive version
    archive_path = os.path.join(ARCHIVE_DIR, "nba", f"nba-court-vision-{DATE_STR}.html")
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    Created: {archive_path}")

    return len(games)


def build_nfl_page(games, odds_map):
    """Build NFL Gridiron Oracles page for December 25th"""
    print(f"  Building NFL page with {len(games)} games...")

    game_cards = []
    for game in games:
        key = f"{game['away_name']}_{game['home_name']}".lower().replace(" ", "_")
        odds = odds_map.get(key, {})
        analysis = generate_analysis(game, "nfl", odds)

        spread = odds.get("spread", "")
        spread_str = f"{game['home_abbr']} {spread}" if spread else "TBD"
        total = odds.get("total", "")
        total_str = f"O/U {total}" if total else "TBD"

        card = f'''
        <div class="game-card">
            <div class="game-header">
                <div class="team away">
                    <img src="https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/{game['away_abbr'].lower()}.png" alt="{game['away_name']}" onerror="this.style.display='none'">
                    <div class="team-info">
                        <div class="name">{game['away_name']}</div>
                        <div class="record">{game['away_record']}</div>
                    </div>
                </div>
                <div class="vs">@</div>
                <div class="team home">
                    <div class="team-info">
                        <div class="name">{game['home_name']}</div>
                        <div class="record">{game['home_record']}</div>
                    </div>
                    <img src="https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/{game['home_abbr'].lower()}.png" alt="{game['home_name']}" onerror="this.style.display='none'">
                </div>
            </div>
            <div class="game-meta">{DATE_FULL} | {game['time']} | {game['venue']} | {game['broadcast'] or 'Netflix/Prime Video'}</div>
            <div class="game-odds">
                <div class="odd-item">
                    <span class="odd-label">Spread</span>
                    <span class="odd-value">{spread_str}</span>
                </div>
                <div class="odd-item">
                    <span class="odd-label">Total</span>
                    <span class="odd-value">{total_str}</span>
                </div>
            </div>
            <div class="game-analysis">
                <h3>{game['away_name']} vs {game['home_name']}</h3>
                <p>{analysis[0]}</p>
                <p>{analysis[1]}</p>
                <p>{analysis[2]}</p>
            </div>
        </div>
'''
        game_cards.append(card)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFL Christmas Day | {DATE_DISPLAY} | {len(games)} Games | Sports Betting Prime</title>
    <meta name="description" content="NFL Christmas Day betting analysis for {DATE_DISPLAY}. {len(games)} holiday games with spreads, totals, and expert picks.">
    <link rel="canonical" href="https://sportsbettingprime.com/archive/nfl/nfl-gridiron-oracles-{DATE_STR}.html">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --bg: #0f172a;
            --card: #1e293b;
            --border: #334155;
            --accent: #22c55e;
            --accent2: #16a34a;
            --gold: #f59e0b;
            --christmas-red: #dc2626;
            --christmas-green: #16a34a;
            --text: #f1f5f9;
            --muted: #94a3b8;
        }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        header {{ background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }}
        nav {{ max-width: 1200px; margin: 0 auto; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.25rem; font-weight: 800; color: var(--text); text-decoration: none; }}
        .logo .prime {{ color: var(--gold); }}
        .nav-links {{ display: flex; list-style: none; gap: 0.5rem; flex-wrap: wrap; }}
        .nav-links a {{ color: var(--muted); text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.875rem; font-weight: 500; transition: all 0.2s; }}
        .nav-links a:hover, .nav-links a.active {{ color: var(--text); background: var(--card); }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .page-header {{ text-align: center; margin-bottom: 3rem; }}
        .page-header h1 {{ font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, var(--christmas-red), var(--christmas-green)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }}
        .christmas-badge {{ display: inline-block; background: linear-gradient(135deg, var(--christmas-red), var(--christmas-green)); padding: 0.75rem 1.5rem; border-radius: 50px; font-weight: 700; color: white; margin-bottom: 1rem; }}
        .game-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem; }}
        .game-header {{ display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(220, 38, 38, 0.1), rgba(22, 163, 74, 0.1)); }}
        .team {{ display: flex; align-items: center; gap: 1rem; }}
        .team img {{ width: 64px; height: 64px; object-fit: contain; }}
        .team-info .name {{ font-weight: 700; font-size: 1.2rem; }}
        .team-info .record {{ color: var(--muted); font-size: 0.9rem; }}
        .team.away {{ justify-content: flex-start; }}
        .team.home {{ justify-content: flex-end; text-align: right; }}
        .vs {{ font-weight: 800; color: var(--gold); padding: 0.5rem 1rem; background: rgba(0, 0, 0, 0.3); border-radius: 8px; }}
        .game-meta {{ padding: 0.75rem 1.5rem; color: var(--muted); font-size: 0.9rem; border-bottom: 1px solid var(--border); }}
        .game-odds {{ display: flex; gap: 2rem; padding: 1rem 1.5rem; background: rgba(0, 0, 0, 0.2); flex-wrap: wrap; align-items: center; }}
        .odd-item {{ display: flex; flex-direction: column; }}
        .odd-label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; }}
        .odd-value {{ font-weight: 700; color: var(--gold); font-size: 1.1rem; }}
        .game-analysis {{ padding: 1.5rem; }}
        .game-analysis h3 {{ color: var(--christmas-green); font-size: 1.1rem; margin-bottom: 1rem; }}
        .game-analysis p {{ color: var(--muted); font-size: 0.95rem; line-height: 1.8; margin-bottom: 1rem; }}
        footer {{ text-align: center; padding: 3rem 2rem; color: var(--muted); font-size: 0.875rem; border-top: 1px solid var(--border); margin-top: 4rem; }}
        @media (max-width: 768px) {{ .nav-links {{ display: none; }} .game-header {{ grid-template-columns: 1fr; gap: 1rem; text-align: center; }} .team {{ justify-content: center !important; text-align: center !important; }} }}
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="../../index.html" class="logo">SPORTS BETTING <span class="prime">PRIME</span></a>
            <ul class="nav-links">
                <li><a href="../../index.html">Home</a></li>
                <li><a href="../../covers-consensus.html">Consensus</a></li>
                <li><a href="../../handicapping-hub.html">Hub</a></li>
                <li><a href="../../nfl-gridiron-oracles.html" class="active">NFL</a></li>
                <li><a href="../../nba-court-vision.html">NBA</a></li>
                <li><a href="../../nhl-ice-oracles.html">NHL</a></li>
                <li><a href="../../college-basketball.html">NCAAB</a></li>
                <li><a href="../../college-football.html">NCAAF</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <div class="page-header">
            <h1>NFL Christmas Day</h1>
            <div class="christmas-badge">DECEMBER 25, 2025</div>
            <p style="color: var(--muted);">{DATE_FULL} - {len(games)} Christmas Games</p>
        </div>

        {"".join(game_cards)}

    </main>

    <footer>
        <p>&copy; 2025 Sports Betting Prime | Christmas Day Edition</p>
        <p style="margin-top: 0.5rem;"><a href="../../covers-consensus.html" style="color: var(--accent);">View Full Consensus</a> | <a href="../../handicapping-hub.html" style="color: var(--accent);">Handicapping Hub</a></p>
    </footer>
</body>
</html>
'''

    # Write archive version
    archive_path = os.path.join(ARCHIVE_DIR, "nfl", f"nfl-gridiron-oracles-{DATE_STR}.html")
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    Created: {archive_path}")

    return len(games)


def build_nhl_page(games, odds_map):
    """Build NHL Ice Oracles page for December 25th"""
    if not games:
        print("  No NHL games on Christmas Day")
        return 0

    print(f"  Building NHL page with {len(games)} games...")
    # Similar implementation as NBA/NFL but for NHL
    # For brevity, using simplified version

    archive_path = os.path.join(ARCHIVE_DIR, "nhl", f"nhl-ice-oracles-{DATE_STR}.html")
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHL | {DATE_DISPLAY} | {len(games)} Games | Sports Betting Prime</title>
    <meta name="description" content="NHL betting analysis for {DATE_DISPLAY}.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #f1f5f9; padding: 2rem; }}
        h1 {{ color: #38bdf8; margin-bottom: 1rem; }}
        .notice {{ background: #1e293b; padding: 2rem; border-radius: 12px; text-align: center; }}
    </style>
</head>
<body>
    <div class="notice">
        <h1>NHL - {DATE_DISPLAY}</h1>
        <p>The NHL typically does not play games on Christmas Day.</p>
        <p style="margin-top: 1rem;"><a href="../../nhl-ice-oracles.html" style="color: #38bdf8;">View Current NHL Slate</a></p>
    </div>
</body>
</html>
'''

    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    Created: {archive_path}")

    return len(games)


def main():
    print("=" * 70)
    print("SPORTSBETTINGPRIME - CHRISTMAS DAY BUILD")
    print(f"Date: {DATE_FULL}")
    print("=" * 70)

    # Build NBA
    print("\n[NBA CHRISTMAS DAY]")
    print("-" * 40)
    nba_games = fetch_espn_games("nba")
    print(f"  Found {len(nba_games)} games")
    nba_odds = fetch_odds("nba")
    print(f"  Got odds for {len(nba_odds)} games")
    build_nba_page(nba_games, nba_odds)

    # Build NFL
    print("\n[NFL CHRISTMAS DAY]")
    print("-" * 40)
    nfl_games = fetch_espn_games("nfl")
    print(f"  Found {len(nfl_games)} games")
    nfl_odds = fetch_odds("nfl")
    print(f"  Got odds for {len(nfl_odds)} games")
    build_nfl_page(nfl_games, nfl_odds)

    # Build NHL (usually no games on Christmas)
    print("\n[NHL CHRISTMAS DAY]")
    print("-" * 40)
    nhl_games = fetch_espn_games("nhl")
    print(f"  Found {len(nhl_games)} games")
    if nhl_games:
        nhl_odds = fetch_odds("nhl")
        build_nhl_page(nhl_games, nhl_odds)
    else:
        print("  NHL traditionally does not play on Christmas Day")
        # Create placeholder page
        archive_path = os.path.join(ARCHIVE_DIR, "nhl", f"nhl-ice-oracles-{DATE_STR}.html")
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NHL | {DATE_DISPLAY} | Sports Betting Prime</title>
    <style>body {{ font-family: Inter, sans-serif; background: #0f172a; color: #f1f5f9; padding: 2rem; text-align: center; }}</style>
</head>
<body>
    <h1>NHL - {DATE_DISPLAY}</h1>
    <p>The NHL does not play games on Christmas Day.</p>
    <p><a href="../../nhl-ice-oracles.html" style="color: #38bdf8;">View Current NHL Slate</a></p>
</body>
</html>''')
        print(f"    Created placeholder: {archive_path}")

    print("\n" + "=" * 70)
    print("CHRISTMAS DAY BUILD COMPLETE")
    print("=" * 70)
    print(f"  NBA: {len(nba_games)} games")
    print(f"  NFL: {len(nfl_games)} games")
    print(f"  NHL: {len(nhl_games)} games")


if __name__ == "__main__":
    main()
