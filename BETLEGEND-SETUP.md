# BetLegend Automation - ZERO SETUP REQUIRED

This automation reads graded picks from the BetLegend Google Sheet and automatically updates the website.

**NO API KEY. NO OAUTH. NO GITHUB SECRETS. NO BULLSHIT.**

## How It Works

Uses Google Sheets public CSV export endpoint - requires ZERO authentication:

```
https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=0
```

## The Complete Pipeline

```
1. You grade pick in Google Sheet (W/L/P in column K)
   ↓
2. Google Apps Script processes it
   ↓
3. Within 15 minutes, GitHub Action runs automatically
   ↓
4. Action fetches CSV from public sheet (no API key)
   ↓
5. Script parses graded picks
   ↓
6. HTML page generated (betlegend-records.html)
   ↓
7. Committed and pushed to GitHub
   ↓
8. Website updates automatically
```

## ONE-TIME SETUP (1 minute)

**Step 1: Make Sheet Public (View Only)**

1. Open the BetLegend Picks Tracker sheet
2. Click **Share** button (top right)
3. Change to: **"Anyone with the link can VIEW"** (NOT edit)
4. Click **Done**

**That's it. You're done.**

## Files Created

- `.github/workflows/update-betlegend.yml` - Runs every 15 minutes
- `scripts/sync-betlegend.js` - Fetches CSV, generates HTML
- `betlegend-records.html` - Auto-generated records page

## What Gets Updated

The `betlegend-records.html` file shows:

- **Overall Stats**: Total record, win rate, net units
- **Per-League Tables**: NFL, NBA, NHL, NCAAF, UEFA (separate sections)
- **Individual Picks**: Date, pick, odds, units, result, net units
- **Auto-Updated**: Every 15 minutes

## View Your Records

Once automation runs:
- `https://yourdomain.com/betlegend-records.html`
- Or: `https://nimadamus.github.io/sportsbettingprime/betlegend-records.html`

## How Grading Works

Script reads Google Sheet and looks for:

- **Column K (11)**: GRADE - Must be W, L, or P
- **Column M (13)**: PROCESSED - Must be YES

Only rows with BOTH are included on the verified records page.

## Customization

### Change Update Frequency

Edit `.github/workflows/update-betlegend.yml`:

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
    # Or change to:
    - cron: '*/30 * * * *'  # Every 30 minutes
    - cron: '0 * * * *'     # Every hour
    - cron: '0 */6 * * *'   # Every 6 hours
```

### Test Locally

No API key needed:

```bash
export SHEET_ID="1izhhxwiazn9S8RqcK8QUpE4pWDRIFnPq5yw5ZISMsmv"
export GID="0"

node scripts/sync-betlegend.js
```

Output: `betlegend-records.html` (generated in repo root)

## Troubleshooting

### "No graded picks found"

**Check:**
- Column K (GRADE) contains W, L, or P
- Column M (PROCESSED) contains YES
- Sheet is public ("Anyone with link can view")

### "Sheet is not public" error

**Fix:**
1. Open Google Sheet
2. Share → "Anyone with link can VIEW"
3. Re-run automation

### GitHub Action not running

**Check:**
- Actions tab in GitHub for errors
- Workflow file is in `.github/workflows/`
- Branch is merged to main (actions run on main)

## Sheet Column Structure

The script expects this EXACT structure:

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
| K (11) | **GRADE** | **W/L/P (required for records)** |
| L (12) | UNIT_RESULT | Calculated by Apps Script |
| M (13) | **PROCESSED** | **YES (required for records)** |

## Why CSV Export Works

Google Sheets allows public viewing through CSV download without authentication:

- ✅ No API key required
- ✅ No OAuth required
- ✅ No service account required
- ✅ No GitHub secrets required
- ✅ Just needs sheet to be "view only"

This is Google's built-in feature for public data access.

## What Happens When You Grade

1. Select W/L/P in column K
2. Apps Script calculates unit result (column L)
3. Apps Script marks PROCESSED = YES (column M)
4. Within 15 minutes, automation runs
5. CSV fetched from public endpoint
6. HTML generated with graded picks
7. Committed to GitHub
8. Website updates

**Fully automatic. Zero manual steps after initial setup.**

## Manual Trigger

To run immediately (without waiting 15 minutes):

1. Go to GitHub → Actions tab
2. Click "Update BetLegend Records"
3. Click "Run workflow"
4. Click green "Run workflow" button
5. Wait ~30 seconds
6. Check if `betlegend-records.html` was updated

## Deployment Checklist

- [x] Set sheet to "Anyone with link can view"
- [x] Merge branch to main
- [x] Wait 15 minutes (or trigger manually)
- [x] Check website for updated records

## Support

If automation stops:

1. Verify sheet is still public
2. Check GitHub Actions logs
3. Verify sheet ID hasn't changed
4. Ensure column structure matches above

**The entire system requires ZERO credentials and ZERO manual intervention after setup.**
