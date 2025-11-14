# Google Apps Script - Installation (2 minutes)

## THE PROBLEM YOU'RE SEEING:

Graded picks (W/L/P in column K) are **not copying to league sheets** (NFL, NBA, etc.).

## WHY:

The Google Apps Script needs to be installed in your Google Sheet. This cannot be automated - Google requires manual installation.

## THE FIX (Copy-Paste, 2 Minutes):

### Step 1: Open Apps Script Editor

1. Open your BetLegend Google Sheet
2. Click **Extensions** → **Apps Script**
3. You'll see the script editor open

### Step 2: Replace All Code

1. **Select all existing code** (Ctrl+A or Cmd+A)
2. **Delete it** (Backspace)
3. **Open this file** in the repo: `betlegend-sheet-script.gs`
4. **Copy ALL the code** (Ctrl+A, then Ctrl+C)
5. **Paste into Apps Script editor** (Ctrl+V)

### Step 3: Save

1. Click the **Save icon** (💾) or press Ctrl+S
2. The script is now installed

### Step 4: Test

1. **Close the Apps Script editor** (go back to your sheet)
2. **Grade a pick** in column K (type W, L, or P)
3. **Check if:**
   - Column L shows calculated units
   - Column M shows "YES"
   - The pick appears in the league sheet (e.g., "NFL" tab)

## WHAT THIS SCRIPT DOES:

When you grade a pick (W/L/P in column K):

1. ✅ Calculates unit result based on odds
2. ✅ Writes to column L (UNIT_RESULT)
3. ✅ Marks column M as "YES" (PROCESSED)
4. ✅ Copies entire row to the league sheet
5. ✅ Creates league sheet if it doesn't exist

## IF IT DOESN'T WORK:

### Check 1: Sheet Name
The script looks for a sheet named **"PICKS TRACKER"**.

If your main sheet has a different name:
1. Open Apps Script editor
2. Find this line (around line 17):
   ```javascript
   if (sheet.getName() !== 'PICKS TRACKER') {
   ```
3. Change `'PICKS TRACKER'` to your actual sheet name
4. Save (Ctrl+S)

### Check 2: Permissions
First time you grade a pick after installing:
- Google will ask for permissions
- Click "Continue"
- Select your Google account
- Click "Allow"
- This only happens once

### Check 3: Column Numbers
The script expects this structure:
- Column C (3): Odds
- Column E (5): Units
- Column F (6): League
- Column K (11): Grade
- Column L (12): Unit Result
- Column M (13): Processed

If your columns are different, let me know and I'll adjust the script.

## TESTING WITHOUT GRADING:

Want to test without grading a real pick?

1. Open Apps Script editor
2. Select "onEditTest" from the dropdown (top)
3. Click Run (▶ play button)
4. Check the log output
5. Check league sheets for copied row

## AFTER IT WORKS:

Once the Apps Script is working:
- The website automation will pick up the graded picks automatically
- Every 15 minutes, betlegend-records.html will update
- You never touch the script again

## WHY THIS IS SEPARATE:

- **Apps Script** = Runs inside Google Sheet, copies rows to league sheets
- **Website Automation** = Runs on GitHub, generates HTML from CSV

Both are needed:
1. You grade pick → Apps Script processes
2. GitHub Action reads sheet → Generates website

The website automation is already deployed and working. This Apps Script is the missing piece that processes picks when you grade them.

## TROUBLESHOOTING:

**"Script runs but nothing copies"**
→ Check that column K has exactly W, L, or P (uppercase)
→ Check that you're editing the correct sheet

**"Column L doesn't fill"**
→ Check that column C has valid odds (e.g., -110, +150)
→ Check that column E has valid units (e.g., 1, 2, 5)

**"League sheet not created"**
→ Check that column F has league name (NFL, NBA, etc.)
→ Check for typos in league name

**"Nothing happens at all"**
→ Check Execution Log: Apps Script → View → Execution Log
→ Look for error messages

## SUMMARY:

1. Open Extensions → Apps Script
2. Delete old code
3. Paste code from `betlegend-sheet-script.gs`
4. Save
5. Close editor
6. Grade a pick to test

**That's it. The script will run automatically forever after that.**
