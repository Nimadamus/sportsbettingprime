"""
Fix canonical URLs and navigation on covers-consensus dated pages.
1. Each page needs its OWN canonical URL (not pointing to main page)
2. Each page needs Previous/Next day navigation
3. Fix og:url to match canonical
"""

import os
import re
from datetime import datetime, timedelta

REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

def get_all_consensus_dates():
    """Get sorted list of all consensus page dates"""
    dates = []
    for filename in os.listdir(REPO_PATH):
        match = re.match(r'covers-consensus-(\d{4}-\d{2}-\d{2})\.html', filename)
        if match:
            dates.append(match.group(1))
    return sorted(dates)

def format_date_short(date_str):
    """Convert 2026-01-24 to Jan 24"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %-d").replace(" 0", " ")
    except:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d").replace(" 0", " ").replace("  ", " ")

def fix_consensus_pages():
    dates = get_all_consensus_dates()
    print(f"Found {len(dates)} consensus pages to fix")

    fixed_count = 0

    for i, date_str in enumerate(dates):
        filename = f"covers-consensus-{date_str}.html"
        filepath = os.path.join(REPO_PATH, filename)

        # Determine prev/next dates
        prev_date = dates[i-1] if i > 0 else None
        next_date = dates[i+1] if i < len(dates)-1 else None

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original = content

            # 1. Fix canonical URL - MUST point to this page, not main page
            correct_canonical = f'<link rel="canonical" href="https://sportsbettingprime.com/{filename}">'
            content = re.sub(
                r'<link rel="canonical" href="https://sportsbettingprime\.com/covers-consensus[^"]*">',
                correct_canonical,
                content
            )

            # 2. Fix og:url - MUST match canonical
            correct_og_url = f'<meta property="og:url" content="https://sportsbettingprime.com/{filename}"/>'
            content = re.sub(
                r'<meta property="og:url" content="[^"]*"/>',
                correct_og_url,
                content
            )

            # 3. Build navigation HTML
            nav_html = '<div style="display:flex;justify-content:space-between;margin:20px 0;padding:15px;background:rgba(0,255,136,0.1);border-radius:10px;">'

            if prev_date:
                prev_filename = f"covers-consensus-{prev_date}.html"
                prev_label = format_date_short(prev_date)
                nav_html += f'<a href="{prev_filename}" style="color:#00ff88;text-decoration:none;">&larr; {prev_label}</a>'
            else:
                nav_html += '<span></span>'

            nav_html += '<a href="covers-consensus.html" style="color:#00f0ff;text-decoration:none;">Archive Calendar</a>'

            if next_date:
                next_filename = f"covers-consensus-{next_date}.html"
                next_label = format_date_short(next_date)
                nav_html += f'<a href="{next_filename}" style="color:#00ff88;text-decoration:none;">{next_label} &rarr;</a>'
            else:
                nav_html += '<span style="color:#666;">Latest</span>'

            nav_html += '</div>'

            # 4. Check if navigation section exists and update it
            # Look for existing navigation pattern
            nav_pattern = r'<div style="display:flex;justify-content:space-between;margin:20px 0[^>]*>.*?</div>'
            if re.search(nav_pattern, content, re.DOTALL):
                content = re.sub(nav_pattern, nav_html, content, count=1, flags=re.DOTALL)
            else:
                # Look for old navigation pattern
                old_nav_pattern = r'<a href="covers-consensus-\d{4}-\d{2}-\d{2}\.html">&larr; Previous Day[^<]*</a>'
                if re.search(old_nav_pattern, content):
                    content = re.sub(old_nav_pattern, nav_html, content, count=1)
                else:
                    # Insert after the filter buttons (look for end of header area)
                    insert_marker = '</header>'
                    if insert_marker in content:
                        content = content.replace(insert_marker, insert_marker + '\n' + nav_html, 1)

            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"Fixed: {filename}")

        except Exception as e:
            print(f"Error with {filename}: {e}")

    print(f"\n=== Fixed {fixed_count} files ===")

if __name__ == '__main__':
    fix_consensus_pages()
