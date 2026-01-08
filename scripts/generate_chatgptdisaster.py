#!/usr/bin/env python3
"""
ChatGPT Disaster Daily Content Generator
=========================================
Generates daily articles about AI failures, ChatGPT controversies,
and tech disasters using Claude API.

Site: chatgptdisaster.com (GitHub hosted: Nimadamus/chatgptdisaster)
"""

import os
import json
import requests
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")

# =============================================================================
# CLAUDE API
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


def generate_article() -> tuple:
    """Generate a daily AI disaster/controversy article"""

    prompt = f"""You are a tech journalist who covers AI failures, ChatGPT controversies, and technology disasters. Today is {DATE_DISPLAY}.

Write a compelling, well-researched article about ONE of these topics (pick the most interesting):

TOPIC OPTIONS:
1. A recent AI hallucination incident (lawyers citing fake cases, medical misdiagnosis, etc.)
2. ChatGPT or AI chatbot controversy (privacy concerns, biased outputs, jailbreaks)
3. AI company scandal or failure (layoffs, product failures, ethical issues)
4. Deepfake or AI-generated misinformation incident
5. AI replacing workers gone wrong
6. AI in healthcare, legal, or finance causing problems
7. Tech giant AI project that flopped
8. AI safety concerns from researchers

REQUIREMENTS:
1. Write 800-1200 words
2. Use a catchy, clickbait-worthy headline
3. Be factual but entertaining - this is for a site called "ChatGPT Disaster"
4. Include specific examples, dates, and details (you can reference real incidents from your knowledge)
5. Add commentary and analysis
6. End with implications for the future of AI
7. Be conversational and engaging, not dry academic writing
8. Include 2-3 subheadings to break up the content

FORMAT YOUR RESPONSE AS:
HEADLINE: [Your catchy headline here]
---
[Article content with HTML formatting: <h2> for subheads, <p> for paragraphs, <strong> for emphasis]

Write the article now:"""

    content = call_claude_api(prompt)

    # Parse headline and body
    parts = content.split('---', 1)
    if len(parts) == 2:
        headline = parts[0].replace('HEADLINE:', '').strip()
        body = parts[1].strip()
    else:
        headline = f"AI Disaster Report - {DATE_DISPLAY}"
        body = content

    return headline, body


def generate_full_html(headline: str, body: str) -> str:
    """Generate full HTML page"""

    seo_desc = f"Daily coverage of AI failures, ChatGPT disasters, and tech controversies. {DATE_DISPLAY} edition."

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline} | ChatGPT Disaster</title>
    <meta name="description" content="{seo_desc}">
    <meta name="keywords" content="ChatGPT, AI failures, AI disasters, artificial intelligence, tech news, AI controversy">
    <meta property="og:title" content="{headline}">
    <meta property="og:description" content="{seo_desc}">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #1a1a1a; --card: #2d2d2d; --accent: #ff4444; --text: #e0e0e0; --muted: #888; }}
        body {{ font-family: 'Georgia', serif; background: var(--bg); color: var(--text); line-height: 1.9; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        header {{ text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid var(--accent); }}
        .site-title {{ color: var(--accent); font-size: 1.2rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 20px; }}
        h1 {{ color: #fff; font-size: 2.2rem; line-height: 1.3; margin-bottom: 15px; }}
        .meta {{ color: var(--muted); font-size: 14px; }}
        article {{ background: var(--card); padding: 35px; border-radius: 8px; }}
        article h2 {{ color: var(--accent); font-size: 1.5rem; margin: 30px 0 15px 0; }}
        article p {{ margin-bottom: 20px; font-size: 18px; }}
        article strong {{ color: #fff; }}
        .back-link {{ text-align: center; margin-top: 40px; }}
        .back-link a {{ color: var(--accent); text-decoration: none; font-weight: bold; }}
        .back-link a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="site-title">ChatGPT Disaster</div>
            <h1>{headline}</h1>
            <p class="meta">{DATE_DISPLAY} | Daily AI Disaster Report</p>
        </header>

        <article>
            {body}
        </article>

        <div class="back-link">
            <a href="index.html">&larr; Back to Home</a>
        </div>
    </div>
</body>
</html>'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("CHATGPT DISASTER CONTENT GENERATOR")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("\n[ERROR] ANTHROPIC_API_KEY not set.")
        return

    # Generate article
    print("\n[1] Generating AI disaster article via Claude API...")
    try:
        headline, body = generate_article()
        print(f"  Generated: {headline[:50]}...")
    except Exception as e:
        print(f"  [ERROR] Failed: {e}")
        return

    # Generate HTML
    html = generate_full_html(headline, body)

    # Save locally
    os.makedirs('daily', exist_ok=True)
    filename = f"daily/cgd-article-{DATE_STR}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n[2] Saved: {filename}")

    # Also save to /tmp for workflow
    tmp_path = f"/tmp/cgd-article-{DATE_STR}.html"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[3] Saved for workflow: {tmp_path}")
    except:
        pass

    print("\n" + "=" * 60)
    print("CHATGPT DISASTER GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
