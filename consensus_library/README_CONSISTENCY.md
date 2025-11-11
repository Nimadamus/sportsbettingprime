# Sharp Consensus Page - Consistency Guidelines

## Daily Update Process

### 1. Run the Covers Scraper
```bash
cd C:\Users\Nima\Desktop\Scripts
python covers_contest_scraper.py
```

### 2. Create New Daily Page
- **Filename format**: `sharp-consensus-YYYY-MM-DD.html` (e.g., `sharp-consensus-2025-11-10.html`)
- **Location**: `consensus_library/`

### 3. Page Styling Requirements
**MUST USE THIS EXACT STYLING:**
```css
background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
```

**Key Design Elements:**
- Blue gradient background (NOT dark space theme)
- White content box with rounded corners
- Gold (#ffd700) accents for highlights
- Grid layout for picks: `grid-template-columns: 80px 100px 300px 180px auto`
- Green border for high-consensus picks (10+)
- Stats bar at top showing: Total Picks, Top Contestants, Sports Covered

### 4. Required Content

**Header:**
```
⭐ Sharp Consensus Board
Live Data from Top 50 Covers Contest Performers
Last Updated: [Month DD, YYYY HH:MM AM/PM ET]
```

**Sport Tabs:**
- ALL SPORTS
- NFL
- NBA
- NHL
- NCAAB (College Basketball)
- NCAAF (College Football)

**Pick Data Requirements:**
- Include at LEAST 40 picks total
- MUST include extensive college basketball coverage (minimum 15+ CBB picks)
- High-consensus picks (10+) get green border and gradient background
- Medium-consensus picks (5-9) get yellow border
- Regular picks (<5) get standard yellow border

### 5. Date Navigation
**MUST include pagination at bottom:**
```html
<div class="pagination">
    <a href="sharp-consensus-YYYY-MM-DD.html">← YYYY-MM-DD</a>
    <span class="current-date">[Current Date]</span>
    <span OR <a href="...">Newer →</a>
</div>
```

**Update previous day's page:**
- Nov 9 should link to → Nov 10
- Nov 10 should link to ← Nov 9

### 6. Homepage Update
**File**: `index.html`

**Update this line:**
```html
<li><a href="consensus_library/sharp-consensus-YYYY-MM-DD.html">Sharp Consensus</a></li>
```
Always point to the MOST RECENT date.

### 7. Never Delete
- NEVER delete old pages
- ALWAYS keep all historical data
- Previous pages remain accessible via pagination links

### 8. Git Commit Message Format
```
Add [Date] sharp consensus page with date navigation

- Created new sharp-consensus-YYYY-MM-DD.html with today's consensus data
- Added "Last Updated" timestamp
- Updated date navigation links between pages
- Updated homepage to link to latest page
- Included XX picks across all sports with extensive CBB coverage

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## File Structure Reference
```
sportsbettingprime/
├── index.html (update Sharp Consensus link)
└── consensus_library/
    ├── sharp-consensus-2025-11-08.html
    ├── sharp-consensus-2025-11-09.html
    ├── sharp-consensus-2025-11-10.html (current)
    └── [future dates...]
```

## Data Source
- CSV file: `covers_contest_picks_aggregated.csv`
- Sort by Count (descending)
- Include picks with count >= 2
- Prioritize high-consensus picks at top

## Quality Checklist
- [ ] Blue gradient background (NOT dark theme)
- [ ] Last Updated timestamp shows correct date/time
- [ ] At least 40 total picks
- [ ] 15+ college basketball picks included
- [ ] Date navigation links work both directions
- [ ] Homepage updated to latest date
- [ ] Previous day's page updated to link forward
- [ ] Sport filter tabs working
- [ ] High-consensus picks have green border
- [ ] All old pages preserved
