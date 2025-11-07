#!/usr/bin/env python3
"""
Example usage of the Covers scraper tools.
Shows how to use the scrapers programmatically in your own scripts.
"""

import json
from datetime import datetime


def example_basic_scraper():
    """Example: Using the basic HTTP scraper."""
    print("="*60)
    print("Example 1: Basic HTTP Scraper")
    print("="*60)

    from covers_scraper import CoversContestScraper

    # Initialize scraper
    scraper = CoversContestScraper(top_n=10, delay=1.0, debug=False)

    # Get leaderboard
    print("\n1. Getting leaderboard...")
    contestants = scraper.get_leaderboard()

    print(f"\nTop 3 Contestants:")
    for contestant in contestants[:3]:
        print(f"  {contestant['rank']}. {contestant['username']} - Streak: {contestant['streak']}")

    # Get picks from first contestant
    if contestants:
        print(f"\n2. Getting picks for {contestants[0]['username']}...")
        picks_data = scraper.get_contestant_picks(contestants[0])
        picks = picks_data['picks']

        if picks:
            print(f"  Found {len(picks)} picks")
        else:
            print("  No picks found (may be loaded via JavaScript)")


def example_consensus_scraper():
    """Example: Using the consensus scraper."""
    print("\n" + "="*60)
    print("Example 2: Consensus Scraper")
    print("="*60)

    from covers_consensus_scraper import CoversConsensusScraper

    # Initialize scraper
    scraper = CoversConsensusScraper(debug=False)

    # Get consensus picks
    print("\n1. Getting consensus picks...")
    picks = scraper.get_consensus_picks()

    if picks:
        print(f"\nTop 3 Consensus Picks:")
        for pick in picks[:3]:
            team = pick.get('team', 'Unknown')
            pct = pick.get('consensus_percentage', 0)
            print(f"  {team}: {pct}%")
    else:
        print("  No consensus picks found (data may be loaded via JavaScript)")


def example_selenium_scraper():
    """Example: Using the Selenium scraper (recommended)."""
    print("\n" + "="*60)
    print("Example 3: Selenium Scraper (RECOMMENDED)")
    print("="*60)

    try:
        from covers_selenium_scraper import CoversSeleniumScraper, SELENIUM_AVAILABLE

        if not SELENIUM_AVAILABLE:
            print("\n⚠️  Selenium not installed. Install with:")
            print("  pip install selenium")
            return

        # Initialize scraper
        scraper = CoversSeleniumScraper(headless=True, debug=False)

        # Get consensus picks
        print("\n1. Getting consensus picks...")
        consensus = scraper.get_consensus_picks()

        if consensus:
            print(f"\nTop 5 Consensus Picks:")
            for i, pick in enumerate(consensus[:5], 1):
                print(f"  {i}. {pick['team']}: {pick['consensus_percentage']}%")

        # Get leaderboard
        print("\n2. Getting leaderboard...")
        leaderboard = scraper.get_leaderboard(top_n=5)

        if leaderboard:
            print(f"\nTop 5 Contestants:")
            for contestant in leaderboard:
                print(f"  {contestant['rank']}. {contestant['username']} - Streak: {contestant['streak']}")

        # Close browser
        scraper.close()

    except ImportError:
        print("\n⚠️  Selenium not installed. Install with:")
        print("  pip install selenium")


def example_save_results():
    """Example: Save results to a custom format."""
    print("\n" + "="*60)
    print("Example 4: Custom Data Processing")
    print("="*60)

    # Load the results from a previous run
    try:
        with open('covers_consensus.json', 'r') as f:
            data = json.load(f)

        print("\n1. Loaded data from covers_consensus.json")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")

        # Process consensus picks
        if 'consensus_picks' in data:
            top_picks = data['consensus_picks'][:5]

            print(f"\n2. Processing top {len(top_picks)} picks...")

            # Create a simple report
            report = []
            report.append("COVERS CONSENSUS REPORT")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            report.append("TOP PICKS:")

            for i, pick in enumerate(top_picks, 1):
                team = pick.get('team', 'Unknown')
                pct = pick.get('consensus_percentage', 0)
                report.append(f"{i}. {team} ({pct}%)")

            report_text = "\n".join(report)

            # Save report
            with open('consensus_report.txt', 'w') as f:
                f.write(report_text)

            print("\n✓ Saved report to consensus_report.txt")
            print("\nReport preview:")
            print(report_text)

        else:
            print("\n⚠️  No consensus picks found in data file")

    except FileNotFoundError:
        print("\n⚠️  No consensus data file found. Run a scraper first:")
        print("  python covers_selenium_scraper.py")


def main():
    """Run all examples."""
    print("COVERS SCRAPER EXAMPLES")
    print("="*60)
    print()
    print("This script demonstrates different ways to use the scrapers.")
    print()

    # Run examples
    example_basic_scraper()
    example_consensus_scraper()
    example_selenium_scraper()
    example_save_results()

    print("\n" + "="*60)
    print("EXAMPLES COMPLETE")
    print("="*60)
    print("\nFor best results, use the Selenium scraper:")
    print("  python covers_selenium_scraper.py")


if __name__ == '__main__':
    main()
