"""
Fix duplicate meta tags on covers-consensus dated pages.
Each page needs unique title and description with the date.
"""

import os
import re
from datetime import datetime

REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

def format_date(date_str):
    """Convert 2026-01-24 to January 24, 2026"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y").replace(" 0", " ")
    except:
        return date_str

def fix_consensus_pages():
    fixed_count = 0

    for filename in os.listdir(REPO_PATH):
        # Match covers-consensus-YYYY-MM-DD.html
        match = re.match(r'covers-consensus-(\d{4}-\d{2}-\d{2})\.html', filename)
        if not match:
            continue

        date_str = match.group(1)
        formatted_date = format_date(date_str)
        filepath = os.path.join(REPO_PATH, filename)

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original = content

            # Fix title tag - make it unique with date
            old_title = '<title>Covers Contest Consensus | SportsBettingPrime</title>'
            new_title = f'<title>Consensus Picks - {formatted_date} | Sports Betting Prime</title>'
            content = content.replace(old_title, new_title)

            # Also handle slight variations
            content = re.sub(
                r'<title>Covers Contest Consensus \| SportsBettingPrime</title>',
                new_title,
                content
            )

            # Fix meta description - make it unique with date
            old_desc_pattern = r'<meta name="description" content="Covers\.com Contest Consensus - Top 200 picks from elite handicappers across NFL, NBA, NHL, College Basketball, College Football\. Grouped by game for easy viewing\."\s*/?\s*>'
            new_desc = f'<meta name="description" content="Expert consensus picks for {formatted_date}. See where 700+ handicappers agree on NFL, NBA, NHL, and college sports betting picks."/>'
            content = re.sub(old_desc_pattern, new_desc, content, flags=re.IGNORECASE)

            # Fix OG title
            old_og_title = '<meta property="og:title" content="Covers Contest Consensus | SportsBettingPrime"/>'
            new_og_title = f'<meta property="og:title" content="Consensus Picks - {formatted_date} | Sports Betting Prime"/>'
            content = content.replace(old_og_title, new_og_title)

            # Fix OG description
            old_og_desc = '<meta property="og:description" content="See what the best handicappers on Covers.com are betting. Top 200 consensus picks grouped by game."/>'
            new_og_desc = f'<meta property="og:description" content="Expert consensus picks for {formatted_date}. See where top handicappers agree."/>'
            content = content.replace(old_og_desc, new_og_desc)

            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"Fixed: {filename} -> {formatted_date}")

        except Exception as e:
            print(f"Error with {filename}: {e}")

    print(f"\n=== Fixed {fixed_count} files with unique meta tags ===")

if __name__ == '__main__':
    fix_consensus_pages()
