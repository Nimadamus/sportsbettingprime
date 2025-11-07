@echo off
echo ============================================================
echo     KING OF COVERS TOP 50 SCRAPER
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
echo Scraping Top 50 by Units Won...
echo Sports: NFL, NBA, NHL, College Football, College Basketball
echo.

python -c "import requests; from bs4 import BeautifulSoup; import json; from datetime import datetime; print('Fetching King of Covers top 50...\n'); sports = [('nfl', 'NFL'), ('nba', 'NBA'), ('nhl', 'NHL'), ('ncaaf', 'College Football'), ('ncaab', 'College Basketball')]; headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}; results = {}; [(lambda s, n: (print(f'{n}...'), r := requests.get(f'https://contests.covers.com/consensus/pickleaders/{s}', headers=headers, timeout=10), soup := BeautifulSoup(r.text, 'html.parser'), table := soup.find('table', class_='table'), rows := table.find_all('tr')[1:51] if table else [], contestants := [{'rank': i+1, 'name': (link.text.strip() if (link := row.find('a', href=lambda x: x and '/user/' in x)) else 'Unknown'), 'record': (cells[1].text.strip() if len(cells) > 1 else ''), 'units': (cells[2].text.strip() if len(cells) > 2 else '')} for i, row in enumerate(rows) if (cells := row.find_all('td'))], results.update({n: contestants}), print(f'  Found {len(contestants)} contestants'))[-1])(sport, name) for sport, name in sports]; json.dump({'timestamp': datetime.now().isoformat(), 'results': results}, open('koc_top50.json', 'w'), indent=2); print(f'\nSaved {sum(len(v) for v in results.values())} total contestants to koc_top50.json'); print('\nTop 5 from each sport:'); [print(f'\n{sport}:') or [print(f'  {c[\"rank\"]}. {c[\"name\"]:20s} {c[\"units\"]:>10s}') for c in data[:5]] for sport, data in results.items() if data]"

echo.
echo ============================================================
echo COMPLETE!
echo ============================================================
echo.
echo File saved: koc_top50.json
echo.
pause
