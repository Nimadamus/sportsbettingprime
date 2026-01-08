#!/usr/bin/env python3
"""
His Name Is Chip Daily Content Generator
=========================================
Generates daily blog/humor content.

Site: hisnameischip.com (FTP hosted)
"""

import os
import json
import requests
import ftplib
import io
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

FTP_CONFIG = {
    'host': os.environ.get('FTP_HOST', '208.109.70.186'),
    'user': os.environ.get('FTP_USER', ''),
    'password': os.environ.get('FTP_PASS', ''),
    'directory': '/hisnameischip.com/'
}

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
    """Generate a daily humor/entertainment article"""

    prompt = f"""You are a witty blogger named Chip who writes entertaining, irreverent takes on modern life. Today is {DATE_DISPLAY}.

Write a funny, engaging blog post about ONE of these topics:

TOPIC OPTIONS:
1. Absurd observations about everyday life
2. Hot takes on current trends or pop culture
3. Satirical commentary on technology and social media
4. Humorous life advice nobody asked for
5. Rants about minor inconveniences
6. Fictional stories about bizarre situations
7. Reviews of mundane things (like different types of socks)
8. Conspiracy theories about harmless things

REQUIREMENTS:
1. Write 500-800 words
2. Be genuinely funny - dry humor, wit, sarcasm welcome
3. Write in first person as "Chip"
4. Include unexpected observations
5. Have a conversational, blog-style tone
6. Add 1-2 subheadings if it fits
7. End with something memorable

FORMAT YOUR RESPONSE AS:
HEADLINE: [Your funny headline here]
---
[Article content with HTML: <h2> for subheads, <p> for paragraphs]

Write the article now:"""

    content = call_claude_api(prompt)

    # Parse headline and body
    parts = content.split('---', 1)
    if len(parts) == 2:
        headline = parts[0].replace('HEADLINE:', '').strip()
        body = parts[1].strip()
    else:
        headline = f"Chip's Daily Dispatch - {DATE_DISPLAY}"
        body = content

    return headline, body


def generate_full_html(headline: str, body: str) -> str:
    """Generate full HTML page"""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline} | His Name Is Chip</title>
    <meta name="description" content="Daily humor and hot takes from Chip. {DATE_DISPLAY}">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Courier New', monospace; background: #fefefe; color: #222; line-height: 1.8; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 50px 20px; }}
        header {{ margin-bottom: 40px; padding-bottom: 20px; border-bottom: 3px solid #222; }}
        .site-title {{ font-size: 0.9rem; text-transform: uppercase; letter-spacing: 4px; color: #666; }}
        h1 {{ font-size: 2rem; margin-top: 15px; line-height: 1.2; }}
        .meta {{ color: #888; font-size: 13px; margin-top: 10px; }}
        article {{ font-size: 18px; }}
        article h2 {{ font-size: 1.3rem; margin: 30px 0 15px 0; border-left: 4px solid #222; padding-left: 15px; }}
        article p {{ margin-bottom: 20px; }}
        .back-link {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .back-link a {{ color: #222; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="site-title">His Name Is Chip</div>
            <h1>{headline}</h1>
            <p class="meta">{DATE_DISPLAY} &bull; By Chip</p>
        </header>
        <article>
            {body}
        </article>
        <div class="back-link">
            <a href="index.html">&larr; More from Chip</a>
        </div>
    </div>
</body>
</html>'''


def upload_to_ftp(html_content: str, filename: str) -> bool:
    """Upload to FTP"""
    if not FTP_CONFIG['user']:
        print("  [WARN] FTP credentials not set")
        return False

    try:
        ftp = ftplib.FTP()
        ftp.connect(FTP_CONFIG['host'], 21, timeout=30)
        ftp.login(FTP_CONFIG['user'], FTP_CONFIG['password'])
        ftp.cwd(FTP_CONFIG['directory'])

        upload_data = io.BytesIO(html_content.encode('utf-8'))
        ftp.storbinary(f'STOR {filename}', upload_data)
        ftp.quit()

        print(f"  [OK] Uploaded to hisnameischip.com")
        return True
    except Exception as e:
        print(f"  [ERROR] FTP: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("HIS NAME IS CHIP CONTENT GENERATOR")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("\n[ERROR] ANTHROPIC_API_KEY not set.")
        return

    # Generate article
    print("\n[1] Generating Chip's daily post...")
    try:
        headline, body = generate_article()
        print(f"  Generated: {headline[:50]}...")
    except Exception as e:
        print(f"  [ERROR] Failed: {e}")
        return

    # Generate HTML
    html = generate_full_html(headline, body)
    filename = f"post-{DATE_STR}.html"

    # Save locally
    os.makedirs('daily', exist_ok=True)
    with open(f"daily/chip-{filename}", 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n[2] Saved locally: daily/chip-{filename}")

    # Upload to FTP
    print("\n[3] Uploading to FTP...")
    upload_to_ftp(html, filename)

    print("\n" + "=" * 60)
    print("HIS NAME IS CHIP GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
