#!/usr/bin/env python3
"""
Real AI Girls Blog Content Generator
=====================================
Generates daily blog articles about AI art, image generation,
tutorials, and industry news.

Site: realaigirls.com (FTP hosted)
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
    'directory': '/realaigirls.com/'
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
    """Generate a daily AI art blog article"""

    prompt = f"""You are a blogger who writes about AI-generated art and images. Today is {DATE_DISPLAY}.

Write an engaging blog post about ONE of these topics (pick the most interesting):

TOPIC OPTIONS:
1. New AI image generation techniques or models (Flux, Stable Diffusion updates, etc.)
2. Tips for creating better AI portraits or character images
3. Prompt engineering secrets for photorealistic results
4. Comparison of different AI image generators
5. The ethics and future of AI-generated imagery
6. How to fix common AI image problems (hands, faces, etc.)
7. Style transfer and artistic techniques with AI
8. Behind the scenes of popular AI art trends

REQUIREMENTS:
1. Write 600-900 words
2. Be helpful and informative
3. Include practical tips readers can use
4. Use a friendly, accessible tone
5. Add 2-3 subheadings
6. Focus on the creative and artistic aspects
7. Keep it tasteful and professional

FORMAT YOUR RESPONSE AS:
HEADLINE: [Your engaging headline here]
---
[Article content with HTML formatting: <h2> for subheads, <p> for paragraphs]

Write the article now:"""

    content = call_claude_api(prompt)

    # Parse headline and body
    parts = content.split('---', 1)
    if len(parts) == 2:
        headline = parts[0].replace('HEADLINE:', '').strip()
        body = parts[1].strip()
    else:
        headline = f"AI Art Insights - {DATE_DISPLAY}"
        body = content

    return headline, body


def generate_full_html(headline: str, body: str) -> str:
    """Generate full HTML page"""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline} | Real AI Girls Blog</title>
    <meta name="description" content="AI art tips, tutorials, and insights. {DATE_DISPLAY}">
    <meta name="keywords" content="AI art, AI images, Stable Diffusion, Flux, AI portraits, prompt engineering">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #e0e0e0; line-height: 1.8; min-height: 100vh; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        header {{ text-align: center; margin-bottom: 40px; }}
        .site-title {{ color: #ff6b9d; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
        h1 {{ color: #fff; font-size: 2rem; line-height: 1.3; margin-bottom: 10px; }}
        .meta {{ color: #888; font-size: 14px; }}
        article {{ background: rgba(255,255,255,0.05); padding: 30px; border-radius: 12px; backdrop-filter: blur(10px); }}
        article h2 {{ color: #ff6b9d; font-size: 1.4rem; margin: 25px 0 12px 0; }}
        article p {{ margin-bottom: 18px; font-size: 17px; }}
        .back-link {{ text-align: center; margin-top: 30px; }}
        .back-link a {{ color: #ff6b9d; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="site-title">Real AI Girls Blog</div>
            <h1>{headline}</h1>
            <p class="meta">{DATE_DISPLAY}</p>
        </header>
        <article>
            {body}
        </article>
        <div class="back-link">
            <a href="blog.html">&larr; Back to Blog</a>
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

        print(f"  [OK] Uploaded to realaigirls.com")
        return True
    except Exception as e:
        print(f"  [ERROR] FTP: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("REAL AI GIRLS BLOG GENERATOR")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("\n[ERROR] ANTHROPIC_API_KEY not set.")
        return

    # Generate article
    print("\n[1] Generating AI art blog article...")
    try:
        headline, body = generate_article()
        print(f"  Generated: {headline[:50]}...")
    except Exception as e:
        print(f"  [ERROR] Failed: {e}")
        return

    # Generate HTML
    html = generate_full_html(headline, body)
    filename = f"blog-{DATE_STR}.html"

    # Save locally
    os.makedirs('daily', exist_ok=True)
    with open(f"daily/rag-{filename}", 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n[2] Saved locally: daily/rag-{filename}")

    # Upload to FTP
    print("\n[3] Uploading to FTP...")
    upload_to_ftp(html, filename)

    print("\n" + "=" * 60)
    print("REAL AI GIRLS GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
