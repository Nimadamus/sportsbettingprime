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
        'St. John\'s (NY)': "St. John's",
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

    def _add_to_side_counter(self, sport, matchup, pick_type, pick_text, weight=1):
        """Add a pick to the side-based counter"""
        matchup = self._normalize_matchup(matchup)
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

    def scrape_public_consensus(self, sport_code):
        """Scrape public consensus data from Covers.com topconsensus pages
        This provides ADDITIONAL data beyond King of Covers contestants"""
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
                        matchup_raw = cells[0].get_text(strip=True)
                        consensus_raw = cells[2].get_text(strip=True)
                        sides_raw = cells[3].get_text(strip=True)

                        # Parse matchup (e.g., "NHLDetBos" -> "Detroit @ Boston")
                        matchup = self.parse_matchup(matchup_raw, sport_code)

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
                        matchup_raw = cells[0].get_text(strip=True)
                        consensus_raw = cells[2].get_text(strip=True)
                        total_line = cells[3].get_text(strip=True)

                        matchup = self.parse_matchup(matchup_raw, sport_code)

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
    }

    def _normalize_profile_team(self, name):
        """Normalize a team name from a Covers.com contestant profile"""
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

    def parse_matchup(self, raw, sport_code):
        """Parse matchup from compressed format like 'NHLDetBos' to 'Detroit @ Boston'"""
        raw = re.sub(r'^(NHL|NBA|NFL|NCAAB|NCAAF)', '', raw, flags=re.IGNORECASE)

        # Handle hyphenated abbreviations before regex split
        for hyph, replacement in self.HYPHENATED_ABBREVS.items():
            raw = raw.replace(hyph, replacement)

        teams = {
            # NHL
            'Ana': 'Anaheim', 'Ari': 'Arizona', 'Bos': 'Boston', 'Buf': 'Buffalo',
            'Cgy': 'Calgary', 'Cal': 'Calgary', 'Car': 'Carolina', 'Chi': 'Chicago',
            'Col': 'Colorado', 'Clb': 'Columbus', 'Dal': 'Dallas', 'Det': 'Detroit',
            'Edm': 'Edmonton', 'Fla': 'Florida', 'La': 'Los Angeles', 'Min': 'Minnesota',
            'Mon': 'Montreal', 'Mtl': 'Montreal', 'Nsh': 'Nashville', 'Nj': 'New Jersey',
            'Nyi': 'NY Islanders', 'Nyr': 'NY Rangers', 'Ott': 'Ottawa', 'Phi': 'Philadelphia',
            'Pit': 'Pittsburgh', 'Sj': 'San Jose', 'Sea': 'Seattle', 'Stl': 'St. Louis',
            'Tb': 'Tampa Bay', 'Tor': 'Toronto', 'Utah': 'Utah', 'Van': 'Vancouver',
            'Veg': 'Vegas', 'Vgk': 'Vegas', 'Win': 'Winnipeg', 'Was': 'Washington', 'Wpg': 'Winnipeg',
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
        }

        # Sport-specific overrides for abbreviation collisions
        # (e.g., "Van" = Vancouver in NHL but Vanderbilt in NCAAB)
        sport_overrides = {
            'nhl': {'Van': 'Vancouver', 'Win': 'Winnipeg', 'Veg': 'Vegas',
                    'Cal': 'Calgary', 'Col': 'Colorado', 'Min': 'Minnesota',
                    'Fla': 'Florida', 'Car': 'Carolina'},
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
                                'Utah', 'Iona', 'Ohio', 'Elon', 'Maine'}
            if away == parts[0] and parts[0] not in known_full_names:
                print(f"    [WARN] Unknown team abbreviation: '{parts[0]}' (sport: {sport_code})")
            if home == parts[1] and parts[1] not in known_full_names:
                print(f"    [WARN] Unknown team abbreviation: '{parts[1]}' (sport: {sport_code})")
            return f"{away} @ {home}"

        return raw

    def get_leaderboard(self, sport_code, pages=4):
        """Fetch top contestants from leaderboard - 4 pages = ~200 contestants"""
        print(f"\n  Fetching {self.sports.get(sport_code, sport_code)} leaderboard...")
        contestants = []

        for page in range(1, pages + 1):
            try:
                url = f"https://contests.covers.com/consensus/pickleaders/{sport_code}?totalPicks=1&orderPickBy=Overall&orderBy=Units&pageNum={page}"
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                table = soup.find('table')
                if not table:
                    continue

                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    link = cells[1].find('a')
                    if not link:
                        continue

                    name = link.text.strip()
                    profile_url = link.get('href', '')
                    if not profile_url.startswith('http'):
                        profile_url = 'https://contests.covers.com' + profile_url

                    units = cells[2].text.strip()
                    record = cells[3].text.strip()

                    try:
                        units_value = float(units.replace('+', '').replace(',', ''))
                    except:
                        units_value = 0.0

                    contestants.append({
                        'name': name,
                        'profile_url': profile_url,
                        'units': units,
                        'units_value': units_value,
                        'record': record,
                        'sport': self.sports.get(sport_code, sport_code)
                    })

                time.sleep(0.5)

            except Exception as e:
                print(f"    Error fetching page {page}: {e}")

        # Sort by units and dedupe
        seen = set()
        unique = []
        for c in sorted(contestants, key=lambda x: -x['units_value']):
            if c['profile_url'] not in seen:
                seen.add(c['profile_url'])
                unique.append(c)

        print(f"    Found {len(unique)} unique contestants (from {len(contestants)} total)")
        return unique[:100]  # Return top 100 (sharper picks)

    def get_contestant_picks(self, contestant, sport):
        """Get pending picks for a contestant"""
        try:
            response = self.session.get(contestant['profile_url'], timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            picks = []
            pending_table = soup.find('table', class_='cmg_contests_pendingpicks')

            if not pending_table:
                return []

            for row in pending_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue

                # Skip finished games
                if len(cells) > 1:
                    score = cells[1].text.strip()
                    if score and any(c.isdigit() for c in score):
                        continue

                # Extract teams and normalize names to match public consensus format
                teams_text = cells[0].text.strip().split('\n')
                teams = [t.strip() for t in teams_text if t.strip()]
                away = self._normalize_profile_team(teams[0]) if teams else ''
                home = self._normalize_profile_team(teams[1]) if len(teams) > 1 else ''

                # Extract picks - get ALL divs and deduplicate (KEY FIX!)
                picks_cell = cells[3] if len(cells) > 3 else None
                if not picks_cell:
                    continue

                # Get ALL pick divs and deduplicate
                pick_divs = picks_cell.find_all('div')
                pick_texts = []
                seen_picks = set()

                for div in pick_divs:
                    pick_text = div.text.strip()
                    if pick_text and pick_text not in seen_picks:
                        pick_texts.append(pick_text)
                        seen_picks.add(pick_text)

                # If no divs found, try getting direct text
                if not pick_texts:
                    direct_text = picks_cell.get_text(strip=True)
                    if direct_text and len(direct_text) >= 3:
                        pick_texts.append(direct_text)

                # Process EACH unique pick for this game
                for pick_text in pick_texts:
                    if not pick_text or len(pick_text) < 3:
                        continue

                    pick_lower = pick_text.lower()

                    # Determine pick type
                    if 'over' in pick_lower:
                        pick_type = 'Total (Over)'
                    elif 'under' in pick_lower:
                        pick_type = 'Total (Under)'
                    elif '+ml' in pick_lower or '-ml' in pick_lower or 'ml' in pick_lower:
                        pick_type = 'Moneyline'
                    else:
                        # Check for moneyline odds (3-digit numbers like +104, -150)
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
                                if num >= 100:
                                    pick_type = 'Moneyline'
                                else:
                                    pick_type = 'Spread (ATS)'
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

        except Exception as e:
            return []

    def scrape_all(self):
        """Scrape all sports - combines King of Covers contestants AND public consensus"""
        print("\n" + "=" * 60)
        print("SCRAPING COVERS.COM CONSENSUS DATA")
        print("=" * 60)

        for sport_code, sport_name in self.sports.items():
            print(f"\n[{sport_name}]")

            # 1. Scrape King of Covers contestants (expert picks)
            contestants = self.get_leaderboard(sport_code, pages=4)  # 4 pages = ~200 contestants

            picks_found = 0
            for i, contestant in enumerate(contestants[:200], 1):  # Process top 200
                picks = self.get_contestant_picks(contestant, sport_name)

                if picks:
                    picks_found += len(picks)
                    self.all_picks.extend(picks)

                    for pick in picks:
                        # Add to side-based counter (expert picks get weight 1 each)
                        self._add_to_side_counter(
                            pick['sport'], pick['matchup'],
                            pick['pick_type'], pick['pick_text'],
                            weight=1
                        )

                time.sleep(0.3)

            print(f"    Expert picks found: {picks_found}")

            # 2. ALSO scrape public consensus (adds more complete coverage, especially totals)
            self.scrape_public_consensus(sport_code)

        return self.aggregate_picks()

    def aggregate_picks(self):
        """Aggregate picks using side-based counter for better grouping.
        "MIA +6.5" and "Miami +5.5" both count under "Miami ATS" now."""
        aggregated = []

        for side_key, count in self.side_counter.most_common():
            if count < 2:
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


def update_covers_consensus(picks):
    """Update covers-consensus.html with game card layout"""
    main_file = os.path.join(REPO, "covers-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] covers-consensus.html not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

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

    # Update date displays
    html = re.sub(
        r'(December|January|February|March|April|May|June|July|August|September|October|November) \d{2}, 2025',
        DATE_DISPLAY,
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
