@echo off
REM ============================================================================
REM           KING OF COVERS - TOP 50 CONTESTANTS SCRAPER
REM              Get Top Players by Units Won + Their Picks
REM ============================================================================

echo ============================================================
echo        KING OF COVERS TOP 50 CONTESTANTS SCRAPER
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed!
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install --quiet requests beautifulsoup4 lxml

echo.
echo ============================================================
echo Scraping King of Covers Top 50 (by Units Won)
echo Sports: NFL, NBA, NHL, NCAAF, NCAAB
echo ============================================================
echo.

python -c "import requests; from bs4 import BeautifulSoup; import json; from datetime import datetime; from collections import defaultdict; sports = {'nfl': 'NFL', 'nba': 'NBA', 'nhl': 'NHL', 'ncaaf': 'NCAAF', 'ncaab': 'NCAAB'}; headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}; all_data = {}; print('Fetching top 50 contestants by units won...\n'); [all_data.update({sport_name: (lambda: (r := requests.get(f'https://contests.covers.com/consensus/pickleaders/{sport}?orderBy=Units', headers=headers), soup := BeautifulSoup(r.text, 'html.parser'), table := soup.find('table'), contestants := [{'rank': i+1, 'username': row.find('a').text.strip() if row.find('a') else '', 'record': cells[1].text.strip() if len(cells) > 1 else '', 'units': cells[2].text.strip() if len(cells) > 2 else ''} for i, row in enumerate(table.find_all('tr')[1:51]) if (cells := row.find_all('td')) and len(cells) >= 3] if table else [], print(f'{sport_name}: Found {len(contestants)} contestants') or contestants)[-1])()}) for sport, sport_name in sports.items()]; output = {'timestamp': datetime.now().isoformat(), 'sports': all_data}; json.dump(output, open('king_of_covers_top50.json', 'w'), indent=2); print(f'\nSaved to: king_of_covers_top50.json'); [print(f'\n{sport}:') or [print(f'  {c[\"rank\"]:2d}. {c[\"username\"]:25s} {c[\"units\"]:>10s} units') for c in contestants[:10]] for sport, contestants in all_data.items() if contestants]"

echo.
echo ============================================================
echo COMPLETE!
echo ============================================================
echo.
echo Results saved to: king_of_covers_top50.json
echo.
echo Note: This scrapes rankings by units won.
echo To see their CURRENT PICKS, visit:
echo   https://contests.covers.com/consensus/pickleaders/all
echo.
pause
