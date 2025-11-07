# sportsbettingprime

## Covers Contest Scraper

A Python tool for scraping Covers.com Streak Survivor contest data and generating consensus reports from top contestants' picks.

### Features

- Scrapes the current Streak Survivor leaderboard
- Extracts consensus picks with percentages
- Multiple scraper versions (basic HTTP, consensus-focused, and Selenium for JavaScript-rendered content)
- Generates detailed JSON reports with pick statistics
- Respectful rate-limiting to avoid overloading the server

### Installation

#### Basic Installation

```bash
pip install -r requirements.txt
```

#### For JavaScript-Rendered Content (Recommended)

The Selenium version can handle dynamically loaded content:

```bash
pip install requests beautifulsoup4 lxml selenium

# Install Chrome/Chromium browser
# Ubuntu/Debian:
sudo apt-get install chromium-browser chromium-chromedriver

# macOS:
brew install chromedriver
```

### Available Scrapers

The project includes three scraper versions:

1. **covers_scraper.py** - Basic HTTP scraper for leaderboard and static content
2. **covers_consensus_scraper.py** - Focused on consensus picks from main page
3. **covers_selenium_scraper.py** - Selenium-based scraper for JavaScript-rendered content (RECOMMENDED)

### Usage

#### Recommended: Selenium Scraper (Handles JavaScript)

Get consensus picks and top contestants:

```bash
python covers_selenium_scraper.py
```

With options:

```bash
# Scrape top 30 contestants
python covers_selenium_scraper.py -n 30

# Save to custom output file
python covers_selenium_scraper.py -o daily_picks.json

# Run in visible browser mode (not headless)
python covers_selenium_scraper.py --no-headless

# Enable debug output
python covers_selenium_scraper.py --debug
```

#### Basic HTTP Scraper

For static leaderboard data only:

```bash
# Scrape top 20 contestants
python covers_scraper.py

# Custom options
python covers_scraper.py -n 50 -o leaderboard.json -d 2.0

# Enable debug mode
python covers_scraper.py --debug
```

#### Consensus-Only Scraper

For attempting to extract consensus from page text:

```bash
python covers_consensus_scraper.py -o consensus.json
```

#### Command Line Arguments

**Selenium Scraper:**
- `-n, --top-n`: Number of top contestants (default: 20)
- `-o, --output`: Output file path (default: covers_consensus.json)
- `--no-headless`: Run browser in visible mode
- `--debug`: Enable debug output

**Basic Scraper:**
- `-n, --top-n`: Number of top contestants (default: 20)
- `-o, --output`: Output file path (default: covers_consensus.json)
- `-d, --delay`: Delay between requests in seconds (default: 1.0)
- `--debug`: Enable debug output

### Output Format

#### Selenium Scraper Output

```json
{
  "timestamp": "2025-11-07T10:30:00.123456",
  "consensus_picks": [
    {
      "team": "Miami Dolphins",
      "consensus_percentage": 81.0,
      "source": "selenium"
    },
    {
      "team": "Detroit Lions",
      "consensus_percentage": 77.0,
      "source": "selenium"
    }
  ],
  "leaderboard": [
    {
      "rank": 1,
      "username": "Baldhead0099",
      "streak": "13",
      "best": "13",
      "profile_url": "https://contests.covers.com/..."
    }
  ],
  "total_consensus_picks": 25,
  "total_contestants": 20
}
```

#### Basic Scraper Output

```json
{
  "timestamp": "2025-11-07T10:30:00.123456",
  "total_contestants_scraped": 20,
  "contestants_with_picks": 0,
  "consensus": []
}
```

**Note:** The basic HTTP scraper may not extract picks if they're loaded via JavaScript. Use the Selenium scraper for complete data.

### Example Output

```
============================================================
Covers Contest Selenium Scraper
============================================================
Target: Top 20 contestants + Consensus picks
Output: covers_consensus.json
============================================================

Initializing browser...
✓ Browser initialized

Fetching consensus picks from https://contests.covers.com/survivor...
✓ Found 25 consensus picks

Fetching leaderboard from https://contests.covers.com/survivor/currentleaderboard...
  #1: Baldhead0099 (Streak: 13)
  #2: Aliquippa (Streak: 12)
  #3: Ballbuster2008 (Streak: 11)
  #4: KeyMaster (Streak: 11)
  #5: kj1121 (Streak: 11)
  ...
✓ Found 20 contestants

✓ Data saved to covers_consensus.json

============================================================
CONSENSUS SUMMARY
============================================================
1. Miami Dolphins
   Consensus: 81.0%

2. Detroit Lions
   Consensus: 77.0%

3. Utah State
   Consensus: 75.0%
```

### Use Cases

- **Daily Pick Analysis**: Run daily to see what top players are picking
- **Consensus Betting**: Use consensus to inform your own betting decisions
- **Trend Analysis**: Track picks over time to identify patterns
- **Research**: Study successful bettors' strategies

### Best Practices

- **Use the Selenium scraper** for best results with JavaScript-rendered content
- Run during active betting periods when contestants have pending picks
- Use reasonable delay values (1-2 seconds) for the basic scraper
- Don't run too frequently - once or twice per day is typically sufficient
- Consider the consensus as one data point among many for betting decisions
- For automated daily runs, consider scheduling with cron or Task Scheduler

### Troubleshooting

#### Selenium Issues

If you encounter browser/driver issues:

```bash
# Ubuntu/Debian - Install Chromium and driver
sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver

# Verify ChromeDriver
chromedriver --version

# If ChromeDriver not in PATH, download manually:
# https://chromedriver.chromium.org/downloads
```

#### No Picks Found

- The basic HTTP scrapers may not work with JavaScript-rendered content
- Use the Selenium scraper (`covers_selenium_scraper.py`) instead
- Ensure you're running during active contest periods
- Check that the website structure hasn't changed

### Disclaimer

This tool is for educational and research purposes. Always gamble responsibly and within your means. Past performance does not guarantee future results.

### License

MIT License