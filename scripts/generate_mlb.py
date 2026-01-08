#!/usr/bin/env python3
"""Generate MLB article from real news"""
import requests
import random
import xml.etree.ElementTree as ET
from datetime import datetime

TODAY = datetime.now()
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
DATE_STR = TODAY.strftime("%Y-%m-%d")

# Try to fetch real MLB news
title = None
try:
    url = "https://news.google.com/rss/search?q=MLB+free+agent+trade&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        root = ET.fromstring(resp.content)
        items = root.findall('.//item')
        if items:
            title = items[0].find('title').text[:80]
except:
    pass

if not title:
    teams = ['Yankees', 'Dodgers', 'Mets', 'Red Sox', 'Cubs', 'Astros']
    title = f"{random.choice(teams)} Offseason Update: {DATE_DISPLAY}"

content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | MLB Predictions</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: sans-serif; background: #1a1a1a; color: #e0e0e0; line-height: 1.8; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ color: #e53935; font-size: 2rem; margin-bottom: 20px; }}
        .meta {{ color: #888; margin-bottom: 30px; }}
        p {{ margin-bottom: 20px; font-size: 17px; }}
        a {{ color: #e53935; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="meta">{DATE_DISPLAY} | MLB Analysis</p>
        <p>The hot stove league continues to heat up as we move deeper into the offseason. Front offices across baseball are working the phones.</p>
        <p>What we're seeing this offseason is a clear divide between the haves and have-nots. Big market teams are spending aggressively.</p>
        <p>Pitching remains the most precious commodity. Teams that invested in starting rotation depth last offseason reaped the benefits.</p>
        <p>As spring training approaches, roster battles will start to take shape.</p>
        <p><a href="index.html">Back to Home</a></p>
    </div>
</body>
</html>'''

with open(f'/tmp/mlb-article-{DATE_STR}.html', 'w') as f:
    f.write(content)
print(f"Generated: {title}")
