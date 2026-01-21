#!/usr/bin/env python3
"""
MLB Research Gatherer
=====================
Gathers REAL MLB news from ESPN APIs and saves structured research.
Does NOT generate final content - Claude Code processes this into elite articles.

The research is saved to pending_content/mlb_research_YYYY-MM-DD.json
When user runs /daily-content, Claude Code reads this and writes quality journalism
for all 3 MLB sites (each gets UNIQUE content, different angles).

Sites:
- dailymlbpicks.com (AI/beginner angle)
- mlbprediction.com (analytics/data angle)
- bestmlbhandicapper.com (sharp/expert angle)
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List
import re

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/tmp')

# ESPN APIs
ESPN_MLB_NEWS = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news"
ESPN_MLB_TRANSACTIONS = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/transactions"
ESPN_MLB_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
ESPN_MLB_TEAMS = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams"

# =============================================================================
# NEWS FETCHING
# =============================================================================

def fetch_mlb_news() -> List[Dict]:
    """Fetch latest MLB news from ESPN API"""
    try:
        response = requests.get(ESPN_MLB_NEWS, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get('articles', [])[:15]:
            articles.append({
                'headline': article.get('headline', ''),
                'description': article.get('description', ''),
                'published': article.get('published', ''),
                'type': article.get('type', 'article'),
                'categories': [c.get('description', '') for c in article.get('categories', [])],
            })

        return articles
    except Exception as e:
        print(f"  [WARN] ESPN News API: {e}")
        return []


def fetch_mlb_transactions() -> List[Dict]:
    """Fetch recent MLB transactions"""
    try:
        response = requests.get(ESPN_MLB_TRANSACTIONS, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()

        transactions = []
        for item in data.get('items', [])[:20]:
            transactions.append({
                'date': item.get('date', ''),
                'description': item.get('description', ''),
                'team': item.get('team', {}).get('displayName', ''),
                'type': item.get('type', ''),
            })

        return transactions
    except Exception as e:
        print(f"  [WARN] Transactions API: {e}")
        return []


def fetch_team_standings() -> List[Dict]:
    """Fetch current MLB standings/teams info"""
    try:
        response = requests.get(ESPN_MLB_TEAMS, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()

        teams = []
        for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
            team_data = team.get('team', {})
            teams.append({
                'name': team_data.get('displayName', ''),
                'abbreviation': team_data.get('abbreviation', ''),
                'location': team_data.get('location', ''),
            })

        return teams
    except Exception as e:
        print(f"  [WARN] Teams API: {e}")
        return []


def extract_player_names(text: str) -> List[str]:
    """Extract player names from text"""
    # Common patterns for player names (First Last)
    names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
    # Filter out common non-names
    skip_words = {'The', 'This', 'That', 'Major League', 'New York', 'Los Angeles', 'San Francisco', 'San Diego'}
    return [n for n in names if n not in skip_words and len(n.split()) <= 3]


def extract_contract_info(text: str) -> List[Dict]:
    """Extract contract/money information from text"""
    contracts = []

    # Dollar amounts
    dollars = re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|M|B))?', text, re.I)
    for d in dollars:
        contracts.append({'type': 'money', 'value': d})

    # Year terms
    years = re.findall(r'(\d+)-year', text, re.I)
    for y in years:
        contracts.append({'type': 'years', 'value': f"{y} years"})

    return contracts


# =============================================================================
# RESEARCH GATHERING
# =============================================================================

def gather_research():
    """Main research gathering function"""
    print("=" * 60)
    print(f"MLB RESEARCH GATHERER - {DATE_DISPLAY}")
    print("=" * 60)

    research = {
        'site': 'mlb_sites',  # Will be used for all 3 MLB sites
        'target_sites': [
            {'name': 'dailymlbpicks', 'angle': 'AI predictions, beginner-friendly, futures focus'},
            {'name': 'mlbprediction', 'angle': 'Analytics, advanced stats (xBA, WAR, xFIP), data-driven'},
            {'name': 'bestmlbhandicapper', 'angle': 'Sharp money, expert handicapping, situational angles'},
        ],
        'date': DATE_STR,
        'gathered_at': datetime.now().isoformat(),
        'status': 'pending_processing',
        'news_items': [],
        'transactions': [],
        'teams': [],
        'extracted_players': [],
        'extracted_contracts': [],
        'key_storylines': [],
    }

    # Fetch news
    print("\n[1/3] Fetching ESPN MLB News...")
    news = fetch_mlb_news()
    research['news_items'] = news
    print(f"  Found {len(news)} news articles")

    # Fetch transactions
    print("\n[2/3] Fetching MLB Transactions...")
    transactions = fetch_mlb_transactions()
    research['transactions'] = transactions
    print(f"  Found {len(transactions)} transactions")

    # Fetch team info
    print("\n[3/3] Fetching Team Data...")
    teams = fetch_team_standings()
    research['teams'] = teams
    print(f"  Found {len(teams)} teams")

    # Extract entities from all text
    print("\n[4/4] Extracting key entities...")
    all_text = ""
    for item in news:
        all_text += f" {item.get('headline', '')} {item.get('description', '')}"
    for item in transactions:
        all_text += f" {item.get('description', '')}"

    # Extract players
    players = extract_player_names(all_text)
    research['extracted_players'] = list(set(players))[:20]
    print(f"  Players mentioned: {len(research['extracted_players'])}")

    # Extract contract info
    contracts = extract_contract_info(all_text)
    research['extracted_contracts'] = contracts
    print(f"  Contract details found: {len(contracts)}")

    # Identify key storylines
    storylines = []
    for item in news[:5]:
        headline = item.get('headline', '')
        if headline:
            storylines.append({
                'headline': headline,
                'description': item.get('description', ''),
                'categories': item.get('categories', []),
            })
    research['key_storylines'] = storylines

    return research


def save_research(research):
    """Save research to JSON files"""
    # Save to /tmp for GitHub Actions
    tmp_path = os.path.join(OUTPUT_DIR, f"mlb_research_{DATE_STR}.json")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(research, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {tmp_path}")

    # Also save to pending_content for local processing
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    pending_dir = os.path.join(repo_dir, 'pending_content')

    try:
        os.makedirs(pending_dir, exist_ok=True)
        local_path = os.path.join(pending_dir, f"mlb_research_{DATE_STR}.json")
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
    print("MLB RESEARCH COMPLETE")
    print("=" * 60)
    print(f"News articles: {len(research['news_items'])}")
    print(f"Transactions: {len(research['transactions'])}")
    print(f"Players mentioned: {len(research['extracted_players'])}")
    print(f"Key storylines: {len(research['key_storylines'])}")
    print(f"\nTarget sites: {', '.join([s['name'] for s in research['target_sites']])}")
    print(f"Each site will get UNIQUE content with different angle")
    print(f"\nStatus: {research['status']}")
    print("Run /daily-content in Claude Code to process into elite articles")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
