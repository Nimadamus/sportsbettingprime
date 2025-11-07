# Covers Contest Scraper - PowerShell Version
# Get top 20 contestants with pending picks

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "COVERS - TOP CONTESTANTS WITH PICKS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Finding top contestants who have pending picks..."
Write-Host "Then creating consensus from their picks"
Write-Host ""

# Run Python script
python -c @"
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from collections import defaultdict
import time
import re

def get_leaderboard_with_picks(max_to_check=50, target_count=20):
    """Get leaderboard and find contestants with pending picks."""

    print(f'📊 Checking leaderboard for contestants with pending picks...')
    print(f'   (Will check up to {max_to_check} to find {target_count} with picks)\n')

    # Get leaderboard
    url = 'https://contests.covers.com/survivor/currentleaderboard'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        contestants_with_picks = []
        checked = 0

        table = soup.find('table')
        if not table:
            print('❌ Could not find leaderboard table')
            return []

        rows = table.find_all('tr')[1:]  # Skip header

        for row in rows[:max_to_check]:
            if len(contestants_with_picks) >= target_count:
                break

            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            # Get contestant info
            username = ''
            profile_url = ''

            for link in row.find_all('a'):
                href = link.get('href', '')
                if '/contestant/' in href.lower():
                    username = link.text.strip()
                    profile_url = href
                    if not profile_url.startswith('http'):
                        profile_url = f'https://contests.covers.com{profile_url}'
                    break

            if not username:
                continue

            streak = cells[2].text.strip() if len(cells) > 2 else '0'
            checked += 1

            # Check if this contestant has pending picks
            print(f'  Checking #{checked}: {username:25s} (Streak: {streak})...', end='')

            picks = check_for_pending_picks(profile_url, username)

            if picks:
                print(f' ✓ Found {len(picks)} pick(s)')
                contestants_with_picks.append({
                    'rank': len(contestants_with_picks) + 1,
                    'username': username,
                    'streak': streak,
                    'profile_url': profile_url,
                    'picks': picks
                })
            else:
                print(f' ⚠️  No pending picks')

            time.sleep(0.5)  # Be respectful

        print(f'\n✓ Found {len(contestants_with_picks)} contestants with pending picks')
        return contestants_with_picks

    except Exception as e:
        print(f'❌ Error: {e}')
        return []

def check_for_pending_picks(profile_url, username):
    """Check contestant profile for pending picks."""

    if not profile_url:
        return []

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(profile_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        html = response.text
        picks = []

        # Look for Next Pick Deadline
        deadline_text = soup.find(string=re.compile('Next Pick Deadline', re.I))
        if deadline_text:
            parent = deadline_text.find_parent()
            if parent and '-' not in parent.get_text():
                # They have a pending pick
                picks.append({
                    'team': 'Pending pick (details not visible)',
                    'type': 'pending'
                })

        # Also check for 'pending' in HTML
        if not picks and 'pending' in html.lower():
            picks.append({
                'team': 'Pending pick (details not visible)',
                'type': 'pending'
            })

        return picks

    except Exception as e:
        return []

def create_consensus(contestants_with_picks):
    """Create consensus from contestants' picks."""

    print('\n' + '='*60)
    print('📊 CREATING CONSENSUS FROM ACTIVE PICKERS')
    print('='*60)

    # Extract all picks
    all_picks = []
    for contestant in contestants_with_picks:
        for pick in contestant['picks']:
            all_picks.append({
                'team': pick['team'],
                'contestant': contestant['username'],
                'streak': contestant['streak'],
                'rank': contestant['rank']
            })

    # Count occurrences
    pick_counts = defaultdict(int)
    pick_details = defaultdict(list)

    for pick in all_picks:
        team = pick['team']
        pick_counts[team] += 1
        pick_details[team].append({
            'contestant': pick['contestant'],
            'streak': pick['streak'],
            'rank': pick['rank']
        })

    # Create consensus list
    consensus = []
    total_pickers = len(contestants_with_picks)

    for team, count in sorted(pick_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_pickers * 100) if total_pickers > 0 else 0
        consensus.append({
            'pick': team,
            'count': count,
            'percentage': round(percentage, 1),
            'picked_by': sorted(pick_details[team],
                              key=lambda x: int(x['streak']) if str(x['streak']).isdigit() else 0,
                              reverse=True)
        })

    return consensus, all_picks

# Main execution
print('Starting scan...\n')

contestants = get_leaderboard_with_picks(max_to_check=50, target_count=20)

if not contestants:
    print('\n⚠️  No contestants with pending picks found')
    print('   Visit https://contests.covers.com/survivor to see live picks')

    output = {
        'timestamp': datetime.now().isoformat(),
        'contestants_with_picks': [],
        'total_checked': 50,
        'total_with_picks': 0,
        'note': 'No pending picks found'
    }
else:
    consensus, all_picks = create_consensus(contestants)

    output = {
        'timestamp': datetime.now().isoformat(),
        'total_checked': 50,
        'total_with_picks': len(contestants),
        'contestants_with_picks': contestants,
        'all_picks': all_picks,
        'consensus': consensus
    }

    # Print results
    print(f'\n{"="*60}')
    print('🎯 CONSENSUS FROM TOP ACTIVE PICKERS')
    print(f'{"="*60}')
    print(f'\nBased on {len(contestants)} contestants with pending picks:\n')

    if consensus:
        for i, item in enumerate(consensus[:15], 1):
            print(f'{i}. {item["pick"]}')
            print(f'   {item["count"]}/{len(contestants)} pickers ({item["percentage"]}%)')
            top_pickers = item['picked_by'][:3]
            for picker in top_pickers:
                print(f'   • {picker["contestant"]} (Streak: {picker["streak"]})')
            print()

# Save to file
with open('covers_active_consensus.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f'{"="*60}')
print('✓ Saved to: covers_active_consensus.json')
print(f'{"="*60}')

if contestants:
    print(f'\n📊 Summary:')
    print(f'   Contestants checked: 50')
    print(f'   With pending picks: {len(contestants)}')
    print(f'   Total picks found: {len(all_picks)}')
    print(f'   Unique picks: {len(consensus)}')
"@

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Done! Check covers_active_consensus.json" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Visit https://contests.covers.com/survivor" -ForegroundColor Yellow
Write-Host "      to see what they're picking!" -ForegroundColor Yellow
