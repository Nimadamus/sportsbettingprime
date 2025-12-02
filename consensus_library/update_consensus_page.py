"""
Automated Sharp Consensus Page Update Script
Runs the scraper, processes data, creates new dated page, and commits to GitHub
"""

import os
import sys
import subprocess
import csv
import json
import re
from datetime import datetime

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_PATH = r"C:\Users\Nima\Desktop\Scripts\covers_contest_scraper.py"
REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Error: {result.stderr}")
    return result

def run_scraper():
    """Run the covers consensus scraper"""
    print("=" * 60)
    print("STEP 1: Running Covers Consensus Scraper")
    print("=" * 60)

    cmd = f'python "{SCRAPER_PATH}"'
    result = run_command(cmd, cwd=SCRIPT_DIR)

    if result.returncode == 0:
        print("[OK] Scraper completed successfully!")
    else:
        print("[ERROR] Scraper failed!")
        sys.exit(1)

def load_consensus_data():
    """Load and process consensus data from CSV"""
    print("\n" + "=" * 60)
    print("STEP 2: Processing Consensus Data")
    print("=" * 60)

    csv_path = os.path.join(SCRIPT_DIR, 'covers_contest_picks_aggregated.csv')

    data = []
    sports = set()
    max_consensus = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= 100:
                break

            pick = {
                'count': int(row['Count']),
                'sport': row['Sport'],
                'matchup': row['Matchup'],
                'pickType': row['Pick Type'],
                'pick': row['Pick']
            }
            data.append(pick)
            sports.add(row['Sport'])
            max_consensus = max(max_consensus, int(row['Count']))
            count += 1

    print(f"[OK] Loaded {len(data)} picks")
    print(f"[OK] Sports: {', '.join(sorted(sports))}")
    print(f"[OK] Highest consensus: {max_consensus} experts")

    return data, len(sports), max_consensus

def create_dated_page(consensus_data, sport_count, max_consensus):
    """Create a new dated consensus page"""
    print("\n" + "=" * 60)
    print("STEP 3: Creating New Dated Page")
    print("=" * 60)

    # Get today's date
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_display = today.strftime("%B %d, %Y")
    date_short = today.strftime("%B %d")
    time_str = today.strftime("%I:%M %p EST")

    # Get yesterday's date for archive link
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    yesterday_display = yesterday.strftime("%B %d")

    day_before = today - timedelta(days=2)
    day_before_str = day_before.strftime("%Y-%m-%d")
    day_before_display = day_before.strftime("%B %d")

    new_filename = f"sharp-consensus-{date_str}.html"
    new_filepath = os.path.join(SCRIPT_DIR, new_filename)

    # Read template
    template_path = os.path.join(SCRIPT_DIR, "sharp-consensus-2025-11-14.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Convert consensus data to JavaScript
    js_data = json.dumps(consensus_data, indent=8)

    # Update metadata
    html_content = html_content.replace(
        'November 14, 2025',
        date_display
    )
    html_content = html_content.replace(
        '2025-11-14',
        date_str
    )
    html_content = html_content.replace(
        'November 14, 2025 - 11:00 AM EST',
        f'{date_display} - {time_str}'
    )

    # Update stats
    html_content = re.sub(
        r'<div class="stat-number" id="topConsensus">\d+</div>',
        f'<div class="stat-number" id="topConsensus">{max_consensus}</div>',
        html_content
    )
    html_content = re.sub(
        r'<div class="stat-number" id="sportCount">\d+</div>',
        f'<div class="stat-number" id="sportCount">{sport_count}</div>',
        html_content
    )

    # Update sport tabs to include all sports
    sport_tabs = '''        <div class="sport-tabs">
            <div class="sport-tab active" data-sport="all">ALL SPORTS</div>
            <div class="sport-tab" data-sport="CFL">CFL</div>
            <div class="sport-tab" data-sport="College Basketball">NCAAB</div>
            <div class="sport-tab" data-sport="College Football">NCAAF</div>
            <div class="sport-tab" data-sport="NBA">NBA</div>
            <div class="sport-tab" data-sport="NFL">NFL</div>
            <div class="sport-tab" data-sport="NHL">NHL</div>
        </div>'''

    html_content = re.sub(
        r'<div class="sport-tabs">.*?</div>\s*</div>',
        sport_tabs + '\n',
        html_content,
        flags=re.DOTALL
    )

    # Update archive links
    html_content = re.sub(
        r'<a href="sharp-consensus-2025-11-13\.html">← November 13</a>',
        f'<a href="sharp-consensus-{yesterday_str}.html">← {yesterday_display}</a>',
        html_content
    )
    html_content = re.sub(
        r'<a href="sharp-consensus-2025-11-12\.html">November 12</a>',
        f'<a href="sharp-consensus-{day_before_str}.html">{day_before_display}</a>',
        html_content
    )

    # Replace consensus data (fix the regex to avoid double brackets)
    pattern = r'const consensusData = \[[^\]]*\];'
    replacement = f'const consensusData = {js_data};'
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)

    # Write new file
    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] Created {new_filename}")

    # Also update main sharp-consensus.html
    main_filepath = os.path.join(SCRIPT_DIR, "sharp-consensus.html")
    with open(main_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] Updated sharp-consensus.html")

    return new_filename, date_str, date_display

def update_index_html(date_str):
    """Update index.html to point to new consensus page"""
    print("\n" + "=" * 60)
    print("STEP 4: Updating index.html")
    print("=" * 60)

    index_path = os.path.join(REPO_PATH, "index.html")

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update the Sharp Consensus link
    content = re.sub(
        r'href="consensus_library/sharp-consensus-\d{4}-\d{2}-\d{2}\.html\?v=\d{8}"',
        f'href="consensus_library/sharp-consensus-{date_str}.html?v={date_str.replace("-", "")}"',
        content
    )

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] Updated index.html to point to {date_str}")

def commit_and_push(date_display, max_consensus, sport_count):
    """Commit and push changes to GitHub"""
    print("\n" + "=" * 60)
    print("STEP 5: Committing and Pushing to GitHub")
    print("=" * 60)

    # Stage all changes
    run_command("git add .", cwd=REPO_PATH)

    # Create commit message
    commit_msg = f"""Update Sharp Consensus to {date_display}

- Added {date_display} consensus page with 100 top picks
- Updated navigation links across all pages
- Updated index.html to point to {date_display} page
- Highest consensus: {max_consensus} experts
- {sport_count} sports covered

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    # Commit
    result = run_command(f'git commit -m "{commit_msg}"', cwd=REPO_PATH)

    if "nothing to commit" in result.stdout:
        print("[OK] No changes to commit")
    else:
        print("[OK] Changes committed")

        # Push
        result = run_command("git push", cwd=REPO_PATH)

        if result.returncode == 0:
            print("[OK] Changes pushed to GitHub!")
        else:
            print("[ERROR] Failed to push to GitHub")
            print(result.stderr)

def main():
    """Main execution flow"""
    print("\n" + "=" * 60)
    print("SHARP CONSENSUS PAGE AUTO-UPDATE")
    print("=" * 60)

    try:
        # Step 1: Run scraper
        run_scraper()

        # Step 2: Load and process data
        consensus_data, sport_count, max_consensus = load_consensus_data()

        # Step 3: Create new dated page
        new_filename, date_str, date_display = create_dated_page(consensus_data, sport_count, max_consensus)

        # Step 4: Update index.html
        update_index_html(date_str)

        # Step 5: Commit and push
        commit_and_push(date_display, max_consensus, sport_count)

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL STEPS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nNew page: {new_filename}")
        print(f"URL: https://www.sportsbettingprime.com/consensus_library/{new_filename}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
