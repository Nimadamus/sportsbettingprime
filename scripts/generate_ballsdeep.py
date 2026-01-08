#!/usr/bin/env python3
"""Generate Balls Deep International sports satire"""
import requests
import random
import re
from datetime import datetime

TODAY = datetime.now()
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")

# Try to get real sports headlines for satire
headline = None
try:
    resp = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        events = data.get('events', [])
        if events:
            headline = events[0].get('name', '')
except:
    pass

templates = [
    "My Bookie Called to Check If I'm Okay After Last Night",
    "I Told My Wife It Was an Investment: A Sports Betting Retrospective",
    "How I Lost Three Parlays and Found Inner Peace",
    "Confessions of a Degenerate: The Daily Edition",
    "Why I Keep Betting Against My Own Team (A Therapy Session)",
]

if headline:
    title = f"The {headline.split(' at ')[0] if ' at ' in headline else headline.split()[0]} Hurt Me and I'm Not Ready to Talk About It"
else:
    title = random.choice(templates)

filename = re.sub(r'[^a-z0-9\s-]', '', title.lower())
filename = re.sub(r'\s+', '-', filename)[:50].rstrip('-') + '.html'

content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Balls Deep International</title>
    <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;700&family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #000; color: #f2f2f2; font-family: 'Rubik', sans-serif; line-height: 1.7; }}
        nav {{ background: rgba(0, 0, 0, 0.95); padding: 20px; text-align: center; border-bottom: 2px solid #ffc107; }}
        nav a {{ color: #ffc107; text-decoration: none; margin: 0 15px; font-weight: 500; text-transform: uppercase; font-size: 14px; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 60px 20px; }}
        h1 {{ font-family: 'Sora', sans-serif; font-size: 2.2rem; color: #ffc107; text-align: center; margin-bottom: 20px; line-height: 1.3; }}
        .meta {{ text-align: center; color: #888; margin-bottom: 40px; }}
        .content p {{ font-size: 17px; color: #ccc; margin-bottom: 24px; }}
        .back-link {{ text-align: center; margin-top: 50px; }}
        .back-link a {{ color: #ffc107; border: 2px solid #ffc107; padding: 12px 30px; border-radius: 25px; text-decoration: none; }}
        footer {{ text-align: center; padding: 40px 20px; color: #666; border-top: 1px solid #333; margin-top: 60px; }}
    </style>
</head>
<body>
<nav>
    <a href="../index.html">Home</a>
    <a href="../blog.html">Blog</a>
    <a href="../debauchery.html">Debauchery</a>
    <a href="../degeneracy.html">Degeneracy</a>
    <a href="../contact.html">Contact</a>
</nav>
<div class="container">
    <h1>{title}</h1>
    <p class="meta">{DATE_DISPLAY} | Filed under: Digital Degeneracy</p>
    <div class="content">
        <p>Look, I'm not proud of what happened. But we're at Balls Deep International, and if we can't be honest here, where can we be?</p>
        <p>It started innocently enough. "Just a small wager," I told myself. The research was watching one highlight clip and reading two tweets.</p>
        <p>The first quarter went exactly as I expected. By halftime, I was checking flights to countries without extradition treaties.</p>
        <p>My wife asked why I was staring at my phone for three hours. I told her I was "monitoring investments."</p>
        <p>The lesson here? There isn't one. I'll do it again tomorrow. That's the beautiful tragedy of sports betting.</p>
    </div>
    <div class="back-link"><a href="../blog.html">Back to Blog</a></div>
</div>
<footer><p>Balls Deep International. All rights reserved. None of this is real. Seek help.</p></footer>
</body>
</html>'''

with open(f'/tmp/bdi-{filename}', 'w') as f:
    f.write(content)
with open('/tmp/bdi-filename.txt', 'w') as f:
    f.write(filename)
print(f"Generated: {title}")
