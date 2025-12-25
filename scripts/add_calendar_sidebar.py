#!/usr/bin/env python3
"""
Add calendar sidebar to all sport pages in sportsbettingprime.
Similar to BetLegend's calendar navigation system.
"""
import os
import re
from datetime import datetime

REPO = r"C:\Users\Nima\sportsbettingprime"
ARCHIVE_DIR = os.path.join(REPO, "archive")

SPORTS = {
    "nfl": {
        "name": "NFL",
        "folder": "nfl",
        "prefix": "nfl-gridiron-oracles",
        "main_page": "nfl-gridiron-oracles.html",
        "accent": "#22c55e"
    },
    "nba": {
        "name": "NBA",
        "folder": "nba",
        "prefix": "nba-court-vision",
        "main_page": "nba-court-vision.html",
        "accent": "#3b82f6"
    },
    "nhl": {
        "name": "NHL",
        "folder": "nhl",
        "prefix": "nhl-ice-oracles",
        "main_page": "nhl-ice-oracles.html",
        "accent": "#38bdf8"
    },
    "ncaab": {
        "name": "NCAAB",
        "folder": "ncaab",
        "prefix": "college-basketball",
        "main_page": "college-basketball.html",
        "accent": "#f97316"
    },
    "ncaaf": {
        "name": "NCAAF",
        "folder": "ncaaf",
        "prefix": "college-football",
        "main_page": "college-football.html",
        "accent": "#a855f7"
    }
}


def get_archive_dates(sport_key):
    """Get list of dates that have archive pages for a sport."""
    config = SPORTS[sport_key]
    folder = os.path.join(ARCHIVE_DIR, config["folder"])

    dates = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            match = re.search(r"(\d{4}-\d{2}-\d{2})", f)
            if match:
                dates.append(match.group(1))

    return sorted(dates)


def generate_calendar_js(sport_key):
    """Generate JavaScript for calendar functionality."""
    config = SPORTS[sport_key]
    dates = get_archive_dates(sport_key)

    # Build archive data
    archive_entries = []
    for d in dates:
        archive_entries.append(f'"{d}": "archive/{config["folder"]}/{config["prefix"]}-{d}.html"')

    archive_data = ",\n            ".join(archive_entries)

    return f'''
<script>
const ARCHIVE_DATA = {{
            {archive_data}
        }};

const CURRENT_SPORT = "{config['name']}";

function initCalendar() {{
    const today = new Date();
    const monthSelect = document.getElementById('month-select');
    const calendarDays = document.getElementById('calendar-days');
    const yearDisplay = document.getElementById('cal-year');
    const mobileSelect = document.getElementById('mobile-archive-select');

    // Populate month dropdown
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December'];

    for (let i = 0; i < 12; i++) {{
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = months[i];
        if (i === today.getMonth()) opt.selected = true;
        monthSelect.appendChild(opt);
    }}

    // Populate mobile dropdown
    Object.keys(ARCHIVE_DATA).sort().reverse().forEach(date => {{
        const opt = document.createElement('option');
        opt.value = ARCHIVE_DATA[date];
        const d = new Date(date + 'T12:00:00');
        opt.textContent = d.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }});
        mobileSelect.appendChild(opt);
    }});

    mobileSelect.addEventListener('change', function() {{
        if (this.value) window.location.href = this.value;
    }});

    function renderCalendar(year, month) {{
        yearDisplay.textContent = year;
        calendarDays.innerHTML = '';

        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {{
            const empty = document.createElement('div');
            empty.className = 'cal-day empty';
            calendarDays.appendChild(empty);
        }}

        // Days of the month
        for (let day = 1; day <= daysInMonth; day++) {{
            const dateStr = `${{year}}-${{String(month + 1).padStart(2, '0')}}-${{String(day).padStart(2, '0')}}`;
            const dayEl = document.createElement('div');
            dayEl.className = 'cal-day';
            dayEl.textContent = day;

            if (ARCHIVE_DATA[dateStr]) {{
                dayEl.classList.add('has-content');
                dayEl.addEventListener('click', () => {{
                    window.location.href = ARCHIVE_DATA[dateStr];
                }});
            }}

            // Highlight today
            if (year === today.getFullYear() && month === today.getMonth() && day === today.getDate()) {{
                dayEl.classList.add('today');
            }}

            calendarDays.appendChild(dayEl);
        }}
    }}

    monthSelect.addEventListener('change', function() {{
        renderCalendar(today.getFullYear(), parseInt(this.value));
    }});

    renderCalendar(today.getFullYear(), today.getMonth());
}}

document.addEventListener('DOMContentLoaded', initCalendar);
</script>
'''


def generate_calendar_css():
    """Generate CSS for calendar sidebar."""
    return '''
/* Calendar Sidebar Styles */
.page-layout { display: flex; gap: 2rem; max-width: 1400px; margin: 0 auto; padding: 2rem; }
.calendar-sidebar { position: sticky; top: 100px; width: 280px; flex-shrink: 0; height: fit-content; }
.main-content { flex: 1; min-width: 0; }
.calendar-box { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }
.calendar-title { font-size: 0.875rem; font-weight: 700; color: var(--gold); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem; text-align: center; }
.year-display { font-size: 1.5rem; font-weight: 800; color: var(--text); text-align: center; margin-bottom: 0.75rem; }
.month-select { width: 100%; background: var(--bg); color: var(--text); border: 1px solid var(--border); padding: 0.625rem; font-size: 0.875rem; border-radius: 6px; cursor: pointer; margin-bottom: 1rem; }
.calendar-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-bottom: 4px; }
.calendar-weekdays span { text-align: center; font-size: 0.7rem; font-weight: 600; color: var(--muted); padding: 4px 0; }
.calendar-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.cal-day { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: var(--muted); background: rgba(0,0,0,0.2); border-radius: 4px; cursor: default; }
.cal-day.empty { background: transparent; }
.cal-day.has-content { background: rgba(34, 197, 94, 0.2); color: #22c55e; cursor: pointer; font-weight: 600; border: 1px solid rgba(34, 197, 94, 0.3); }
.cal-day.has-content:hover { background: rgba(34, 197, 94, 0.4); transform: scale(1.1); }
.cal-day.today { box-shadow: inset 0 0 0 2px var(--gold); }
.mobile-archive { display: none; background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }
.mobile-archive-title { font-size: 0.8rem; font-weight: 600; color: var(--gold); margin-bottom: 0.5rem; }
.mobile-archive-select { width: 100%; background: var(--bg); color: var(--text); border: 1px solid var(--border); padding: 0.5rem; font-size: 0.875rem; border-radius: 6px; }
@media (max-width: 1024px) { .calendar-sidebar { display: none; } .mobile-archive { display: block; } .page-layout { padding: 1rem; } }
'''


def generate_calendar_html():
    """Generate HTML for calendar sidebar."""
    return '''
<aside class="calendar-sidebar">
    <div class="calendar-box">
        <div class="calendar-title">Archive Calendar</div>
        <div class="year-display" id="cal-year">2025</div>
        <select class="month-select" id="month-select"></select>
        <div class="calendar-weekdays">
            <span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span>
        </div>
        <div class="calendar-days" id="calendar-days"></div>
    </div>
</aside>
<div class="mobile-archive">
    <div class="mobile-archive-title">Browse Archive</div>
    <select class="mobile-archive-select" id="mobile-archive-select">
        <option value="">Jump to date...</option>
    </select>
</div>
'''


def update_sport_page(sport_key):
    """Update a sport page with calendar sidebar."""
    config = SPORTS[sport_key]
    page_path = os.path.join(REPO, config["main_page"])

    if not os.path.exists(page_path):
        print(f"  [SKIP] {config['main_page']} not found")
        return False

    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already has calendar
    if 'calendar-sidebar' in content:
        print(f"  [SKIP] {config['main_page']} already has calendar")
        return False

    # Add calendar CSS to existing styles
    calendar_css = generate_calendar_css()
    content = content.replace('</style>', calendar_css + '\n    </style>')

    # Wrap main content with layout and add sidebar
    calendar_html = generate_calendar_html()

    # Find main tag and wrap its contents
    main_match = re.search(r'(<main[^>]*>)(.*?)(</main>)', content, re.DOTALL)
    if main_match:
        main_open = main_match.group(1)
        main_content = main_match.group(2)
        main_close = main_match.group(3)

        new_main = f'''{main_open}
    <div class="page-layout">
        {calendar_html}
        <div class="main-content">
            {main_content.strip()}
        </div>
    </div>
{main_close}'''

        content = content[:main_match.start()] + new_main + content[main_match.end():]

    # Add JavaScript before </body>
    calendar_js = generate_calendar_js(sport_key)
    content = content.replace('</body>', calendar_js + '\n</body>')

    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] Updated {config['main_page']}")
    return True


def main():
    print("=" * 60)
    print("ADDING CALENDAR SIDEBAR TO SPORT PAGES")
    print("=" * 60)

    updated = 0
    for sport_key in SPORTS:
        print(f"\n{SPORTS[sport_key]['name']}:")
        if update_sport_page(sport_key):
            updated += 1

    print(f"\n{'=' * 60}")
    print(f"Updated {updated} pages")
    print("=" * 60)


if __name__ == "__main__":
    main()
