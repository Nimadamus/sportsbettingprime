#!/usr/bin/env python3
"""
generate_sitemap.py - Generate a focused sitemap.xml for sportsbettingprime.com.

The sitemap should surface index-worthy pages only:
- current hubs and evergreen guides
- long-form feature articles

It should not advertise:
- archive trees
- internal consensus library files
- legacy duplicate consensus files
- pages explicitly marked noindex
"""

import os
import re
from datetime import datetime
from urllib.parse import urlparse

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://sportsbettingprime.com"
SKIP_FILES = {
    "404.html",
    "archive-calendar.html",
    "handicapping-hub-calendar.html",
    "google6f74b54ecd988601.html",
    "performance-telemetry.html",
    "the-prime-protocol.html",
}
SKIP_DIRS = {".git", "__pycache__", "node_modules", "scripts", "consensus_library", "archive", "blog", "daily"}


def should_skip(rel_path, html):
    """Return True when a file should be excluded from the XML sitemap."""
    if rel_path in SKIP_FILES:
        return True

    # Keep the sitemap focused on canonical, user-facing pages.
    skip_prefixes = (
        "covers-consensus-",
        "sportsbettingprime-covers-consensus-",
    )
    if rel_path.startswith(skip_prefixes):
        return True

    # Skip pages marked noindex.
    robots_match = re.search(
        r'<meta\s+name="robots"\s+content="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    if robots_match and "noindex" in robots_match.group(1).lower():
        return True

    return False

def get_priority(rel_path):
    if rel_path == "index.html":
        return "1.0"
    if rel_path in (
        "nba-court-vision.html",
        "nhl-ice-oracles.html",
        "nfl-gridiron-oracles.html",
        "college-basketball.html",
        "college-football.html",
        "mlb-prime-directives.html",
        "covers-consensus.html",
        "handicapping-hub.html",
        "the-data-stream.html",
        "betting-guide.html",
    ):
        return "0.9"
    if (
        rel_path.endswith("-guide.html")
        or rel_path.endswith("-explained.html")
        or rel_path.endswith("-strategy.html")
    ):
        return "0.8"
    if "/" not in rel_path and rel_path.startswith("0"):
        return "0.7"
    return "0.6"

def get_changefreq(rel_path):
    if rel_path == "index.html":
        return "daily"
    if rel_path in (
        "nba-court-vision.html",
        "nhl-ice-oracles.html",
        "nfl-gridiron-oracles.html",
        "college-basketball.html",
        "college-football.html",
        "mlb-prime-directives.html",
        "covers-consensus.html",
        "handicapping-hub.html",
        "the-data-stream.html",
    ):
        return "daily"
    return "weekly"

def generate_sitemap():
    urls = []
    for root, dirs, files in os.walk(REPO_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            if not filename.endswith('.html'):
                continue
            if filename in SKIP_FILES:
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, REPO_DIR).replace(os.sep, '/')
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
            if should_skip(rel_path, html):
                continue
            mtime = os.path.getmtime(filepath)
            lastmod = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            url = f"{BASE_URL}/{rel_path}"
            if rel_path == 'index.html':
                url = f"{BASE_URL}/"
            priority = get_priority(rel_path)
            changefreq = get_changefreq(rel_path)
            urls.append((url, lastmod, changefreq, priority))

    urls.sort(key=lambda x: (x[0] != f"{BASE_URL}/", -float(x[3]), x[0]))

    sitemap_path = os.path.join(REPO_DIR, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url, lastmod, changefreq, priority in urls:
            f.write('  <url>\n')
            f.write(f'    <loc>{url}</loc>\n')
            f.write(f'    <lastmod>{lastmod}</lastmod>\n')
            f.write(f'    <changefreq>{changefreq}</changefreq>\n')
            f.write(f'    <priority>{priority}</priority>\n')
            f.write('  </url>\n')
        f.write('</urlset>\n')

    generate_html_sitemap(urls)

    print(f"Sitemap generated: {len(urls)} focused URLs")
    print(f"Saved to: {sitemap_path}")
    return len(urls)


def generate_html_sitemap(urls):
    """Create a crawl-friendly HTML sitemap that mirrors the focused XML sitemap."""
    sections = {
        "Core Pages": [],
        "Sports Hubs": [],
        "Feature Articles": [],
        "Betting Guides": [],
        "Reference": [],
    }

    for url, _, _, _ in urls:
        path = urlparse(url).path.lstrip("/")
        if not path:
            path = "index.html"
        if path == "sitemap.html":
            continue

        if path in {
            "index.html",
            "covers-consensus.html",
            "handicapping-hub.html",
            "the-data-stream.html",
        }:
            sections["Core Pages"].append(path)
        elif path in {
            "nba-court-vision.html",
            "nhl-ice-oracles.html",
            "nfl-gridiron-oracles.html",
            "college-basketball.html",
            "college-football.html",
            "mlb-prime-directives.html",
        }:
            sections["Sports Hubs"].append(path)
        elif (
            path.endswith("-guide.html")
            or path.endswith("-explained.html")
            or path.endswith("-strategy.html")
            or path in {"bankroll-calculator.html", "about.html", "faq.html"}
        ):
            sections["Betting Guides"].append(path)
        elif re.match(r"^\d", path):
            sections["Feature Articles"].append(path)
        else:
            sections["Reference"].append(path)

    def title_for(path):
        if path == "index.html":
            return "Home"
        stem = path.replace(".html", "")
        return stem.replace("-", " ").title()

    section_html = []
    for heading, paths in sections.items():
        if not paths:
            continue
        items = "\n".join(
            f'                <li><a href="{path}">{title_for(path)}</a></li>'
            for path in sorted(paths)
        )
        section_html.append(
            f"""        <div class="sitemap-section">
            <h2>{heading}</h2>
            <ul>
{items}
            </ul>
        </div>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitemap | Sports Betting Prime</title>
    <meta name="description" content="Focused sitemap for Sports Betting Prime covering the site's current hubs, feature articles, and betting guides.">
    <link rel="canonical" href="https://sportsbettingprime.com/sitemap.html">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="Sitemap | Sports Betting Prime">
    <meta property="og:description" content="Focused sitemap for Sports Betting Prime covering current hubs, feature articles, and betting guides.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://sportsbettingprime.com/sitemap.html">
    <meta property="og:image" content="https://sportsbettingprime.com/og-image.png">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0f172a; --card: #1e293b; --border: #334155; --accent: #22c55e; --gold: #f59e0b; --text: #f1f5f9; --muted: #94a3b8; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        header {{ background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }}
        nav {{ max-width: 1200px; margin: 0 auto; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.25rem; font-weight: 800; color: var(--text); text-decoration: none; }}
        .logo .prime {{ color: var(--gold); }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        h1 {{ text-align: center; font-size: 2.5rem; margin-bottom: 0.75rem; background: linear-gradient(135deg, var(--accent), var(--gold)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ text-align: center; color: var(--muted); max-width: 760px; margin: 0 auto 2rem; }}
        .sitemap-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        .sitemap-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
        .sitemap-section h2 {{ color: var(--gold); font-size: 1.1rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }}
        .sitemap-section ul {{ list-style: none; }}
        .sitemap-section li {{ margin-bottom: 0.55rem; }}
        .sitemap-section a {{ color: var(--muted); text-decoration: none; font-size: 0.95rem; transition: color 0.2s; }}
        .sitemap-section a:hover {{ color: var(--accent); }}
        footer {{ text-align: center; padding: 3rem; color: var(--muted); font-size: 0.875rem; border-top: 1px solid var(--border); margin-top: 2rem; }}
        footer a {{ color: var(--accent); text-decoration: none; }}
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="index.html" class="logo">SPORTS BETTING <span class="prime">PRIME</span></a>
        </nav>
    </header>
    <main>
        <h1>Sitemap</h1>
        <p class="subtitle">Focused index of the pages Sports Betting Prime actively wants users and search engines to find.</p>
        <div class="sitemap-grid">
{os.linesep.join(section_html)}
        </div>
    </main>
    <footer>
        <p>&copy; {datetime.now().year} Sports Betting Prime. <a href="index.html">Back to home</a></p>
    </footer>
</body>
</html>
"""

    with open(os.path.join(REPO_DIR, "sitemap.html"), "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == '__main__':
    generate_sitemap()
