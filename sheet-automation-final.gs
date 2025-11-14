/**
 * FINAL WORKING SHEET AUTOMATION SCRIPT
 *
 * COLUMN STRUCTURE (VERIFIED AND LOCKED):
 * A (1)  = Date
 * B (2)  = Pick
 * C (3)  = Odds
 * D (4)  = Result (unused)
 * E (5)  = Units
 * F (6)  = League (NFL, NBA, NHL, NCAAF, UEFA, etc.)
 * G (7)  = Sport
 * H (8)  = Ready
 * I (9)  = PostedAt
 * J (10) = Pushed
 * K (11) = GRADE (W/L/P) - TRIGGER COLUMN
 * L (12) = UNIT_RESULT - Script writes calculated result here
 * M (13) = PROCESSED - Script marks "YES" here
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('BetLegend')
    .addItem('Setup GRADE Column', 'setupGradeColumn')
    .addToUi();
}

function setupGradeColumn() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Sheet1 not found!');
    return;
  }

  sheet.getRange('K1').setValue('GRADE');
  sheet.getRange('L1').setValue('UNIT_RESULT');
  sheet.getRange('M1').setValue('PROCESSED');

  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    const rule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['W', 'L', 'P'], true)
      .build();
    sheet.getRange(2, 11, lastRow - 1, 1).setDataValidation(rule);
  }

  sheet.getRange('K1:M1').setFontWeight('bold').setBackground('#d9ead3');
  SpreadsheetApp.getUi().alert('Setup complete! Column K=GRADE, L=UNIT_RESULT, M=PROCESSED');
}

/**
 * AUTO-TRIGGER FUNCTION - Runs on every edit
 * Triggers when column K (GRADE) is edited
 */
function onEdit(e) {
  try {
    // Validate event object
    if (!e || !e.range) {
      Logger.log('No event object or range');
      return;
    }

    const sheet = e.range.getSheet();
    const row = e.range.getRow();
    const col = e.range.getColumn();

    // CRITICAL: Only process Sheet1, column K (11), skip header row 1
    if (sheet.getName() !== 'Sheet1') {
      Logger.log('Skipped: Not Sheet1 (sheet=' + sheet.getName() + ')');
      return;
    }

    if (col !== 11) {
      Logger.log('Skipped: Not column K (col=' + col + ')');
      return;
    }

    if (row === 1) {
      Logger.log('Skipped: Header row');
      return;
    }

    // Get and validate the GRADE value
    const grade = e.value;
    if (!grade) {
      Logger.log('Skipped: No grade value');
      return;
    }

    const gradeUpper = String(grade).toUpperCase().trim();
    if (!['W', 'L', 'P'].includes(gradeUpper)) {
      Logger.log('Skipped: Invalid grade (' + grade + ')');
      return;
    }

    Logger.log('Processing row ' + row + ' with grade: ' + gradeUpper);

    // Check if already processed (column M = 13)
    const processedValue = sheet.getRange(row, 13).getValue();
    if (processedValue === 'YES' || processedValue === 'PROCESSED') {
      Logger.log('Skipped: Already processed');
      return;
    }

    // Read required values from specific columns
    const leagueName = String(sheet.getRange(row, 6).getValue()).trim();  // Column F (6)
    const odds = parseFloat(sheet.getRange(row, 3).getValue());          // Column C (3)
    const units = parseFloat(sheet.getRange(row, 5).getValue());         // Column E (5)

    Logger.log('League: ' + leagueName + ', Odds: ' + odds + ', Units: ' + units);

    // Validate required data
    if (!leagueName || leagueName === '') {
      Logger.log('ERROR: No league name in column F');
      return;
    }

    if (isNaN(odds) || isNaN(units)) {
      Logger.log('ERROR: Invalid odds or units');
      return;
    }

    // Calculate unit result based on grade
    let unitResult = 0;

    if (gradeUpper === 'W') {
      // WIN: Calculate profit based on odds
      if (odds >= 0) {
        // Positive odds (e.g., +150): profit = units * (odds / 100)
        unitResult = units * (odds / 100);
      } else {
        // Negative odds (e.g., -110): profit = units * (100 / |odds|)
        unitResult = units * (100 / Math.abs(odds));
      }
    } else if (gradeUpper === 'L') {
      // LOSS: Always lose the units wagered
      unitResult = -units;
    } else if (gradeUpper === 'P') {
      // PUSH: No gain or loss
      unitResult = 0;
    }

    // Round to 2 decimal places
    unitResult = Math.round(unitResult * 100) / 100;

    Logger.log('Calculated unit result: ' + unitResult);

    // Write unit result to column L (12)
    sheet.getRange(row, 12).setValue(unitResult);
    SpreadsheetApp.flush(); // Force write

    // Get the spreadsheet
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // Find or create the target sheet based on league name
    let targetSheet = ss.getSheetByName(leagueName);

    if (!targetSheet) {
      Logger.log('Creating new sheet: ' + leagueName);
      targetSheet = ss.insertSheet(leagueName);

      // Add headers to the new sheet
      const headers = [
        'Date', 'Pick', 'Odds', 'Result', 'Units', 'League',
        'Sport', 'Ready', 'PostedAt', 'Pushed', 'GRADE',
        'UNIT_RESULT', 'PROCESSED'
      ];
      targetSheet.getRange(1, 1, 1, 13).setValues([headers]);
      targetSheet.getRange(1, 1, 1, 13).setFontWeight('bold').setBackground('#4285f4').setFontColor('#ffffff');
      SpreadsheetApp.flush(); // Force write
    }

    // Read the entire row data (all 13 columns A through M)
    const rowData = sheet.getRange(row, 1, 1, 13).getValues()[0];

    Logger.log('Row data to copy: ' + JSON.stringify(rowData));

    // Append to target sheet (find next available row)
    const targetLastRow = targetSheet.getLastRow();
    const targetRow = targetLastRow + 1;

    Logger.log('Copying to ' + leagueName + ' sheet, row ' + targetRow);

    // Write the row to target sheet
    targetSheet.getRange(targetRow, 1, 1, 13).setValues([rowData]);
    SpreadsheetApp.flush(); // Force write

    // Mark as processed in column M (13) of Sheet1
    sheet.getRange(row, 13).setValue('YES');
    SpreadsheetApp.flush(); // Force write

    // Highlight the processed row for visual confirmation
    sheet.getRange(row, 11, 1, 3).setBackground('#d9ead3');
    SpreadsheetApp.flush(); // Force write

    Logger.log('SUCCESS: Row ' + row + ' processed and copied to ' + leagueName);

  } catch (error) {
    Logger.log('ERROR in onEdit: ' + error.toString());
    Logger.log('Stack trace: ' + error.stack);

    // Show error to user
    SpreadsheetApp.getUi().alert('Error processing row: ' + error.toString());
  }
}

/**
 * Manual test function - Can be run from Script Editor
 */
function testScript() {
  Logger.log('Testing script manually...');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Sheet1');

  if (!sheet) {
    Logger.log('ERROR: Sheet1 not found');
    return;
  }

  Logger.log('Sheet1 found. Last row: ' + sheet.getLastRow());
  Logger.log('Test complete. Check Execution log for details.');
}
