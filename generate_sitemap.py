#!/usr/bin/env python3
"""
Sports Betting Prime - Sitemap Generator (FIXED)

This script ACTUALLY READS each HTML file before including it in the sitemap.
It checks for noindex meta tags, verifies the file has real content, and uses
actual file modification dates instead of stamping everything with today's date.

Previous versions blindly dumped every .html file into the sitemap without
reading them, which meant 300+ noindex pages and 120+ dead URLs ended up
in the sitemap. Google saw the contradictions and deprioritized the entire site.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Auto-detect repo root: if run from the repo, use cwd; otherwise use hardcoded path
SCRIPT_DIR = Path(__file__).resolve().parent
if (SCRIPT_DIR / 'index.html').exists():
    REPO_PATH = SCRIPT_DIR
elif (Path(r'C:\Users\Nima\sportsbettingprime') / 'index.html').exists():
    REPO_PATH = Path(r'C:\Users\Nima\sportsbettingprime')
else:
    REPO_PATH = Path.cwd()

# Cache for git commit dates (populated once, used for all files)
_git_dates_cache = None

DOMAIN = "https://sportsbettingprime.com"

# Directories to skip entirely (never walk into these)
SKIP_DIRS = {'.git', 'scripts', '.github', 'node_modules', '__pycache__'}

# Filename patterns to always exclude
EXCLUDE_FILENAMES = {
    '404.html',
    'sportsbettingprime.html',
    'covers-consensus-nov20.html',
}

EXCLUDE_SUBSTRINGS = [
    'google6f74b54ecd988601',
    'BACKUP',
    'template',
]


def is_noindex(filepath):
    """Read the HTML file and check if it contains a noindex directive.

    This is THE critical check that was missing from all previous generators.
    If a page says noindex, it must NOT be in the sitemap.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Only need to read the <head> section, not the whole file
            head_content = ''
            for line in f:
                head_content += line
                if '</head>' in line.lower():
                    break
                # Safety limit: don't read more than 200 lines looking for </head>
                if head_content.count('\n') > 200:
                    break

        head_lower = head_content.lower()

        # Check for noindex in meta robots tag
        # Matches: <meta name="robots" content="noindex...">
        # Matches: <meta name="googlebot" content="noindex...">
        noindex_pattern = r'<meta\s+name=["\'](?:robots|googlebot)["\']\s+content=["\'][^"\']*noindex[^"\']*["\']'
        if re.search(noindex_pattern, head_lower):
            return True

        # Also check reversed attribute order: content before name
        noindex_pattern2 = r'<meta\s+content=["\'][^"\']*noindex[^"\']*["\']\s+name=["\'](?:robots|googlebot)["\']'
        if re.search(noindex_pattern2, head_lower):
            return True

        return False
    except Exception:
        # If we can't read the file, skip it
        return True


def get_git_dates():
    """Build a dict of {relative_path: last_commit_date} using git log.

    This is the FIX for the identical-lastmod problem. The old code used
    os.path.getmtime() which returns the checkout/build time on GitHub Actions,
    making every file show today's date. Git log gives the actual last meaningful
    commit date for each file.
    """
    global _git_dates_cache
    if _git_dates_cache is not None:
        return _git_dates_cache

    _git_dates_cache = {}
    try:
        result = subprocess.run(
            ['git', 'log', '--format=%ai', '--name-only', '--diff-filter=ACMR'],
            capture_output=True, text=True, cwd=str(REPO_PATH), timeout=60
        )
        if result.returncode == 0:
            current_date = None
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Date lines look like: 2026-03-30 17:05:26 -0700
                if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
                    current_date = line[:10]  # Just the YYYY-MM-DD part
                elif current_date and line.endswith('.html'):
                    # Only store the FIRST (most recent) date we see for each file
                    normalized = line.replace('\\', '/')
                    if normalized not in _git_dates_cache:
                        _git_dates_cache[normalized] = current_date
    except Exception as e:
        print(f"  Warning: git log failed ({e}), falling back to file mtime")

    return _git_dates_cache


def has_real_content(filepath):
    """Check if the file has actual content (not just a shell/redirect)."""
    try:
        size = os.path.getsize(filepath)
        # Files under 500 bytes are likely empty shells or redirects
        if size < 500:
            return False
        return True
    except Exception:
        return False


def should_exclude_by_name(filepath, filename):
    """Check filename-based exclusion rules."""
    if filename in EXCLUDE_FILENAMES:
        return True
    for substr in EXCLUDE_SUBSTRINGS:
        if substr.lower() in str(filepath).lower():
            return True
    return False


def get_priority_and_freq(rel_path):
    """Assign priority and change frequency based on page type."""
    path_lower = rel_path.lower()
    filename = os.path.basename(path_lower)

    # Homepage
    if rel_path == 'index.html':
        return '1.0', 'daily'

    # Main sport pages (current day's content)
    main_pages = [
        'covers-consensus.html', 'handicapping-hub.html',
        'nfl-gridiron-oracles.html', 'nba-court-vision.html',
        'nhl-ice-oracles.html', 'college-basketball.html',
        'college-football.html', 'mlb-prime-directives.html',
        'the-data-stream.html',
    ]
    if filename in main_pages:
        return '0.9', 'daily'

    # Static informational pages
    if filename in ['about.html', 'faq.html', 'sitemap.html', 'archive-calendar.html']:
        return '0.7', 'monthly'

    # Guides and evergreen content
    if any(x in path_lower for x in ['guide', 'strategy', 'betting-']):
        return '0.8', 'monthly'

    # Recent archive pages (last 30 days of content)
    if 'archive/' in path_lower:
        # Extract date from filename if possible
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            try:
                page_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                days_old = (datetime.now() - page_date).days
                if days_old <= 7:
                    return '0.7', 'weekly'
                elif days_old <= 30:
                    return '0.6', 'monthly'
                else:
                    return '0.4', 'yearly'
            except ValueError:
                pass
        return '0.5', 'monthly'

    # Consensus library
    if 'consensus_library/' in path_lower:
        return '0.6', 'monthly'

    # Dated consensus pages
    if 'covers-consensus-202' in path_lower:
        return '0.5', 'monthly'

    # Everything else
    return '0.6', 'weekly'


def generate_sitemap():
    """Generate sitemap.xml by READING each HTML file and checking for noindex."""

    print("=" * 60)
    print("SPORTSBETTINGPRIME SITEMAP GENERATOR")
    print("=" * 60)
    print(f"Repo: {REPO_PATH}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    urls = []
    skipped_noindex = 0
    skipped_empty = 0
    skipped_name = 0
    total_scanned = 0

    for root, dirs, files in os.walk(REPO_PATH):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if not filename.endswith('.html'):
                continue

            total_scanned += 1
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, REPO_PATH).replace('\\', '/')

            # Check 1: Filename exclusions
            if should_exclude_by_name(filepath, filename):
                skipped_name += 1
                continue

            # Check 2: Does the file have real content?
            if not has_real_content(filepath):
                skipped_empty += 1
                continue

            # Check 3: THE KEY CHECK - does it have noindex?
            if is_noindex(filepath):
                skipped_noindex += 1
                continue

            # Build URL
            if rel_path == 'index.html':
                url = f"{DOMAIN}/"
            else:
                url = f"{DOMAIN}/{rel_path}"

            # Get last meaningful commit date from git (not filesystem mtime)
            git_dates = get_git_dates()
            lastmod = git_dates.get(rel_path)
            if not lastmod:
                # Fallback: try file mtime, then today
                try:
                    mtime = os.path.getmtime(filepath)
                    lastmod = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                except Exception:
                    lastmod = datetime.now().strftime('%Y-%m-%d')

            priority, changefreq = get_priority_and_freq(rel_path)

            urls.append({
                'loc': url,
                'lastmod': lastmod,
                'changefreq': changefreq,
                'priority': priority,
            })

    # Sort: homepage first, then by priority descending, then alphabetically
    urls.sort(key=lambda x: (x['loc'] != f"{DOMAIN}/", -float(x['priority']), x['loc']))

    # Generate XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for url_data in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url_data["loc"]}</loc>')
        xml_lines.append(f'    <lastmod>{url_data["lastmod"]}</lastmod>')
        xml_lines.append(f'    <changefreq>{url_data["changefreq"]}</changefreq>')
        xml_lines.append(f'    <priority>{url_data["priority"]}</priority>')
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')

    # Write sitemap
    sitemap_path = REPO_PATH / 'sitemap.xml'
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines) + '\n')

    # Report
    print(f"Scanned:  {total_scanned} HTML files")
    print(f"Included: {len(urls)} URLs in sitemap")
    print(f"Skipped:  {skipped_noindex} (noindex meta tag)")
    print(f"Skipped:  {skipped_empty} (empty/tiny files)")
    print(f"Skipped:  {skipped_name} (excluded by filename)")
    print()

    # Breakdown by section
    sections = {}
    for url in urls:
        loc = url['loc']
        if '/archive/' in loc:
            sections['Archive'] = sections.get('Archive', 0) + 1
        elif '/consensus_library/' in loc:
            sections['Consensus Library'] = sections.get('Consensus Library', 0) + 1
        elif 'covers-consensus-202' in loc:
            sections['Daily Consensus'] = sections.get('Daily Consensus', 0) + 1
        else:
            sections['Main Pages'] = sections.get('Main Pages', 0) + 1

    print("URL breakdown:")
    for section, count in sorted(sections.items()):
        print(f"  {section}: {count}")

    # Priority breakdown
    print()
    print("Priority breakdown:")
    for p in ['1.0', '0.9', '0.8', '0.7', '0.6', '0.5', '0.4']:
        count = sum(1 for u in urls if u['priority'] == p)
        if count > 0:
            print(f"  {p}: {count} URLs")

    print()
    print(f"Saved to: {sitemap_path}")
    print("=" * 60)

    return len(urls)


if __name__ == '__main__':
    count = generate_sitemap()
    sys.exit(0)
