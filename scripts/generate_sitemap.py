#!/usr/bin/env python3
"""
Comprehensive Sitemap Generator for Sports Betting Prime
Generates sitemap.xml with ALL HTML pages, proper lastmod dates, and consistent canonical URLs.
"""

import os
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(r'C:\Users\Nima\sportsbettingprime')
SITE_URL = 'https://sportsbettingprime.com'

# Pages to exclude from sitemap (verification files, templates, backups)
EXCLUDE_PATTERNS = [
    'google6f74b54ecd988601',  # Google verification files
    'BACKUP',
    'template',
    'history/',
    'sportsbettingprime.html',  # Duplicate of index
    'sportsbettingprime-covers-consensus-',  # Old format duplicates
]

def should_include(filepath):
    """Check if file should be included in sitemap."""
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in filepath_str.lower():
            return False
    return True

def get_priority(filepath):
    """Determine URL priority based on page type."""
    filepath_str = str(filepath)

    # Homepage gets highest priority
    if filepath_str.endswith('index.html'):
        return '1.0'

    # Main section pages get high priority
    main_pages = [
        'covers-consensus.html',
        'handicapping-hub.html',
        'nfl-gridiron-oracles.html',
        'nba-court-vision.html',
        'nhl-ice-oracles.html',
        'college-basketball.html',
        'college-football.html',
    ]
    for page in main_pages:
        if filepath_str.endswith(page):
            return '0.9'

    # Archive calendar and sitemap
    if 'archive-calendar' in filepath_str or 'sitemap.html' in filepath_str:
        return '0.8'

    # Daily content pages
    if 'consensus_library' in filepath_str or 'archive/' in filepath_str:
        return '0.7'

    # Dated pages
    if '-2025-' in filepath_str:
        return '0.6'

    return '0.5'

def get_changefreq(filepath):
    """Determine change frequency based on page type."""
    filepath_str = str(filepath)

    # Main pages update daily
    if filepath_str.endswith('index.html') or 'covers-consensus.html' in filepath_str:
        return 'daily'
    if 'handicapping-hub' in filepath_str or 'gridiron' in filepath_str:
        return 'daily'
    if 'court-vision' in filepath_str or 'ice-oracles' in filepath_str:
        return 'daily'
    if 'college-' in filepath_str and '-2025-' not in filepath_str:
        return 'daily'

    # Archive pages are static
    if 'archive/' in filepath_str or '-2025-' in filepath_str:
        return 'monthly'

    return 'weekly'

def generate_sitemap():
    """Generate comprehensive sitemap.xml"""
    urls = []

    # Walk through all HTML files
    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip .git and scripts directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'scripts', '.github']]

        for filename in files:
            if not filename.endswith('.html'):
                continue

            filepath = Path(root) / filename

            if not should_include(filepath):
                continue

            # Get relative path from repo root
            rel_path = filepath.relative_to(REPO_ROOT)

            # Build URL (use forward slashes, no www)
            url_path = str(rel_path).replace('\\', '/')

            # Handle index.html as root
            if url_path == 'index.html':
                full_url = f'{SITE_URL}/'
            else:
                full_url = f'{SITE_URL}/{url_path}'

            # Get file modification time for lastmod
            try:
                mtime = os.path.getmtime(filepath)
                lastmod = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            except:
                lastmod = datetime.now().strftime('%Y-%m-%d')

            priority = get_priority(filepath)
            changefreq = get_changefreq(filepath)

            urls.append({
                'loc': full_url,
                'lastmod': lastmod,
                'changefreq': changefreq,
                'priority': priority,
            })

    # Sort URLs: homepage first, then by priority, then alphabetically
    urls.sort(key=lambda x: (x['priority'] != '1.0', -float(x['priority']), x['loc']))

    # Generate XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for url in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url["loc"]}</loc>')
        xml_lines.append(f'    <lastmod>{url["lastmod"]}</lastmod>')
        xml_lines.append(f'    <changefreq>{url["changefreq"]}</changefreq>')
        xml_lines.append(f'    <priority>{url["priority"]}</priority>')
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')

    # Write sitemap
    sitemap_path = REPO_ROOT / 'sitemap.xml'
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))

    print(f'Generated sitemap.xml with {len(urls)} URLs')
    print(f'Saved to: {sitemap_path}')

    # Print summary by section
    sections = {}
    for url in urls:
        loc = url['loc']
        if '/archive/' in loc:
            section = 'Archive'
        elif '/consensus_library/' in loc:
            section = 'Consensus Library'
        elif 'covers-consensus-2025' in loc:
            section = 'Daily Consensus'
        else:
            section = 'Main Pages'
        sections[section] = sections.get(section, 0) + 1

    print('\nURL breakdown:')
    for section, count in sorted(sections.items()):
        print(f'  {section}: {count}')

    return len(urls)

if __name__ == '__main__':
    generate_sitemap()
