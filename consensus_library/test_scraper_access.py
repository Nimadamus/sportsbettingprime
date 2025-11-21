#!/usr/bin/env python3
"""
Test script to verify Covers.com access and HTML structure
Run this to see if the contest pages are accessible
"""

import requests
from bs4 import BeautifulSoup

# Test URLs
TEST_URLS = {
    'NBA Leaderboard': 'https://contests.covers.com/kingofcovers/overallleaderboard/fullleaderboard/10a69d87-c79f-4687-a90d-b20200cbc2d3',
    'NHL Leaderboard': 'https://contests.covers.com/kingofcovers/overallleaderboard/fullleaderboard/51158eb0-5430-4719-a589-b366014e38e1',
}

def test_url_access():
    """Test if we can access Covers.com contest pages"""
    print("\n" + "=" * 60)
    print("TESTING COVERS.COM ACCESS")
    print("=" * 60 + "\n")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for name, url in TEST_URLS.items():
        print(f"Testing: {name}")
        print(f"URL: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status Code: {response.status_code}")
            print(f"  Page Size: {len(response.text)} bytes")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for key elements
                tables = soup.find_all('table')
                links = soup.find_all('a', href=lambda x: x and '/contestant/' in x)

                print(f"  ✓ Tables found: {len(tables)}")
                print(f"  ✓ Contestant links found: {len(links)}")

                if links:
                    print(f"  Sample contestant link: {links[0].get('href', 'N/A')}")
                    print(f"  Sample contestant name: {links[0].text.strip()}")

            else:
                print(f"  ✗ Failed to access page (status {response.status_code})")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        print()

if __name__ == "__main__":
    test_url_access()
