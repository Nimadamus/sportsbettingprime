@echo off
echo ============================================================
echo            COVERS CONSENSUS SCRAPER
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install --quiet requests beautifulsoup4 lxml

echo.
echo Scraping top 20 contestants...
echo.

python -c "import requests; from bs4 import BeautifulSoup; import json; from datetime import datetime; url = 'https://contests.covers.com/survivor/currentleaderboard'; headers = {'User-Agent': 'Mozilla/5.0'}; r = requests.get(url, headers=headers); soup = BeautifulSoup(r.text, 'html.parser'); table = soup.find('table'); contestants = []; [contestants.append({'rank': i+1, 'username': link.text.strip(), 'streak': cells[2].text.strip()}) or print(f'#{i+1}: {link.text.strip():25s} Streak: {cells[2].text.strip()}') for i, row in enumerate(table.find_all('tr')[1:21]) if len(cells := row.find_all('td')) >= 3 for link in [next((l for l in row.find_all('a') if '/contestant/' in l.get('href', '').lower()), None)] if link]; json.dump({'timestamp': datetime.now().isoformat(), 'contestants': contestants}, open('covers_data.json', 'w'), indent=2); print(f'\nSaved {len(contestants)} contestants to covers_data.json')"

echo.
echo ============================================================
echo DONE! Check covers_data.json
echo.
echo Next: Visit https://contests.covers.com/survivor
echo       to see consensus picks
echo ============================================================
pause
