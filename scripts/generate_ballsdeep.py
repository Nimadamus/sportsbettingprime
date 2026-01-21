#!/usr/bin/env python3
"""
Balls Deep International Research Gatherer
===========================================
Gathers REAL sports news, scores, and betting content for satire material.
Does NOT generate final content - Claude Code processes this into elite satire.

The research is saved to pending_content/ballsdeep_research_YYYY-MM-DD.json
When user runs /daily-content, Claude Code reads this and writes quality satire.

Site: ballsdeepinternational.neocities.org
Tone: Sports betting satire, degenerate humor, self-deprecating gambling content
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/tmp')

# ESPN API endpoints for multiple sports
ESPN_APIS = {
    'nba': "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    'nfl': "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    'nhl': "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    'mlb': "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    'ncaab': "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
    'ncaaf': "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
}

# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_espn_scores(sport: str, api_url: str) -> List[Dict]:
    """Fetch scores from ESPN API"""
    games = []
    try:
        resp = requests.get(api_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            for event in data.get('events', [])[:10]:
                game = {
                    'name': event.get('name', ''),
                    'short_name': event.get('shortName', ''),
                    'status': event.get('status', {}).get('type', {}).get('description', ''),
                    'sport': sport,
                }

                # Get scores if available
                competitions = event.get('competitions', [])
                if competitions:
                    comp = competitions[0]
                    competitors = comp.get('competitors', [])
                    if len(competitors) >= 2:
                        game['home_team'] = competitors[0].get('team', {}).get('displayName', '')
                        game['home_score'] = competitors[0].get('score', '0')
                        game['away_team'] = competitors[1].get('team', {}).get('displayName', '')
                        game['away_score'] = competitors[1].get('score', '0')

                        # Check for blowouts (great for satire)
                        try:
                            score_diff = abs(int(game['home_score']) - int(game['away_score']))
                            game['is_blowout'] = score_diff > 20 if sport in ['nba', 'ncaab'] else score_diff > 14
                        except:
                            game['is_blowout'] = False

                games.append(game)
    except Exception as e:
        print(f"  [WARN] ESPN {sport} fetch failed: {e}")
    return games


def fetch_espn_headlines(sport: str) -> List[Dict]:
    """Fetch news headlines from ESPN"""
    headlines = []
    try:
        if sport == 'nba':
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news"
        elif sport == 'nfl':
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news"
        elif sport == 'nhl':
            url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/news"
        else:
            return headlines

        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            for article in data.get('articles', [])[:10]:
                headlines.append({
                    'headline': article.get('headline', ''),
                    'description': article.get('description', ''),
                    'sport': sport,
                })
    except Exception as e:
        print(f"  [WARN] ESPN headlines fetch failed: {e}")
    return headlines


def identify_satire_angles(games: List[Dict], headlines: List[Dict]) -> List[Dict]:
    """Identify potential satire angles from the data"""
    angles = []

    # Find blowout games (great for "I lost everything" narratives)
    blowouts = [g for g in games if g.get('is_blowout')]
    for game in blowouts:
        loser = game['away_team'] if int(game.get('away_score', 0)) < int(game.get('home_score', 0)) else game['home_team']
        angles.append({
            'type': 'blowout_loss',
            'team': loser,
            'description': f"The {loser} got absolutely destroyed",
            'game': game['name'],
            'sport': game['sport'],
        })

    # Find close games (great for "bad beat" content)
    close_games = []
    for g in games:
        try:
            diff = abs(int(g.get('home_score', 0)) - int(g.get('away_score', 0)))
            if 1 <= diff <= 3 and g.get('status') in ['Final', 'Final/OT']:
                close_games.append(g)
        except:
            pass

    for game in close_games:
        angles.append({
            'type': 'bad_beat',
            'description': f"A heartbreaker decided by just {abs(int(game.get('home_score', 0)) - int(game.get('away_score', 0)))} points",
            'game': game['name'],
            'sport': game['sport'],
        })

    # Headlines that could be spun into satire
    for headline in headlines:
        h = headline['headline'].lower()
        if any(word in h for word in ['injury', 'out', 'miss', 'hurt', 'questionable']):
            angles.append({
                'type': 'injury_excuse',
                'description': headline['headline'],
                'sport': headline['sport'],
            })
        elif any(word in h for word in ['trade', 'sign', 'deal', 'contract']):
            angles.append({
                'type': 'roster_move',
                'description': headline['headline'],
                'sport': headline['sport'],
            })

    return angles


# =============================================================================
# RESEARCH GATHERING
# =============================================================================

def gather_research():
    """Main research gathering function"""
    print("=" * 60)
    print(f"BALLS DEEP INTERNATIONAL RESEARCH GATHERER - {DATE_DISPLAY}")
    print("=" * 60)

    research = {
        'site': 'ballsdeep',
        'date': DATE_STR,
        'gathered_at': datetime.now().isoformat(),
        'status': 'pending_processing',
        'games': [],
        'headlines': [],
        'satire_angles': [],
        'suggested_topics': [],
    }

    # Gather scores from all sports
    print("\n[1/3] Fetching sports scores...")
    all_games = []
    for sport, api_url in ESPN_APIS.items():
        print(f"  Fetching {sport.upper()}...")
        games = fetch_espn_scores(sport, api_url)
        all_games.extend(games)
        print(f"    Found {len(games)} games")

    research['games'] = all_games
    print(f"  Total games: {len(research['games'])}")

    # Gather headlines
    print("\n[2/3] Fetching sports headlines...")
    all_headlines = []
    for sport in ['nba', 'nfl', 'nhl']:
        headlines = fetch_espn_headlines(sport)
        all_headlines.extend(headlines)
        print(f"  {sport.upper()}: {len(headlines)} headlines")

    research['headlines'] = all_headlines

    # Identify satire angles
    print("\n[3/3] Identifying satire angles...")
    angles = identify_satire_angles(all_games, all_headlines)
    research['satire_angles'] = angles
    print(f"  Found {len(angles)} potential satire angles")

    # Generate suggested topics
    research['suggested_topics'] = []

    if any(a['type'] == 'blowout_loss' for a in angles):
        team = next((a['team'] for a in angles if a['type'] == 'blowout_loss'), 'a team')
        research['suggested_topics'].append(f"Why I Bet on {team} and Now I'm Questioning My Life Choices")

    if any(a['type'] == 'bad_beat' for a in angles):
        research['suggested_topics'].append("The Bad Beat That Made Me Consider Selling a Kidney")

    if any(a['type'] == 'injury_excuse' for a in angles):
        research['suggested_topics'].append("Injuries I'm Blaming for My Losing Streak (A Comprehensive List)")

    # Default topics if nothing specific found
    if not research['suggested_topics']:
        research['suggested_topics'] = [
            "Confessions of a Degenerate: Today's Edition",
            "My Bankroll Management Strategy (LOL JK I Have None)",
            "How Many Parlays Does It Take to Realize Parlays Are Stupid?",
        ]

    return research


def save_research(research):
    """Save research to JSON files"""
    # Save to /tmp for GitHub Actions
    tmp_path = os.path.join(OUTPUT_DIR, f"ballsdeep_research_{DATE_STR}.json")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(research, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {tmp_path}")

    # Also save to pending_content for local processing
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    pending_dir = os.path.join(repo_dir, 'pending_content')

    try:
        os.makedirs(pending_dir, exist_ok=True)
        local_path = os.path.join(pending_dir, f"ballsdeep_research_{DATE_STR}.json")
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(research, f, indent=2, ensure_ascii=False)
        print(f"Also saved to: {local_path}")
    except Exception as e:
        print(f"[WARN] Could not save to pending_content: {e}")

    return tmp_path


# =============================================================================
# MAIN
# =============================================================================

def main():
    research = gather_research()
    save_research(research)

    print("\n" + "=" * 60)
    print("RESEARCH COMPLETE")
    print("=" * 60)
    print(f"Games gathered: {len(research['games'])}")
    print(f"Headlines gathered: {len(research['headlines'])}")
    print(f"Satire angles found: {len(research['satire_angles'])}")
    print(f"\nSuggested topics:")
    for topic in research['suggested_topics']:
        print(f"  - {topic}")
    print(f"\nStatus: {research['status']}")
    print("Run /daily-content in Claude Code to process into elite satire")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
