/**
 * BetLegend Picks Tracker - Auto-copy graded picks to league sheets
 *
 * This script runs automatically when you grade a pick (column K).
 * It calculates the unit result, marks as processed, and copies to the league sheet.
 *
 * INSTALLATION:
 * 1. Open your BetLegend Google Sheet
 * 2. Extensions → Apps Script
 * 3. Delete any existing code
 * 4. Paste this entire file
 * 5. Save (Ctrl+S)
 * 6. Close and return to sheet
 * 7. Grade a pick to test
 */

function onEdit(e) {
  try {
    // Get the spreadsheet from event object (more reliable than getActiveSpreadsheet)
    const ss = e.source;
    const sheet = e.range.getSheet();

    // Only process "PICKS TRACKER" sheet (adjust name if different)
    if (sheet.getName() !== 'PICKS TRACKER') {
      return;
    }

    const row = e.range.getRow();
    const col = e.range.getColumn();

    // Column K = 11 (GRADE column)
    if (col !== 11 || row < 2) {
      return;
    }

    const grade = e.value ? String(e.value).trim().toUpperCase() : '';

    // Only process W, L, or P grades
    if (!['W', 'L', 'P'].includes(grade)) {
      return;
    }

    // Get the odds and units from same row
    const odds = sheet.getRange(row, 3).getValue(); // Column C
    const units = sheet.getRange(row, 5).getValue(); // Column E
    const league = sheet.getRange(row, 6).getValue(); // Column F

    // Calculate unit result
    let unitResult = 0;

    if (grade === 'W') {
      // Win: calculate profit based on American odds
      const oddsNum = parseFloat(odds);
      if (oddsNum > 0) {
        // Positive odds: profit = units * (odds/100)
        unitResult = units * (oddsNum / 100);
      } else {
        // Negative odds: profit = units / (abs(odds)/100)
        unitResult = units / (Math.abs(oddsNum) / 100);
      }
    } else if (grade === 'L') {
      // Loss: lose the units wagered
      unitResult = -units;
    } else if (grade === 'P') {
      // Push: no win or loss
      unitResult = 0;
    }

    // Round to 2 decimal places
    unitResult = Math.round(unitResult * 100) / 100;

    // Write unit result to column L (12)
    sheet.getRange(row, 12).setValue(unitResult);

    // Mark as processed in column M (13) BEFORE reading row data
    sheet.getRange(row, 13).setValue('YES');

    // Force immediate write to sheet
    SpreadsheetApp.flush();

    // NOW read the entire row data (includes updated L and M values)
    const rowData = sheet.getRange(row, 1, 1, 13).getValues()[0];

    // Get or create the league sheet
    let leagueSheet = ss.getSheetByName(league);

    if (!leagueSheet) {
      // Create the league sheet if it doesn't exist
      leagueSheet = ss.insertSheet(league);

      // Add header row
      const headers = [
        'Date', 'Pick', 'Odds', 'Book', 'Units', 'League',
        'Player Prop', 'Reasoning', 'Record', 'Notes',
        'Grade', 'Unit Result', 'Processed'
      ];
      leagueSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      leagueSheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    }

    // Append the graded pick to the league sheet
    leagueSheet.appendRow(rowData);

    Logger.log(`Successfully copied ${grade} pick to ${league} sheet (${unitResult} units)`);

  } catch (error) {
    Logger.log('Error in onEdit: ' + error.toString());
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
  }
}

/**
 * Test function - run this manually to verify the script works
 *
 * HOW TO TEST:
 * 1. Click the "onEditTest" function in the dropdown
 * 2. Click Run (play button)
 * 3. Grant permissions when prompted
 * 4. Check Execution Log for results
 */
function onEditTest() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('PICKS TRACKER');

  if (!sheet) {
    Logger.log('ERROR: No sheet named "PICKS TRACKER" found');
    Logger.log('Available sheets: ' + ss.getSheets().map(s => s.getName()).join(', '));
    return;
  }

  // Find first row with a grade but no processed status
  const lastRow = sheet.getLastRow();

  for (let i = 2; i <= lastRow; i++) {
    const grade = sheet.getRange(i, 11).getValue(); // Column K
    const processed = sheet.getRange(i, 13).getValue(); // Column M

    if (['W', 'L', 'P'].includes(String(grade).toUpperCase()) && !processed) {
      Logger.log(`Found unprocessed graded pick at row ${i}`);

      // Simulate edit event
      const mockEvent = {
        source: ss,
        range: sheet.getRange(i, 11),
        value: grade
      };

      onEdit(mockEvent);
      Logger.log('Test complete - check league sheets for copied row');
      return;
    }
  }

  Logger.log('No unprocessed graded picks found. Add a W/L/P to column K and run again.');
}
