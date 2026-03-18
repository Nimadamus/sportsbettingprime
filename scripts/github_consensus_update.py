#!/usr/bin/env python3
"""
SPORTSBETTINGPRIME SHARP CONSENSUS UPDATE - GitHub Actions Version
===================================================================
Runs on GitHub's servers to update the Sharp Consensus page daily.

WHAT THIS SCRIPT DOES:
1. Scrapes top contestants from Covers.com King of Covers
2. Aggregates their pending picks
3. Groups picks by game (card layout)
4. Updates both sharp-consensus.html and covers-consensus.html
(Git commit/push handled by GitHub Actions workflow)

AGGREGATION FIX (Feb 2026):
- Uses SIDE-BASED aggregation so expert picks and public consensus combine
- "MIA +6.5" and "Miami +5.5" both count as "Miami ATS" picks
- Public consensus weighted by percentage strength, not raw count
- College team abbreviations properly resolved
"""

import os
import re
import json
import shutil
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import time

import requests
from bs4 import BeautifulSoup

# Configuration - auto-detect repo root (works on both Windows local and GitHub Actions)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPT_DIR)  # Go up one level from scripts/ to repo root
# Fallback to Windows path if running outside repo structure
if not os.path.exists(os.path.join(REPO, "covers-consensus.html")):
    REPO = r"C:\Users\Nima\sportsbettingprime"
CONSENSUS_DIR = os.path.join(REPO, "consensus_library")
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
DATE_FULL = TODAY.strftime("%A, %B %d, %Y")


# ESPN sport mapping for schedule lookups
ESPN_SPORT_MAP = {
    'NHL': ('hockey', 'nhl'),
    'NBA': ('basketball', 'nba'),
    'NFL': ('football', 'nfl'),
    'College Basketball': ('basketball', 'mens-college-basketball'),
    'College Football': ('football', 'college-football'),
}


def fetch_espn_schedule():
    """Fetch today's games from ESPN scoreboard API for all active sports.
    Returns dict: {sport_name: [(away_display, home_display), ...]}"""
    schedule = {}
    today_str = TODAY.strftime("%Y%m%d")

    for sport_name, (league, sport_path) in ESPN_SPORT_MAP.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/{league}/{sport_path}/scoreboard?dates={today_str}"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            games = []
            for event in data.get('events', []):
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) == 2:
                    away = home = None
                    for c in competitors:
                        name = c.get('team', {}).get('displayName', '')
                        if c.get('homeAway') == 'away':
                            away = name
                        else:
                            home = name
                    if away and home:
                        games.append((away, home))
            schedule[sport_name] = games
            if games:
                print(f"    ESPN {sport_name}: {len(games)} games today")
        except Exception as e:
            print(f"    ESPN {sport_name}: error fetching schedule ({e})")
            # If ESPN fails for a sport, don't filter that sport at all
            schedule[sport_name] = None

    return schedule


# Common abbreviation expansions for team name matching
_TEAM_EXPANSIONS = {
    'ny': 'new york', 'l.a.': 'los angeles', 'la': 'los angeles',
}

# Aliases for team name matching (Covers name -> ESPN name or vice versa)
_TEAM_ALIASES = {
    'uconn': 'connecticut',
    'connecticut': 'uconn',
    'ole miss': 'mississippi',
    'pitt': 'pittsburgh',
    'umass': 'massachusetts',
    'detroit mercy': 'detroit',
    'ut rio grande valley': 'texas rio grande valley',
    'monmouth': 'monmouth',
    'miss valley st': 'mississippi valley state',
    'mississippi valley state': 'mississippi valley',
    'northern ky': 'northern kentucky',
    'northern co': 'northern colorado',
    'eastern wa': 'eastern washington',
    'weber st': 'weber state',
    'wright st': 'wright state',
    'alcorn st': 'alcorn state',
    "st john's": "st. john's",
    "saint mary's": "saint marys",
    'etsu': 'east tennessee state',
    'east tennessee state': 'etsu',
    'grambling': 'grambling state',
    'grambling state': 'grambling',
    'miss valley state': 'mississippi valley state',
    'mississippi valley state': 'miss valley state',
}

# Suffixes that change team identity (not just mascot names)
# "Virginia Tech" is a DIFFERENT team than "Virginia"
# "Georgia Tech" is a DIFFERENT team than "Georgia"
_IDENTITY_SUFFIXES = {'tech', 'state', 'a&m', 'southern', 'western', 'eastern', 'northern', 'central'}


def _normalize_for_match(name):
    """Normalize a team name for fuzzy matching.
    Strips periods, replaces hyphens with spaces, strips qualifiers like (FL)/(OH).
    Also normalizes 'St.' to 'state' and common state abbreviations."""
    n = name.lower().strip()
    n = n.replace('-', ' ')    # Loyola-Chicago -> Loyola Chicago, Miami-Florida -> Miami Florida
    n = re.sub(r'\s*\(.*?\)', '', n)  # Miami (FL) -> Miami
    # Normalize "st." and "st" at end of word to "state" (but not "st." in "st. john's")
    # Only do this if "st" is at the END of the name or followed by a space then non-period
    if n.endswith(' st.') or n.endswith(' st'):
        n = n.rsplit(' ', 1)[0] + ' state'
    n = n.replace('.', '')     # L.A. -> LA, remaining periods
    n = re.sub(r'\s+', ' ', n).strip()
    return n


def _team_matches(covers_name, espn_name):
    """Check if a Covers team name matches an ESPN team name.
    Handles: periods (L.A. vs LA), hyphens (Loyola-Chicago vs Loyola Chicago),
    qualifiers (Miami-Florida vs Miami Hurricanes), abbreviations (NY vs New York)."""
    c = _normalize_for_match(covers_name)
    e = _normalize_for_match(espn_name)

    # Direct substring match after normalization
    # Guard against "virginia" matching "virginia tech" - check identity suffixes
    if c == e:
        return True
    if len(c) > 1 and len(e) > 1:
        # Check if shorter is contained in longer
        shorter, longer = (c, e) if len(c) <= len(e) else (e, c)
        if shorter in longer:
            # Get the remaining text after the match
            idx = longer.index(shorter)
            remainder = longer[idx + len(shorter):].strip()
            # If remainder starts with an identity-changing suffix, NOT a match
            # e.g., "virginia" in "virginia tech hokies" -> remainder="tech hokies" -> "tech" is identity suffix -> NO MATCH
            if remainder:
                first_remaining_word = remainder.split()[0]
                if first_remaining_word in _IDENTITY_SUFFIXES:
                    pass  # Not a match, fall through
                else:
                    return True
            else:
                return True  # Exact match or shorter is the entire longer string

    # Try expanding common abbreviations in the Covers name
    for abbr, full in _TEAM_EXPANSIONS.items():
        if c.startswith(abbr + ' ') or c == abbr:
            expanded = full + c[len(abbr):]
            if expanded in e or e in expanded:
                return True

    # Try alias matching (e.g. "uconn" <-> "connecticut")
    c_alias = _TEAM_ALIASES.get(c)
    if c_alias and (c_alias in e or e in c_alias):
        return True
    e_alias = _TEAM_ALIASES.get(e.split()[0] if e.split() else e)
    if e_alias and (e_alias in c or c in e_alias):
        return True

    # Single-word covers name: match if it equals ESPN's first word
    # BUT only for single-word names to prevent "Michigan State" matching "Michigan Wolverines"
    # AND check that ESPN's second word isn't an identity suffix (tech, state, a&m)
    c_words = c.split()
    e_words = e.split()
    if len(c_words) == 1 and len(c_words[0]) >= 4:
        if c_words[0] == e_words[0]:
            # Check if ESPN's second word changes the team identity
            if len(e_words) >= 2 and e_words[1] in _IDENTITY_SUFFIXES:
                return False  # "Virginia" should NOT match "Virginia Tech"
            return True

    return False


def is_game_on_today(matchup, espn_games):
    """Check if a Covers matchup (e.g. 'St. Louis @ Seattle') is on today's ESPN schedule.
    espn_games is a list of (away_display, home_display) tuples from ESPN.
    Returns True if the matchup is found, or if espn_games is None (ESPN failed)."""
    if espn_games is None:
        return True  # Don't filter if ESPN data unavailable

    covers_parts = matchup.split(' @ ')
    if len(covers_parts) != 2:
        return True  # Can't parse, keep it
    covers_away = covers_parts[0].strip()
    covers_home = covers_parts[1].strip()

    for espn_away, espn_home in espn_games:
        if _team_matches(covers_away, espn_away) and _team_matches(covers_home, espn_home):
            return True

    return False


class CoversConsensusScraper:
    """Scrape Covers.com King of Covers contests"""

    # Map ALL-CAPS abbreviations (from expert pick text) to full names
    TEAM_ABBREV = {
        # NBA
        'MIA': 'Miami', 'BOS': 'Boston', 'PHO': 'Phoenix', 'PHX': 'Phoenix',
        'DET': 'Detroit', 'LAL': 'L.A. Lakers', 'LAC': 'L.A. Clippers',
        'GS': 'Golden State', 'GSW': 'Golden State', 'HOU': 'Houston',
        'IND': 'Indiana', 'MIL': 'Milwaukee', 'MIN': 'Minnesota',
        'NO': 'New Orleans', 'NOP': 'New Orleans', 'NY': 'New York',
        'NYK': 'New York', 'OKC': 'Oklahoma City', 'ORL': 'Orlando',
        'SAC': 'Sacramento', 'SA': 'San Antonio', 'SAS': 'San Antonio',
        'POR': 'Portland', 'MEM': 'Memphis', 'CHA': 'Charlotte',
        'CHI': 'Chicago', 'CLE': 'Cleveland', 'DAL': 'Dallas',
        'DEN': 'Denver', 'ATL': 'Atlanta', 'BKN': 'Brooklyn', 'BK': 'Brooklyn',
        'TOR': 'Toronto', 'UTA': 'Utah', 'WAS': 'Washington',
        # NHL
        'ANA': 'Anaheim', 'ARI': 'Arizona', 'BUF': 'Buffalo',
        'CGY': 'Calgary', 'CAR': 'Carolina', 'COL': 'Colorado',
        'CBJ': 'Columbus', 'EDM': 'Edmonton', 'FLA': 'Florida',
        'LA': 'Los Angeles', 'LAK': 'Los Angeles', 'MTL': 'Montreal',
        'NSH': 'Nashville', 'NJ': 'New Jersey', 'NJD': 'New Jersey',
        'NYI': 'NY Islanders', 'NYR': 'NY Rangers', 'OTT': 'Ottawa',
        'PHI': 'Philadelphia', 'PIT': 'Pittsburgh', 'SJ': 'San Jose',
        'SJS': 'San Jose', 'SEA': 'Seattle', 'STL': 'St. Louis',
        'TB': 'Tampa Bay', 'TBL': 'Tampa Bay', 'VAN': 'Vancouver',
        'VEG': 'Vegas', 'VGK': 'Vegas', 'WIN': 'Winnipeg', 'WPG': 'Winnipeg',
        # NFL
        'BAL': 'Baltimore', 'CIN': 'Cincinnati', 'GB': 'Green Bay',
        'GNB': 'Green Bay', 'JAX': 'Jacksonville', 'KC': 'Kansas City',
        'KAN': 'Kansas City', 'LV': 'Las Vegas', 'LAR': 'L.A. Rams',
        'NE': 'New England', 'NEP': 'New England',
        'NYG': 'NY Giants', 'NYJ': 'NY Jets', 'SF': 'San Francisco',
        'TEN': 'Tennessee',
        # NCAAB/NCAAF - abbreviations used in expert pick text
        'VT': 'Virginia Tech', 'GT': 'Georgia Tech', 'OKST': 'Oklahoma State',
        'MIZZ': 'Missouri', 'KU': 'Kansas', 'KSU': 'Kansas State',
        'ASU': 'Arizona State', 'FSU': 'Florida State', 'OSU': 'Ohio State',
        'UNC': 'North Carolina', 'NCST': 'NC State', 'CLB': 'Columbus',
        'GMU': 'George Mason', 'GW': 'George Washington',
        'GTWN': 'Georgetown', 'PROV': 'Providence', 'SLU': 'Saint Louis',
        'DUQ': 'Duquesne', 'PITT': 'Pittsburgh', 'SYR': 'Syracuse',
        'LOU': 'Louisville', 'DUKE': 'Duke', 'UVA': 'Virginia',
        'BAMA': 'Alabama', 'AUB': 'Auburn', 'ARK': 'Arkansas',
        'TENN': 'Tennessee', 'VAND': 'Vanderbilt', 'MISS': 'Ole Miss',
        'MSST': 'Mississippi State', 'LSU': 'LSU', 'TAMU': 'Texas A&M',
        'TTU': 'Texas Tech', 'ISU': 'Iowa State', 'WVU': 'West Virginia',
        'OU': 'Oklahoma', 'UT': 'Texas', 'TCU': 'TCU', 'BAY': 'Baylor',
        'CONN': 'UConn', 'MARQ': 'Marquette', 'NOVA': 'Villanova',
        'XAVIER': 'Xavier', 'CREIGH': 'Creighton', 'BUT': 'Butler',
        'DEPAUL': 'DePaul', 'HALL': 'Seton Hall',
        'ARIZ': 'Arizona', 'UCLA': 'UCLA', 'USC': 'USC', 'STAN': 'Stanford',
        'ORE': 'Oregon', 'WASH': 'Washington', 'COLO': 'Colorado',
        'UTAH': 'Utah', 'CAL': 'California',
        'WISC': 'Wisconsin', 'MICH': 'Michigan', 'MSU': 'Michigan State',
        'IOWA': 'Iowa', 'MINN': 'Minnesota', 'NW': 'Northwestern',
        'PUR': 'Purdue', 'ILL': 'Illinois', 'NEB': 'Nebraska',
        'PSU': 'Penn State', 'RUTG': 'Rutgers', 'MD': 'Maryland',
        'UGA': 'Georgia', 'FLA': 'Florida', 'UK': 'Kentucky',
        'SC': 'South Carolina', 'MO': 'Missouri',
        'FAU': 'Florida Atlantic', 'FIU': 'Florida International',
        'SMU': 'SMU', 'UCF': 'UCF', 'USF': 'South Florida',
        'UNLV': 'UNLV', 'SDSU': 'San Diego State', 'BSU': 'Boise State',
        'CSU': 'Colorado State', 'NMSU': 'New Mexico State',
        'UNM': 'New Mexico', 'USU': 'Utah State', 'WYO': 'Wyoming',
        'NDSU': 'North Dakota State', 'SHSU': 'Sam Houston',
        'HOF': 'Hofstra', 'HOFSTRA': 'Hofstra',
    }

    # Normalize alternate team names to ONE canonical form
    # This prevents "Connecticut @ St. John's" and "UConn @ St. John's" from being separate games
    TEAM_NAME_CANONICAL = {
        'Connecticut': 'UConn',
        'Illinois-Chicago': 'UIC',
        'Illinois St.': 'Illinois State',
        'Loyola Chicago': 'Loyola-Chicago',
        'N.C. State': 'NC State',
        'N.C.State': 'NC State',
        'UTSA': 'UT San Antonio',
        'UTEP': 'UT El Paso',
        'UMass': 'Massachusetts',
        'UConn': 'UConn',
        'SMU': 'SMU',
        'USC': 'USC',
        'UCLA': 'UCLA',
        'UCF': 'UCF',
        'LSU': 'LSU',
        'BYU': 'BYU',
        'VCU': 'VCU',
        'UIC': 'UIC',
        'UNLV': 'UNLV',
        'Miami (FL)': 'Miami',
        'Miami-Florida': 'Miami',
        'Miami Florida': 'Miami',
        'St. John\'s (NY)': "St. John's",
        'Virginia Tech': 'Virginia Tech',
        'Georgia Tech': 'Georgia Tech',
        'Oklahoma State': 'Oklahoma State',
        'Mississippi State': 'Mississippi State',
        'Michigan State': 'Michigan State',
        'Ohio State': 'Ohio State',
        'Kansas State': 'Kansas State',
        'Arizona State': 'Arizona State',
        'Florida State': 'Florida State',
        'Penn State': 'Penn State',
        'Iowa State': 'Iowa State',
        'Boise State': 'Boise State',
        'Colorado State': 'Colorado State',
        'MS State': 'Mississippi State',
        'Louisiana State': 'LSU',
        'Texas Christian': 'TCU',
        'CSU Fullerton': 'Cal State Fullerton',
        'CSU Northridge': 'Cal State Northridge',
        'CA Baptist': 'Cal Baptist',
        'Long Beach St.': 'Long Beach State',
        'Sam Houston St.': 'Sam Houston',
        'Middle TN': 'Middle Tennessee',
        'Missouri St.': 'Missouri State',
        'Utah St.': 'Utah State',
        'New Mexico St.': 'New Mexico State',
        'Jacksonville St.': 'Jacksonville State',
        'Texas-El Paso': 'UTEP',
        'Texas-Arlington': 'UT Arlington',
        'Elon University': 'Elon',
        'Mississippi': 'Ole Miss',
        'Central Florida': 'UCF',
        # Common public-consensus abbreviated forms
        'Monmouth-NJ': 'Monmouth',
        'Texas R-G Valley': 'UT Rio Grande Valley',
        'Detroit Mercy': 'Detroit Mercy',
        'Alcorn St.': 'Alcorn State',
        'Northern KY': 'Northern Kentucky',
        'Northern CO': 'Northern Colorado',
        'Weber St.': 'Weber State',
        'Eastern WA': 'Eastern Washington',
        'Miss Valley St': 'Mississippi Valley State',
        'Miss Valley St.': 'Mississippi Valley State',
        'Miss Valley State': 'Mississippi Valley State',
        'Miss Valley St Delta': 'Mississippi Valley State',
        'Grambling': 'Grambling State',
        'ETSU': 'East Tennessee State',
        'E. Tennessee St.': 'East Tennessee State',
        'E. Tennessee State': 'East Tennessee State',
        'East Tennessee St.': 'East Tennessee State',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        self.sports = {
            'nfl': 'NFL',
            'nba': 'NBA',
            'nhl': 'NHL',
            'ncaab': 'College Basketball',
            'ncaaf': 'College Football',
        }

        self.all_picks = []

        # Side-based aggregation: groups picks by SIDE (team + direction)
        # instead of exact line value, so "MIA +6.5" and "Miami +5.5" combine
        self.side_counter = Counter()       # "sport|matchup|side" -> total count
        self.side_lines = defaultdict(Counter)  # "sport|matchup|side" -> {line_text: count}
        self.side_type = {}                 # "sport|matchup|side" -> pick_type

    def _consensus_weight(self, pct):
        """Convert consensus percentage to weight for pick counting.
        Stronger consensus = higher weight. This replaces the old count//20
        formula which produced uniform ~8 for every game."""
        if pct >= 75:
            return 8
        elif pct >= 70:
            return 6
        elif pct >= 65:
            return 5
        elif pct >= 60:
            return 4
        elif pct >= 55:
            return 3
        elif pct >= 52:
            return 2
        else:
            return 1

    def _resolve_team_abbrev(self, abbrev):
        """Resolve a team abbreviation to full name"""
        return self.TEAM_ABBREV.get(abbrev.upper(), abbrev)

    def _match_team_to_side(self, token, away, home):
        """Match a team token from pick text to away/home team name"""
        token_clean = token.upper().rstrip('.,;:')

        # Direct full-name match
        if token_clean == away.upper() or away.upper().startswith(token_clean):
            return away
        if token_clean == home.upper() or home.upper().startswith(token_clean):
            return home

        # Abbreviation lookup
        full = self.TEAM_ABBREV.get(token_clean)
        if full:
            if full.lower() in away.lower() or away.lower() in full.lower():
                return away
            if full.lower() in home.lower() or home.lower() in full.lower():
                return home

        # Partial/substring match
        for team in [away, home]:
            team_compressed = team.upper().replace(' ', '').replace('.', '')
            if token_clean in team_compressed or team_compressed.startswith(token_clean):
                return team

        return token  # Fallback to raw token

    def _extract_side(self, pick_text, pick_type, matchup):
        """Extract the betting SIDE from pick text for aggregation.
        Returns (side_label, display_line) where:
        - side_label: e.g. "Miami ATS" or "Over" (used as aggregation key)
        - display_line: e.g. "+5.5" or "229.5" (used for display)"""
        teams = matchup.split(' @ ')
        away = teams[0].strip() if teams else ''
        home = teams[1].strip() if len(teams) > 1 else ''

        if 'Over' in pick_type:
            # Extract total number
            match = re.search(r'(\d+\.?\d*)', pick_text)
            line = match.group(1) if match else ''
            return 'Over', line

        if 'Under' in pick_type:
            match = re.search(r'(\d+\.?\d*)', pick_text)
            line = match.group(1) if match else ''
            return 'Under', line

        # For spread/ML, identify the team
        first_token = pick_text.split()[0] if pick_text.split() else ''
        team = self._match_team_to_side(first_token, away, home)

        # Extract the line value
        line_match = re.search(r'([+-]\d+\.?\d*)', pick_text)
        line = line_match.group(1) if line_match else ''

        if 'Moneyline' in pick_type:
            # For ML, extract odds
            ml_match = re.search(r'\(([+-]\d+)\)', pick_text)
            odds = ml_match.group(1) if ml_match else line
            return f"{team} ML", odds
        else:
            return f"{team} ATS", line

    def _normalize_team_name(self, name):
        """Normalize a single team name to its canonical form"""
        canonical = self.TEAM_NAME_CANONICAL.get(name)
        if canonical:
            return canonical
        # Also try stripping trailing period variations
        if name.endswith('.'):
            canonical = self.TEAM_NAME_CANONICAL.get(name[:-1])
            if canonical:
                return canonical
        return name

    def _normalize_matchup(self, matchup):
        """Normalize a matchup string so the same game always has the same key.
        e.g. 'Connecticut @ St. John's' and 'UConn @ St. John's' both become 'UConn @ St. John's'"""
        parts = matchup.split(' @ ')
        if len(parts) == 2:
            away = self._normalize_team_name(parts[0].strip())
            home = self._normalize_team_name(parts[1].strip())
            return f"{away} @ {home}"
        return matchup

    def _find_canonical_matchup(self, sport, matchup):
        """Find an existing matchup that fuzzy-matches the given one.
        This permanently handles name mismatches between expert picks
        (short names like 'Calgary') and public consensus (full names
        like 'Calgary Flames') without needing any dictionary updates."""
        parts = matchup.split(' @ ')
        if len(parts) != 2:
            return matchup
        away_new, home_new = parts[0].strip(), parts[1].strip()

        # Collect all unique matchups already seen for this sport
        seen_matchups = set()
        for key in self.side_counter:
            key_parts = key.split('|')
            if len(key_parts) >= 2 and key_parts[0] == sport:
                seen_matchups.add(key_parts[1])

        for existing_matchup in seen_matchups:
            existing_parts = existing_matchup.split(' @ ')
            if len(existing_parts) != 2:
                continue
            away_ex, home_ex = existing_parts[0].strip(), existing_parts[1].strip()
            if _team_matches(away_new, away_ex) and _team_matches(home_new, home_ex):
                return existing_matchup

        return matchup

    def _add_to_side_counter(self, sport, matchup, pick_type, pick_text, weight=1):
        """Add a pick to the side-based counter"""
        matchup = self._normalize_matchup(matchup)
        matchup = self._find_canonical_matchup(sport, matchup)
        side_label, display_line = self._extract_side(pick_text, pick_type, matchup)
        side_key = f"{sport}|{matchup}|{side_label}"
        self.side_counter[side_key] += weight
        self.side_lines[side_key][display_line] += weight
        self.side_type[side_key] = pick_type

    # Minimum pick count thresholds per sport for public consensus.
    # NHL gets far fewer public picks (~30-100 per game) compared to
    # NBA (~100-200) or NCAAB (~200-500), so a universal threshold of 50
    # filters out most NHL games. Sport-specific thresholds fix this.
    MIN_PICKS_THRESHOLD = {
        'nhl': 10,
        'nfl': 20,
        'nba': 30,
        'ncaab': 30,
        'ncaaf': 20,
    }

    # Known mascot words. Stripping these from img alt names like
    # "Calgary Flames Picks" -> "Calgary" to match expert pick names.
    # This list covers ALL major pro teams and common college mascots.
    # Missing an entry is safe - _find_canonical_matchup does fuzzy dedup.
    _MASCOTS_SINGLE = {
        # NHL
        'ducks', 'bruins', 'sabres', 'flames', 'hurricanes', 'blackhawks',
        'avalanche', 'stars', 'oilers', 'panthers', 'kings', 'wild',
        'canadiens', 'predators', 'devils', 'islanders', 'rangers',
        'senators', 'flyers', 'penguins', 'sharks', 'kraken', 'blues',
        'lightning', 'canucks', 'jets', 'capitals', 'mammoth',
        # NBA
        'hawks', 'celtics', 'nets', 'hornets', 'bulls', 'cavaliers',
        'mavericks', 'nuggets', 'pistons', 'warriors', 'rockets', 'pacers',
        'clippers', 'lakers', 'grizzlies', 'heat', 'bucks', 'timberwolves',
        'pelicans', 'knicks', 'thunder', 'magic', '76ers', 'suns', 'kings',
        'spurs', 'raptors', 'jazz', 'wizards',
        # NFL
        'cardinals', 'falcons', 'ravens', 'bills', 'bengals', 'browns',
        'cowboys', 'broncos', 'lions', 'packers', 'texans', 'colts',
        'jaguars', 'chiefs', 'chargers', 'rams', 'dolphins', 'vikings',
        'patriots', 'saints', 'giants', 'eagles', 'steelers', '49ers',
        'seahawks', 'buccaneers', 'titans', 'commanders',
        # MLB
        'diamondbacks', 'braves', 'orioles', 'cubs', 'reds', 'guardians',
        'rockies', 'tigers', 'astros', 'royals', 'angels', 'dodgers',
        'marlins', 'brewers', 'twins', 'mets', 'yankees', 'athletics',
        'phillies', 'pirates', 'padres', 'mariners', 'rays', 'rangers',
        'nationals', 'reds',
        # Common college mascots (covers most Covers.com entries)
        'wildcats', 'bulldogs', 'eagles', 'tigers', 'bears', 'cougars',
        'huskies', 'spartans', 'wolverines', 'gators', 'sooners',
        'longhorns', 'aggies', 'seminoles', 'volunteers', 'rebels',
        'crimson', 'hoosiers', 'jayhawks', 'mountaineers', 'wolfpack',
        'demon', 'deacons', 'owls', 'friars', 'redbirds', 'salukis',
        'colonials', 'vaqueros', 'camels', 'gaels', 'broncos', 'raiders',
        'norse', 'titans', 'hawks', 'trojans', 'paladins', 'hornets',
        'braves', 'beavers', 'dons', 'toreros', 'musketeers', 'bluejays',
        'billikens', 'bonnies', 'explorers', 'peacocks', 'bobcats',
        'terriers', 'catamounts', 'retrievers', 'spiders', 'monarchs',
        'dukes', 'phoenix', 'anteaters', 'matadors', 'roadrunners',
    }
    _MASCOTS_MULTI = {
        'blue jackets', 'red wings', 'trail blazers', 'maple leafs',
        'golden knights', 'red sox', 'white sox', 'blue jays',
        'blue devils', 'yellow jackets', 'tar heels', 'nittany lions',
        'golden eagles', 'golden bears', 'golden flashes', 'mean green',
        'scarlet knights', 'red raiders', 'fighting irish', 'fighting illini',
        'fighting camels', 'red foxes', 'blue raiders', 'blue hens',
        'black bears', 'golden gophers', 'golden hurricane', 'running rebels',
        'delta devils', 'purple aces', 'beach riders',
    }

    def _strip_mascot(self, full_name):
        """Strip mascot/nickname from a team's full name extracted from img alt.
        'Calgary Flames' -> 'Calgary', 'Weber St. Wildcats' -> 'Weber St.'
        Leaves name unchanged if stripping would make it too short."""
        words = full_name.split()
        if len(words) <= 1:
            return full_name

        # Check multi-word mascots first (last 2 words)
        if len(words) >= 3:
            last_two = ' '.join(words[-2:]).lower()
            if last_two in self._MASCOTS_MULTI:
                return ' '.join(words[:-2])

        # Check single-word mascot (last word)
        if words[-1].lower() in self._MASCOTS_SINGLE:
            result = ' '.join(words[:-1])
            # Don't strip if result is too short (e.g., "NY" from "NY Rangers")
            if len(result) >= 3:
                return result

        return full_name

    def _extract_teams_from_cell(self, cell, sport_code):
        """Extract full team names from a matchup cell using img alt attributes.
        The Covers.com HTML has <img alt='Weber St. Wildcats Picks'> which contains
        the FULL team name. This is permanent - no abbreviation dictionary needed.
        Falls back to parse_matchup() if img alts aren't found."""
        imgs = cell.find_all('img', class_='covers-CoversConsensus-mainLogo')
        team_names = []
        for img in imgs:
            alt = img.get('alt', '')
            if alt:
                # Strip " Picks" suffix: "Weber St. Wildcats Picks" -> "Weber St. Wildcats"
                name = re.sub(r'\s+Picks$', '', alt).strip()
                # Strip mascot: "Weber St. Wildcats" -> "Weber St."
                name = self._strip_mascot(name)
                team_names.append(name)

        if len(team_names) >= 2:
            away = self._normalize_profile_team(team_names[0])
            home = self._normalize_profile_team(team_names[1])
            matchup = f"{away} @ {home}"
            return self._normalize_matchup(matchup)

        # Fallback: parse from compressed text
        matchup_raw = cell.get_text(strip=True)
        return self.parse_matchup(matchup_raw, sport_code)

    def scrape_public_consensus(self, sport_code):
        """Scrape public consensus data from Covers.com topconsensus pages.
        Uses img alt attributes for team names (permanent fix - no dictionary needed).
        This provides ADDITIONAL data beyond King of Covers contestants."""
        sport_name = self.sports.get(sport_code, sport_code)
        print(f"\n  Fetching {sport_name} public consensus...")

        picks_added = 0
        min_picks = self.MIN_PICKS_THRESHOLD.get(sport_code, 30)

        # Scrape SIDES (spread/ML) consensus
        try:
            sides_url = f"https://contests.covers.com/consensus/topconsensus/{sport_code}/overall"
            response = self.session.get(sides_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table', class_='responsive')
            if table:
                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        # Extract team names from img alt attributes (PERMANENT FIX)
                        matchup = self._extract_teams_from_cell(cells[0], sport_code)

                        consensus_raw = cells[2].get_text(strip=True)
                        sides_raw = cells[3].get_text(strip=True)

                        # Parse consensus percentages (e.g., "45%55%" -> [45, 55])
                        pcts = re.findall(r'(\d+)%', consensus_raw)
                        if len(pcts) >= 2:
                            pct1, pct2 = int(pcts[0]), int(pcts[1])

                            # Parse pick counts - use separator for <br/> tags (e.g., "201<br/>307")
                            picks_text = cells[4].get_text(separator='|', strip=True)
                            pick_counts = re.findall(r'(\d+)', picks_text)
                            if len(pick_counts) >= 2:
                                count1, count2 = int(pick_counts[0]), int(pick_counts[1])

                                # Parse sides (e.g., "+113-116" or "+8.5-8.5")
                                sides_parts = re.findall(r'([+-]\d+\.?\d*)', sides_raw)
                                if len(sides_parts) >= 2:
                                    # Extract team names from matchup (e.g., "Detroit @ Boston")
                                    teams = matchup.split(' @ ')
                                    away_team = teams[0].strip() if len(teams) >= 1 else "Away"
                                    home_team = teams[1].strip() if len(teams) >= 2 else "Home"

                                    # Determine pick type based on value
                                    # Moneylines are typically >= 100, spreads < 100
                                    val1 = abs(float(sides_parts[0]))
                                    val2 = abs(float(sides_parts[1]))

                                    # Use percentage-based weight instead of count//20
                                    weight1 = self._consensus_weight(pct1)
                                    weight2 = self._consensus_weight(pct2)

                                    # Add picks if enough consensus (sport-specific threshold)
                                    if count1 >= min_picks:
                                        if val1 >= 100:
                                            pick_type1 = 'Moneyline'
                                            pick_text1 = f"{away_team} ML ({sides_parts[0]})"
                                        else:
                                            pick_type1 = 'Spread (ATS)'
                                            pick_text1 = f"{away_team} {sides_parts[0]}"
                                        self._add_to_side_counter(sport_name, matchup, pick_type1, pick_text1, weight1)
                                        picks_added += 1

                                    if count2 >= min_picks:
                                        if val2 >= 100:
                                            pick_type2 = 'Moneyline'
                                            pick_text2 = f"{home_team} ML ({sides_parts[1]})"
                                        else:
                                            pick_type2 = 'Spread (ATS)'
                                            pick_text2 = f"{home_team} {sides_parts[1]}"
                                        self._add_to_side_counter(sport_name, matchup, pick_type2, pick_text2, weight2)
                                        picks_added += 1
        except Exception as e:
            print(f"    Error scraping sides: {e}")

        # Scrape TOTALS (over/under) consensus
        try:
            totals_url = f"https://contests.covers.com/consensus/topoverunderconsensus/{sport_code}/overall"
            response = self.session.get(totals_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table', class_='responsive')
            if table:
                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        # Extract team names from img alt attributes (PERMANENT FIX)
                        matchup = self._extract_teams_from_cell(cells[0], sport_code)

                        # Read the total line (e.g., "5.5", "223")
                        # Try cells[1] first, but validate the number is reasonable
                        total_line = ''
                        for cell_idx in [1, 2, 3]:
                            if cell_idx < len(cells):
                                cell_text = cells[cell_idx].get_text(strip=True)
                                total_match = re.search(r'^(\d+\.?\d*)$', cell_text.strip())
                                if total_match:
                                    val = float(total_match.group(1))
                                    # Sanity check: totals should be reasonable per sport
                                    # NHL: 3-9, NBA: 190-260, NCAAB: 110-180, NFL: 30-60
                                    if val < 500:  # No sport has a total over 500
                                        total_line = total_match.group(1)
                                        break
                        if not total_line:
                            # Fallback: extract first reasonable number from cells[1]
                            total_line_raw = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            total_line_match = re.search(r'(\d+\.?\d*)', total_line_raw)
                            if total_line_match:
                                val = float(total_line_match.group(1))
                                if val < 500:
                                    total_line = total_line_match.group(1)

                        # Read consensus percentages from this row
                        consensus_raw = cells[2].get_text(strip=True) if len(cells) > 2 else ''

                        # Parse "73 % Over27 % Under" format
                        over_match = re.search(r'(\d+)\s*%\s*Over', consensus_raw)
                        under_match = re.search(r'(\d+)\s*%\s*Under', consensus_raw)

                        if over_match and under_match:
                            over_pct = int(over_match.group(1))
                            under_pct = int(under_match.group(1))

                            # Parse pick counts - use separator for <br/> tags
                            picks_text = cells[4].get_text(separator='|', strip=True)
                            pick_counts = re.findall(r'(\d+)', picks_text)
                            if len(pick_counts) >= 2:
                                over_count, under_count = int(pick_counts[0]), int(pick_counts[1])

                                # Add Over picks if significant (sport-specific threshold)
                                if over_count >= min_picks:
                                    over_weight = self._consensus_weight(over_pct)
                                    pick_text_over = f"Over {total_line}"
                                    self._add_to_side_counter(sport_name, matchup, 'Total (Over)', pick_text_over, over_weight)
                                    picks_added += 1

                                # Add Under picks if significant
                                if under_count >= min_picks:
                                    under_weight = self._consensus_weight(under_pct)
                                    pick_text_under = f"Under {total_line}"
                                    self._add_to_side_counter(sport_name, matchup, 'Total (Under)', pick_text_under, under_weight)
                                    picks_added += 1
        except Exception as e:
            print(f"    Error scraping totals: {e}")

        print(f"    Added {picks_added} public consensus picks")
        return picks_added

    # Common abbreviated team names from Covers.com profile pages
    # Maps "profile name" -> "full name" to prevent duplicate matchups
    PROFILE_TEAM_NORMALIZE = {
        'Murray St.': 'Murray State', 'Michigan St.': 'Michigan State',
        'Oklahoma St.': 'Oklahoma State', 'Oregon St.': 'Oregon State',
        'Arizona St.': 'Arizona State', 'Boise St.': 'Boise State',
        'Colorado St.': 'Colorado State', 'Fresno St.': 'Fresno State',
        'Iowa St.': 'Iowa State', 'Kansas St.': 'Kansas State',
        'Kent St.': 'Kent State', 'Mississippi St.': 'Mississippi State',
        'Penn St.': 'Penn State', 'Ohio St.': 'Ohio State',
        'San Diego St.': 'San Diego State', 'San Jose St.': 'San Jose State',
        'Washington St.': 'Washington State', 'Wichita St.': 'Wichita State',
        'Ball St.': 'Ball State', 'Appalachian St.': 'Appalachian State',
        'N. Dakota St.': 'North Dakota State', 'S. Dakota St.': 'South Dakota State',
        'Southern IL': 'Southern Illinois', 'Northern IL': 'Northern Illinois',
        'E. Michigan': 'Eastern Michigan', 'W. Michigan': 'Western Michigan',
        'C. Michigan': 'Central Michigan', 'N. Illinois': 'Northern Illinois',
        'S. Illinois': 'Southern Illinois', 'E. Kentucky': 'Eastern Kentucky',
        'W. Kentucky': 'Western Kentucky', 'N. Carolina': 'North Carolina',
        'S. Carolina': 'South Carolina', 'N. Texas': 'North Texas',
        'W. Virginia': 'West Virginia',
        'G. Washington': 'George Washington', 'G. Mason': 'George Mason',
        # Common abbreviated forms from Covers pending picks pages
        'N. Kentucky': 'Northern Kentucky', 'Northern KY': 'Northern Kentucky',
        'N. Colorado': 'Northern Colorado', 'Northern CO': 'Northern Colorado',
        'E. Washington': 'Eastern Washington', 'Eastern WA': 'Eastern Washington',
        'Weber St.': 'Weber State', 'Wright St.': 'Wright State',
        'Alcorn St.': 'Alcorn State', 'Detroit Mercy': 'Detroit Mercy',
        'Monmouth-NJ': 'Monmouth',
        'TX R-G Valley': 'UT Rio Grande Valley',
        'Texas R-G Valley': 'UT Rio Grande Valley',
        'Miss Valley St.': 'Mississippi Valley State',
        'Grambling St.': 'Grambling',
        'Alabama St.': 'Alabama State',
        'Morehead St.': 'Morehead State',
        'Norfolk St.': 'Norfolk State',
        'Coppin St.': 'Coppin State',
        'Morgan St.': 'Morgan State',
        'NC A&T': 'NC A&T',
        'Sam Houston St.': 'Sam Houston',
    }

    def _normalize_profile_team(self, name):
        """Normalize a team name from a Covers.com contestant profile.
        Handles abbreviated forms like 'Northern KY', 'Wright St.', etc."""
        # Direct mapping
        normalized = self.PROFILE_TEAM_NORMALIZE.get(name)
        if normalized:
            return normalized
        # Try removing trailing period from abbreviated names
        if name.endswith('.'):
            no_dot = name[:-1]
            normalized = self.PROFILE_TEAM_NORMALIZE.get(no_dot + '.')
            if normalized:
                return normalized

        # Handle common abbreviated state/region suffixes
        # "Northern KY" -> "Northern Kentucky", "Wright St." -> "Wright State", etc.
        _STATE_ABBREVS = {
            'KY': 'Kentucky', 'OH': 'Ohio', 'FL': 'Florida',
            'IL': 'Illinois', 'IN': 'Indiana', 'WA': 'Washington',
            'CO': 'Colorado', 'PA': 'Pennsylvania', 'VA': 'Virginia',
            'NC': 'North Carolina', 'SC': 'South Carolina',
            'MO': 'Missouri', 'TX': 'Texas', 'TN': 'Tennessee',
            'AL': 'Alabama', 'GA': 'Georgia', 'LA': 'Louisiana',
            'MI': 'Michigan', 'MN': 'Minnesota', 'WI': 'Wisconsin',
            'NJ': 'New Jersey', 'CT': 'Connecticut', 'MD': 'Maryland',
            'MS': 'Mississippi', 'AR': 'Arkansas', 'AZ': 'Arizona',
            'NM': 'New Mexico', 'MT': 'Montana', 'ND': 'North Dakota',
            'SD': 'South Dakota', 'NE': 'Nebraska', 'IA': 'Iowa',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'UT': 'Utah',
            'NV': 'Nevada', 'ID': 'Idaho', 'WY': 'Wyoming',
            'HI': 'Hawaii', 'ME': 'Maine', 'NH': 'New Hampshire',
            'VT': 'Vermont', 'RI': 'Rhode Island', 'DE': 'Delaware',
            'KS': 'Kansas', 'WV': 'West Virginia',
        }
        parts = name.rsplit(' ', 1)
        if len(parts) == 2:
            prefix, suffix = parts
            # "Northern KY" -> "Northern Kentucky"
            if suffix in _STATE_ABBREVS:
                return f"{prefix} {_STATE_ABBREVS[suffix]}"
            # "Wright St." -> "Wright State"
            if suffix == 'St.' or suffix == 'St':
                return f"{prefix} State"

        return name

    # Known hyphenated abbreviations from Covers.com
    # These must be replaced BEFORE the [A-Z][a-z]+ regex split
    HYPHENATED_ABBREVS = {
        'M-Oh': 'Mioh',   # Miami (OH)
        'W-Ky': 'Wky',    # Western Kentucky
        'E-Ky': 'Eky',    # Eastern Kentucky
        'W-Mi': 'Wmu',    # Western Michigan
        'E-Mi': 'Emic',   # Eastern Michigan
        'C-Mi': 'Cent',   # Central Michigan
        'N-Il': 'Noil',   # Northern Illinois
        'S-Il': 'Siu',    # Southern Illinois
    }

    # Multi-word team names that the [A-Z][a-z]+ regex would split incorrectly
    # These get collapsed to a single token BEFORE the regex split
    MULTIWORD_COLLAPSE = {
        'GreenBay': 'Grnby',      # Green Bay -> single token
        'SanDiego': 'Sdgo',       # San Diego State
        'SanJose': 'Sjsu',        # San Jose State
        'SanFrancisco': 'Sfpa',   # San Francisco
        'SanAntonio': 'Sa',       # San Antonio
        'NewYork': 'Ny',          # New York
        'NewOrleans': 'No',       # New Orleans
        'NewMexico': 'Nmex',      # New Mexico
        'LongBeach': 'Lbsu',      # Long Beach State
        'OklahomaCity': 'Okc',    # Oklahoma City
        'LosAngeles': 'La',       # Los Angeles
        'TampaBay': 'Tb',         # Tampa Bay
        'LasVegas': 'Lv',         # Las Vegas
        'GeorgeMason': 'Gmu',     # George Mason
        'GeorgeWashington': 'Gw', # George Washington
    }

    def parse_matchup(self, raw, sport_code):
        """Parse matchup from compressed format like 'NHLDetBos' to 'Detroit @ Boston'"""
        raw = re.sub(r'^(NHL|NBA|NFL|NCAAB|NCAAF)', '', raw, flags=re.IGNORECASE)

        # Handle hyphenated abbreviations before regex split
        for hyph, replacement in self.HYPHENATED_ABBREVS.items():
            raw = raw.replace(hyph, replacement)

        # Collapse multi-word team names into single tokens before regex split
        for multi, single in self.MULTIWORD_COLLAPSE.items():
            raw = raw.replace(multi, single)

        teams = {
            # NHL
            'Ana': 'Anaheim', 'Ari': 'Arizona', 'Bos': 'Boston', 'Buf': 'Buffalo',
            'Cgy': 'Calgary', 'Cal': 'California', 'Car': 'Carolina', 'Chi': 'Chicago',
            'Col': 'Colorado', 'Clb': 'Columbus', 'Dal': 'Dallas', 'Det': 'Detroit',
            'Edm': 'Edmonton', 'Fla': 'Florida', 'La': 'Los Angeles', 'Min': 'Minnesota',
            'Mon': 'Montreal', 'Mtl': 'Montreal', 'Nsh': 'Nashville', 'Nj': 'New Jersey',
            'Nyi': 'NY Islanders', 'Nyr': 'NY Rangers', 'Ott': 'Ottawa', 'Phi': 'Philadelphia',
            'Pit': 'Pittsburgh', 'Sj': 'San Jose', 'Sea': 'Seattle', 'Stl': 'St. Louis',
            'Tb': 'Tampa Bay', 'Tor': 'Toronto', 'Utah': 'Utah', 'Van': 'Vancouver',
            'Veg': 'Vegas', 'Vgk': 'Vegas', 'Win': 'Winthrop', 'Was': 'Washington', 'Wpg': 'Winnipeg',
            # NBA
            'Atl': 'Atlanta', 'Bkn': 'Brooklyn', 'Bk': 'Brooklyn', 'Cha': 'Charlotte',
            'Cle': 'Cleveland', 'Den': 'Denver', 'Gsw': 'Golden State', 'Gs': 'Golden State',
            'Hou': 'Houston', 'Ind': 'Indiana', 'Lac': 'L.A. Clippers', 'Lal': 'L.A. Lakers',
            'Mem': 'Memphis', 'Mia': 'Miami', 'Mil': 'Milwaukee', 'No': 'New Orleans',
            'Ny': 'New York', 'Okc': 'Oklahoma City', 'Orl': 'Orlando', 'Phx': 'Phoenix',
            'Pho': 'Phoenix', 'Por': 'Portland', 'Sac': 'Sacramento', 'Sa': 'San Antonio',
            'Uta': 'Utah',
            # NFL
            'Arz': 'Arizona', 'Bal': 'Baltimore', 'Cin': 'Cincinnati', 'Gb': 'Green Bay',
            'Jax': 'Jacksonville', 'Kc': 'Kansas City', 'Lv': 'Las Vegas', 'Lar': 'L.A. Rams',
            'Ne': 'New England', 'Nyg': 'NY Giants', 'Nyj': 'NY Jets', 'Sf': 'San Francisco',
            'Ten': 'Tennessee',
            # NCAAB / NCAAF - Covers.com abbreviations
            'Alab': 'Alabama', 'Ala': 'Alabama', 'Alb': 'Albany',
            'Alst': 'Alabama State', 'Amec': 'American',
            'Apst': 'Appalachian State', 'Ariz': 'Arizona', 'Arst': 'Arizona State',
            'Ark': 'Arkansas', 'Arks': 'Arkansas State', 'Army': 'Army',
            'Aub': 'Auburn', 'Ball': 'Ball State', 'Bay': 'Baylor',
            'Bel': 'Belmont', 'Bgr': 'Bowling Green', 'Bois': 'Boise State',
            'Brad': 'Bradley', 'Brwn': 'Brown', 'Brya': 'Bryant', 'Bry': 'Bryant',
            'Buck': 'Bucknell', 'Butl': 'Butler', 'Byu': 'BYU',
            'Camp': 'Campbell', 'Cani': 'Canisius',
            'Cent': 'Central Michigan', 'Char': 'Charlotte', 'Chat': 'Chattanooga',
            'Chso': 'Charleston Southern', 'Cinn': 'Cincinnati', 'Cit': 'The Citadel',
            'Clem': 'Clemson', 'Clev': 'Cleveland State', 'Coas': 'Coastal Carolina',
            'Colg': 'Colgate', 'Conn': 'UConn', 'Cop': 'Coppin State',
            'Corn': 'Cornell', 'Crei': 'Creighton', 'Dart': 'Dartmouth',
            'Dav': 'Davidson', 'Day': 'Dayton', 'Dela': 'Delaware',
            'Depa': 'DePaul', 'Drke': 'Drake', 'Drew': 'Drew', 'Drex': 'Drexel',
            'Duke': 'Duke', 'Duqu': 'Duquesne', 'Ecar': 'East Carolina',
            'Eill': 'Eastern Illinois', 'Eky': 'Eastern Kentucky',
            'Emic': 'Eastern Michigan', 'Ewas': 'Eastern Washington',
            'Elon': 'Elon', 'Evan': 'Evansville', 'Fair': 'Fairfield',
            'Fdu': 'FDU', 'Flor': 'Florida', 'Flat': 'Florida Atlantic',
            'Flin': 'Florida International', 'Flst': 'Florida State',
            'Ford': 'Fordham', 'Fres': 'Fresno State', 'Furl': 'Furman',
            'Gema': 'George Mason', 'Gewa': 'George Washington',
            'Geto': 'Georgetown', 'Gast': 'Georgia State', 'Gate': 'Georgia Tech',
            'Ga': 'Georgia', 'Gonz': 'Gonzaga',
            'Gram': 'Grambling', 'Harv': 'Harvard', 'Haw': 'Hawaii',
            'Hart': 'Hartford', 'Hofs': 'Hofstra', 'Hocr': 'Holy Cross',
            'Hous': 'Houston', 'How': 'Howard', 'Idah': 'Idaho',
            'Idst': 'Idaho State', 'Il': 'Illinois', 'Ill': 'Illinois',
            'Ilst': 'Illinois State', 'Inch': 'Incarnate Word',
            'Iowa': 'Iowa', 'Iost': 'Iowa State',
            'Iupui': 'IUPUI', 'Jkst': 'Jackson State',
            'Jmu': 'James Madison', 'Kans': 'Kansas', 'Knst': 'Kansas State',
            'Kent': 'Kent State', 'Ken': 'Kentucky', 'Laf': 'Lafayette',
            'Lam': 'Lamar', 'Lasa': 'La Salle', 'Lehi': 'Lehigh',
            'Lib': 'Liberty', 'Lips': 'Lipscomb',
            'Liub': 'LIU Brooklyn', 'Long': 'Long Beach State',
            'Lou': 'Louisville', 'Loyt': 'Loyola Chicago',
            'Loym': 'Loyola Marymount', 'Lsu': 'LSU', 'Main': 'Maine',
            'Manh': 'Manhattan', 'Mari': 'Marist', 'Marq': 'Marquette',
            'Mars': 'Marshall', 'Mary': 'Maryland', 'Massl': 'UMass Lowell',
            'Mass': 'UMass', 'Mcne': 'McNeese', 'Memp': 'Memphis',
            'Merc': 'Mercer', 'Mich': 'Michigan', 'Mist': 'Michigan State',
            'Mioh': 'Miami (OH)', 'Miss': 'Ole Miss', 'Msst': 'Mississippi State', 'Msu': 'Michigan State',
            'Mist': 'Michigan State', 'Mo': 'Missouri', 'Most': 'Missouri State',
            'Mona': 'Monmouth', 'Mont': 'Montana', 'Mnst': 'Montana State',
            'More': 'Morehead State', 'Morg': 'Morgan State',
            'Murr': 'Murray State', 'Navy': 'Navy',
            'Neb': 'Nebraska', 'Nev': 'Nevada', 'Niag': 'Niagara',
            'Nich': 'Nicholls', 'Njit': 'NJIT',
            'Nmex': 'New Mexico', 'Nmst': 'New Mexico State',
            'Norf': 'Norfolk State', 'Noal': 'North Alabama',
            'Nc': 'North Carolina', 'Ncat': 'NC A&T', 'Nccu': 'NC Central',
            'Ncst': 'NC State', 'Ndak': 'North Dakota', 'Ndst': 'North Dakota State',
            'Nofl': 'North Florida', 'Ntex': 'North Texas',
            'Neoh': 'Northeast Ohio', 'Noil': 'Northern Illinois',
            'Niow': 'Northern Iowa', 'Nky': 'Northern Kentucky',
            'Nwes': 'Northwestern', 'Nwst': 'Northwestern State',
            'Notr': 'Notre Dame', 'Oak': 'Oakland', 'Ohio': 'Ohio',
            'Ohst': 'Ohio State', 'Okla': 'Oklahoma', 'Okst': 'Oklahoma State',
            'Oldm': 'Old Dominion', 'Oreg': 'Oregon', 'Orst': 'Oregon State',
            'Pac': 'Pacific', 'Penn': 'Penn', 'Pnst': 'Penn State',
            'Pepp': 'Pepperdine', 'Port': 'Portland',
            'Prv': 'Providence', 'Purd': 'Purdue',
            'Quin': 'Quinnipiac', 'Radf': 'Radford', 'Rice': 'Rice',
            'Rich': 'Richmond', 'Ride': 'Rider', 'Robe': 'Robert Morris',
            'Rutg': 'Rutgers', 'Sacr': 'Sacramento State',
            'Shll': 'Seton Hall', 'Shu': 'Sacred Heart',
            'Sjsu': 'San Jose State', 'Sju': "St. John's",
            'Slou': 'Saint Louis', 'Smar': "Saint Mary's",
            'Sbon': 'St. Bonaventure', 'Stjo': "St. Joseph's",
            'Smu': 'SMU', 'Sdst': 'South Dakota State', 'Sdak': 'South Dakota',
            'Sfla': 'South Florida', 'Scar': 'South Carolina',
            'Scst': 'SC State', 'Sela': 'SE Louisiana', 'Semo': 'Southeast Missouri',
            'Siue': 'SIU Edwardsville', 'Siu': 'Southern Illinois',
            'Smis': 'Southern Miss', 'Sout': 'Southern',
            'Stan': 'Stanford', 'Step': 'Stephen F. Austin',
            'Sten': 'Stetson', 'Ston': 'Stony Brook', 'Syra': 'Syracuse',
            'Tcu': 'TCU', 'Temp': 'Temple', 'Tenn': 'Tennessee',
            'Tnst': 'Tennessee State', 'Tntc': 'Tennessee Tech',
            'Tex': 'Texas', 'Txam': 'Texas A&M', 'Txar': 'UT Arlington',
            'Txch': 'Texas Tech', 'Txso': 'Texas Southern', 'Txst': 'Texas State',
            'Tols': 'Toledo', 'Town': 'Towson', 'Troy': 'Troy',
            'Tuln': 'Tulane', 'Tuls': 'Tulsa', 'Uab': 'UAB',
            'Ucf': 'UCF', 'Ucla': 'UCLA', 'Uic': 'UIC',
            'Unc': 'North Carolina', 'Uncg': 'UNC Greensboro',
            'Unca': 'UNC Asheville', 'Uncw': 'UNC Wilmington',
            'Uni': 'Northern Iowa', 'Unlv': 'UNLV',
            'Utep': 'UTEP', 'Utsa': 'UTSA',
            'Valp': 'Valparaiso', 'Vand': 'Vanderbilt', 'Van': 'Vanderbilt',
            'Vcu': 'VCU', 'Vill': 'Villanova', 'Virg': 'Virginia',
            'Vtec': 'Virginia Tech', 'Vmi': 'VMI',
            'Wag': 'Wagner', 'Wake': 'Wake Forest',
            'Wash': 'Washington', 'Wast': 'Washington State',
            'Webb': 'Weber State', 'West': 'West Virginia', 'Wisc': 'Wisconsin',
            'Wof': 'Wofford', 'Wrst': 'Wright State', 'Wyo': 'Wyoming',
            'Uk': 'Kentucky', 'Ky': 'Kentucky',
            'Xav': 'Xavier', 'Yale': 'Yale', 'Yosu': 'Youngstown State',
            # Additional Covers.com abbreviations (shorter forms used on consensus pages)
            'Akr': 'Akron', 'App': 'Appalachian State', 'Can': 'Canisius',
            'Ccar': 'Coastal Carolina', 'Clmb': 'Columbia', 'Cor': 'Cornell',
            'Gaso': 'Georgia Southern', 'Gw': 'George Washington',
            'Iona': 'Iona', 'Isu': 'Iowa State', 'Ku': 'Kansas',
            'Man': 'Manhattan', 'Mrsh': 'Marshall', 'Msm': "Mount St. Mary's",
            'Mw': 'Merrimack', 'Odu': 'Old Dominion', 'Oh': 'Ohio',
            'Prin': 'Princeton', 'Rid': 'Rider', 'Sie': 'Siena',
            'Spc': "St. Peter's", 'Ttu': 'Texas Tech', 'Ull': 'Louisiana',
            'Ulm': 'UL Monroe', 'Usa': 'South Alabama', 'Usm': 'Southern Miss',
            'Uva': 'Virginia', 'Wmu': 'Western Michigan', 'Mioh': 'Miami (OH)',
            'Wky': 'Western Kentucky', 'Stet': 'Stetson', 'Sfa': 'Stephen F. Austin',
            'Hamp': 'Hampton', 'Norf': 'Norfolk State', 'Prv': 'Providence',
            'High': 'High Point', 'Loy': 'Loyola Chicago', 'Sfpa': 'San Francisco',
            'Rmu': 'Robert Morris', 'Sac': 'Sacramento State',
            'Wint': 'Winthrop', 'Ncat': 'NC A&T', 'Gard': 'Gardner-Webb',
            'Stet': 'Stetson', 'Tol': 'Toledo', 'Buff': 'Buffalo',
            'Emu': 'Eastern Michigan', 'Cmu': 'Central Michigan',
            'Niu': 'Northern Illinois', 'Wiu': 'Western Illinois',
            'Sam': 'Sam Houston', 'Lam': 'Lamar', 'Nwst': 'Northwestern State',
            'Sela': 'SE Louisiana', 'Mcn': 'McNeese', 'Nic': 'Nicholls',
            'Abil': 'Abilene Christian', 'Tar': 'Tarleton State',
            'Utrgv': 'UT Rio Grande Valley', 'Siu': 'Southern Illinois',
            # Added March 6, 2026 - from WARN output
            'Hp': 'High Point', 'Pre': 'Presbyterian', 'Rad': 'Radford',
            'Sdsu': 'San Diego State', 'Mizz': 'Missouri',
            'Neom': 'Nebraska Omaha', 'Fgcu': 'Florida Gulf Coast',
            'Lip': 'Lipscomb', 'Wsu': 'Wichita State',
            'Hall': 'Seton Hall', 'Bell': 'Bellarmine',
            'Cark': 'Central Arkansas', 'Und': 'North Dakota',
            'Bgsu': 'Bowling Green', 'Wvu': 'West Virginia',
            # Added March 7, 2026 - NHL missing
            'Nas': 'Nashville',
            # Added March 7, 2026 - NCAAB missing abbreviations from WARN output
            'Idho': 'Idaho', 'Nau': 'Northern Arizona', 'Tows': 'Towson',
            'Las': 'La Salle', 'Joes': "Saint Joseph's",
            'Wis': 'Wisconsin', 'Pur': 'Purdue', 'Nw': 'Northwestern',
            'Minn': 'Minnesota', 'Alby': 'Albany',
            'Csb': 'Cal State Bakersfield', 'Cp': 'Cal Poly',
            'Wm': 'William & Mary', 'Gt': 'Georgia Tech',
            'Lbsu': 'Long Beach State', 'Wcu': 'Western Carolina',
            'Mer': 'Mercer', 'Bsu': 'Boise State', 'Csu': 'Colorado State',
            'Fau': 'Florida Atlantic', 'Wich': 'Wichita State',
            'Colo': 'Colorado', 'Unh': 'New Hampshire',
            'Umbc': 'UMBC', 'Etsu': 'East Tennessee State',
            'Csf': 'Cal State Fullerton', 'Csn': 'Cal State Northridge',
            'Vt': 'Virginia Tech', 'Lt': 'Louisiana Tech',
            'Del': 'Delaware', 'Uvm': 'Vermont',
            'Stone': 'Stonehill', 'Mehst': 'Morgan State',
            'Ore': 'Oregon', 'Uri': 'Rhode Island',
            'For': 'Fordham', 'Osu': 'Ohio State', 'Fur': 'Furman',
            'Me': 'Maine', 'Uga': 'Georgia', 'Ndsu': 'North Dakota State',
            'Mrst': 'Marist', 'But': 'Butler', 'Dep': 'DePaul',
            'Kenn': 'Kennesaw State', 'Nmsu': 'New Mexico State',
            'Prov': 'Providence', 'Gtwn': 'Georgetown',
            # Added March 8, 2026 - NCAAB missing abbreviations from WARN output
            'Bu': 'Boston University', 'Cofc': 'College of Charleston',
            'Nku': 'Northern Kentucky', 'Usf': 'South Florida',
            'Hbu': 'Houston Christian', 'Uno': 'New Orleans',
            'Tem': 'Temple', 'Tlsa': 'Tulsa', 'Md': 'Maryland',
            'Ecu': 'East Carolina', 'Psu': 'Penn State',
            'Mtst': 'Montana State', 'Leh': 'Lehigh',
            'Monm': 'Monmouth',
            'Usc': 'USC', 'Asu': 'Arizona State',
            'Ac': 'Abilene Christian', 'Liu': 'LIU',
            'Afa': 'Air Force', 'Slu': 'Saint Louis',
            'Gmu': 'George Mason', 'Duq': 'Duquesne',
            'Pitt': 'Pittsburgh', 'Syr': 'Syracuse',
            'Ksu': 'Kansas State', 'Cbu': 'Cal Baptist',
            'Suu': 'Southern Utah', 'Unm': 'New Mexico',
            'Usu': 'Utah State', 'Uvu': 'Utah Valley',
            'Utech': 'Utah Tech', 'Fsu': 'Florida State',
            'Wku': 'Western Kentucky', 'Fiu': 'Florida International',
            'Ucd': 'UC Davis', 'Uci': 'UC Irvine',
            'Shsu': 'Sam Houston', 'Ucsd': 'UC San Diego',
            'Ucsb': 'UC Santa Barbara', 'Jvst': 'Jacksonville State',
            'Gc': 'Grand Canyon', 'Mtu': 'Middle Tennessee',
            'Mosu': 'Morehead State', 'Hof': 'Hofstra',
            # Added March 9, 2026 - missing abbreviations from WARN output
            'Web': 'Weber State', 'Ewu': 'Eastern Washington',
            'Unco': 'Northern Colorado', 'Alcn': 'Alcorn State',
            'Scu': 'Santa Clara', 'Smc': "Saint Mary's",
            'Mvsu': 'Mississippi Valley State',
            'Utrgv': 'UT Rio Grande Valley',
            'Noco': 'Northern Colorado', 'Ncol': 'Northern Colorado',
            'Eku': 'Eastern Kentucky', 'Wiu': 'Western Illinois',
            'Siu': 'Southern Illinois', 'Niu': 'Northern Illinois',
            'Txrv': 'UT Rio Grande Valley',
            # Collapsed multi-word tokens (from MULTIWORD_COLLAPSE pre-processing)
            'Grnby': 'Green Bay', 'Sdgo': 'San Diego', 'Lv': 'Las Vegas',
        }

        # Sport-specific overrides for abbreviation collisions
        # (e.g., "Van" = Vancouver in NHL but Vanderbilt in NCAAB)
        sport_overrides = {
            'nhl': {'Van': 'Vancouver', 'Win': 'Winnipeg', 'Veg': 'Vegas',
                    'Cal': 'Calgary', 'Col': 'Colorado', 'Min': 'Minnesota',
                    'Fla': 'Florida', 'Car': 'Carolina', 'Nas': 'Nashville'},
            'nba': {'Min': 'Minnesota', 'Cha': 'Charlotte', 'Ind': 'Indiana',
                    'Orl': 'Orlando', 'Mil': 'Milwaukee', 'Sac': 'Sacramento'},
        }

        # Also handle multi-character uppercase abbreviations (e.g., 'Utrgv')
        # and single-word teams that might not match [A-Z][a-z]+
        parts = re.findall(r'[A-Z][a-z]+', raw)
        if len(parts) >= 2:
            overrides = sport_overrides.get(sport_code, {})
            away = overrides.get(parts[0]) or teams.get(parts[0], parts[0])
            home = overrides.get(parts[1]) or teams.get(parts[1], parts[1])
            # Warn about unresolved abbreviations so we can add them
            # Skip warning for names that are already valid (e.g., Duke, Yale, Troy)
            known_full_names = {'Duke', 'Yale', 'Penn', 'Troy', 'Rice', 'Navy', 'Army',
                                'Utah', 'Iona', 'Ohio', 'Elon', 'Maine', 'ACU', 'FDU',
                                'SMU', 'UCF', 'BYU', 'LSU', 'TCU', 'USC', 'VCU', 'VMI',
                                'UNLV', 'UTEP', 'UTSA', 'NJIT', 'UAB', 'ORU', 'Iowa'}
            if away == parts[0] and parts[0] not in known_full_names:
                print(f"    [WARN] Unknown team abbreviation: '{parts[0]}' (sport: {sport_code})")
            if home == parts[1] and parts[1] not in known_full_names:
                print(f"    [WARN] Unknown team abbreviation: '{parts[1]}' (sport: {sport_code})")
            return f"{away} @ {home}"

        return raw

    def get_leaderboard_with_picks(self, sport_code, sport_name, max_pages=10, target=50):
        """Fetch leaderboard contestants who have TODAY's pending picks.
        Walks up to max_pages of the leaderboard, checking each contestant
        for today's picks. Stops once we find `target` contestants with picks.
        This matches the proven approach from the v3.1 scraper."""
        print(f"\n  Fetching {sport_name} leaderboard...")
        entries_with_picks = []
        seen_names = set()
        total_checked = 0

        for page in range(1, max_pages + 1):
            try:
                url = f"https://contests.covers.com/consensus/pickleaders/{sport_code}?totalPicks=1&orderPickBy=Overall&orderBy=Units&pageNum={page}"
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                table = soup.find('table')
                if not table:
                    break

                rows = table.find_all('tr')[1:]
                if not rows:
                    break

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    link = cells[1].find('a')
                    if not link:
                        continue

                    name = link.text.strip()
                    if name in seen_names:
                        continue
                    seen_names.add(name)

                    profile_url = link.get('href', '')
                    if not profile_url.startswith('http'):
                        profile_url = 'https://contests.covers.com' + profile_url

                    contestant = {
                        'name': name,
                        'profile_url': profile_url,
                        'sport': sport_name,
                    }

                    # Check if this contestant has today's picks
                    picks = self.get_contestant_picks(contestant, sport_name, sport_code)
                    total_checked += 1
                    time.sleep(0.1)

                    if picks:
                        entries_with_picks.append((contestant, picks))
                        if len(entries_with_picks) >= target:
                            print(f"    Found {target} contestants with picks (checked {total_checked})")
                            return entries_with_picks

                time.sleep(0.2)

            except Exception as e:
                print(f"    Error fetching leaderboard page {page}: {e}")

        print(f"    Found {len(entries_with_picks)} contestants with picks (checked {total_checked})")
        return entries_with_picks

    def get_contestant_picks(self, contestant, sport, sport_code):
        """Get pending picks for a contestant.
        Uses sport-specific pending picks URL and filters to today's date only.
        This prevents cross-sport contamination and stale picks from other days."""
        username = contestant['name']

        # Use sport-specific pending picks URL (NOT the general profile page)
        # The general profile shows ALL sports' picks which causes cross-contamination
        picks_url = f"https://contests.covers.com/kingofcovers/contestant/pendingpicks/{username}/{sport_code}"

        soup = None
        try:
            response = self.session.get(picks_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
        except Exception:
            pass

        # Fallback to general profile URL if sport-specific fails
        if not soup:
            try:
                response = self.session.get(contestant['profile_url'], timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception:
                return []

        # Filter by today's date heading - only extract picks under today's h3
        # Date headings look like "Monday, March 9" - we match on "March 9"
        today_month_day = f"{TODAY.strftime('%B')} {TODAY.day}"
        picks = []
        is_today = False

        for element in soup.find_all(['h3', 'table']):
            if element.name == 'h3':
                heading_text = element.text.strip()
                is_today = today_month_day in heading_text
            elif (element.name == 'table' and
                  'cmg_contests_pendingpicks' in (element.get('class') or [])):
                if not is_today:
                    continue

                # Extract picks from this table (today's picks only)
                for row in element.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    # Extract teams and normalize names
                    teams_text = cells[0].text.strip().split('\n')
                    team_parts = [t.strip() for t in teams_text if t.strip()]
                    away = self._normalize_profile_team(team_parts[0]) if team_parts else ''
                    home = self._normalize_profile_team(team_parts[1]) if len(team_parts) > 1 else ''

                    if not away or not home:
                        continue

                    # Extract picks - get ALL divs and deduplicate
                    picks_cell = cells[3] if len(cells) > 3 else None
                    if not picks_cell:
                        continue

                    pick_divs = picks_cell.find_all('div')
                    pick_texts = []
                    seen_picks = set()

                    for div in pick_divs:
                        pick_text = div.text.strip()
                        if pick_text and pick_text not in seen_picks:
                            pick_texts.append(pick_text)
                            seen_picks.add(pick_text)

                    if not pick_texts:
                        direct_text = picks_cell.get_text(strip=True)
                        if direct_text and len(direct_text) >= 3:
                            pick_texts.append(direct_text)

                    for pick_text in pick_texts:
                        if not pick_text or len(pick_text) < 3:
                            continue

                        pick_lower = pick_text.lower()

                        if 'over' in pick_lower:
                            pick_type = 'Total (Over)'
                        elif 'under' in pick_lower:
                            pick_type = 'Total (Under)'
                        elif '+ml' in pick_lower or '-ml' in pick_lower or 'ml' in pick_lower:
                            pick_type = 'Moneyline'
                        else:
                            ml_pattern = re.search(r'[+-]\d{3,}', pick_text)
                            spread_pattern = re.search(r'[+-]\d+\.5', pick_text)

                            if ml_pattern and not spread_pattern:
                                pick_type = 'Moneyline'
                            elif spread_pattern:
                                pick_type = 'Spread (ATS)'
                            elif '+' in pick_text or '-' in pick_text:
                                num_match = re.search(r'[+-](\d+)', pick_text)
                                if num_match:
                                    num = int(num_match.group(1))
                                    pick_type = 'Moneyline' if num >= 100 else 'Spread (ATS)'
                                else:
                                    pick_type = 'Spread (ATS)'
                            else:
                                pick_type = 'Moneyline'

                        picks.append({
                            'sport': sport,
                            'matchup': f"{away} @ {home}",
                            'pick_type': pick_type,
                            'pick_text': pick_text
                        })

        return picks

    def scrape_all(self):
        """Scrape all sports - combines King of Covers contestants AND public consensus.
        For expert picks: walks up to 10 leaderboard pages per sport to find 50
        contestants who actually have today's picks (not just 50 random top-ranked ones).
        This matches the proven v3.1 scraper approach that produces high consensus counts."""
        print("\n" + "=" * 60)
        print("SCRAPING COVERS.COM CONSENSUS DATA")
        print("=" * 60)

        for sport_code, sport_name in self.sports.items():
            print(f"\n[{sport_name}]")

            # 1. Scrape King of Covers contestants WITH today's picks
            # Walks leaderboard pages until we find 50 who have picks
            entries = self.get_leaderboard_with_picks(sport_code, sport_name, max_pages=4, target=50)

            picks_found = 0
            for contestant, picks in entries:
                picks_found += len(picks)
                self.all_picks.extend(picks)

                for pick in picks:
                    self._add_to_side_counter(
                        pick['sport'], pick['matchup'],
                        pick['pick_type'], pick['pick_text'],
                        weight=1
                    )

            print(f"    Expert picks found: {picks_found}")

            # 2. ALSO scrape public consensus (adds more complete coverage, especially totals)
            self.scrape_public_consensus(sport_code)

        return self.aggregate_picks()

    def aggregate_picks(self):
        """Aggregate picks using side-based counter for better grouping.
        "MIA +6.5" and "Miami +5.5" both count under "Miami ATS" now."""
        aggregated = []

        for side_key, count in self.side_counter.most_common():
            if count < 1:
                continue

            parts = side_key.split('|', 2)
            if len(parts) != 3:
                continue

            sport, matchup, side_label = parts
            pick_type = self.side_type.get(side_key, 'Spread (ATS)')

            # Get the most common line value for display
            line_counts = self.side_lines[side_key]
            best_line = line_counts.most_common(1)[0][0] if line_counts else ''

            # Build display text
            if 'Over' in side_label:
                display_pick = f"Over {best_line}" if best_line else "Over"
            elif 'Under' in side_label:
                display_pick = f"Under {best_line}" if best_line else "Under"
            elif 'ML' in side_label:
                team_name = side_label.replace(' ML', '')
                display_pick = f"{team_name} ML ({best_line})" if best_line else f"{team_name} ML"
            else:
                # ATS
                team_name = side_label.replace(' ATS', '')
                display_pick = f"{team_name} {best_line}" if best_line else team_name

            aggregated.append({
                'count': count,
                'sport': sport,
                'matchup': matchup,
                'pickType': pick_type,
                'pick': display_pick
            })

        aggregated.sort(key=lambda x: -x['count'])
        print(f"\n[OK] Aggregated {len(aggregated)} consensus picks (side-based)")
        return aggregated  # Return ALL, not limited


def group_picks_by_game(picks):
    """Group picks by matchup, sorted by highest consensus"""
    games = defaultdict(list)

    for pick in picks:
        key = (pick['sport'], pick['matchup'])
        games[key].append(pick)

    # Sort picks within each game by count
    for key in games:
        games[key].sort(key=lambda x: -x['count'])

    # Convert to list and sort by highest consensus pick per game
    game_list = []
    for (sport, matchup), game_picks in games.items():
        top_consensus = max(p['count'] for p in game_picks)
        game_list.append({
            'sport': sport,
            'matchup': matchup,
            'top_consensus': top_consensus,
            'picks': game_picks
        })

    # Sort games by top consensus (highest first)
    game_list.sort(key=lambda x: -x['top_consensus'])

    return game_list


def get_consensus_class(count):
    """Get CSS class based on consensus count"""
    if count >= 10:
        return 'consensus-high'
    elif count >= 5:
        return 'consensus-medium'
    return 'consensus-low'


def get_pick_class(pick_type):
    """Get CSS class based on pick type"""
    if 'Over' in pick_type:
        return 'pick-total-over'
    elif 'Under' in pick_type:
        return 'pick-total-under'
    elif 'Spread' in pick_type:
        return 'pick-spread'
    return 'pick-moneyline'


def get_sport_class(sport):
    """Get CSS class for sport tag"""
    return {
        'NFL': 'sport-nfl',
        'NBA': 'sport-nba',
        'NHL': 'sport-nhl',
        'College Basketball': 'sport-ncaab',
        'College Football': 'sport-ncaaf'
    }.get(sport, 'sport-nfl')


def get_sport_abbrev(sport):
    """Get sport abbreviation"""
    return {
        'College Basketball': 'NCAAB',
        'College Football': 'NCAAF'
    }.get(sport, sport)


def generate_game_cards_html(games):
    """Generate HTML for game cards"""
    cards_html = []

    for game in games:
        picks_html = []
        for pick in game['picks']:
            pick_row = f'''                            <div class="pick-row">
                                <span class="consensus-badge {get_consensus_class(pick['count'])}">{pick['count']}x</span>
                                <span class="pick-type-badge {get_pick_class(pick['pickType'])}">{pick['pickType']}</span>
                                <span class="pick-value">{pick['pick']}</span>
                            </div>'''
            picks_html.append(pick_row)

        card = f'''                <div class="game-card" data-sport="{game['sport']}">
                    <div class="game-header">
                        <span class="sport-tag {get_sport_class(game['sport'])}">{get_sport_abbrev(game['sport'])}</span>
                        <span class="game-matchup">{game['matchup']}</span>
                        <span class="game-top-consensus">{game['top_consensus']}x TOP</span>
                    </div>
                    <div class="game-picks">
{chr(10).join(picks_html)}
                    </div>
                </div>'''
        cards_html.append(card)

    return '\n'.join(cards_html)


def _repair_page_structure(html):
    """PERMANENT FIX: Validate and repair critical page structure.

    Ensures the page ALWAYS has:
    1. The filterSport() JavaScript function (with NCAAB/NCAAF mapping)
    2. Proper </body></html> closing tags
    3. No leftover merge conflict markers

    This runs EVERY time the page is saved, so even if merge conflicts
    or truncation corrupt the file, the next scraper run auto-heals it.
    """
    repairs = []

    # 1. Strip any remaining merge conflict markers
    if '<<<<<<< ' in html or '=======' in html or '>>>>>>> ' in html:
        clean_lines = []
        skip = False
        for line in html.splitlines(True):
            s = line.strip()
            if s.startswith('<<<<<<< '):
                skip = False
                continue
            elif s == '=======':
                skip = True
                continue
            elif s.startswith('>>>>>>> '):
                skip = False
                continue
            if not skip:
                clean_lines.append(line)
        html = ''.join(clean_lines)
        repairs.append("stripped merge conflict markers")

    # 2. Ensure filterSport() function exists
    if 'function filterSport' not in html:
        repairs.append("added missing filterSport() function")
        # Find where to insert - after games-container closing div, before </body>
        filter_script = '''
<script>
        // Sport filter function - AUTO-REPAIRED by scraper
        function filterSport(sport) {
            const cards = document.querySelectorAll('.game-card');
            const buttons = document.querySelectorAll('.filter-btn');

            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Map button labels to data-sport attribute values
            const sportMap = {
                'NCAAB': 'College Basketball',
                'NCAAF': 'College Football'
            };
            const matchSport = sportMap[sport] || sport;

            cards.forEach(card => {
                if (sport === 'all') {
                    card.style.display = '';
                } else {
                    const cardSport = card.getAttribute('data-sport');
                    card.style.display = cardSport === matchSport ? '' : 'none';
                }
            });
        }
    </script>
'''
        # Insert before </body> if it exists, otherwise before </html>, otherwise append
        if '</body>' in html:
            html = html.replace('</body>', filter_script + '\n    </body>')
        elif '</html>' in html:
            html = html.replace('</html>', filter_script + '\n    </body>\n</html>')
        else:
            html += filter_script + '\n    </body>\n</html>'

    # 3. Ensure filterSport has the NCAAB/NCAAF sport mapping
    # Old versions compared data-sport directly without mapping
    if 'function filterSport' in html and 'sportMap' not in html:
        repairs.append("added NCAAB/NCAAF sport mapping to filterSport")
        html = html.replace(
            "const cardSport = card.getAttribute('data-sport');\n"
            "                    card.style.display = cardSport === sport ? '' : 'none';",
            "const cardSport = card.getAttribute('data-sport');\n"
            "                    const sportMap = {'NCAAB': 'College Basketball', 'NCAAF': 'College Football'};\n"
            "                    const matchSport = sportMap[sport] || sport;\n"
            "                    card.style.display = cardSport === matchSport ? '' : 'none';"
        )

    # 4. Ensure </body></html> closing tags exist
    if '</body>' not in html:
        repairs.append("added missing </body> tag")
        if '</html>' in html:
            html = html.replace('</html>', '    </body>\n</html>')
        else:
            html += '\n    </body>\n</html>'
    if '</html>' not in html:
        repairs.append("added missing </html> tag")
        html += '\n</html>'

    if repairs:
        print(f"  [REPAIR] Auto-healed page structure: {', '.join(repairs)}")

    return html


def update_covers_consensus(picks):
    """Update covers-consensus.html with game card layout"""
    main_file = os.path.join(REPO, "covers-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] covers-consensus.html not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # PERMANENT FIX: Strip any git merge conflict markers before processing
    # These get introduced when GitHub Actions and local runs collide
    if '<<<<<<< ' in html:
        print("  [REPAIR] Found merge conflict markers - stripping them (keeping HEAD content)")
        clean_lines = []
        skip = False
        for line in html.splitlines(True):
            s = line.strip()
            if s.startswith('<<<<<<< '):
                skip = False  # keep HEAD (ours) content
                continue
            elif s == '=======':
                skip = True  # skip theirs
                continue
            elif s.startswith('>>>>>>> '):
                skip = False  # resume
                continue
            if not skip:
                clean_lines.append(line)
        html = ''.join(clean_lines)
        print(f"  [REPAIR] Merge conflicts resolved")

    # Group picks by game
    games = group_picks_by_game(picks)

    # Generate game cards HTML
    cards_html = generate_game_cards_html(games)

    # Calculate stats
    total_picks = sum(p['count'] for p in picks)
    num_games = len(games)
    num_sports = len(set(p['sport'] for p in picks))
    top_consensus = max(p['count'] for p in picks) if picks else 0

    # Update date
    html = re.sub(
        r'<div class="update-date">[^<]+</div>',
        f'<div class="update-date">{DATE_FULL}</div>',
        html
    )

    # Update stats
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Total Picks)',
        f'\\g<1>{len(picks)}\\2',
        html
    )
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Games)',
        f'\\g<1>{num_games}\\2',
        html
    )
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Sports)',
        f'\\g<1>{num_sports}\\2',
        html
    )
    html = re.sub(
        r'(<div class="stat-value">)\d+x(</div>\s*<div class="stat-label">Top Consensus)',
        f'\\g<1>{top_consensus}x\\2',
        html
    )

    # Replace games container content
    games_start = html.find('<div class="games-container">')
    if games_start == -1:
        print("  [ERROR] Could not find games-container")
        return False

    # Find the closing div for games-container
    # Count nested divs to find the right closing tag
    pos = games_start + len('<div class="games-container">')
    depth = 1
    while depth > 0 and pos < len(html):
        if html[pos:pos+4] == '<div':
            depth += 1
        elif html[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                break
        pos += 1

    games_end = pos

    # Replace content
    new_games_section = f'''<div class="games-container">
{cards_html}
            </div>'''

    html = html[:games_start] + new_games_section + html[games_end + 6:]

    # Update timestamp
    timestamp = TODAY.strftime('%B %d, %Y at %I:%M %p ET')
    html = re.sub(
        r'<strong>Last Updated:</strong>[^<]+',
        f'<strong>Last Updated:</strong> {timestamp}',
        html
    )

    # Update page navigation with correct previous day link
    # Find the most recent previous day that has a consensus file
    prev_day_link = '<span class="disabled">&larr; Previous Day</span>'
    for i in range(1, 10):
        prev_date = TODAY - timedelta(days=i)
        prev_date_str = prev_date.strftime('%Y-%m-%d')
        prev_date_short = prev_date.strftime('%b %-d') if os.name != 'nt' else prev_date.strftime('%b %d').replace(' 0', ' ')
        prev_file = f"covers-consensus-{prev_date_str}.html"
        if os.path.exists(os.path.join(REPO, prev_file)):
            prev_day_link = f'<a href="{prev_file}">&larr; Previous Day ({prev_date_short})</a>'
            break

    new_page_nav = f'''<!-- Page Navigation -->
        <div class="page-nav">
            {prev_day_link}
            <span class="disabled">Next Day &rarr;</span>
        </div>'''

    html = re.sub(
        r'<!-- Page Navigation -->.*?</div>',
        new_page_nav,
        html,
        flags=re.DOTALL
    )

    # PERMANENT FIX: Validate and repair critical page structure before saving
    # This ensures the page ALWAYS has working tab filters and proper HTML closure
    # regardless of merge conflicts, truncation, or any other corruption
    html = _repair_page_structure(html)

    # Save updated file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated covers-consensus.html with {len(games)} games, {len(picks)} picks")

    # Create dated archive
    archive_file = os.path.join(REPO, f"covers-consensus-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Created archive: covers-consensus-{DATE_STR}.html")

    return True


def update_sharp_consensus(picks):
    """Update sharp-consensus.html in consensus_library"""
    main_file = os.path.join(CONSENSUS_DIR, "sharp-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] sharp-consensus.html not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Generate JavaScript data
    js_data = json.dumps(picks[:100], indent=8)  # Top 100 for this view

    # Replace consensusData
    pattern = r'const consensusData = \[[\s\S]*?\];'
    replacement = f'const consensusData = {js_data};'
    html = re.sub(pattern, replacement, html)

    # Update title and meta
    html = re.sub(
        r'<title>[^<]*</title>',
        f'<title>Sharp Consensus Picks Today - {DATE_DISPLAY} | NFL NBA NHL Expert Picks</title>',
        html
    )

    # Update date displays (matches any year, not just 2025)
    html = re.sub(
        r'(December|January|February|March|April|May|June|July|August|September|October|November) \d{2}, 20\d{2}',
        DATE_DISPLAY,
        html
    )

    # Update the "Data from" timestamp
    time_now = TODAY.strftime('%I:%M %p EST')
    html = re.sub(
        r'<span id="updateTime">[^<]+</span>',
        f'<span id="updateTime">{DATE_DISPLAY} - {time_now}</span>',
        html
    )

    # Update canonical URL
    html = re.sub(
        r'sharp-consensus-\d{4}-\d{2}-\d{2}\.html',
        f'sharp-consensus-{DATE_STR}.html',
        html
    )

    # Update stats
    max_consensus = max(p['count'] for p in picks) if picks else 0
    sports_covered = len(set(p['sport'] for p in picks))

    html = re.sub(
        r'<div class="stat-number" id="topConsensus">\d+</div>',
        f'<div class="stat-number" id="topConsensus">{max_consensus}</div>',
        html
    )
    html = re.sub(
        r'<div class="stat-number" id="sportCount">\d+</div>',
        f'<div class="stat-number" id="sportCount">{sports_covered}</div>',
        html
    )

    # Save main file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated sharp-consensus.html with {min(len(picks), 100)} picks")

    # Create dated archive
    archive_file = os.path.join(CONSENSUS_DIR, f"sharp-consensus-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Created archive: sharp-consensus-{DATE_STR}.html")

    return True


def update_index_html():
    """Update index.html links"""
    index_file = os.path.join(REPO, "index.html")

    if not os.path.exists(index_file):
        return

    # No changes needed - links already point to consensus pages
    print(f"  index.html OK")


def sync_archive_calendar():
    """Sync ARCHIVE_DATA in covers-consensus.html with all dated files on disk.
    This ensures the calendar sidebar always shows every available date."""
    main_file = os.path.join(REPO, "covers-consensus.html")
    if not os.path.exists(main_file):
        print("  [ERROR] covers-consensus.html not found")
        return

    # Find all dated consensus files
    consensus_files = []
    for filename in os.listdir(REPO):
        match = re.match(r'covers-consensus-(\d{4}-\d{2}-\d{2})\.html', filename)
        if match:
            consensus_files.append((match.group(1), filename))
    consensus_files.sort()

    if not consensus_files:
        print("  No dated consensus files found")
        return

    # Build new ARCHIVE_DATA entries
    archive_entries = []
    for date_str, filename in consensus_files:
        archive_entries.append(f'            {{ date: "{date_str}", page: "{filename}" }}')
    new_archive_data = "const ARCHIVE_DATA = [\n" + ",\n".join(archive_entries) + "\n        ];"

    # Pattern to match existing ARCHIVE_DATA
    pattern = r'const ARCHIVE_DATA = \[.*?\];'

    # Update main consensus page
    with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    updated = re.sub(pattern, new_archive_data, content, flags=re.DOTALL)
    if updated != content:
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(updated)

    # Update today's dated archive page too (it was copied before calendar sync)
    today_archive = os.path.join(REPO, f"covers-consensus-{DATE_STR}.html")
    if os.path.exists(today_archive):
        with open(today_archive, 'r', encoding='utf-8', errors='ignore') as f:
            arc_content = f.read()
        arc_updated = re.sub(pattern, new_archive_data, arc_content, flags=re.DOTALL)
        if arc_updated != arc_content:
            with open(today_archive, 'w', encoding='utf-8') as f:
                f.write(arc_updated)

    print(f"  Synced ARCHIVE_DATA with {len(consensus_files)} dated files")


def main():
    print("=" * 60)
    print("SPORTSBETTINGPRIME CONSENSUS UPDATE")
    print(f"Date: {DATE_FULL}")
    print(f"Running from: {REPO}")
    print("=" * 60)

    # 1. Scrape data
    print("\n[1] Scraping Covers.com...")
    scraper = CoversConsensusScraper()
    picks = scraper.scrape_all()

    if not picks:
        print("\n[ERROR] No picks found - skipping update")
        return 1

    # 1b. Filter picks to today's games only (ESPN cross-reference)
    # Only filter a sport if ESPN returned a reasonable number of games.
    # When ESPN returns very few games, it may be missing data, so we skip
    # filtering that sport to avoid removing legitimate games.
    print("\n[1b] Filtering to today's games only (ESPN schedule)...")
    espn_schedule = fetch_espn_schedule()

    # Minimum ESPN games required to trust filtering for each sport
    _MIN_ESPN_GAMES_TO_FILTER = {
        'NBA': 3, 'NHL': 3, 'College Basketball': 3,
        'NFL': 1, 'College Football': 1,
    }

    # Disable filtering for sports where ESPN returned too few games
    for sport_name, games_list in espn_schedule.items():
        if games_list is not None:
            min_required = _MIN_ESPN_GAMES_TO_FILTER.get(sport_name, 3)
            if len(games_list) < min_required:
                print(f"    ESPN {sport_name}: only {len(games_list)} games (< {min_required} threshold) - SKIPPING filter for this sport")
                espn_schedule[sport_name] = None  # None = don't filter

    original_count = len(picks)
    original_games = len(group_picks_by_game(picks))
    filtered_picks = []
    filtered_out = set()
    for pick in picks:
        sport = pick['sport']
        matchup = pick['matchup']
        espn_games = espn_schedule.get(sport)
        if is_game_on_today(matchup, espn_games):
            filtered_picks.append(pick)
        else:
            if (sport, matchup) not in filtered_out:
                filtered_out.add((sport, matchup))
                print(f"    FILTERED: {sport} - {matchup} (not on today's ESPN schedule)")
    picks = filtered_picks
    new_games = len(group_picks_by_game(picks))
    print(f"    Filtered {original_count - len(picks)} picks ({original_games - new_games} games) not on today's schedule")

    # 2. Update covers-consensus.html (game cards layout)
    print("\n[2] Updating covers-consensus.html (game cards)...")
    update_covers_consensus(picks)

    # 3. Update sharp-consensus.html (list layout)
    print("\n[3] Updating sharp-consensus.html...")
    if os.path.exists(CONSENSUS_DIR):
        update_sharp_consensus(picks)
    else:
        print(f"  Skipping - consensus_library not found")

    # 4. Update index.html
    print("\n[4] Checking index.html...")
    update_index_html()

    # 5. Sync calendar ARCHIVE_DATA with all dated files
    print("\n[5] Syncing calendar ARCHIVE_DATA...")
    sync_archive_calendar()

    print("\n" + "=" * 60)
    print("CONSENSUS UPDATE COMPLETE!")
    print(f"  - {len(picks)} total consensus picks")
    print(f"  - {len(group_picks_by_game(picks))} games")
    print(f"  - Highest consensus: {max(p['count'] for p in picks)}x")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
