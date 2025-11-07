# Covers Consensus Scraper - Simple PowerShell Version
# Run this in PowerShell to get top 20 contestants with picks

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " COVERS CONSENSUS SCRAPER" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python found: $($pythonCmd.Source)" -ForegroundColor Green
Write-Host ""

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow

$packagesOK = $true
$packages = @("requests", "beautifulsoup4", "lxml")

foreach ($pkg in $packages) {
    python -c "import $($pkg.Replace('beautifulsoup4', 'bs4'))" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Missing: $pkg" -ForegroundColor Red
        $packagesOK = $false
    } else {
        Write-Host "  Found: $pkg" -ForegroundColor Green
    }
}

if (-not $packagesOK) {
    Write-Host ""
    Write-Host "Installing missing packages..." -ForegroundColor Yellow
    pip install requests beautifulsoup4 lxml

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Could not install packages" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Running scraper..." -ForegroundColor Cyan
Write-Host ""

# Run the Python scraper
$scriptPath = Join-Path $PSScriptRoot "get_active_pickers.sh"

# Check if on Desktop
if (Test-Path ".\get_active_pickers.sh") {
    python .\quick_covers_scraper.py
} else {
    # Fall back to inline Python
    python -c @"
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

url = 'https://contests.covers.com/survivor/currentleaderboard'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print('Fetching top 20 contestants...\n')

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    contestants = []
    table = soup.find('table')

    if table:
        rows = table.find_all('tr')[1:21]

        for i, row in enumerate(rows):
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            username = ''
            for link in row.find_all('a'):
                if '/contestant/' in link.get('href', '').lower():
                    username = link.text.strip()
                    break

            if not username and len(cells) > 1:
                username = cells[1].text.strip()

            streak = cells[2].text.strip() if len(cells) > 2 else '0'

            if username:
                contestants.append({
                    'rank': i + 1,
                    'username': username,
                    'streak': streak
                })
                emoji = '🔥' if int(streak) >= 10 else '📊'
                print(f'  {emoji} #{i+1:2d}: {username:25s} Streak: {streak}')

    output = {
        'timestamp': datetime.now().isoformat(),
        'contestants': contestants,
        'total': len(contestants)
    }

    with open('covers_data.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f'\n✓ Saved {len(contestants)} contestants to covers_data.json')
    print(f'\nTop 5 Hottest:')
    for c in contestants[:5]:
        streak_num = int(c['streak']) if c['streak'].isdigit() else 0
        emoji = '🔥' if streak_num >= 10 else '📊'
        print(f'  {emoji} {c["username"]:25s} - {c["streak"]} wins')

except Exception as e:
    print(f'Error: {e}')
"@
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host " COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Data saved to: covers_data.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step:" -ForegroundColor Yellow
Write-Host "Visit: https://contests.covers.com/survivor" -ForegroundColor Yellow
Write-Host "To see what they're picking!" -ForegroundColor Yellow
Write-Host ""
