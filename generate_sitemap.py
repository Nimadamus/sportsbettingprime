#!/usr/bin/env python3
"""
generate_sitemap.py - Generate a comprehensive sitemap.xml for sportsbettingprime.com
Includes ALL HTML files except 404.html.
"""

import os
import sys
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://sportsbettingprime.com"
SKIP_FILES = {'404.html'}
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', 'scripts'}

def get_priority(rel_path):
    if rel_path == 'index.html':
        return '1.0'
    if rel_path in ('nba-court-vision.html', 'nhl-ice-oracles.html', 'nfl-gridiron-oracles.html',
                     'college-basketball.html', 'college-football.html', 'mlb-prime-directives.html',
                     'covers-consensus.html', 'handicapping-hub.html'):
        return '0.9'
    if rel_path.endswith('-guide.html') or rel_path.endswith('-explained.html') or rel_path.endswith('-strategy.html'):
        return '0.8'
    if '/' not in rel_path and rel_path.startswith('0'):
        return '0.7'
    if rel_path.startswith('blog/'):
        return '0.6'
    if 'covers-consensus-' in rel_path and not rel_path.startswith('consensus_library/'):
        return '0.5'
    if rel_path.startswith('archive/') or rel_path.startswith('consensus_library/'):
        return '0.4'
    return '0.5'

def get_changefreq(rel_path):
    if rel_path == 'index.html':
        return 'daily'
    if rel_path in ('nba-court-vision.html', 'nhl-ice-oracles.html', 'nfl-gridiron-oracles.html',
                     'college-basketball.html', 'college-football.html', 'mlb-prime-directives.html',
                     'covers-consensus.html', 'handicapping-hub.html'):
        return 'daily'
    if 'archive/' in rel_path or 'consensus_library/' in rel_path:
        return 'monthly'
    return 'weekly'

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

    print(f"Sitemap generated: {len(urls)} URLs (was 311)")
    print(f"Saved to: {sitemap_path}")
    return len(urls)

if __name__ == '__main__':
    generate_sitemap()
