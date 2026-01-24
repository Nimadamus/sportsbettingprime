"""
Fix canonical URLs on all archive sport pages.
Each page needs its OWN canonical URL (not pointing to main sport page).
Also fix og:url to match.
"""

import os
import re

REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

def fix_archive_pages():
    fixed_count = 0

    for sport in ['nba', 'nfl', 'nhl', 'ncaab', 'ncaaf']:
        archive_path = os.path.join(REPO_PATH, 'archive', sport)

        if not os.path.exists(archive_path):
            print(f"Directory not found: {archive_path}")
            continue

        for filename in os.listdir(archive_path):
            if not filename.endswith('.html'):
                continue

            filepath = os.path.join(archive_path, filename)

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                original = content

                # Correct canonical URL for this archive page
                correct_canonical = f'<link rel="canonical" href="https://sportsbettingprime.com/archive/{sport}/{filename}">'
                correct_og_url = f'<meta property="og:url" content="https://sportsbettingprime.com/archive/{sport}/{filename}"/>'

                # Fix canonical - might have various patterns
                content = re.sub(
                    r'<link rel="canonical" href="[^"]+">',
                    correct_canonical,
                    content
                )

                # Fix og:url
                content = re.sub(
                    r'<meta property="og:url" content="[^"]+"/>',
                    correct_og_url,
                    content
                )

                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += 1
                    print(f"Fixed: archive/{sport}/{filename}")

            except Exception as e:
                print(f"Error with {filename}: {e}")

    print(f"\n=== Fixed {fixed_count} archive files ===")

if __name__ == '__main__':
    fix_archive_pages()
