#!/usr/bin/env python3
"""
ChatGPT Disaster Research Gatherer
====================================
Gathers REAL AI failure news, ChatGPT controversies, and tech disasters.
Does NOT generate final content - Claude Code processes this into elite articles.

The research is saved to pending_content/chatgptdisaster_research_YYYY-MM-DD.json
When user runs /daily-content, Claude Code reads this and writes quality journalism.

Site: chatgptdisaster.com (GitHub hosted: Nimadamus/chatgptdisaster)
Topics: AI failures, hallucinations, controversies, tech disasters, AI safety
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus
import re

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/tmp')

# Search queries for AI disaster news
SEARCH_QUERIES = [
    "ChatGPT failure",
    "AI hallucination lawsuit",
    "artificial intelligence controversy",
    "OpenAI scandal",
    "AI bias discrimination",
    "deepfake misinformation",
    "AI job replacement disaster",
    "AI safety concerns",
    "ChatGPT lawsuit",
    "AI generated mistakes",
]

# =============================================================================
# NEWS FETCHING
# =============================================================================

def fetch_google_news_rss(query):
    """Fetch news from Google News RSS"""
    results = []
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item')[:5]:
                title_el = item.find('title')
                link_el = item.find('link')
                pub_date_el = item.find('pubDate')
                desc_el = item.find('description')

                if title_el is not None:
                    results.append({
                        'title': title_el.text,
                        'url': link_el.text if link_el is not None else '',
                        'date': pub_date_el.text if pub_date_el is not None else '',
                        'snippet': desc_el.text[:300] if desc_el is not None and desc_el.text else '',
                        'source': 'google_news',
                        'query': query,
                    })
    except Exception as e:
        print(f"  [WARN] Google News fetch failed for '{query}': {e}")
    return results


def fetch_hacker_news_ai():
    """Fetch AI-related controversy posts from Hacker News"""
    results = []
    try:
        # Search for AI controversy/failure stories
        url = "https://hn.algolia.com/api/v1/search?query=AI%20failure%20OR%20ChatGPT%20OR%20OpenAI&tags=story&hitsPerPage=15"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for hit in data.get('hits', [])[:15]:
                title = hit.get('title', '').lower()
                # Filter for controversy/failure related posts
                if any(word in title for word in ['fail', 'problem', 'issue', 'concern', 'wrong', 'lawsuit', 'controversy', 'bias', 'harm', 'danger', 'mistake', 'error']):
                    results.append({
                        'title': hit.get('title', ''),
                        'url': hit.get('url', f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"),
                        'points': hit.get('points', 0),
                        'comments': hit.get('num_comments', 0),
                        'source': 'hacker_news',
                    })
    except Exception as e:
        print(f"  [WARN] Hacker News fetch failed: {e}")
    return results


def fetch_reddit_ai_controversy():
    """Fetch from AI controversy subreddits"""
    results = []
    subreddits = ['ChatGPT', 'artificial', 'technology', 'Futurology']

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/search.json?q=AI+failure+OR+controversy+OR+problem&restrict_sr=1&limit=5&sort=new"
            resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0 (research bot)'})
            if resp.status_code == 200:
                data = resp.json()
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    if not post_data.get('stickied', False):
                        results.append({
                            'title': post_data.get('title', ''),
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'upvotes': post_data.get('ups', 0),
                            'comments': post_data.get('num_comments', 0),
                            'subreddit': sub,
                            'source': 'reddit',
                        })
        except Exception as e:
            print(f"  [WARN] Reddit fetch failed for r/{sub}: {e}")

    return results


def categorize_stories(items):
    """Categorize stories by type of AI disaster"""
    categories = {
        'hallucination': [],
        'lawsuit': [],
        'bias': [],
        'job_loss': [],
        'safety': [],
        'deepfake': [],
        'privacy': [],
        'general_failure': [],
    }

    keywords = {
        'hallucination': ['hallucination', 'made up', 'fake', 'fabricated', 'invented', 'false'],
        'lawsuit': ['lawsuit', 'sued', 'legal', 'court', 'lawyer', 'attorney'],
        'bias': ['bias', 'discriminat', 'racist', 'sexist', 'unfair'],
        'job_loss': ['job', 'layoff', 'replace', 'automat', 'worker', 'employment'],
        'safety': ['safety', 'danger', 'risk', 'harm', 'concern', 'warning'],
        'deepfake': ['deepfake', 'fake video', 'synthetic', 'impersonat'],
        'privacy': ['privacy', 'data', 'leak', 'breach', 'personal information'],
    }

    for item in items:
        title_lower = item.get('title', '').lower()
        snippet_lower = item.get('snippet', '').lower()
        text = title_lower + ' ' + snippet_lower

        categorized = False
        for category, kws in keywords.items():
            if any(kw in text for kw in kws):
                categories[category].append(item)
                categorized = True
                break

        if not categorized:
            categories['general_failure'].append(item)

    return categories


def extract_companies_mentioned(items):
    """Extract AI companies mentioned in the news"""
    companies = []
    company_patterns = [
        'OpenAI', 'ChatGPT', 'GPT-4', 'GPT-5',
        'Google', 'Gemini', 'Bard',
        'Anthropic', 'Claude',
        'Microsoft', 'Copilot', 'Bing',
        'Meta', 'Llama',
        'Midjourney', 'Stable Diffusion', 'DALL-E',
        'Tesla', 'Autopilot', 'FSD',
        'Amazon', 'Alexa',
        'Apple', 'Siri',
    ]

    for item in items:
        text = item.get('title', '') + ' ' + item.get('snippet', '')
        for company in company_patterns:
            if company.lower() in text.lower():
                if company not in companies:
                    companies.append(company)

    return companies


# =============================================================================
# RESEARCH GATHERING
# =============================================================================

def gather_research():
    """Main research gathering function"""
    print("=" * 60)
    print(f"CHATGPT DISASTER RESEARCH GATHERER - {DATE_DISPLAY}")
    print("=" * 60)

    research = {
        'site': 'chatgptdisaster',
        'date': DATE_STR,
        'gathered_at': datetime.now().isoformat(),
        'status': 'pending_processing',
        'news_items': [],
        'hacker_news': [],
        'reddit_posts': [],
        'categories': {},
        'companies_mentioned': [],
        'suggested_topics': [],
    }

    # Gather from Google News
    print("\n[1/3] Fetching AI Disaster News...")
    all_news = []
    for query in SEARCH_QUERIES:
        print(f"  Searching: {query}")
        items = fetch_google_news_rss(query)
        all_news.extend(items)
        print(f"    Found {len(items)} results")

    # Deduplicate by title
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title_key = item['title'].lower()[:50] if item.get('title') else ''
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(item)

    research['news_items'] = unique_news[:20]
    print(f"  Total unique news items: {len(research['news_items'])}")

    # Gather from Hacker News
    print("\n[2/3] Fetching Hacker News...")
    hn_items = fetch_hacker_news_ai()
    research['hacker_news'] = hn_items[:10]
    print(f"  Found {len(research['hacker_news'])} relevant HN posts")

    # Gather from Reddit
    print("\n[3/3] Fetching Reddit discussions...")
    reddit_items = fetch_reddit_ai_controversy()
    research['reddit_posts'] = reddit_items[:10]
    print(f"  Found {len(research['reddit_posts'])} Reddit posts")

    # Categorize all stories
    print("\n[4/4] Categorizing stories...")
    all_items = research['news_items'] + research['hacker_news'] + research['reddit_posts']
    research['categories'] = categorize_stories(all_items)

    for cat, items in research['categories'].items():
        if items:
            print(f"  {cat}: {len(items)} stories")

    # Extract companies mentioned
    research['companies_mentioned'] = extract_companies_mentioned(all_items)
    print(f"  Companies mentioned: {research['companies_mentioned']}")

    # Generate suggested topics
    research['suggested_topics'] = []

    if research['categories']['hallucination']:
        research['suggested_topics'].append("AI Hallucination: When Chatbots Make Things Up")

    if research['categories']['lawsuit']:
        research['suggested_topics'].append("The Legal Battles Brewing in AI-Land")

    if research['categories']['bias']:
        research['suggested_topics'].append("AI's Bias Problem Isn't Getting Better")

    if research['categories']['safety']:
        research['suggested_topics'].append("AI Safety Warnings You Should Actually Pay Attention To")

    if 'OpenAI' in research['companies_mentioned'] or 'ChatGPT' in research['companies_mentioned']:
        research['suggested_topics'].append("OpenAI's Latest Mess: A Deep Dive")

    if not research['suggested_topics']:
        research['suggested_topics'] = [
            "This Week in AI Disasters",
            "Why Your AI Chatbot Can't Be Trusted",
            "The AI Hype vs Reality Check",
        ]

    return research


def save_research(research):
    """Save research to JSON files"""
    # Save to /tmp for GitHub Actions
    tmp_path = os.path.join(OUTPUT_DIR, f"chatgptdisaster_research_{DATE_STR}.json")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(research, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {tmp_path}")

    # Also save to pending_content for local processing
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    pending_dir = os.path.join(repo_dir, 'pending_content')

    try:
        os.makedirs(pending_dir, exist_ok=True)
        local_path = os.path.join(pending_dir, f"chatgptdisaster_research_{DATE_STR}.json")
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
    print(f"News items gathered: {len(research['news_items'])}")
    print(f"Hacker News posts: {len(research['hacker_news'])}")
    print(f"Reddit posts: {len(research['reddit_posts'])}")
    print(f"Companies mentioned: {', '.join(research['companies_mentioned']) or 'None'}")
    print(f"\nSuggested topics:")
    for topic in research['suggested_topics']:
        print(f"  - {topic}")
    print(f"\nStatus: {research['status']}")
    print("Run /daily-content in Claude Code to process into elite article")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
