#!/usr/bin/env python3
"""
generate_sitemap.py - Generate a complete sitemap.xml for sportsbettingprime.com.

Policy: every content page is indexable. The sitemap surfaces every HTML file
across the repo (root, archive/, blog/, daily/, consensus_library/) so search
engines can discover daily content, dated archives, and evergreen guides
together.

Excluded only:
  - 404.html (not a content page)
  - google*.html (Search Console verification file)
  - .git, __pycache__, node_modules, scripts, pending_content
  - consensus_library/history (internal snapshots)
  - consensus_library/archive (internal raw data)
"""

import os
import re
from datetime import datetime
from urllib.parse import urlparse

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://sportsbettingprime.com"

EXCLUDE_FILE_NAMES = {"404.html"}
EXCLUDE_FILE_PREFIXES = ("google",)  # Search Console verification

EXCLUDE_TOPLEVEL_DIRS = {".git", "__pycache__", "node_modules", "scripts", "pending_content"}
# Sub-paths (relative to repo root, forward slash) that should be excluded
EXCLUDE_PATH_PREFIXES = (
    "consensus_library/history",
    "consensus_library/archive",
)

META_ROBOTS_RE = re.compile(
    r"""<meta\b(?=[^>]*\bname\s*=\s*['"]robots['"])(?=[^>]*\bcontent\s*=\s*['"]([^'"]+)['"])[^>]*>""",
    re.I | re.S,
)
CANONICAL_RE = re.compile(
    r"""<link\b(?=[^>]*\brel\s*=\s*['"]canonical['"])(?=[^>]*\bhref\s*=\s*['"]([^'"]+)['"])[^>]*>""",
    re.I | re.S,
)
META_REFRESH_RE = re.compile(r"""<meta\b(?=[^>]*http-equiv\s*=\s*['"]refresh['"])[^>]*>""", re.I | re.S)


HUB_PAGES = {
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
    "sportsbook.html",
    "performance-telemetry.html",
    "archive-calendar.html",
    "handicapping-hub-calendar.html",
    "the-prime-protocol.html",
}


def is_excluded(rel_path: str) -> bool:
    rel = rel_path.replace(os.sep, "/")
    if rel in {"sitemap.xml", "sitemap.html"}:
        return True
    name = rel.rsplit("/", 1)[-1]
    if name in EXCLUDE_FILE_NAMES:
        return True
    if any(name.startswith(p) for p in EXCLUDE_FILE_PREFIXES):
        return True
    if any(rel.startswith(p) for p in EXCLUDE_PATH_PREFIXES):
        return True
    return False


def canonical_url_for(rel_path: str) -> str:
    return f"{BASE_URL}/{rel_path}" if rel_path != "index.html" else f"{BASE_URL}/"


def is_indexable_self_canonical(filepath: str, rel_path: str) -> bool:
    text = open(filepath, encoding="utf-8", errors="ignore").read()
    robots = META_ROBOTS_RE.search(text)
    if robots and "noindex" in robots.group(1).lower():
        return False
    if META_REFRESH_RE.search(text):
        return False
    canonical = CANONICAL_RE.search(text)
    if canonical and canonical.group(1).rstrip("/") != canonical_url_for(rel_path).rstrip("/"):
        return False
    return True


def get_priority(rel_path: str) -> str:
    rel = rel_path.replace(os.sep, "/")
    if rel == "index.html":
        return "1.0"
    name = rel.rsplit("/", 1)[-1]
    if rel in HUB_PAGES or name in HUB_PAGES:
        return "0.9"
    if (
        name.endswith("-guide.html")
        or name.endswith("-explained.html")
        or name.endswith("-strategy.html")
        or name.endswith("-strategy-guide.html")
    ):
        return "0.8"
    if name in {"about.html", "faq.html", "editorial-policy.html",
                "responsible-gambling.html", "bankroll-calculator.html"}:
        return "0.6"
    if rel.startswith("archive/"):
        return "0.6"
    if rel.startswith("blog/"):
        return "0.7"
    if rel.startswith("daily/"):
        return "0.7"
    if rel.startswith("consensus_library/") or name.startswith("covers-consensus-") \
       or name.startswith("sportsbettingprime-covers-consensus-"):
        return "0.6"
    # Daily slate articles (numeric date prefix like 0420-, 220-, 221-)
    if re.match(r"^\d{3,4}-", name):
        return "0.7"
    # Dated long-tail slate analysis articles
    if re.search(r"-(january|february|march|april|may|june|july|august|september|october|november|december)-\d+-2026", name):
        return "0.7"
    return "0.7"


def get_changefreq(rel_path: str) -> str:
    rel = rel_path.replace(os.sep, "/")
    if rel == "index.html":
        return "daily"
    name = rel.rsplit("/", 1)[-1]
    if name in HUB_PAGES:
        return "daily"
    # Dated content stops changing once games are over
    if name.startswith("covers-consensus-") or rel.startswith("archive/") or rel.startswith("daily/"):
        return "monthly"
    if re.match(r"^\d{3,4}-", name):
        return "monthly"
    if re.search(r"-(january|february|march|april|may|june|july|august|september|october|november|december)-\d+-2026", name):
        return "monthly"
    return "weekly"


def collect_urls():
    urls = []
    for root, dirs, files in os.walk(REPO_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_TOPLEVEL_DIRS]
        for filename in files:
            if not filename.endswith(".html"):
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, REPO_DIR).replace(os.sep, "/")
            if is_excluded(rel_path):
                continue
            if not is_indexable_self_canonical(filepath, rel_path):
                continue
            mtime = os.path.getmtime(filepath)
            lastmod = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            url = canonical_url_for(rel_path)
            urls.append((url, lastmod, get_changefreq(rel_path), get_priority(rel_path), rel_path))
    return urls


def write_sitemap_xml(urls):
    # Order: home first, then by priority desc, then alphabetical
    urls.sort(key=lambda x: (x[0] != f"{BASE_URL}/", -float(x[3]), x[0]))
    out_path = os.path.join(REPO_DIR, "sitemap.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url, lastmod, changefreq, priority, _rel in urls:
            f.write("  <url>\n")
            f.write(f"    <loc>{url}</loc>\n")
            f.write(f"    <lastmod>{lastmod}</lastmod>\n")
            f.write(f"    <changefreq>{changefreq}</changefreq>\n")
            f.write(f"    <priority>{priority}</priority>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")
    return out_path


def write_sitemap_html(urls):
    """HTML sitemap that mirrors the XML one. Groups by section."""
    sections = {
        "Core Pages": [],
        "Sports Hubs": [],
        "Betting Guides & Education": [],
        "Daily Slate Articles": [],
        "Covers Consensus (Daily)": [],
        "Archive — NBA": [],
        "Archive — NHL": [],
        "Archive — NFL": [],
        "Archive — NCAAB": [],
        "Archive — NCAAF": [],
        "Blog": [],
        "Daily": [],
        "Reference & Policy": [],
    }

    for url, _lastmod, _cf, _prio, rel in urls:
        path = urlparse(url).path.lstrip("/")
        if not path:
            path = "index.html"
        name = path.rsplit("/", 1)[-1]
        if path == "index.html" or name in {"covers-consensus.html", "handicapping-hub.html",
                                            "the-data-stream.html", "the-prime-protocol.html",
                                            "performance-telemetry.html", "sportsbook.html"}:
            sections["Core Pages"].append(path)
        elif name in {"nba-court-vision.html", "nhl-ice-oracles.html", "nfl-gridiron-oracles.html",
                      "college-basketball.html", "college-football.html", "mlb-prime-directives.html",
                      "mlb-prime-directives-page2.html"}:
            sections["Sports Hubs"].append(path)
        elif (name.endswith("-guide.html") or name.endswith("-explained.html")
              or name.endswith("-strategy.html") or name.endswith("-strategy-guide.html")
              or name in {"bankroll-calculator.html"}):
            sections["Betting Guides & Education"].append(path)
        elif rel.startswith("archive/nba/"):
            sections["Archive — NBA"].append(path)
        elif rel.startswith("archive/nhl/"):
            sections["Archive — NHL"].append(path)
        elif rel.startswith("archive/nfl/"):
            sections["Archive — NFL"].append(path)
        elif rel.startswith("archive/ncaab/"):
            sections["Archive — NCAAB"].append(path)
        elif rel.startswith("archive/ncaaf/"):
            sections["Archive — NCAAF"].append(path)
        elif rel.startswith("blog/"):
            sections["Blog"].append(path)
        elif rel.startswith("daily/") or rel.startswith("consensus_library/"):
            sections["Daily"].append(path)
        elif name.startswith("covers-consensus-") or name.startswith("sportsbettingprime-covers-consensus-"):
            sections["Covers Consensus (Daily)"].append(path)
        elif re.match(r"^\d{3,4}-", name) or re.search(
            r"-(january|february|march|april|may|june|july|august|september|october|november|december)-\d+-2026",
            name,
        ):
            sections["Daily Slate Articles"].append(path)
        elif name in {"about.html", "faq.html", "editorial-policy.html",
                      "responsible-gambling.html", "archive-calendar.html",
                      "handicapping-hub-calendar.html"}:
            sections["Reference & Policy"].append(path)
        else:
            sections["Reference & Policy"].append(path)

    def title_for(path):
        if path == "index.html":
            return "Home"
        stem = path.rsplit("/", 1)[-1].replace(".html", "")
        return stem.replace("-", " ").title()

    section_html = []
    for heading, paths in sections.items():
        if not paths:
            continue
        items = "\n".join(
            f'                <li><a href="/{p}">{title_for(p)}</a></li>'
            for p in sorted(set(paths))
        )
        section_html.append(
            f"""        <div class="sitemap-section">
            <h2>{heading} <span class="count">({len(set(paths))})</span></h2>
            <ul>
{items}
            </ul>
        </div>"""
        )

    total = sum(len(set(v)) for v in sections.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitemap | Sports Betting Prime</title>
    <meta name="description" content="Complete sitemap for Sports Betting Prime: hubs, daily slate articles, covers consensus archive, sport archives, and evergreen betting guides.">
    <link rel="canonical" href="https://sportsbettingprime.com/sitemap.html">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
    <meta property="og:title" content="Sitemap | Sports Betting Prime">
    <meta property="og:description" content="Complete sitemap for Sports Betting Prime covering hubs, daily slate articles, covers consensus archive, sport archives, and evergreen betting guides.">
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
        .total {{ text-align:center; color: var(--gold); margin-bottom: 2rem; font-weight:600; }}
        .sitemap-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
        .sitemap-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
        .sitemap-section h2 {{ color: var(--gold); font-size: 1.1rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); display:flex; justify-content:space-between; align-items:baseline; }}
        .sitemap-section h2 .count {{ color: var(--muted); font-size: 0.85rem; font-weight: 500; }}
        .sitemap-section ul {{ list-style: none; max-height: 380px; overflow-y: auto; }}
        .sitemap-section li {{ margin-bottom: 0.45rem; }}
        .sitemap-section a {{ color: var(--muted); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }}
        .sitemap-section a:hover {{ color: var(--accent); }}
        footer {{ text-align: center; padding: 3rem; color: var(--muted); font-size: 0.875rem; border-top: 1px solid var(--border); margin-top: 2rem; }}
        footer a {{ color: var(--accent); text-decoration: none; }}
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="/index.html" class="logo">SPORTS BETTING <span class="prime">PRIME</span></a>
        </nav>
    </header>
    <main>
        <h1>Sitemap</h1>
        <p class="subtitle">Every indexable page on Sports Betting Prime, grouped by section. Daily slates, covers consensus archives, sport archives, blog, and evergreen guides are all included.</p>
        <p class="total">{total} pages indexed</p>
        <div class="sitemap-grid">
{os.linesep.join(section_html)}
        </div>
    </main>
    <footer>
        <p>&copy; {datetime.now().year} Sports Betting Prime. <a href="/index.html">Back to home</a></p>
    </footer>
</body>
</html>
"""
    out_path = os.path.join(REPO_DIR, "sitemap.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def main():
    urls = collect_urls()
    xml_path = write_sitemap_xml(urls)
    html_path = write_sitemap_html(urls)
    print(f"Indexed {len(urls)} URLs")
    print(f"  XML: {xml_path}")
    print(f"  HTML: {html_path}")


if __name__ == "__main__":
    main()
