#!/usr/bin/env python3
"""
Test to examine a contestant's profile page and pick structure
"""

import requests
from bs4 import BeautifulSoup

def examine_contestant_profile():
    """Examine a top contestant's profile to see pick structure"""

    # Top contestant from NBA: SmoothPicks804
    url = 'https://contests.covers.com/kingofcovers/contestant/2b2c67e6-d6fc-4c66-8ad1-b2b1008ebf19'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("\n" + "=" * 60)
    print("EXAMINING CONTESTANT PROFILE: SmoothPicks804")
    print("=" * 60 + "\n")

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    print(f"Page size: {len(response.text)} bytes\n")

    # Look for picks section
    picks_section = soup.find(id='CompletedPicks')
    if picks_section:
        print("✓ Found #CompletedPicks section\n")
    else:
        print("✗ No #CompletedPicks section found")
        # Try to find any picks-related elements
        print("\nSearching for pick-related elements...")
        pick_elements = soup.find_all(class_=lambda x: x and 'pick' in x.lower())
        print(f"Found {len(pick_elements)} elements with 'pick' in class name")

    # Look for tables
    tables = soup.find_all('table')
    print(f"\n✓ Found {len(tables)} table(s)")

    if tables:
        print("\nExamining first table...")
        table = tables[0]

        # Get headers
        headers_row = table.find('thead')
        if headers_row:
            headers = [th.text.strip() for th in headers_row.find_all('th')]
            print(f"Headers: {headers}")

        # Get first few rows
        rows = table.find_all('tr')[:10]
        print(f"\nFirst 5 data rows:")

        for i, row in enumerate(rows[1:6]):  # Skip header row
            cells = row.find_all(['td', 'th'])
            print(f"\nRow {i+1}:")
            for j, cell in enumerate(cells):
                # Check for links or buttons
                link = cell.find('a')
                if link:
                    print(f"  Cell {j}: [LINK] {cell.text.strip()[:50]} → {link.get('href', '')[:50]}")
                else:
                    print(f"  Cell {j}: {cell.text.strip()[:50]}")

    # Look for JavaScript data
    print("\n\nLooking for JavaScript data...")
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('pick' in script.string.lower() or 'game' in script.string.lower()):
            content = script.string[:500]
            if any(keyword in content.lower() for keyword in ['picks', 'games', 'matchup']):
                print(f"\nFound relevant script (showing first 500 chars):")
                print(content)
                break

if __name__ == "__main__":
    examine_contestant_profile()
