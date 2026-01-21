#!/usr/bin/env python3
"""
Real AI Girls Research Gatherer
================================
Gathers REAL AI art/image generation news from multiple sources.
Does NOT generate final content - Claude Code processes this into elite articles.

The research is saved to pending_content/realaigirls_research_YYYY-MM-DD.json
When user runs /daily-content, Claude Code reads this and writes quality blog posts.

Topics covered:
- AI image generation tools (Flux, Stable Diffusion, Midjourney, DALL-E)
- Prompt engineering techniques
- AI art trends and tutorials
- Industry news and model releases
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

# Search queries for AI art news
SEARCH_QUERIES = [
    "Stable Diffusion new model",
    "Flux AI image generator",
    "Midjourney update",
    "AI art prompt engineering",
    "AI image generation tutorial",
    "DALL-E news",
    "AI portrait generation",
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
    """Fetch AI-related posts from Hacker News"""
    results = []
    try:
        # Search HN for AI image-related posts
        url = "https://hn.algolia.com/api/v1/search?query=AI%20image%20generation&tags=story&hitsPerPage=10"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for hit in data.get('hits', [])[:10]:
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


def fetch_reddit_ai_art():
    """Fetch from AI art subreddits"""
    results = []
    subreddits = ['StableDiffusion', 'midjourney', 'aiArt']

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
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


def extract_ai_tools_mentioned(text):
    """Extract AI tools/models mentioned in text"""
    tools = []
    if not text:
        return tools

    text_lower = text.lower()

    tool_patterns = [
        ('Stable Diffusion', ['stable diffusion', 'sd 3', 'sdxl', 'sd1.5', 'sd2']),
        ('Flux', ['flux', 'flux.1', 'flux pro', 'flux dev']),
        ('Midjourney', ['midjourney', 'mj', 'midj']),
        ('DALL-E', ['dall-e', 'dalle', 'dall e', 'dalle 3']),
        ('ComfyUI', ['comfyui', 'comfy ui']),
        ('Automatic1111', ['automatic1111', 'a1111', 'webui']),
        ('LoRA', ['lora', 'loras']),
        ('ControlNet', ['controlnet', 'control net']),
        ('Runway', ['runway', 'runway ml']),
        ('Leonardo AI', ['leonardo ai', 'leonardo.ai']),
    ]

    for tool_name, patterns in tool_patterns:
        for pattern in patterns:
            if pattern in text_lower:
                if tool_name not in tools:
                    tools.append(tool_name)
                break

    return tools


def extract_techniques(text):
    """Extract prompt engineering techniques mentioned"""
    techniques = []
    if not text:
        return techniques

    text_lower = text.lower()

    technique_patterns = [
        'prompt engineering',
        'negative prompt',
        'img2img',
        'inpainting',
        'outpainting',
        'upscaling',
        'face fix',
        'adetailer',
        'cfg scale',
        'sampling',
        'denoising',
        'seed',
        'batch',
        'checkpoint',
        'embedding',
        'textual inversion',
    ]

    for technique in technique_patterns:
        if technique in text_lower:
            techniques.append(technique)

    return techniques


# =============================================================================
# RESEARCH GATHERING
# =============================================================================

def gather_research():
    """Main research gathering function"""
    print("=" * 60)
    print(f"REAL AI GIRLS RESEARCH GATHERER - {DATE_DISPLAY}")
    print("=" * 60)

    research = {
        'site': 'realaigirls',
        'date': DATE_STR,
        'gathered_at': datetime.now().isoformat(),
        'status': 'pending_processing',
        'news_items': [],
        'hacker_news': [],
        'reddit_posts': [],
        'tools_mentioned': [],
        'techniques_found': [],
        'suggested_topics': [],
    }

    # Gather from Google News
    print("\n[1/3] Fetching AI Art News...")
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

    research['news_items'] = unique_news[:15]
    print(f"  Total unique news items: {len(research['news_items'])}")

    # Gather from Hacker News
    print("\n[2/3] Fetching Hacker News...")
    hn_items = fetch_hacker_news_ai()
    research['hacker_news'] = hn_items[:10]
    print(f"  Found {len(research['hacker_news'])} HN posts")

    # Gather from Reddit
    print("\n[3/3] Fetching Reddit AI Art Communities...")
    reddit_items = fetch_reddit_ai_art()
    research['reddit_posts'] = reddit_items[:15]
    print(f"  Found {len(research['reddit_posts'])} Reddit posts")

    # Extract tools and techniques from all content
    print("\n[4/4] Extracting tools and techniques...")
    all_text = ""
    for item in research['news_items']:
        all_text += f" {item.get('title', '')} {item.get('snippet', '')}"
    for item in research['hacker_news']:
        all_text += f" {item.get('title', '')}"
    for item in research['reddit_posts']:
        all_text += f" {item.get('title', '')}"

    research['tools_mentioned'] = extract_ai_tools_mentioned(all_text)
    research['techniques_found'] = extract_techniques(all_text)
    print(f"  Tools mentioned: {research['tools_mentioned']}")
    print(f"  Techniques found: {research['techniques_found']}")

    # Generate suggested topics based on findings
    research['suggested_topics'] = []
    if 'Flux' in research['tools_mentioned']:
        research['suggested_topics'].append("Flux model update/tutorial")
    if 'Stable Diffusion' in research['tools_mentioned']:
        research['suggested_topics'].append("Stable Diffusion tips and tricks")
    if 'LoRA' in research['tools_mentioned']:
        research['suggested_topics'].append("LoRA training guide")
    if 'prompt engineering' in research['techniques_found']:
        research['suggested_topics'].append("Prompt engineering deep dive")
    if len(research['reddit_posts']) > 5:
        research['suggested_topics'].append("Community trends roundup")

    return research


def save_research(research):
    """Save research to JSON files"""
    # Save to /tmp for GitHub Actions
    tmp_path = os.path.join(OUTPUT_DIR, f"realaigirls_research_{DATE_STR}.json")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(research, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {tmp_path}")

    # Also save to pending_content for local processing
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    pending_dir = os.path.join(repo_dir, 'pending_content')

    try:
        os.makedirs(pending_dir, exist_ok=True)
        local_path = os.path.join(pending_dir, f"realaigirls_research_{DATE_STR}.json")
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
    print(f"AI tools mentioned: {', '.join(research['tools_mentioned']) or 'None'}")
    print(f"\nSuggested topics: {research['suggested_topics']}")
    print(f"\nStatus: {research['status']}")
    print("Run /daily-content in Claude Code to process into elite blog post")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
