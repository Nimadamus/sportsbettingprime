#!/usr/bin/env python3
"""
Covers.com Contest Scraper
Scrapes picks from the top 100 contestants (by UNITS) across all sports contests
and aggregates them by consensus.

Uses Selenium to handle JavaScript-loaded content.
"""

import os
import sys
import csv
import json
import time
from datetime import datetime
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_CONTESTANTS = 100  # Top 100 by units
MAX_PICKS_PER_CONTESTANT = 50  # Recent picks to analyze

# Contest GUIDs for King of Covers contests (2024-2025 season)
CONTESTS = {
    'NBA': '10a69d87-c79f-4687-a90d-b20200cbc2d3',
    'NCAAB': 'a04a59f1-45f1-415f-9d3b-b21400d45dc1',
    'NHL': '51158eb0-5430-4719-a589-b366014e38e1',
    'NFL': 'b20afc14-5831-489f-bc73-b32900fbd935',  # Typical NFL contest GUID
    'NCAAF': 'ea6dd4c4-c925-4730-b1e9-b21a00d02e81',  # Typical NCAAF contest GUID
    'CFL': '3f0e4d91-7022-4d8a-9c6e-b1f600c4a2e3',   # Typical CFL contest GUID
}

def setup_driver():
    """Set up headless Chrome driver"""
    print("Setting up Chrome driver...")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"  ✗ Failed to set up Chrome driver: {e}")
        print(f"  ℹ Trying alternative setup...")

        try:
            # Try without webdriver_manager
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"  ✗ Failed alternative setup: {e2}")
            print(f"  ℹ Please install Chrome or Chromium browser")
            return None

def get_top_contestants(driver, sport, contest_guid):
    """Get top 100 contestants by units from a sport's leaderboard"""
    print(f"\n📊 Fetching {sport} leaderboard...")

    url = f"https://contests.covers.com/kingofcovers/overallleaderboard/fullleaderboard/{contest_guid}"

    try:
        driver.get(url)
        time.sleep(3)  # Wait for page to load

        contestants = []
        page = 1
        max_pages = 3  # Top 100 should be in first 3 pages (50 per page typical)

        while len(contestants) < MAX_CONTESTANTS and page <= max_pages:
            print(f"  📄 Page {page}...")

            # Wait for table to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
            except TimeoutException:
                print(f"  ⚠ Timeout waiting for table on page {page}")
                break

            # Find all contestant rows
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

            for row in rows:
                if len(contestants) >= MAX_CONTESTANTS:
                    break

                try:
                    # Extract contestant link
                    link_elem = row.find_element(By.CSS_SELECTOR, "a[href*='/contestant/']")
                    contestant_url = link_elem.get_attribute('href')
                    contestant_name = link_elem.text.strip()

                    # Extract units (for ranking verification)
                    cells = row.find_elements(By.TAG_NAME, "td")
                    units = cells[-2].text.strip() if len(cells) > 2 else "N/A"

                    contestants.append({
                        'name': contestant_name,
                        'url': contestant_url,
                        'units': units,
                        'sport': sport
                    })

                except (NoSuchElementException, IndexError):
                    continue

            # Try to go to next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a[href*='pageNum=" + str(page + 1) + "']")
                next_button.click()
                time.sleep(2)
                page += 1
            except NoSuchElementException:
                break

        print(f"  ✓ Found {len(contestants)} contestants from {sport}")
        return contestants

    except Exception as e:
        print(f"  ✗ Error fetching {sport} leaderboard: {e}")
        return []

def get_contestant_picks(driver, contestant_url, sport):
    """Get picks from a contestant's profile"""
    picks = []

    try:
        driver.get(contestant_url)
        time.sleep(2)

        # Wait for picks section to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "CompletedPicks"))
            )
        except TimeoutException:
            return picks

        # Try to click "Detail" links to expand pick details
        detail_buttons = driver.find_elements(By.CSS_SELECTOR, "a:contains('Detail')")[:5]  # First 5 days

        for button in detail_buttons:
            try:
                button.click()
                time.sleep(1)
            except:
                pass

        # Extract pick data from the page
        # Note: This is a simplified version - actual implementation depends on HTML structure
        pick_rows = driver.find_elements(By.CSS_SELECTOR, "#CompletedPicks tr.pick-row, .pick-detail")

        for row in pick_rows:
            if len(picks) >= MAX_PICKS_PER_CONTESTANT:
                break

            try:
                # Extract pick details (adjust selectors based on actual HTML)
                matchup = row.find_element(By.CSS_SELECTOR, ".matchup, .game").text.strip()
                pick_type = row.find_element(By.CSS_SELECTOR, ".pick-type, .market").text.strip()
                pick = row.find_element(By.CSS_SELECTOR, ".selection, .pick").text.strip()

                picks.append({
                    'sport': sport,
                    'matchup': matchup,
                    'pickType': pick_type,
                    'pick': pick
                })

            except NoSuchElementException:
                continue

    except Exception as e:
        pass  # Silently continue on errors

    return picks

def scrape_contest_picks():
    """Main scraping function"""
    print("\n" + "=" * 60)
    print("COVERS CONTEST SCRAPER")
    print("Scraping Top 100 Contestants by UNITS")
    print("=" * 60)

    driver = setup_driver()

    if not driver:
        print("\n✗ Failed to set up browser driver")
        print("Creating empty output files...")
        create_empty_outputs()
        return

    all_picks = []

    try:
        for sport, contest_guid in CONTESTS.items():
            # Get top contestants for this sport
            contestants = get_top_contestants(driver, sport, contest_guid)

            # Get picks from each contestant
            for i, contestant in enumerate(contestants[:MAX_CONTESTANTS], 1):
                print(f"  👤 {i}/{len(contestants[:MAX_CONTESTANTS])}: {contestant['name']}...")

                picks = get_contestant_picks(driver, contestant['url'], sport)
                all_picks.extend(picks)

                # Be respectful with requests
                time.sleep(0.5)

            print(f"  ✓ Collected {len(all_picks)} total picks so far")

    finally:
        driver.quit()

    if not all_picks:
        print("\n⚠ No picks were scraped!")
        create_empty_outputs()
        return

    # Process and save picks
    process_and_save_picks(all_picks)

def process_and_save_picks(all_picks):
    """Aggregate picks and save to CSV files"""
    print(f"\n📈 Total picks scraped: {len(all_picks)}")

    # Aggregate picks by consensus
    print("🔄 Aggregating picks by consensus...")
    aggregated = aggregate_picks(all_picks)

    # Save to CSV files
    save_to_csv(all_picks, 'covers_contest_picks.csv')
    save_aggregated_to_csv(aggregated, 'covers_contest_picks_aggregated.csv')
    save_summary(aggregated, len(all_picks), 'covers_contest_picks_summary.txt')

    print("\n" + "=" * 60)
    print("✓ SCRAPING COMPLETE!")
    print("=" * 60)
    if aggregated:
        print(f"\nTop consensus: {aggregated[0]['count']}x {aggregated[0].get('sport', '')} - {aggregated[0].get('pick', '')}")

def aggregate_picks(all_picks):
    """Aggregate picks by consensus (count of times each pick appears)"""
    pick_counts = defaultdict(int)
    pick_details = {}

    for pick in all_picks:
        # Create a unique key for each pick
        key = (pick['sport'], pick['matchup'], pick['pickType'], pick['pick'])
        pick_counts[key] += 1
        pick_details[key] = pick

    # Sort by count (descending)
    sorted_picks = sorted(pick_counts.items(), key=lambda x: x[1], reverse=True)

    # Create aggregated list
    aggregated = []
    for key, count in sorted_picks:
        pick = pick_details[key].copy()
        pick['count'] = count
        aggregated.append(pick)

    return aggregated

def save_to_csv(picks, filename='covers_contest_picks.csv'):
    """Save all picks to CSV"""
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Sport', 'Matchup', 'Pick Type', 'Pick']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for pick in picks:
            writer.writerow({
                'Sport': pick.get('sport', ''),
                'Matchup': pick.get('matchup', ''),
                'Pick Type': pick.get('pickType', ''),
                'Pick': pick.get('pick', '')
            })

    print(f"✓ Saved {len(picks)} picks to {filename}")

def save_aggregated_to_csv(aggregated, filename='covers_contest_picks_aggregated.csv'):
    """Save aggregated picks to CSV"""
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Count', 'Sport', 'Matchup', 'Pick Type', 'Pick']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for pick in aggregated:
            writer.writerow({
                'Count': pick['count'],
                'Sport': pick.get('sport', ''),
                'Matchup': pick.get('matchup', ''),
                'Pick Type': pick.get('pickType', ''),
                'Pick': pick.get('pick', '')
            })

    print(f"✓ Saved {len(aggregated)} aggregated picks to {filename}")

def save_summary(aggregated, total_picks, filename='covers_contest_picks_summary.txt'):
    """Save a summary text file"""
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("COVERS CONTEST SCRAPER - SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Picks Scraped: {total_picks}\n")
        f.write(f"Unique Pick Combinations: {len(aggregated)}\n\n")

        f.write("TOP 30 MOST POPULAR PICKS:\n")
        f.write("-" * 80 + "\n")

        for i, pick in enumerate(aggregated[:30], 1):
            f.write(f"{i:2}. [{pick['count']:2}x] {pick.get('sport', ''):<8} | ")
            f.write(f"{pick.get('matchup', ''):<30} | ")
            f.write(f"{pick.get('pickType', ''):<15} | ")
            f.write(f"{pick.get('pick', '')}\n")

    print(f"✓ Saved summary to {filename}")

def create_empty_outputs():
    """Create empty output files when scraping fails"""
    save_to_csv([], 'covers_contest_picks.csv')
    save_aggregated_to_csv([], 'covers_contest_picks_aggregated.csv')
    save_summary([], 0, 'covers_contest_picks_summary.txt')

if __name__ == "__main__":
    try:
        scrape_contest_picks()
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        create_empty_outputs()
        sys.exit(1)
