# ✅ COMPLETE: BetLegend Records → League Pages Automation

## What's Built

A fully automated system that reads graded picks from your BetLegend Google Sheet and pushes them to the appropriate league pages on your website.

---

## How It Works

### 1. **Data Source: CSV Export (No API Key)**
- Fetches from: `https://docs.google.com/spreadsheets/d/e/2PACX-1vQjW2l6hBUafumAiOdJblACLIx3GTtdJDcytUcN1nu2QHJmHnUMN9_5Tp2v7VqMTZaATfdmcJ-SK4jD/pub?output=csv`
- No authentication required
- No API keys needed
- No OAuth setup

### 2. **Parsing & Filtering**
- Parses CSV rows
- Filters for graded picks where:
  - **Column K (GRADE)** = W, L, or P
  - **Column M (PROCESSED)** = YES
- Extracts: Date, Pick, Odds, Units, League, Grade, Unit Result

### 3. **Grouping by League**
- Groups picks by **Column F (League)**
- Supported leagues:
  - **NFL** → `nfl-gridiron-oracles.html`
  - **NHL** → `nhl-ice-oracles.html`
  - **NCAAF** → `college-football.html`
  - **MLB** → `mlb-prime-directives.html`
  - **NBA** → `nba.html` (if exists)

### 4. **Generating Verified Records Sections**
For each league, generates a styled section with:
- **Stats Summary**: Record, Win Rate, Net Units, Total Picks
- **Pick Table**: Date, Pick, Odds, Units, Result, Net Units
- **Color-coded results**: Green (WIN), Red (LOSS), Gray (PUSH)
- **Last Updated timestamp**

### 5. **Inserting into League Pages**
- Finds the corresponding HTML file for each league
- Inserts BetLegend section after the hero section
- Uses HTML comment markers to replace existing sections:
  ```html
  <!-- BETLEGEND_RECORDS_START -->
  ...verified records section...
  <!-- BETLEGEND_RECORDS_END -->
  ```
- If section exists: **replaces it** with updated data
- If section doesn't exist: **inserts new section** after first `</section>` tag

### 6. **Committing & Pushing**
- Commits all updated HTML files:
  - `betlegend-records.html` (main records page)
  - `nfl-gridiron-oracles.html` (if NFL picks exist)
  - `nhl-ice-oracles.html` (if NHL picks exist)
  - `college-football.html` (if NCAAF picks exist)
  - `mlb-prime-directives.html` (if MLB picks exist)
  - `nba.html` (if NBA picks exist)
- Push message: "Update BetLegend verified records [automated]"

---

## The Complete Flow

```
YOU: Grade pick in Google Sheet
  - Add W/L/P to Column K
  - Mark "YES" in Column M
    ↓
GOOGLE SHEET: CSV export updates automatically
    ↓
GITHUB ACTION: (runs every 15 minutes + on push)
  1. Fetch CSV from published URL
  2. Parse all rows
  3. Filter: WHERE K=W/L/P AND M=YES
  4. Group by Column F (league)
  5. For each league:
     - Calculate stats
     - Generate HTML section
     - Update league page
  6. Generate main betlegend-records.html
  7. Commit all changes
  8. Push to GitHub
    ↓
WEBSITE: All league pages update automatically
  - nfl-gridiron-oracles.html shows NFL verified records
  - nhl-ice-oracles.html shows NHL verified records
  - college-football.html shows NCAAF verified records
  - etc.
```

---

## What You Need to Do

### To Make Column M Say "YES":

The automation reads Column M (PROCESSED) to know which picks to include. You can mark it in any of these ways:

**Option 1: Manual**
- When you grade a pick (Column K), type "YES" in Column M

**Option 2: Formula**
- In Column M, row 2: `=IF(K2<>"", "YES", "")`
- Copy down to all rows
- When you grade Column K, Column M automatically fills "YES"

**Option 3: Apps Script** (if you want automation)
- Use Google Apps Script to auto-fill Column M when Column K is filled
- Script runs on edit, checks if Column K changed, fills Column M
- Up to you - not required

**Option 4: Any Other Method**
- The CSV automation doesn't care HOW Column M gets filled
- It just reads the CSV and looks for rows where M = "YES"

---

## What Happens Automatically

### Every 15 Minutes:
- GitHub Action wakes up
- Fetches latest CSV
- Parses graded picks
- Updates league pages
- Commits and pushes if anything changed

### On Every Push:
- Same process runs immediately
- Ensures pages update quickly after code changes

### Manual Trigger:
- Go to GitHub → Actions
- Click "Update BetLegend Records"
- Click "Run workflow"
- Wait ~30 seconds
- All pages updated

---

## Example Output

When you visit `nfl-gridiron-oracles.html`, you'll see a new section:

```
┌─────────────────────────────────────────────┐
│   BetLegend Verified NFL Records            │
├─────────────────────────────────────────────┤
│  Record     Win Rate    Net Units   Picks   │
│   2-1        66.7%       +1.80       3      │
├─────────────────────────────────────────────┤
│ Date      Pick           Odds  Units  Result│
│ 11/10    Packers PK     -110   2     WIN   │
│ 11/09    Chiefs -3      -110   1     LOSS  │
│ 11/08    Bills ML       +150   1     WIN   │
└─────────────────────────────────────────────┘
   Last Updated: November 14, 2025 at 5:45 PM
```

---

## Files Modified by Automation

The GitHub Action will automatically update these files when graded picks exist:

- ✅ `betlegend-records.html` (always)
- ✅ `nfl-gridiron-oracles.html` (if NFL picks exist)
- ✅ `nhl-ice-oracles.html` (if NHL picks exist)
- ✅ `college-football.html` (if NCAAF picks exist)
- ✅ `mlb-prime-directives.html` (if MLB picks exist)
- ✅ `nba.html` (if NBA picks exist and file exists)

---

## No Manual Work Required

After you merge this branch to main:

❌ No manual HTML editing
❌ No pasting code
❌ No running scripts locally
❌ No testing
❌ No deployment steps
❌ No involvement

✅ Just grade picks in Google Sheet
✅ Make sure Column M = "YES"
✅ Everything else is automatic

---

## Current Status

**✅ Built and Ready**
- Automation script: `scripts/sync-betlegend.js`
- GitHub Action: `.github/workflows/update-betlegend.yml`
- League mapping configured
- HTML generation styled
- Commit/push automated

**🔄 Triggered**
- Just pushed to branch
- GitHub Action should be running now
- Check: GitHub → Actions tab

**📋 To Activate Permanently**
```bash
git checkout main
git merge claude/fix-sheet-automation-script-01C5UwKdAWW84PCSJAN8CGpT
git push
```

Once merged to main, the automation runs forever on a 15-minute schedule.

---

## Summary

**Your Part:**
1. Grade picks (W/L/P in Column K)
2. Mark processed (YES in Column M)

**Automated Part:**
1. Fetch CSV every 15 minutes
2. Parse graded picks
3. Group by league
4. Generate HTML sections for each league
5. Update league pages
6. Commit and push
7. Website reflects changes

**Zero manual intervention. 100% automated. CSV-only. No API keys. No Apps Script required.**
