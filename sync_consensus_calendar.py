"""
Sync the ARCHIVE_DATA calendar in covers-consensus.html with actual files.
Scans for all covers-consensus-YYYY-MM-DD.html files and updates the array.
"""

import os
import re

REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

def get_all_consensus_files():
    """Get sorted list of all dated consensus files"""
    files = []
    for filename in os.listdir(REPO_PATH):
        match = re.match(r'covers-consensus-(\d{4}-\d{2}-\d{2})\.html', filename)
        if match:
            files.append((match.group(1), filename))
    return sorted(files)

def sync_calendar():
    consensus_files = get_all_consensus_files()
    print(f"Found {len(consensus_files)} dated consensus files")

    # Build new ARCHIVE_DATA array
    archive_entries = []
    for date_str, filename in consensus_files:
        archive_entries.append(f'            {{ date: "{date_str}", page: "{filename}" }}')

    new_archive_data = "const ARCHIVE_DATA = [\n" + ",\n".join(archive_entries) + "\n        ];"

    # Read main consensus page
    main_page = os.path.join(REPO_PATH, "covers-consensus.html")
    with open(main_page, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Replace ARCHIVE_DATA array
    pattern = r'const ARCHIVE_DATA = \[.*?\];'
    content = re.sub(pattern, new_archive_data, content, flags=re.DOTALL)

    if content != original:
        with open(main_page, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated covers-consensus.html with {len(consensus_files)} calendar entries")
    else:
        print("No changes needed")

    # Also check the individual dated pages for their ARCHIVE_DATA (if they have it)
    updated_count = 0
    for date_str, filename in consensus_files:
        filepath = os.path.join(REPO_PATH, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                page_content = f.read()

            if 'ARCHIVE_DATA' in page_content:
                page_original = page_content
                page_content = re.sub(pattern, new_archive_data, page_content, flags=re.DOTALL)
                if page_content != page_original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    updated_count += 1
        except Exception as e:
            print(f"Error with {filename}: {e}")

    if updated_count > 0:
        print(f"Also updated ARCHIVE_DATA in {updated_count} individual dated pages")

if __name__ == '__main__':
    sync_calendar()
