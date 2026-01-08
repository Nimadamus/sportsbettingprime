#!/usr/bin/env python3
"""
MLB Daily News Generator
=========================
Generates daily MLB news articles during the offseason.
Searches for latest MLB news, sends to Claude API for human-quality writing,
and uploads to all 3 MLB sites via FTP.

Sites:
- dailymlbpicks.com
- mlbprediction.com
- bestmlbhandicapper.com
"""

import os
import json
import requests
import ftplib
import io
from datetime import datetime
from typing import Dict, List

# =============================================================================
# CONFIGURATION
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# FTP Configuration (from environment variables)
FTP_CONFIG = {
    'host': os.environ.get('FTP_HOST', ''),
    'user': os.environ.get('FTP_USER', ''),
    'password': os.environ.get('FTP_PASS', ''),
}

MLB_SITES = [
    {'dir': '/dailymlbpicks.com/', 'name': 'Daily MLB Picks'},
    {'dir': '/mlbprediction.com/', 'name': 'MLB Prediction'},
    {'dir': '/bestmlbhandicapper.com/', 'name': 'Best MLB Handicapper'},
]

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")

# ESPN MLB News API
ESPN_MLB_NEWS = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news"

# =============================================================================
# NEWS FETCHING
# =============================================================================

def fetch_mlb_news() -> List[Dict]:
    """Fetch latest MLB news from ESPN API"""
    try:
        response = requests.get(ESPN_MLB_NEWS, timeout=30)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get('articles', [])[:10]:  # Get top 10 stories
            articles.append({
                'headline': article.get('headline', ''),
                'description': article.get('description', ''),
                'published': article.get('published', ''),
                'type': article.get('type', 'article'),
            })

        return articles
    except Exception as e:
        print(f"  [ERROR] ESPN News API: {e}")
        return []


def fetch_mlb_transactions() -> List[Dict]:
    """Fetch recent MLB transactions"""
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/transactions"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        transactions = []
        for item in data.get('items', [])[:15]:  # Get recent transactions
            transactions.append({
                'date': item.get('date', ''),
                'description': item.get('description', ''),
                'team': item.get('team', {}).get('displayName', ''),
            })

        return transactions
    except Exception as e:
        print(f"  [WARN] Transactions API: {e}")
        return []


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


def generate_news_article(news: List[Dict], transactions: List[Dict]) -> str:
    """Generate a daily news article using Claude API"""

    # Build news summary for Claude
    news_summary = "\n".join([
        f"- {item['headline']}: {item['description']}"
        for item in news if item['headline']
    ])

    transaction_summary = "\n".join([
        f"- {item['team']}: {item['description']}"
        for item in transactions if item['description']
    ]) or "No major transactions today."

    prompt = f"""You are a veteran baseball writer covering MLB for a popular sports betting site. Today is {DATE_DISPLAY}.

Write an engaging daily MLB news roundup article. Here's today's news and transactions:

**TOP HEADLINES:**
{news_summary}

**RECENT TRANSACTIONS:**
{transaction_summary}

REQUIREMENTS:
1. Write 5-7 paragraphs covering the most interesting stories
2. Be conversational and engaging - write like a passionate baseball fan
3. Include analysis on how news affects betting futures (team win totals, division odds, MVP odds)
4. Mention specific players and their fantasy/betting implications
5. Use contractions and casual language
6. Include a section on "What This Means for Bettors"
7. End with what to watch for tomorrow
8. NO placeholder text, NO generic filler
9. Make it feel like insider analysis, not just news regurgitation

Format your response as the article body HTML (just the content, I'll add the wrapper):
<div class="article-content">
    <p class="intro">[Opening hook paragraph]</p>
    <h2>Today's Top Stories</h2>
    <p>[Story 1 analysis]</p>
    <p>[Story 2 analysis]</p>
    <h2>Transaction Wire</h2>
    <p>[Transaction analysis]</p>
    <h2>What This Means for Bettors</h2>
    <p>[Betting implications]</p>
    <h2>Looking Ahead</h2>
    <p>[What to watch tomorrow]</p>
</div>

Write the article now. Make it feel like expert analysis from someone who lives and breathes baseball."""

    return call_claude_api(prompt)


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_full_html(article_html: str, headline: str) -> str:
    """Generate full HTML page with SEO optimization"""

    seo_desc = f"MLB Daily News for {DATE_DISPLAY}. Latest trades, signings, rumors and what they mean for baseball bettors."

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- SEO -->
    <title>{headline} | MLB Daily News - {DATE_DISPLAY}</title>
    <meta name="description" content="{seo_desc}">
    <meta name="keywords" content="MLB news, baseball news, MLB trades, MLB signings, MLB rumors, baseball betting, {DATE_DISPLAY}">
    <meta name="author" content="MLB Prediction">
    <meta name="robots" content="index, follow">

    <!-- OpenGraph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{headline}">
    <meta property="og:description" content="{seo_desc}">
    <meta property="og:image" content="https://a.espncdn.com/i/teamlogos/mlb/500/mlb.png">
    <meta property="article:published_time" content="{DATE_STR}T10:00:00-05:00">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{headline}">
    <meta name="twitter:description" content="{seo_desc}">

    <!-- JSON-LD -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": "{headline}",
        "datePublished": "{DATE_STR}",
        "author": {{"@type": "Organization", "name": "MLB Prediction"}},
        "publisher": {{"@type": "Organization", "name": "MLB Prediction"}}
    }}
    </script>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #1a1a2e; --card: #16213e; --accent: #e94560; --gold: #f1c40f; --text: #eee; }}
        body {{ font-family: 'Georgia', serif; background: var(--bg); color: var(--text); line-height: 1.9; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        header {{ text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid var(--accent); }}
        h1 {{ color: var(--gold); font-size: 2rem; margin-bottom: 10px; }}
        .date {{ color: #888; font-size: 14px; }}
        .article-content {{ background: var(--card); padding: 30px; border-radius: 12px; }}
        .article-content h2 {{ color: var(--accent); font-size: 1.4rem; margin: 25px 0 15px 0; padding-bottom: 8px; border-bottom: 1px solid #333; }}
        .article-content p {{ margin-bottom: 18px; font-size: 17px; }}
        .intro {{ font-size: 19px !important; font-style: italic; color: #ccc; }}
        .back-link {{ text-align: center; margin-top: 30px; }}
        .back-link a {{ color: var(--accent); text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{headline}</h1>
            <p class="date">{DATE_DISPLAY} | MLB Daily News</p>
        </header>

        {article_html}

        <div class="back-link">
            <a href="index.html">← Back to Home</a>
        </div>
    </div>
</body>
</html>'''


# =============================================================================
# FTP UPLOAD
# =============================================================================

def upload_to_site(html_content: str, site_config: Dict, filename: str) -> bool:
    """Upload HTML content to a site via FTP"""
    try:
        ftp = ftplib.FTP()
        ftp.connect(FTP_CONFIG['host'], 21, timeout=30)
        ftp.login(FTP_CONFIG['user'], FTP_CONFIG['password'])
        ftp.cwd(site_config['dir'])

        # Upload the file
        upload_data = io.BytesIO(html_content.encode('utf-8'))
        ftp.storbinary(f'STOR {filename}', upload_data)

        ftp.quit()
        print(f"  ✓ Uploaded to {site_config['name']}")
        return True
    except Exception as e:
        print(f"  ✗ Failed {site_config['name']}: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("MLB DAILY NEWS GENERATOR")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("\n[ERROR] ANTHROPIC_API_KEY not set.")
        return

    # Fetch news
    print("\n[1] Fetching MLB news from ESPN...")
    news = fetch_mlb_news()
    print(f"  Found {len(news)} news articles")

    print("\n[2] Fetching MLB transactions...")
    transactions = fetch_mlb_transactions()
    print(f"  Found {len(transactions)} transactions")

    if not news:
        print("\n[ERROR] No news found. Skipping generation.")
        return

    # Generate article via Claude
    print("\n[3] Generating article via Claude API...")
    try:
        article_html = generate_news_article(news, transactions)
        print(f"  Generated {len(article_html)} characters")
    except Exception as e:
        print(f"  [ERROR] Failed: {e}")
        return

    # Create headline from top story
    headline = f"MLB Daily: {news[0]['headline'][:50]}..." if news else f"MLB News Roundup - {DATE_DISPLAY}"

    # Generate full HTML
    html = generate_full_html(article_html, headline)

    # Save locally
    filename = f"mlb-news-{DATE_STR}.html"
    os.makedirs('daily', exist_ok=True)
    local_path = f"daily/{filename}"
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n[4] Saved locally: {local_path}")

    # Upload to all MLB sites
    print("\n[5] Uploading to MLB sites...")
    for site in MLB_SITES:
        upload_to_site(html, site, filename)

    # Also save to /tmp for GitHub Actions
    tmp_path = f"/tmp/mlb-article-{DATE_STR}.html"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n[6] Saved for workflow: {tmp_path}")
    except:
        pass

    print("\n" + "=" * 60)
    print("MLB NEWS GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
