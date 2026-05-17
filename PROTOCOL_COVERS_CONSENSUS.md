# SportsBettingPrime Covers Consensus - Daily Update Protocol

## Repository Location
```
C:\Users\Nima\Documents\GitHub\sportsbettingprime
```
**GitHub:** https://github.com/Nimadamus/sportsbettingprime.git

## File Naming Convention
- **Main page:** `covers-consensus.html`
- **Archives:** `covers-consensus-YYYY-MM-DD.html` (e.g., `covers-consensus-2025-11-25.html`)

**IMPORTANT:** Do NOT use `sportsbettingprime-covers-consensus-*.html` naming - those files are in a different repo (nimadamus.github.io/betlegendpicks).

## Daily Update Process

### Publishing Completion Gate: No Orphan Pages
A published page is not complete unless it is linked from the correct live site structure.

Every future page, article, pick page, preview page, or blog post must be connected in the same task to the correct location, such as:
- homepage/latest card
- blog/news/picks archive
- sport-specific index
- calendar/date archive
- hub page
- sitemap if that site requires manual sitemap updates
- pagination/card rotation system if applicable

Before any future publishing task is marked complete, run an orphan-page check. If a newly created HTML page has no valid inbound internal link from a homepage, archive, index, calendar, hub, or sitemap structure, the task fails and cannot be called complete.

Never create or publish standalone orphan pages. Page creation and internal linking are one task, not separate tasks.

## Canonical and Sitemap Guardrail

SportsBettingPrime uses `https://sportsbettingprime.com/` as the canonical host. Do not publish `https://www.sportsbettingprime.com/` canonicals, Open Graph URLs, or sitemap URLs unless DNS and redirects are explicitly changed first.

Before any sitemap update is committed, run:

```bash
python generate_sitemap.py
python scripts/verify_sitemap_indexability.py
```

The guard must pass with zero failures. It rejects sitemap URLs that are missing locally, blocked by robots.txt, noindexed, redirect stubs, or non-self-canonical. For post-deploy verification, run the same guard with `--live` to check HTTP 200 status, redirects, X-Robots-Tag, and deployed canonicals.

### Step 1: Run the Covers Scraper
```bash
python "C:\Users\Nima\Desktop\Scripts\covers_contest_scraper.py"
```
Or use the desktop shortcut: `COVERS SCRAPER.lnk`

**Output files:**
- `C:\Users\Nima\Desktop\Scripts\covers_contest_picks_summary.txt`
- `C:\Users\Nima\Desktop\Scripts\covers_contest_picks_aggregated.csv`
- `C:\Users\Nima\Desktop\Scripts\covers_contest_picks.csv`

### Step 2: Archive the Current Page
Copy the current `covers-consensus.html` to an archive file with yesterday's date:
```bash
copy covers-consensus.html covers-consensus-YYYY-MM-DD.html
```

### Step 3: Update the Main Page
Update `covers-consensus.html` with:
1. **New date** in the header (e.g., "Wednesday, November 26, 2025")
2. **New game data** from the scraper output
3. **Updated pagination links** pointing to the two most recent archives
4. **Updated archive count**

### Step 4: Update Archive Pagination
Update the newly created archive page to include:
- Link to latest version (`covers-consensus.html`)
- Links to adjacent archive dates
- Updated archive count

### Step 5: Commit and Push
```bash
cd "C:\Users\Nima\Documents\GitHub\sportsbettingprime"
git add covers-consensus*.html
git commit -m "Update Covers Consensus for [DATE]"
git push origin main
```

## Pagination Link Format
```html
<div style="margin-top: 20px; margin-bottom: 20px;">
    <a href="covers-consensus.html" style="color: var(--accent-color); ...">View Latest Version</a>
    <a href="covers-consensus-YYYY-MM-DD.html" style="color: var(--accent-gold); ...">View Version from [DATE]</a>
    <a href="covers-consensus-YYYY-MM-DD.html" style="color: var(--accent-gold); ...">View Version from [DATE]</a>
    <a href="sportsbettingprime.html" style="color: var(--text-muted); ...">View All Archives (X total)</a>
</div>
```

## Stats to Update
Located in the Stats Bar section:
- Total Picks Tracked
- Top Picks Shown
- Sports Covered
- Highest Consensus

## Common Mistakes to Avoid
1. Using wrong file naming (`sportsbettingprime-covers-consensus-*` vs `covers-consensus-*`)
2. Updating wrong repository (betlegendpicks vs sportsbettingprime)
3. Only changing date without updating actual game data
4. Broken pagination links pointing to non-existent files

## Existing Archive Files
- covers-consensus-2025-11-20.html
- covers-consensus-2025-11-22.html
- covers-consensus-2025-11-24.html
- covers-consensus-2025-11-25.html
