/**
 * SHEET AUTOMATION SCRIPT - FINAL VERSION
 *
 * COLUMN STRUCTURE:
 * A (1)  - Date
 * B (2)  - Pick
 * C (3)  - Odds
 * D (4)  - Result
 * E (5)  - Units
 * F (6)  - League (determines target sheet)
 * G (7)  - Sport
 * H (8)  - Ready
 * I (9)  - PostedAt
 * J (10) - Pushed
 * K (11) - GRADE (W/L/P dropdown - TRIGGER COLUMN)
 * L (12) - UNIT_F (calculated unit result)
 * M (13) - _PROCESS (processed marker)
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('BetLegend')
    .addItem('Setup GRADE Column', 'setupGradeColumn')
    .addToUi();
}

function setupGradeColumn() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  sheet.getRange('K1').setValue('GRADE');
  sheet.getRange('L1').setValue('UNIT_F');
  sheet.getRange('M1').setValue('_PROCESS');

  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    const rule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['W', 'L', 'P'], true)
      .build();
    sheet.getRange(2, 11, lastRow - 1, 1).setDataValidation(rule);
  }

  sheet.getRange('K1:M1').setFontWeight('bold').setBackground('#d9ead3');
  SpreadsheetApp.getUi().alert('Setup complete!');
}

function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const row = e.range.getRow();
  const col = e.range.getColumn();

  // Only trigger on Sheet1, column K (11), not header
  if (sheet.getName() !== 'Sheet1' || col !== 11 || row === 1) return;

  const grade = e.value;
  if (!grade || !['W', 'L', 'P'].includes(grade.toUpperCase())) return;

  // Check if already processed (column M = 13)
  if (sheet.getRange(row, 13).getValue() === 'PROCESSED') return;

  // Read league name from column F (6)
  const leagueName = String(sheet.getRange(row, 6).getValue()).trim();

  // Read odds from column C (3)
  const odds = parseFloat(sheet.getRange(row, 3).getValue());

  // Read units from column E (5)
  const units = parseFloat(sheet.getRange(row, 5).getValue());

  if (!leagueName || isNaN(odds) || isNaN(units)) return;

  // Calculate unit result - CORRECT BETTING MATH
  const g = grade.toUpperCase();
  let result = 0;

  if (g === 'W') {
    // WIN calculation
    if (odds >= 0) {
      // Positive odds: profit = units * (odds / 100)
      result = units * (odds / 100);
    } else {
      // Negative odds: profit = units * (100 / abs(odds))
      result = units * (100 / Math.abs(odds));
    }
  } else if (g === 'L') {
    // LOSS: always lose your stake, regardless of odds
    result = -units;
  } else if (g === 'P') {
    // PUSH: no gain/loss
    result = 0;
  }

  result = Math.round(result * 100) / 100;

  // Write unit result to column L (12)
  sheet.getRange(row, 12).setValue(result);

  // Find or create target sheet by league name
  const ss = e.source;
  let targetSheet = ss.getSheetByName(leagueName);

  if (!targetSheet) {
    // Create the sheet if it doesn't exist
    targetSheet = ss.insertSheet(leagueName);

    // Add headers to new sheet
    const headers = ['Date', 'Pick', 'Odds', 'Result', 'Units', 'League', 'Sport', 'Ready', 'PostedAt', 'Pushed', 'GRADE', 'UNIT_F', '_PROCESS'];
    targetSheet.getRange(1, 1, 1, 13).setValues([headers]);
    targetSheet.getRange(1, 1, 1, 13).setFontWeight('bold');
  }

  // Copy all 13 columns (A through M) to target sheet
  const rowData = sheet.getRange(row, 1, 1, 13).getValues()[0];
  const lastRow = targetSheet.getLastRow() + 1;
  targetSheet.getRange(lastRow, 1, 1, 13).setValues([rowData]);

  // Mark as processed in column M (13)
  sheet.getRange(row, 13).setValue('PROCESSED');

  // Highlight the graded row
  sheet.getRange(row, 11, 1, 3).setBackground('#d9ead3');
}
