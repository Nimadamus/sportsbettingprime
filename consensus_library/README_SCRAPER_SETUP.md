# Covers Contest Scraper - Setup Guide

## Overview

This scraper harvests consensus picks from the top 100 contestants (ranked by UNITS) across all Covers.com "King of Covers" contests for NFL, NBA, NHL, NCAAB, NCAAF, and CFL.

## Quick Start

### Prerequisites

1. **Python 3.7+** with pip
2. **Google Chrome or Chromium browser**

### Installation

```bash
# Install required Python packages
pip3 install beautifulsoup4 requests selenium webdriver-manager

# On Ubuntu/Debian (for Chrome):
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# OR install Chromium:
sudo apt install chromium-browser
```

## Usage

### Option 1: Run Full Automation (Recommended)

This runs the scraper, processes data, creates the HTML page, and pushes to GitHub:

```bash
cd consensus_library
python3 update_consensus_page.py
```

### Option 2: Run Scraper Only

To just scrape the data without updating the website:

```bash
cd consensus_library
python3 covers_contest_scraper.py
```

This creates:
- `covers_contest_picks.csv` - All individual picks
- `covers_contest_picks_aggregated.csv` - Picks sorted by consensus count
- `covers_contest_picks_summary.txt` - Summary statistics

## How It Works

### 1. Scraper Process (`covers_contest_scraper.py`)

The scraper:
1. Sets up a headless Chrome browser using Selenium
2. For each sport (NFL, NBA, NHL, NCAAB, NCAAF, CFL):
   - Fetches the "King of Covers" leaderboard
   - Gets the top 100 contestants sorted by UNITS
   - Visits each contestant's profile page
   - Extracts their recent picks (up to 50 picks per contestant)
3. Aggregates all picks by consensus (how many experts picked the same thing)
4. Saves to CSV files

**Expected Runtime**: 5-15 minutes depending on network speed

### 2. Page Update Process (`update_consensus_page.py`)

After scraping, this script:
1. Loads the aggregated consensus data from CSV
2. Creates a new dated HTML page (e.g., `sharp-consensus-2025-11-21.html`)
3. Updates the main `sharp-consensus.html` file
4. Updates archive navigation links
5. Commits and pushes to GitHub

## Configuration

### Contest GUIDs

The scraper uses these contest IDs (in `covers_contest_scraper.py`):

```python
CONTESTS = {
    'NBA': '10a69d87-c79f-4687-a90d-b20200cbc2d3',
    'NCAAB': 'a04a59f1-45f1-415f-9d3b-b21400d45dc1',
    'NHL': '51158eb0-5430-4719-a589-b366014e38e1',
    # NFL, NCAAF, CFL GUIDs may need to be updated each season
}
```

**Note**: If a sport's contest URL changes, update the GUID in the script.

### Scraper Settings

Adjust these constants in `covers_contest_scraper.py`:

```python
MAX_CONTESTANTS = 100  # How many top contestants to scrape per sport
MAX_PICKS_PER_CONTESTANT = 50  # How many recent picks to get from each contestant
```

## Troubleshooting

### Chrome Driver Issues

If you see: `selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH`

**Solution**: The script uses `webdriver-manager` to auto-download ChromeDriver, but you can manually install it:

```bash
# Ubuntu/Debian
sudo apt install chromium-chromedriver

# Or download manually from:
# https://chromedriver.chromium.org/downloads
```

### No Picks Scraped

If the scraper returns empty results:

1. **Check if Covers.com structure changed**: Visit the contest pages manually and inspect the HTML
2. **Update CSS selectors**: The scraper may need updated selectors in `get_contestant_picks()`
3. **Check contest GUIDs**: Verify the contest URLs are still valid

### Git Push Fails

```bash
# Make sure you're authenticated with GitHub
git config --global user.email "your@email.com"
git config --global user.name "Your Name"

# If using SSH, make sure your key is added:
ssh -T git@github.com
```

## Advanced Usage

### Scheduled Automation

Set up a cron job to run daily:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 10 AM
0 10 * * * cd /home/user/sportsbettingprime/consensus_library && /usr/bin/python3 update_consensus_page.py >> /var/log/covers_scraper.log 2>&1
```

### Manual Data Review

Before pushing to production, review the scraped data:

```bash
# View top 20 consensus picks
head -n 21 covers_contest_picks_aggregated.csv

# Check summary
cat covers_contest_picks_summary.txt
```

## Files

- `covers_contest_scraper.py` - Main scraper (Selenium-based)
- `update_consensus_page.py` - Automated page generator
- `covers_contest_picks.csv` - Raw picks data
- `covers_contest_picks_aggregated.csv` - Consensus-sorted picks
- `covers_contest_picks_summary.txt` - Statistics summary
- `sharp-consensus.html` - Main consensus page
- `sharp-consensus-YYYY-MM-DD.html` - Dated archive pages

## Support

If scraping fails or data looks incorrect:

1. Check that Chrome/Chromium is installed and working
2. Verify the contest URLs are accessible
3. Review the scraper logs for error messages
4. Update CSS selectors if Covers.com changed their HTML structure

## Notes

- The scraper respects Covers.com with delays between requests
- Only active, current-season contests are scraped
- Picks are from the top 100 contestants ranked by UNITS (not win %)
- Data is aggregated to show what the sharpest bettors are picking
