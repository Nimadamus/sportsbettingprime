#!/usr/bin/env python3
"""
LOLSBA Research Gatherer
========================
Gathers REAL SBA/PPP news from multiple sources and saves structured research.
Does NOT generate final content - Claude Code processes this into elite articles.

The research is saved to pending_content/lolsba_research_YYYY-MM-DD.json
When user runs /daily-content, Claude Code reads this and writes quality journalism.
"""
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus
import re

TODAY = datetime.now()
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
DATE_STR = TODAY.strftime("%Y-%m-%d")
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/tmp')

# Multiple search queries for comprehensive research
SEARCH_QUERIES = [
    "SBA PPP fraud arrest",
    "SBA EIDL investigation",
    "PPP loan fraud sentenced",
    "SBA inspector general",
    "small business loan fraud charges",
]

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

def fetch_doj_rss():
    """Fetch from DOJ press releases RSS"""
    results = []
    try:
        # DOJ Press Releases RSS
        url = "https://www.justice.gov/feeds/opa/justice-news.xml"
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item')[:20]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')

                title = title_el.text if title_el is not None else ''
                # Filter for SBA/PPP related
                if any(kw in title.lower() for kw in ['sba', 'ppp', 'eidl', 'covid', 'relief', 'loan fraud', 'pandemic']):
                    results.append({
                        'title': title,
                        'url': link_el.text if link_el is not None else '',
                        'snippet': desc_el.text[:500] if desc_el is not None and desc_el.text else '',
                        'source': 'doj_official',
                        'query': 'DOJ feed',
                    })
    except Exception as e:
        print(f"  [WARN] DOJ RSS fetch failed: {e}")
    return results

def extract_facts_from_text(text):
    """Extract key facts from news text"""
    facts = []
    if not text:
        return facts

    # Dollar amounts
    dollars = re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|M|B))?', text, re.I)
    for d in dollars:
        facts.append({'type': 'money', 'value': d})

    # Prison sentences
    sentences = re.findall(r'(\d+)\s*(?:year|month)s?\s*(?:in\s*)?(?:prison|jail|federal)', text, re.I)
    for s in sentences:
        facts.append({'type': 'sentence', 'value': f"{s} years/months"})

    # People charged/arrested
    charged = re.findall(r'(\d+)\s*(?:people|individuals|defendants?|persons?)\s*(?:charged|arrested|indicted)', text, re.I)
    for c in charged:
        facts.append({'type': 'charged', 'value': f"{c} people"})

    # Locations (states)
    states = re.findall(r'(?:in|from)\s+(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)', text, re.I)
    for s in states:
        facts.append({'type': 'location', 'value': s})

    return facts

def gather_research():
    """Main research gathering function"""
    print("=" * 60)
    print(f"LOLSBA RESEARCH GATHERER - {DATE_DISPLAY}")
    print("=" * 60)

    research = {
        'site': 'lolsba',
        'date': DATE_STR,
        'gathered_at': datetime.now().isoformat(),
        'status': 'pending_processing',
        'news_items': [],
        'extracted_facts': [],
        'doj_items': [],
        'suggested_topics': [],
    }

    # Gather from Google News
    print("\n[1/2] Fetching Google News...")
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
        title_key = item['title'].lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(item)

    research['news_items'] = unique_news[:15]
    print(f"  Total unique news items: {len(research['news_items'])}")

    # Gather from DOJ
    print("\n[2/2] Fetching DOJ Press Releases...")
    doj_items = fetch_doj_rss()
    research['doj_items'] = doj_items[:10]
    print(f"  Found {len(research['doj_items'])} relevant DOJ items")

    # Extract facts from all content
    print("\n[3/3] Extracting key facts...")
    all_facts = []
    for item in research['news_items'] + research['doj_items']:
        text = f"{item.get('title', '')} {item.get('snippet', '')}"
        facts = extract_facts_from_text(text)
        all_facts.extend(facts)

    # Deduplicate facts
    seen_facts = set()
    unique_facts = []
    for fact in all_facts:
        key = f"{fact['type']}:{fact['value']}"
        if key not in seen_facts:
            seen_facts.add(key)
            unique_facts.append(fact)

    research['extracted_facts'] = unique_facts
    print(f"  Extracted {len(unique_facts)} unique facts")

    # Generate suggested topics based on findings
    research['suggested_topics'] = []
    if any('doj' in item.get('source', '') for item in research['doj_items']):
        research['suggested_topics'].append("DOJ enforcement action analysis")
    if any(f['type'] == 'money' for f in unique_facts):
        research['suggested_topics'].append("Financial impact breakdown")
    if any(f['type'] == 'sentence' for f in unique_facts):
        research['suggested_topics'].append("Sentencing trends analysis")
    if any(f['type'] == 'charged' for f in unique_facts):
        research['suggested_topics'].append("Prosecution statistics roundup")

    return research

def save_research(research):
    """Save research to JSON files"""
    # Save to /tmp for GitHub Actions
    tmp_path = os.path.join(OUTPUT_DIR, f"lolsba_research_{DATE_STR}.json")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(research, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {tmp_path}")

    # Also save to pending_content for local processing
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    pending_dir = os.path.join(repo_dir, 'pending_content')

    try:
        os.makedirs(pending_dir, exist_ok=True)
        local_path = os.path.join(pending_dir, f"lolsba_research_{DATE_STR}.json")
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(research, f, indent=2, ensure_ascii=False)
        print(f"Also saved to: {local_path}")
    except Exception as e:
        print(f"[WARN] Could not save to pending_content: {e}")

    return tmp_path

def main():
    research = gather_research()
    save_research(research)

    print("\n" + "=" * 60)
    print("RESEARCH COMPLETE")
    print("=" * 60)
    print(f"News items gathered: {len(research['news_items'])}")
    print(f"DOJ items gathered: {len(research['doj_items'])}")
    print(f"Facts extracted: {len(research['extracted_facts'])}")
    print(f"\nStatus: {research['status']}")
    print("Run /daily-content in Claude Code to process into elite article")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    exit(main())
