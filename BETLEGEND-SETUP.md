# BetLegend Automation Setup

This automation system reads graded picks from the BetLegend Google Sheet and automatically updates the website.

## How It Works

1. **Google Sheet → Script → Website**
   - Every 15 minutes, a GitHub Action runs
   - Reads all rows from the BetLegend Picks Tracker sheet
   - Filters for graded picks (W/L/P in column K, "YES" in column M)
   - Generates an HTML page with all verified records
   - Commits and pushes to GitHub
   - Website updates automatically

2. **Files Created**
   - `.github/workflows/update-betlegend.yml` - GitHub Action workflow
   - `scripts/sync-betlegend.js` - Sync script
   - `betlegend-records.html` - Generated records page (auto-updated)

## Setup Instructions

### 1. Get Google Sheets API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Sheets API"
4. Go to Credentials → Create Credentials → API Key
5. Copy the API key

### 2. Add API Key to GitHub

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `GOOGLE_SHEETS_API_KEY`
5. Value: Paste your API key
6. Click "Add secret"

### 3. Make Sheet Public (Read-Only)

1. Open the BetLegend Picks Tracker sheet
2. Click Share → Change to "Anyone with the link can view"
3. This allows the API to read without authentication

### 4. Test the Automation

1. Push these files to GitHub
2. Go to Actions tab
3. Click "Update BetLegend Records"
4. Click "Run workflow"
5. Wait for it to complete
6. Check if `betlegend-records.html` was created/updated

### 5. View the Results

Once the automation runs:
- Visit: `https://yourdomain.com/betlegend-records.html`
- Or: `https://nimadamus.github.io/sportsbettingprime/betlegend-records.html`

## Manual Run

To test locally:

```bash
# Set API key
export GOOGLE_SHEETS_API_KEY="your-api-key-here"
export SHEET_ID="1izhhxwiazn9S8RqcK8QUpE4pWDRIFnPq5yw5ZISMsmv"

# Install dependencies
npm install googleapis

# Run script
node scripts/sync-betlegend.js
```

## How Grading Works

The script reads from the Google Sheet and looks for:

- **Column K (11)**: GRADE - Must be W, L, or P
- **Column M (13)**: PROCESSED - Must be "YES"

Only rows meeting both criteria are included in the verified records page.

## What Gets Updated

The `betlegend-records.html` file contains:

- **Overall Stats**: Total record, win rate, net units
- **Per-League Tables**: Separate sections for NFL, NBA, NHL, NCAAF, UEFA
- **Individual Pick Details**: Date, pick, odds, units, result, net units
- **Auto-generated**: Updates every 15 minutes

## Customization

### Change Update Frequency

Edit `.github/workflows/update-betlegend.yml`:

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
    # Change to:
    - cron: '*/30 * * * *'  # Every 30 minutes
    - cron: '0 * * * *'     # Every hour
    - cron: '0 */6 * * *'   # Every 6 hours
```

### Change Output File

Edit `scripts/sync-betlegend.js`:

```javascript
const OUTPUT_FILE = path.join(__dirname, '..', 'betlegend-records.html');
// Change to your preferred filename
```

### Modify HTML Styling

The generated HTML includes embedded CSS. Edit the `generateHTML()` function in `scripts/sync-betlegend.js` to customize appearance.

## Troubleshooting

### Workflow Not Running

- Check GitHub Actions tab for errors
- Verify `GOOGLE_SHEETS_API_KEY` secret is set
- Make sure sheet is public (view-only)

### No Records Showing

- Verify rows in Google Sheet have:
  - Column K = W, L, or P
  - Column M = YES
- Check GitHub Actions logs for errors

### API Quota Exceeded

Google Sheets API has daily quotas:
- Free tier: 500 requests/day per project
- Each workflow run = 1 request
- If running every 15 min = 96 requests/day (well within limit)

## Sheet Column Structure

The script expects this exact structure:

| Column | Name | Description |
|--------|------|-------------|
| A (1) | Date | Date of pick |
| B (2) | Pick | Pick description |
| C (3) | Odds | Betting odds |
| D (4) | Result | (unused) |
| E (5) | Units | Units wagered |
| F (6) | League | NFL, NBA, NHL, NCAAF, UEFA |
| G (7) | Sport | Sport name |
| H (8) | Ready | Ready flag |
| I (9) | PostedAt | Posting timestamp |
| J (10) | Pushed | Push flag |
| K (11) | **GRADE** | **W/L/P (required)** |
| L (12) | UNIT_RESULT | Calculated result |
| M (13) | **PROCESSED** | **YES (required)** |

## Support

If the automation stops working:

1. Check GitHub Actions logs
2. Verify API key is valid
3. Verify sheet is still public
4. Check sheet ID hasn't changed
5. Ensure column structure matches above

## What Happens When You Grade a Pick

1. You select W/L/P in column K of the Google Sheet
2. Google Apps Script calculates unit result (column L)
3. Google Apps Script marks row as processed (column M = "YES")
4. Within 15 minutes, GitHub Action runs
5. Script reads all processed rows
6. HTML page is generated
7. Changes are committed and pushed
8. Website updates automatically

**The entire process is fully automatic after setup.**
