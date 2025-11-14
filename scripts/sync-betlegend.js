/**
 * BetLegend Verified Records Sync Script
 * Reads graded picks from Google Sheets CSV export and updates the website
 *
 * NO API KEY REQUIRED - Uses public CSV export endpoint
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// Configuration
const SHEET_ID = process.env.SHEET_ID || '1izhhxwiazn9S8RqcK8QUpE4pWDRIFnPq5yw5ZISMsmv';
const GID = process.env.GID || '0'; // Sheet1 = 0
const CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=${GID}`;

// Output HTML file
const OUTPUT_FILE = path.join(__dirname, '..', 'betlegend-records.html');

/**
 * Fetch CSV from Google Sheets public export
 * NO AUTHENTICATION REQUIRED if sheet is set to "Anyone with link can view"
 */
async function fetchCSV() {
  return new Promise((resolve, reject) => {
    console.log(`Fetching CSV from: ${CSV_URL}`);

    https.get(CSV_URL, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        // Follow redirect
        https.get(res.headers.location, (redirectRes) => {
          let data = '';
          redirectRes.on('data', (chunk) => { data += chunk; });
          redirectRes.on('end', () => resolve(data));
          redirectRes.on('error', reject);
        }).on('error', reject);
      } else if (res.statusCode === 200) {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => resolve(data));
      } else {
        reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
      }
    }).on('error', reject);
  });
}

/**
 * Parse CSV into rows
 */
function parseCSV(csvText) {
  const lines = csvText.split('\n');
  const rows = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Simple CSV parsing (handles quoted fields)
    const row = [];
    let current = '';
    let inQuotes = false;

    for (let j = 0; j < line.length; j++) {
      const char = line[j];

      if (char === '"') {
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

/**
 * Parse and filter graded rows
 */
function parseGradedRows(rows) {
  const gradedPicks = [];

  // Skip header row (index 0)
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];

    // Column indices (0-based):
    // A=0(Date), B=1(Pick), C=2(Odds), D=3(Result), E=4(Units), F=5(League),
    // G=6(Sport), H=7(Ready), I=8(PostedAt), J=9(Pushed), K=10(GRADE),
    // L=11(UNIT_RESULT), M=12(PROCESSED)

    if (row.length < 13) continue; // Skip incomplete rows

    const grade = row[10] ? String(row[10]).trim().toUpperCase() : '';
    const processed = row[12] ? String(row[12]).trim().toUpperCase() : '';

    // Only include rows that have been graded (W/L/P) and processed (YES)
    if (['W', 'L', 'P'].includes(grade) && processed === 'YES') {
      gradedPicks.push({
        date: row[0] || '',
        pick: row[1] || '',
        odds: row[2] || '',
        result: row[3] || '',
        units: row[4] || '',
        league: row[5] || '',
        sport: row[6] || '',
        ready: row[7] || '',
        postedAt: row[8] || '',
        pushed: row[9] || '',
        grade: grade,
        unitResult: row[11] || '',
        processed: processed
      });
    }
  }

  return gradedPicks;
}

/**
 * Group picks by league
 */
function groupByLeague(picks) {
  const grouped = {};

  for (const pick of picks) {
    const league = pick.league || 'Other';
    if (!grouped[league]) {
      grouped[league] = [];
    }
    grouped[league].push(pick);
  }

  return grouped;
}

/**
 * Calculate stats for a set of picks
 */
function calculateStats(picks) {
  let wins = 0;
  let losses = 0;
  let pushes = 0;
  let totalUnits = 0;

  for (const pick of picks) {
    if (pick.grade === 'W') wins++;
    else if (pick.grade === 'L') losses++;
    else if (pick.grade === 'P') pushes++;

    const units = parseFloat(pick.unitResult);
    if (!isNaN(units)) {
      totalUnits += units;
    }
  }

  const totalPicks = wins + losses + pushes;
  const winRate = totalPicks > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : '0.0';

  return {
    wins,
    losses,
    pushes,
    totalPicks,
    totalUnits: totalUnits.toFixed(2),
    winRate,
    record: `${wins}-${losses}${pushes > 0 ? `-${pushes}` : ''}`
  };
}

/**
 * Generate HTML table rows
 */
function generateTableRows(picks) {
  return picks.map(pick => {
    const gradeClass = pick.grade === 'W' ? 'win' : pick.grade === 'L' ? 'loss' : 'push';
    const gradeText = pick.grade === 'W' ? 'WIN' : pick.grade === 'L' ? 'LOSS' : 'PUSH';
    const unitSign = parseFloat(pick.unitResult) > 0 ? '+' : '';

    return `
                    <tr class="${gradeClass}">
                        <td>${pick.date}</td>
                        <td>${pick.league}</td>
                        <td>${pick.pick}</td>
                        <td>${pick.odds}</td>
                        <td>${pick.units}</td>
                        <td class="grade-${gradeClass}">${gradeText}</td>
                        <td class="unit-result">${unitSign}${pick.unitResult}</td>
                    </tr>`;
  }).join('');
}

/**
 * Generate complete HTML page
 */
function generateHTML(groupedPicks, overallStats) {
  const leagueNames = Object.keys(groupedPicks).sort();

  const leagueTables = leagueNames.map(league => {
    const picks = groupedPicks[league];
    const stats = calculateStats(picks);

    return `
        <section class="league-section">
            <h2>${league} - ${stats.record} (${stats.winRate}% Win Rate)</h2>
            <div class="stats-summary">
                <span class="stat">Total Picks: ${stats.totalPicks}</span>
                <span class="stat">Wins: ${stats.wins}</span>
                <span class="stat">Losses: ${stats.losses}</span>
                ${stats.pushes > 0 ? `<span class="stat">Pushes: ${stats.pushes}</span>` : ''}
                <span class="stat units-total">Net Units: ${parseFloat(stats.totalUnits) > 0 ? '+' : ''}${stats.totalUnits}</span>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>League</th>
                            <th>Pick</th>
                            <th>Odds</th>
                            <th>Units</th>
                            <th>Result</th>
                            <th>Net Units</th>
                        </tr>
                    </thead>
                    <tbody>
${generateTableRows(picks)}
                    </tbody>
                </table>
            </div>
        </section>
`;
  }).join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BetLegend - Verified Records</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #01000f;
            --text-color: #eaf8ff;
            --neon-cyan: #00ffff;
            --neon-gold: #FFD700;
            --win-green: #00ff00;
            --loss-red: #ff0040;
            --push-gray: #888;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            padding: 20px;
            min-height: 100vh;
        }
        header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, rgba(0,255,255,0.1), rgba(255,215,0,0.1));
            border-radius: 15px;
            margin-bottom: 40px;
        }
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 3rem;
            color: var(--neon-gold);
            text-shadow: 0 0 20px var(--neon-gold);
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2rem;
            color: var(--neon-cyan);
        }
        .overall-stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(0,255,255,0.05);
            border-radius: 10px;
        }
        .overall-stat {
            text-align: center;
            padding: 15px 25px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        .overall-stat-label {
            font-size: 0.9rem;
            color: rgba(234,248,255,0.7);
            margin-bottom: 5px;
        }
        .overall-stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--neon-gold);
        }
        .league-section {
            margin-bottom: 50px;
            background: rgba(255,255,255,0.02);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid rgba(0,255,255,0.2);
        }
        .league-section h2 {
            font-family: 'Orbitron', sans-serif;
            color: var(--neon-cyan);
            margin-bottom: 20px;
            font-size: 1.8rem;
        }
        .stats-summary {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 25px;
            padding: 15px;
            background: rgba(0,255,255,0.05);
            border-radius: 8px;
        }
        .stat {
            font-size: 1rem;
            padding: 8px 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }
        .units-total {
            color: var(--neon-gold);
            font-weight: bold;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(0,0,0,0.3);
        }
        thead {
            background: rgba(0,255,255,0.1);
        }
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: var(--neon-cyan);
            border-bottom: 2px solid var(--neon-cyan);
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        tr.win {
            background: rgba(0,255,0,0.05);
        }
        tr.loss {
            background: rgba(255,0,64,0.05);
        }
        tr.push {
            background: rgba(136,136,136,0.05);
        }
        .grade-win {
            color: var(--win-green);
            font-weight: bold;
        }
        .grade-loss {
            color: var(--loss-red);
            font-weight: bold;
        }
        .grade-push {
            color: var(--push-gray);
            font-weight: bold;
        }
        .unit-result {
            font-weight: bold;
            font-size: 1.1rem;
        }
        footer {
            text-align: center;
            padding: 30px;
            color: rgba(234,248,255,0.5);
            font-size: 0.9rem;
        }
        .last-updated {
            text-align: center;
            color: rgba(234,248,255,0.6);
            font-size: 0.9rem;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <header>
        <h1>BETLEGEND</h1>
        <p class="subtitle">Verified Records - All Graded Picks</p>
    </header>

    <div class="last-updated">
        Last Updated: ${new Date().toLocaleString('en-US', {
            timeZone: 'America/New_York',
            dateStyle: 'full',
            timeStyle: 'long'
        })}
    </div>

    <div class="overall-stats">
        <div class="overall-stat">
            <div class="overall-stat-label">Record</div>
            <div class="overall-stat-value">${overallStats.record}</div>
        </div>
        <div class="overall-stat">
            <div class="overall-stat-label">Win Rate</div>
            <div class="overall-stat-value">${overallStats.winRate}%</div>
        </div>
        <div class="overall-stat">
            <div class="overall-stat-label">Total Picks</div>
            <div class="overall-stat-value">${overallStats.totalPicks}</div>
        </div>
        <div class="overall-stat">
            <div class="overall-stat-label">Net Units</div>
            <div class="overall-stat-value">${parseFloat(overallStats.totalUnits) > 0 ? '+' : ''}${overallStats.totalUnits}</div>
        </div>
    </div>

${leagueTables}

    <footer>
        <p>BetLegend Verified Records - Automatically synced from Google Sheets</p>
        <p>All picks are graded and verified</p>
    </footer>
</body>
</html>`;
}

/**
 * Main execution
 */
async function main() {
  try {
    console.log('BetLegend Sync - Using CSV Export (No API Key Required)');
    console.log('========================================================\n');

    console.log('Fetching CSV from Google Sheets...');
    const csvText = await fetchCSV();
    console.log(`✓ Fetched ${csvText.length} characters`);

    console.log('Parsing CSV...');
    const rows = parseCSV(csvText);
    console.log(`✓ Parsed ${rows.length} rows`);

    console.log('Filtering graded picks...');
    const gradedPicks = parseGradedRows(rows);
    console.log(`✓ Found ${gradedPicks.length} graded picks`);

    if (gradedPicks.length === 0) {
      console.log('\n⚠️  No graded picks found. Make sure:');
      console.log('   - Column K (GRADE) contains W, L, or P');
      console.log('   - Column M (PROCESSED) contains YES');
      console.log('   - Sheet is set to "Anyone with link can view"');
      return;
    }

    console.log('Grouping by league...');
    const groupedPicks = groupByLeague(gradedPicks);
    console.log(`✓ Grouped into ${Object.keys(groupedPicks).length} leagues`);

    console.log('Calculating overall stats...');
    const overallStats = calculateStats(gradedPicks);
    console.log(`✓ Overall record: ${overallStats.record}, Units: ${overallStats.totalUnits}`);

    console.log('Generating HTML...');
    const html = generateHTML(groupedPicks, overallStats);

    console.log(`Writing to ${OUTPUT_FILE}...`);
    fs.writeFileSync(OUTPUT_FILE, html, 'utf8');
    console.log('✓ HTML file updated successfully\n');

    console.log('=== SUMMARY ===');
    console.log(`Total Picks: ${overallStats.totalPicks}`);
    console.log(`Record: ${overallStats.record}`);
    console.log(`Win Rate: ${overallStats.winRate}%`);
    console.log(`Net Units: ${overallStats.totalUnits}\n`);

    console.log('Leagues:');
    for (const league of Object.keys(groupedPicks).sort()) {
      const stats = calculateStats(groupedPicks[league]);
      console.log(`  ${league}: ${stats.record} (${stats.totalUnits} units)`);
    }

    console.log('\n✅ Sync complete!');

  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    if (error.message.includes('403') || error.message.includes('401')) {
      console.error('\nSheet is not public. To fix:');
      console.error('1. Open the Google Sheet');
      console.error('2. Click Share → Change to "Anyone with link can VIEW"');
      console.error('3. Re-run this script');
    }
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { fetchCSV, parseCSV, parseGradedRows, calculateStats };
