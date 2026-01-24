#!/usr/bin/env python3
"""
Fix canonical tag issues:
1. Standardize all canonical URLs to use sportsbettingprime.com (no www)
2. Add canonical tags to pages missing them
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(r'C:\Users\Nima\sportsbettingprime')
SITE_URL = 'https://sportsbettingprime.com'

def fix_canonical_in_file(filepath):
    """Fix canonical URL in a single file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content
    changes = []

    # Pattern to find canonical links
    canonical_pattern = r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']'

    match = re.search(canonical_pattern, content, re.IGNORECASE)

    if match:
        old_url = match.group(1)
        # Fix www to non-www
        if 'sportsbettingprime.com' in old_url:
            new_url = old_url.replace('sportsbettingprime.com', 'sportsbettingprime.com')
            content = content.replace(old_url, new_url)
            changes.append(f'Fixed www: {old_url} -> {new_url}')
    else:
        # No canonical found - add one
        rel_path = filepath.relative_to(REPO_ROOT)
        url_path = str(rel_path).replace('\\', '/')

        if url_path == 'index.html':
            canonical_url = f'{SITE_URL}/'
        else:
            canonical_url = f'{SITE_URL}/{url_path}'

        # Find where to insert canonical tag (after meta viewport or charset)
        viewport_pattern = r'(<meta\s+name=["\']viewport["\'][^>]*>)'
        viewport_match = re.search(viewport_pattern, content, re.IGNORECASE)

        if viewport_match:
            insert_pos = viewport_match.end()
            canonical_tag = f'\n    <link rel="canonical" href="{canonical_url}">'
            content = content[:insert_pos] + canonical_tag + content[insert_pos:]
            changes.append(f'Added canonical: {canonical_url}')
        else:
            # Try after <head>
            head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
            if head_match:
                insert_pos = head_match.end()
                canonical_tag = f'\n    <link rel="canonical" href="{canonical_url}">'
                content = content[:insert_pos] + canonical_tag + content[insert_pos:]
                changes.append(f'Added canonical (after head): {canonical_url}')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes

    return []

def main():
    fixed_count = 0
    added_count = 0

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in ['.git', 'scripts', '.github']]

        for filename in files:
            if not filename.endswith('.html'):
                continue

            filepath = Path(root) / filename
            changes = fix_canonical_in_file(filepath)

            if changes:
                print(f'{filepath.name}: {", ".join(changes)}')
                for c in changes:
                    if 'Fixed www' in c:
                        fixed_count += 1
                    elif 'Added canonical' in c:
                        added_count += 1

    print(f'\nSummary:')
    print(f'  Fixed www canonical URLs: {fixed_count}')
    print(f'  Added missing canonicals: {added_count}')

if __name__ == '__main__':
    main()
