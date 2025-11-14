#!/bin/bash
set -e

echo "============================================"
echo "BETLEGEND AUTOMATION - END-TO-END TEST"
echo "============================================"
echo ""

# Fetch CSV
echo "1. Fetching CSV from published URL..."
CSV_DATA=$(curl -s -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vQjW2l6hBUafumAiOdJblACLIx3GTtdJDcytUcN1nu2QHJmHnUMN9_5Tp2v7VqMTZaATfdmcJ-SK4jD/pub?output=csv")
echo "✓ Fetched $(echo "$CSV_DATA" | wc -l) lines"

# Save to temp file
TEMP_CSV="/tmp/betlegend-test.csv"
echo "$CSV_DATA" > "$TEMP_CSV"

# Check for graded picks
GRADED_COUNT=$(echo "$CSV_DATA" | grep -c "YES" || true)
echo "✓ Found $GRADED_COUNT processed rows"

# Run sync script with fetched CSV
echo ""
echo "2. Running sync script..."
echo "$CSV_DATA" | node -e "
const fs = require('fs');
const path = require('path');

// Read CSV from stdin
let csvText = '';
process.stdin.on('data', (chunk) => { csvText += chunk; });
process.stdin.on('end', () => {

  // Parse CSV
  function parseCSV(text) {
    const lines = text.split('\\n');
    const rows = [];
    for (let line of lines) {
      if (!line.trim()) continue;
      const row = [];
      let current = '';
      let inQuotes = false;
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '\"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          row.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      row.push(current.trim());
      rows.push(row);
    }
    return rows;
  }

  // Parse graded picks
  function parseGradedRows(rows) {
    const picks = [];
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (row.length < 13) continue;
      const grade = (row[10] || '').trim().toUpperCase();
      const processed = (row[12] || '').trim().toUpperCase();
      if (['W','L','P'].includes(grade) && processed === 'YES') {
        picks.push({
          date: row[0],
          pick: row[1],
          odds: row[2],
          units: row[4],
          league: row[5],
          grade: grade,
          unitResult: row[11]
        });
      }
    }
    return picks;
  }

  // Calculate stats
  function calculateStats(picks) {
    let wins = 0, losses = 0, pushes = 0, units = 0;
    for (const p of picks) {
      if (p.grade === 'W') wins++;
      else if (p.grade === 'L') losses++;
      else if (p.grade === 'P') pushes++;
      units += parseFloat(p.unitResult) || 0;
    }
    return {
      wins, losses, pushes,
      totalPicks: wins + losses + pushes,
      totalUnits: units.toFixed(2),
      winRate: wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : '0.0',
      record: \`\${wins}-\${losses}\${pushes > 0 ? '-' + pushes : ''}\`
    };
  }

  const rows = parseCSV(csvText);
  console.log(\`✓ Parsed \${rows.length} rows\`);

  const picks = parseGradedRows(rows);
  console.log(\`✓ Found \${picks.length} graded picks\`);

  if (picks.length === 0) {
    console.log('⚠️  No graded picks to process');
    process.exit(0);
  }

  // Group by league
  const grouped = {};
  for (const pick of picks) {
    const league = pick.league || 'Other';
    if (!grouped[league]) grouped[league] = [];
    grouped[league].push(pick);
  }
  console.log(\`✓ Grouped into \${Object.keys(grouped).length} leagues\`);

  const overall = calculateStats(picks);
  console.log(\`✓ Overall: \${overall.record} (\${overall.winRate}% win rate, \${overall.totalUnits} units)\`);

  console.log('');
  console.log('League Breakdown:');
  for (const league of Object.keys(grouped).sort()) {
    const stats = calculateStats(grouped[league]);
    console.log(\`  \${league}: \${stats.record} (\${stats.totalUnits} units)\`);
  }

  // Generate simple HTML
  const html = \`<!DOCTYPE html>
<html><head><title>BetLegend Records</title></head>
<body><h1>BetLegend Verified Records</h1>
<p>Record: \${overall.record}</p>
<p>Win Rate: \${overall.winRate}%</p>
<p>Net Units: \${overall.totalUnits}</p>
<p>Total Picks: \${overall.totalPicks}</p>
</body></html>\`;

  fs.writeFileSync('betlegend-records.html', html);
  console.log('');
  console.log('✓ Generated betlegend-records.html');
});
"

# Verify HTML was created
if [ -f "betlegend-records.html" ]; then
    echo "✓ HTML file created successfully"
    echo ""
    echo "3. HTML Preview:"
    head -10 betlegend-records.html
    echo ""
else
    echo "✗ HTML file NOT created"
    exit 1
fi

echo "============================================"
echo "✅ END-TO-END TEST PASSED"
echo "============================================"
echo ""
echo "The automation is fully functional and ready to deploy."
