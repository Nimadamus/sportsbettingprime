@echo off
REM ============================================================================
REM                    COVERS CONSENSUS SCRAPER
REM            Get Top 20 Contestants Daily Picks - All Sports
REM ============================================================================
REM
REM Just double-click this file to run!
REM ============================================================================

echo.
echo ============================================================
echo            COVERS CONSENSUS SCRAPER
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Install required packages
echo Installing dependencies...
pip install --quiet requests beautifulsoup4 lxml 2>nul

echo.
echo ============================================================
echo Running scraper...
echo ============================================================
echo.

REM Run the inline Python scraper
python -c ^"^
import requests; ^
from bs4 import BeautifulSoup; ^
import json; ^
from datetime import datetime; ^
^
url = 'https://contests.covers.com/survivor/currentleaderboard'; ^
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}; ^
^
print('Fetching top 20 contestants...\n'); ^
^
try: ^
    response = requests.get(url, headers=headers); ^
    soup = BeautifulSoup(response.text, 'html.parser'); ^
    contestants = []; ^
    table = soup.find('table'); ^
    if table: ^
        rows = table.find_all('tr')[1:21]; ^
        for i, row in enumerate(rows): ^
            cells = row.find_all('td'); ^
            if len(cells) ^< 3: continue; ^
            username = ''; ^
            for link in row.find_all('a'): ^
                if '/contestant/' in link.get('href', '').lower(): ^
                    username = link.text.strip(); break; ^
            if not username and len(cells) ^> 1: username = cells[1].text.strip(); ^
            streak = cells[2].text.strip() if len(cells) ^> 2 else '0'; ^
            if username: ^
                contestants.append({'rank': i + 1, 'username': username, 'streak': streak}); ^
                emoji = '^^!' if int(streak) ^>= 10 else '  '; ^
                print(f'{emoji} #{i+1:2d}: {username:25s} Streak: {streak}'); ^
    output = {'timestamp': datetime.now().isoformat(), 'contestants': contestants, 'total': len(contestants)}; ^
    with open('covers_data.json', 'w') as f: json.dump(output, f, indent=2); ^
    print(f'\n[OK] Saved {len(contestants)} contestants to covers_data.json'); ^
    print(f'\nTop 5 Hottest:'); ^
    for c in contestants[:5]: ^
        streak_num = int(c['streak']) if c['streak'].isdigit() else 0; ^
        emoji = '^^!' if streak_num ^>= 10 else '  '; ^
        print(f'{emoji} {c[\"username\"]:25s} - {c[\"streak\"]} wins'); ^
except Exception as e: print(f'Error: {e}'); ^
^"

echo.
echo ============================================================
echo COMPLETE!
echo ============================================================
echo.
echo Results saved to: covers_data.json
echo.
echo NEXT STEP:
echo   Visit: https://contests.covers.com/survivor
echo   To see what they're picking (consensus percentages)
echo.
echo Look for picks with 70%% or higher consensus!
echo.
pause
