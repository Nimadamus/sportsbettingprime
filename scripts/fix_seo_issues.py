#!/usr/bin/env python3
"""
SEO Fix Script for SportsBettingPrime.com
Fixes duplicate canonical tags and generates comprehensive sitemap
"""

import os
import re
from datetime import datetime
from pathlib import Path

REPO_PATH = r'C:\Users\Nima\sportsbettingprime'
SITE_URL = 'https://sportsbettingprime.com'

def fix_duplicate_canonicals():
    """Remove duplicate canonical tags pointing to wrong URLs"""
    bad_canonical = '<link href="https://sportsbettingprime.com/sportsbettingprime-covers-consensus.html" rel="canonical"/>'

    files_fixed = 0
    for root, dirs, files in os.walk(REPO_PATH):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    if bad_canonical in content:
                        new_content = content.replace(bad_canonical, '')
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        files_fixed += 1
                        print(f"  Fixed: {filename}")
                except Exception as e:
                    print(f"  Error processing {filename}: {e}")

    return files_fixed

def generate_sitemap():
    """Generate comprehensive sitemap with all HTML pages"""

    # Collect all HTML files
    html_files = []
    exclude_patterns = [
        'google6f74b54ecd988601',  # Google verification files
        'BACKUP',
        '.git'
    ]

    for root, dirs, files in os.walk(REPO_PATH):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                # Skip excluded files
                if any(pattern in filename for pattern in exclude_patterns):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, REPO_PATH).replace('\\', '/')

                # Skip hidden/internal history files
                if 'history/' in rel_path and '23-44' in rel_path:
                    continue

                html_files.append(rel_path)

    # Sort files for consistent ordering
    html_files.sort()

    # Determine priorities and change frequencies
    def get_priority_and_freq(path):
        if path == 'index.html':
            return '1.0', 'daily'
        elif path in ['covers-consensus.html', 'handicapping-hub.html']:
            return '1.0', 'daily'
        elif path.startswith('nba-') or path.startswith('nfl-') or path.startswith('nhl-'):
            return '0.9', 'daily'
        elif path.startswith('college-'):
            return '0.8', 'daily'
        elif 'archive/' in path:
            return '0.6', 'monthly'
        elif 'consensus_library/' in path:
            return '0.7', 'weekly'
        elif 'sharp-consensus' in path:
            return '0.7', 'weekly'
        else:
            return '0.5', 'weekly'

    today = datetime.now().strftime('%Y-%m-%d')

    # Build sitemap XML
    sitemap_entries = []
    for path in html_files:
        url = f"{SITE_URL}/{path}"
        priority, freq = get_priority_and_freq(path)

        entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        sitemap_entries.append(entry)

    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_entries)}
</urlset>
'''

    # Write sitemap
    sitemap_path = os.path.join(REPO_PATH, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_xml)

    return len(html_files)

def create_html_sitemap():
    """Create an HTML sitemap page for users and additional crawl signals"""

    html_files = []
    for root, dirs, files in os.walk(REPO_PATH):
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                if 'google6f74b54ecd988601' in filename or 'BACKUP' in filename:
                    continue
                if 'history/' in os.path.join(root, filename):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, REPO_PATH).replace('\\', '/')
                html_files.append(rel_path)

    html_files.sort()

    # Group by category
    categories = {
        'Main Pages': [],
        'Sports Analysis': [],
        'Consensus Data': [],
        'Sharp Picks': [],
        'Archive': []
    }

    for path in html_files:
        if path in ['index.html', 'covers-consensus.html', 'handicapping-hub.html', 'sitemap.html']:
            categories['Main Pages'].append(path)
        elif path.startswith(('nba-', 'nfl-', 'nhl-', 'college-', 'mlb-')):
            categories['Sports Analysis'].append(path)
        elif 'consensus' in path.lower() and 'sharp' not in path.lower():
            categories['Consensus Data'].append(path)
        elif 'sharp' in path.lower():
            categories['Sharp Picks'].append(path)
        elif 'archive/' in path:
            categories['Archive'].append(path)
        else:
            categories['Main Pages'].append(path)

    links_html = ""
    for category, pages in categories.items():
        if pages:
            links_html += f'<h2>{category}</h2>\n<ul>\n'
            for page in pages:
                title = page.replace('.html', '').replace('-', ' ').replace('/', ' - ').title()
                links_html += f'  <li><a href="{page}">{title}</a></li>\n'
            links_html += '</ul>\n'

    sitemap_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitemap | Sports Betting Prime</title>
    <meta name="description" content="Complete sitemap of Sports Betting Prime - find all our sports betting analysis, consensus picks, and sharp money reports.">
    <link rel="canonical" href="https://sportsbettingprime.com/sitemap.html">
    <meta name="robots" content="index, follow">
    <style>
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0f172a; color: #f1f5f9; line-height: 1.8; padding: 2rem; max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #3b82f6; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem; }}
        h2 {{ color: #f59e0b; margin-top: 2rem; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 0.5rem 0; }}
        a {{ color: #60a5fa; text-decoration: none; }}
        a:hover {{ color: #93c5fd; text-decoration: underline; }}
        .back {{ margin-top: 2rem; }}
    </style>
</head>
<body>
    <h1>Sports Betting Prime - Site Map</h1>
    <p>Complete index of all pages on SportsBettingPrime.com. Last updated: {datetime.now().strftime('%B %d, %Y')}</p>

{links_html}

    <div class="back">
        <a href="index.html">&larr; Back to Home</a>
    </div>
</body>
</html>
'''

    sitemap_path = os.path.join(REPO_PATH, 'sitemap.html')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_html)

    return len(html_files)

if __name__ == '__main__':
    print("=" * 60)
    print("SportsBettingPrime.com SEO Fix Script")
    print("=" * 60)

    print("\n1. Fixing duplicate canonical tags...")
    fixed = fix_duplicate_canonicals()
    print(f"   Fixed {fixed} files with duplicate canonicals")

    print("\n2. Generating comprehensive sitemap.xml...")
    pages = generate_sitemap()
    print(f"   Generated sitemap with {pages} URLs")

    print("\n3. Creating HTML sitemap page...")
    html_pages = create_html_sitemap()
    print(f"   Created HTML sitemap with {html_pages} links")

    print("\n" + "=" * 60)
    print("SEO fixes complete!")
    print("=" * 60)
