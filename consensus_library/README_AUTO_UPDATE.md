# Sharp Consensus Auto-Update Instructions

## Quick Start (ONE-CLICK UPDATE)

### Option 1: Double-click the Batch File
1. Navigate to: `C:\Users\Nima\Documents\GitHub\sportsbettingprime\consensus_library`
2. Double-click: **`UPDATE_CONSENSUS.bat`**
3. Wait for it to complete (2-5 minutes)
4. Done! The page is updated and pushed to GitHub.

### Option 2: Run from Command Line
```cmd
cd C:\Users\Nima\Documents\GitHub\sportsbettingprime\consensus_library
python update_consensus_page.py
```

## What the Script Does Automatically

The automation script performs these 5 steps:

1. **Runs the Scraper**
   - Executes `covers_contest_scraper.py`
   - Scrapes top 100 contestants by units from all Covers.com contests
   - Generates CSV files with aggregated consensus data

2. **Processes Data**
   - Loads top 100 consensus picks from CSV
   - Calculates stats (highest consensus, sport count)
   - Converts to JavaScript format

3. **Creates New Page**
   - Creates `sharp-consensus-YYYY-MM-DD.html` with today's date
   - Updates all metadata (title, description, canonical URLs)
   - Injects consensus data into JavaScript array
   - Updates stats (highest consensus, sport count)
   - Updates archive navigation links
   - Updates main `sharp-consensus.html` file

4. **Updates Navigation**
   - Updates `index.html` to point to new consensus page
   - Updates date parameter in URL

5. **Commits & Pushes**
   - Stages all changes
   - Creates descriptive commit message
   - Pushes to GitHub
   - Page goes live automatically

## Files Created

The script creates these files in the consensus_library folder:

- `sharp-consensus-YYYY-MM-DD.html` - New dated page
- `covers_contest_picks.csv` - Raw individual picks
- `covers_contest_picks_aggregated.csv` - Aggregated consensus data
- `covers_contest_picks_summary.txt` - Summary stats

## Troubleshooting

### If the script fails:

1. **Check Python is installed**
   ```cmd
   python --version
   ```
   Should show Python 3.x

2. **Check scraper exists**
   - Verify file exists: `C:\Users\Nima\Desktop\Scripts\covers_contest_scraper.py`

3. **Check Git is working**
   ```cmd
   cd C:\Users\Nima\Documents\GitHub\sportsbettingprime
   git status
   ```

4. **Run manually to see errors**
   ```cmd
   cd C:\Users\Nima\Documents\GitHub\sportsbettingprime\consensus_library
   python update_consensus_page.py
   ```

### Common Issues:

- **"No module named 'requests'"**
  - Run: `pip install requests beautifulsoup4`

- **Git push fails**
  - Make sure you're logged into GitHub
  - Check internet connection

- **Scraper times out**
  - Run again - sometimes Covers.com is slow

## Scheduling (Optional)

To run this automatically every day:

1. Open Task Scheduler (Windows)
2. Create Basic Task
3. Trigger: Daily at your preferred time
4. Action: Start a program
   - Program: `C:\Users\Nima\Documents\GitHub\sportsbettingprime\consensus_library\UPDATE_CONSENSUS.bat`
5. Save

## Manual Override

If you need to manually edit something:

1. Edit the dated file directly: `sharp-consensus-YYYY-MM-DD.html`
2. Copy to main file: `cp sharp-consensus-YYYY-MM-DD.html sharp-consensus.html`
3. Commit and push:
   ```cmd
   git add .
   git commit -m "Manual update"
   git push
   ```

## Support

If something breaks, you can always:
1. Check the generated files in the consensus_library folder
2. Review the CSV files to verify data was scraped correctly
3. Open the HTML files in a browser to test locally before pushing
