"""
Sports Betting Prime - Comprehensive Sitemap Generator
Generates sitemap.xml with ALL HTML pages on the site
"""

import os
from datetime import datetime

DOMAIN = "https://sportsbettingprime.com"
REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

# Files/patterns to exclude from sitemap
EXCLUDE_PATTERNS = [
    'google6f74b54ecd988601',  # Google verification files
    '.git',
    'template',
    'BACKUP',
    'sportsbettingprime.html',  # Duplicate of index
    'covers-consensus-nov20.html',  # Old format
]

def should_include(filepath):
    """Check if file should be included in sitemap"""
    filename = os.path.basename(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in filepath.lower():
            return False
    return True

def get_priority(filepath):
    """Assign priority based on page type"""
    filename = os.path.basename(filepath).lower()

    if filename == 'index.html':
        return '1.0', 'daily'
    elif filename in ['covers-consensus.html', 'handicapping-hub.html']:
        return '0.9', 'daily'
    elif filename in ['about.html', 'faq.html', 'betting-guide.html', 'sitemap.html']:
        return '0.8', 'monthly'
    elif any(x in filename for x in ['nfl-gridiron', 'nba-court', 'nhl-ice', 'college-football', 'college-basketball', 'mlb-prime']):
        if 'archive' in filepath.lower():
            return '0.5', 'monthly'
        return '0.8', 'daily'
    elif 'the-data-stream' in filename:
        return '0.9', 'daily'
    elif any(x in filename for x in ['guide', 'strategy', 'betting']):
        return '0.7', 'weekly'
    elif 'covers-consensus-2026' in filename:
        return '0.6', 'monthly'
    elif 'covers-consensus-2025' in filename:
        return '0.5', 'monthly'
    elif 'sharp-consensus' in filename:
        return '0.5', 'monthly'
    elif 'archive' in filepath.lower():
        return '0.4', 'monthly'
    else:
        return '0.6', 'weekly'

def generate_sitemap():
    """Generate comprehensive sitemap.xml"""

    today = datetime.now().strftime('%Y-%m-%d')
    urls = []

    # Walk through all directories
    for root, dirs, files in os.walk(REPO_PATH):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if not filename.endswith('.html'):
                continue

            filepath = os.path.join(root, filename)

            if not should_include(filepath):
                continue

            # Get relative path for URL
            rel_path = os.path.relpath(filepath, REPO_PATH)
            rel_path = rel_path.replace('\\', '/')

            # Handle index.html
            if rel_path == 'index.html':
                url = f"{DOMAIN}/"
            else:
                url = f"{DOMAIN}/{rel_path}"

            priority, changefreq = get_priority(filepath)

            urls.append({
                'loc': url,
                'lastmod': today,
                'changefreq': changefreq,
                'priority': priority
            })

    # Sort by priority (highest first)
    urls.sort(key=lambda x: (-float(x['priority']), x['loc']))

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
    sitemap_path = os.path.join(REPO_PATH, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines) + '\n')

    print(f"Generated sitemap.xml with {len(urls)} URLs")
    print(f"\nURL Breakdown:")
    print(f"  Priority 1.0: {sum(1 for u in urls if u['priority'] == '1.0')}")
    print(f"  Priority 0.9: {sum(1 for u in urls if u['priority'] == '0.9')}")
    print(f"  Priority 0.8: {sum(1 for u in urls if u['priority'] == '0.8')}")
    print(f"  Priority 0.7: {sum(1 for u in urls if u['priority'] == '0.7')}")
    print(f"  Priority 0.6: {sum(1 for u in urls if u['priority'] == '0.6')}")
    print(f"  Priority 0.5: {sum(1 for u in urls if u['priority'] == '0.5')}")
    print(f"  Priority 0.4: {sum(1 for u in urls if u['priority'] == '0.4')}")

    return len(urls)

if __name__ == '__main__':
    generate_sitemap()
