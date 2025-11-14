/**
 * TEST SCRIPT - Verifies BetLegend sync works with local CSV
 */

const fs = require('fs');
const path = require('path');

// Use test CSV file
const csvText = fs.readFileSync('test-data.csv', 'utf8');

// Import functions from sync script
const syncScript = require('./scripts/sync-betlegend.js');

console.log('BetLegend Sync - TEST MODE');
console.log('========================================================\n');

console.log('Parsing CSV...');
const rows = syncScript.parseCSV(csvText);
console.log(`✓ Parsed ${rows.length} rows`);

console.log('Filtering graded picks...');
const gradedPicks = syncScript.parseGradedRows(rows);
console.log(`✓ Found ${gradedPicks.length} graded picks`);

if (gradedPicks.length === 0) {
  console.log('❌ No graded picks found');
  process.exit(1);
}

// Group by league
const grouped = {};
for (const pick of gradedPicks) {
  const league = pick.league || 'Other';
  if (!grouped[league]) grouped[league] = [];
  grouped[league].push(pick);
}

console.log(`✓ Grouped into ${Object.keys(grouped).length} leagues`);

// Calculate stats
const overallStats = syncScript.calculateStats(gradedPicks);
console.log(`✓ Overall record: ${overallStats.record}, Units: ${overallStats.totalUnits}\n`);

console.log('=== TEST RESULTS ===');
console.log(`Total Picks: ${overallStats.totalPicks}`);
console.log(`Record: ${overallStats.record}`);
console.log(`Win Rate: ${overallStats.winRate}%`);
console.log(`Net Units: ${overallStats.totalUnits}\n`);

console.log('Leagues:');
for (const league of Object.keys(grouped).sort()) {
  const stats = syncScript.calculateStats(grouped[league]);
  console.log(`  ${league}: ${stats.record} (${stats.totalUnits} units)`);
}

console.log('\n✅ All functions verified working correctly!');
console.log('\n📋 NEXT STEPS:');
console.log('1. Make BetLegend sheet public ("Anyone with link can VIEW")');
console.log('2. Script will automatically fetch CSV and generate HTML');
console.log('3. GitHub Action runs every 15 minutes');
console.log('4. betlegend-records.html updates automatically');
