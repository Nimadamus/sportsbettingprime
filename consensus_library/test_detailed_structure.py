#!/usr/bin/env python3
"""
Detailed test to examine Covers.com HTML structure
"""

import requests
from bs4 import BeautifulSoup
import json

def examine_leaderboard():
    """Examine the NBA leaderboard structure in detail"""
    url = 'https://contests.covers.com/kingofcovers/overallleaderboard/fullleaderboard/10a69d87-c79f-4687-a90d-b20200cbc2d3'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("\n" + "=" * 60)
    print("EXAMINING NBA LEADERBOARD STRUCTURE")
    print("=" * 60 + "\n")

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table
    table = soup.find('table')
    if not table:
        print("✗ No table found!")
        return

    print("✓ Table found\n")

    # Examine table headers
    headers = table.find_all('th')
    print(f"Table Headers ({len(headers)}):")
    for i, th in enumerate(headers):
        print(f"  {i}: {th.text.strip()}")

    print()

    # Examine first 5 rows
    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
    print(f"\nFirst 5 Contestant Rows:\n")

    for i, row in enumerate(rows[:5]):
        cells = row.find_all('td')
        print(f"Row {i + 1}:")

        for j, cell in enumerate(cells):
            # Look for links
            link = cell.find('a')
            if link:
                href = link.get('href', '')
                text = link.text.strip()
                print(f"  Cell {j}: [LINK] {text} → {href}")
            else:
                print(f"  Cell {j}: {cell.text.strip()}")

        print()

        # Try to find contestant profile link
        profile_link = row.find('a', href=lambda x: x and '/contestant/' in x)
        if profile_link:
            print(f"  ✓ Profile Link Found: {profile_link.get('href')}")
            print(f"  ✓ Contestant Name: {profile_link.text.strip()}")
        print()

if __name__ == "__main__":
    examine_leaderboard()
