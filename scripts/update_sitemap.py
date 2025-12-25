#!/usr/bin/env python3
"""
Update archive calendar and generate sitemap for sportsbettingprime.
Scans all archive folders and creates proper navigation.
"""
import os
import re
from datetime import datetime

REPO = r"C:\Users\Nima\sportsbettingprime"
ARCHIVE_DIR = os.path.join(REPO, "archive")
TODAY = datetime.now()

# Sport configurations
SPORTS = {
    "nfl": {
        "name": "NFL",
        "folder": "nfl",
        "prefix": "nfl-gridiron-oracles",
        "main_page": "nfl-gridiron-oracles.html",
        "color": "#22c55e"
    },
    "nba": {
        "name": "NBA",
        "folder": "nba",
        "prefix": "nba-court-vision",
        "main_page": "nba-court-vision.html",
        "color": "#3b82f6"
    },
    "nhl": {
        "name": "NHL",
        "folder": "nhl",
        "prefix": "nhl-ice-oracles",
        "main_page": "nhl-ice-oracles.html",
        "color": "#38bdf8"
    },
    "ncaab": {
        "name": "College Basketball",
        "folder": "ncaab",
        "prefix": "college-basketball",
        "main_page": "college-basketball.html",
        "color": "#f97316"
    },
    "ncaaf": {
        "name": "College Football",
        "folder": "ncaaf",
        "prefix": "college-football",
        "main_page": "college-football.html",
        "color": "#a855f7"
    }
}


def scan_archive_pages():
    """Scan archive folders and return all pages by sport."""
    pages = {}

    for sport_key, config in SPORTS.items():
        folder = os.path.join(ARCHIVE_DIR, config["folder"])
        if not os.path.exists(folder):
            continue

        sport_pages = []
        for f in os.listdir(folder):
            if f.endswith(".html"):
                # Extract date from filename
                match = re.search(r"(\d{4}-\d{2}-\d{2})", f)
                if match:
                    date_str = match.group(1)
                    sport_pages.append({
                        "file": f,
                        "date": date_str,
                        "path": f"archive/{config['folder']}/{f}"
                    })

        # Sort by date descending
        sport_pages.sort(key=lambda x: x["date"], reverse=True)
        pages[sport_key] = sport_pages

    return pages


def generate_archive_calendar(pages):
    """Generate the archive-calendar.html page."""

    sections_html = ""
    for sport_key, config in SPORTS.items():
        sport_pages = pages.get(sport_key, [])
        if not sport_pages:
            continue

        links_html = ""
        for page in sport_pages:
            dt = datetime.strptime(page["date"], "%Y-%m-%d")
            display_date = dt.strftime("%b %d, %Y")
            links_html += f'                    <a href="{page["path"]}" class="archive-link">{display_date}</a>\n'

        sections_html += f'''
            <div class="sport-section">
                <h2>{config["name"]}</h2>
                <div class="archive-grid">
{links_html}                </div>
            </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive Calendar | Sports Betting Prime</title>
    <meta name="description" content="Browse historical sports betting analysis by date. NFL, NBA, NHL, NCAAB, NCAAF archives.">
    <link rel="canonical" href="https://sportsbettingprime.com/archive-calendar.html">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0f172a; --card: #1e293b; --border: #334155; --accent: #22c55e; --gold: #f59e0b; --text: #f1f5f9; --muted: #94a3b8; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        header {{ background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }}
        nav {{ max-width: 1200px; margin: 0 auto; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.25rem; font-weight: 800; color: var(--text); text-decoration: none; }}
        .logo .prime {{ color: var(--gold); }}
        .nav-links {{ display: flex; list-style: none; gap: 0.5rem; }}
        .nav-links a {{ color: var(--muted); text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.875rem; }}
        .nav-links a:hover {{ color: var(--text); background: var(--card); }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        h1 {{ text-align: center; font-size: 2.5rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, var(--accent), var(--gold)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ text-align: center; color: var(--muted); margin-bottom: 3rem; }}
        .sport-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; }}
        .sport-section h2 {{ color: var(--gold); margin-bottom: 1rem; font-size: 1.5rem; }}
        .archive-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 0.75rem; }}
        .archive-link {{ display: block; padding: 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text); text-decoration: none; text-align: center; font-size: 0.8rem; transition: all 0.2s; }}
        .archive-link:hover {{ background: var(--accent); border-color: var(--accent); transform: translateY(-2px); }}
        footer {{ text-align: center; padding: 3rem; color: var(--muted); font-size: 0.875rem; border-top: 1px solid var(--border); margin-top: 2rem; }}
        footer a {{ color: var(--accent); text-decoration: none; }}
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="index.html" class="logo">SPORTS BETTING <span class="prime">PRIME</span></a>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="covers-consensus.html">Consensus</a></li>
                <li><a href="nfl-gridiron-oracles.html">NFL</a></li>
                <li><a href="nba-court-vision.html">NBA</a></li>
                <li><a href="nhl-ice-oracles.html">NHL</a></li>
                <li><a href="college-basketball.html">NCAAB</a></li>
                <li><a href="college-football.html">NCAAF</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <h1>Archive Calendar</h1>
        <p class="subtitle">Browse historical sports betting analysis by date</p>
{sections_html}
    </main>
    <footer>
        <p><a href="index.html">Home</a> | <a href="sitemap.html">Sitemap</a></p>
        <p>Sports Betting Prime - Archive | Updated: {TODAY.strftime("%B %d, %Y")}</p>
    </footer>
</body>
</html>
'''

    with open(os.path.join(REPO, "archive-calendar.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated archive-calendar.html")


def generate_sitemap_xml(pages):
    """Generate sitemap.xml for SEO."""

    urls = []

    # Main pages
    main_pages = [
        "index.html",
        "covers-consensus.html",
        "handicapping-hub.html",
        "archive-calendar.html",
        "sitemap.html",
        "nfl-gridiron-oracles.html",
        "nba-court-vision.html",
        "nhl-ice-oracles.html",
        "college-basketball.html",
        "college-football.html",
    ]

    for page in main_pages:
        urls.append(f"https://sportsbettingprime.com/{page}")

    # Archive pages
    for sport_key, sport_pages in pages.items():
        for page in sport_pages:
            urls.append(f"https://sportsbettingprime.com/{page['path']}")

    # Consensus pages
    for f in os.listdir(REPO):
        if f.startswith("covers-consensus-") and f.endswith(".html"):
            urls.append(f"https://sportsbettingprime.com/{f}")

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in urls:
        xml_content += f'''  <url>
    <loc>{url}</loc>
    <lastmod>{TODAY.strftime("%Y-%m-%d")}</lastmod>
    <changefreq>daily</changefreq>
  </url>
'''

    xml_content += '</urlset>\n'

    with open(os.path.join(REPO, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Updated sitemap.xml ({len(urls)} URLs)")


def generate_sitemap_html(pages):
    """Generate human-readable sitemap.html."""

    # Build sections
    main_section = '''
        <div class="sitemap-section">
            <h2>Main Pages</h2>
            <ul>
                <li><a href="index.html">Home</a></li>
                <li><a href="covers-consensus.html">Covers Consensus</a></li>
                <li><a href="handicapping-hub.html">Handicapping Hub</a></li>
                <li><a href="archive-calendar.html">Archive Calendar</a></li>
            </ul>
        </div>'''

    sports_section = '''
        <div class="sitemap-section">
            <h2>Sports Analysis (Current)</h2>
            <ul>
                <li><a href="nfl-gridiron-oracles.html">NFL Gridiron Oracles</a></li>
                <li><a href="nba-court-vision.html">NBA Court Vision</a></li>
                <li><a href="nhl-ice-oracles.html">NHL Ice Oracles</a></li>
                <li><a href="college-basketball.html">College Basketball</a></li>
                <li><a href="college-football.html">College Football</a></li>
            </ul>
        </div>'''

    # Archive sections by sport
    archive_sections = ""
    for sport_key, config in SPORTS.items():
        sport_pages = pages.get(sport_key, [])
        if not sport_pages:
            continue

        links = ""
        for page in sport_pages:
            dt = datetime.strptime(page["date"], "%Y-%m-%d")
            display = dt.strftime("%B %d, %Y")
            links += f'                <li><a href="{page["path"]}">{display}</a></li>\n'

        archive_sections += f'''
        <div class="sitemap-section">
            <h2>{config["name"]} Archive</h2>
            <ul>
{links}            </ul>
        </div>'''

    # Consensus archives
    consensus_files = sorted([f for f in os.listdir(REPO) if f.startswith("covers-consensus-2025") and f.endswith(".html")], reverse=True)
    consensus_links = ""
    for f in consensus_files[:20]:  # Last 20
        match = re.search(r"(\d{4}-\d{2}-\d{2})", f)
        if match:
            dt = datetime.strptime(match.group(1), "%Y-%m-%d")
            display = dt.strftime("%B %d, %Y")
            consensus_links += f'                <li><a href="{f}">{display}</a></li>\n'

    consensus_section = f'''
        <div class="sitemap-section">
            <h2>Covers Consensus Archive</h2>
            <ul>
{consensus_links}            </ul>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitemap | Sports Betting Prime</title>
    <meta name="description" content="Complete sitemap for Sports Betting Prime - all pages, archives, and resources.">
    <link rel="canonical" href="https://sportsbettingprime.com/sitemap.html">
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
        h1 {{ text-align: center; font-size: 2.5rem; margin-bottom: 2rem; background: linear-gradient(135deg, var(--accent), var(--gold)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .sitemap-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        .sitemap-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
        .sitemap-section h2 {{ color: var(--gold); font-size: 1.1rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }}
        .sitemap-section ul {{ list-style: none; }}
        .sitemap-section li {{ margin-bottom: 0.5rem; }}
        .sitemap-section a {{ color: var(--muted); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }}
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
        <div class="sitemap-grid">
{main_section}
{sports_section}
{archive_sections}
{consensus_section}
        </div>
    </main>
    <footer>
        <p><a href="index.html">Home</a> | <a href="archive-calendar.html">Archive Calendar</a></p>
        <p>Sports Betting Prime | Updated: {TODAY.strftime("%B %d, %Y")}</p>
    </footer>
</body>
</html>
'''

    with open(os.path.join(REPO, "sitemap.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated sitemap.html")


def main():
    print("=" * 60)
    print("SPORTSBETTINGPRIME - SITEMAP & ARCHIVE UPDATE")
    print("=" * 60)

    # Scan archive
    print("\nScanning archive folders...")
    pages = scan_archive_pages()

    total = sum(len(p) for p in pages.values())
    print(f"Found {total} archive pages:")
    for sport, sport_pages in pages.items():
        print(f"  - {sport.upper()}: {len(sport_pages)} pages")

    # Generate files
    print("\nGenerating files...")
    generate_archive_calendar(pages)
    generate_sitemap_xml(pages)
    generate_sitemap_html(pages)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
