#!/usr/bin/env python3
"""
HPQT MLB-SPECIFIC TREND ANALYSIS ENGINE
=======================================
Comprehensive MLB trend detection with all baseball-specific variables.

Variable Categories for MLB:
- Pitching: Starters, bullpen usage, pitch counts, velocity, splits
- Hitting: Lineup construction, platoon splits, recent form, clutch stats
- Situational: Day/night, home/road, grass/turf, dome/outdoor
- Weather: Wind direction, temperature, humidity, altitude
- Historical: H2H pitcher vs hitters, park factors, umpire tendencies
- Scheduling: Travel, rest, doubleheaders, day games after night games
- Betting: Line movement, reverse line movement, sharp money indicators
- Regression: BABIP, FIP/xFIP, ERA vs advanced metrics, HR/FB rate
"""

import os
import sys
import json
import math
import statistics
import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PitcherType(Enum):
    """Types of pitchers"""
    ACE = "ace"
    SOLID = "solid"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    BULLPEN_DAY = "bullpen_day"
    UNKNOWN = "unknown"


class HittingForm(Enum):
    """Team hitting form"""
    HOT = "hot"
    GOOD = "good"
    AVERAGE = "average"
    COLD = "cold"
    ICE_COLD = "ice_cold"


@dataclass
class PitcherStats:
    """Comprehensive pitcher statistics"""
    name: str
    team: str
    era: float = 4.50
    whip: float = 1.35
    k_per_9: float = 8.0
    bb_per_9: float = 3.0
    hr_per_9: float = 1.2
    babip: float = 0.300
    fip: float = 4.50
    xfip: float = 4.50
    innings_pitched: float = 0.0
    pitch_count_avg: int = 95
    last_start_ip: float = 6.0
    days_rest: int = 4
    is_home: bool = True
    vs_opponent_era: float = 4.50
    vs_opponent_whip: float = 1.35
    recent_form: str = "average"  # hot, good, average, poor, terrible
    
    def get_fatigue_score(self) -> float:
        """Calculate pitcher fatigue (0-100, higher = more fatigued)"""
        score = 0
        
        # Pitch count fatigue
        if self.pitch_count_avg > 105:
            score += 25
        elif self.pitch_count_avg > 95:
            score += 15
        
        # Short rest
        if self.days_rest < 4:
            score += 20
        elif self.days_rest < 5:
            score += 10
        
        # Innings workload
        if self.innings_pitched > 180:
            score += 15
        elif self.innings_pitched > 160:
            score += 10
        
        # Recent short outings
        if self.last_start_ip < 5:
            score += 15
        
        return min(100, score)
    
    def get_trust_score(self) -> float:
        """Calculate how trustworthy this pitcher is (0-100)"""
        score = 50  # Base
        
        # ERA component
        if self.era < 3.00:
            score += 20
        elif self.era < 3.50:
            score += 15
        elif self.era < 4.00:
            score += 10
        elif self.era > 5.00:
            score -= 15
        elif self.era > 4.50:
            score -= 10
        
        # WHIP component
        if self.whip < 1.10:
            score += 15
        elif self.whip < 1.20:
            score += 10
        elif self.whip > 1.45:
            score -= 10
        
        # K/BB ratio
        k_bb = self.k_per_9 / max(0.5, self.bb_per_9)
        if k_bb > 4:
            score += 10
        elif k_bb > 3:
            score += 5
        elif k_bb < 1.5:
            score -= 10
        
        # FIP vs ERA (luck factor)
        fip_diff = self.era - self.fip
        if fip_diff > 0.5:  # ERA higher than FIP = unlucky, due for improvement
            score += 5
        elif fip_diff < -0.5:  # ERA lower than FIP = lucky, due for regression
            score -= 5
        
        return max(0, min(100, score))


@dataclass
class HittingStats:
    """Team hitting statistics"""
    team: str
    runs_per_game: float = 4.5
    ops: float = 0.730
    avg: float = 0.250
    obp: float = 0.320
    slg: float = 0.410
    hr_per_game: float = 1.2
    k_rate: float = 22.0
    bb_rate: float = 8.5
    babip: float = 0.295
    wrc_plus: int = 100
    
    # Situational
    vs_rhp_ops: float = 0.730
    vs_lhp_ops: float = 0.730
    home_ops: float = 0.740
    away_ops: float = 0.720
    
    # Recent form (last 7 games)
    last_7_rpg: float = 4.5
    last_7_ops: float = 0.730
    last_7_babip: float = 0.295
    
    def get_form_rating(self) -> HittingForm:
        """Determine current hitting form"""
        # Compare recent to season
        rpg_diff = self.last_7_rpg - self.runs_per_game
        ops_diff = self.last_7_ops - self.ops
        
        score = rpg_diff * 10 + ops_diff * 200
        
        if score > 1.5:
            return HittingForm.HOT
        elif score > 0.5:
            return HittingForm.GOOD
        elif score > -0.5:
            return HittingForm.AVERAGE
        elif score > -1.5:
            return HittingForm.COLD
        else:
            return HittingForm.ICE_COLD
    
    def get_platoonsplit_rating(self, opponent_pitcher_hand: str = 'R') -> float:
        """Get OPS vs specific handedness"""
        if opponent_pitcher_hand == 'L':
            return self.vs_lhp_ops
        return self.vs_rhp_ops


@dataclass
class BallparkFactors:
    """Ballpark factors (100 = neutral, >100 favors, <100 suppresses)"""
    park_name: str
    runs_factor: float = 100.0
    hr_factor: float = 100.0
    doubles_factor: float = 100.0
    walks_factor: float = 100.0
    avg_factor: float = 100.0
    
    # Dimensions
    left_field: int = 330
    left_center: int = 375
    center_field: int = 400
    right_center: int = 375
    right_field: int = 330
    
    # Surface
    surface: str = "grass"  # grass, turf
    roof: str = "open"  # open, closed, retractable
    
    def get_scoring_environment(self) -> str:
        """Classify scoring environment"""
        if self.runs_factor > 110:
            return "HITTER_FRIENDLY"
        elif self.runs_factor > 105:
            return "SLIGHTLY_HITTER"
        elif self.runs_factor < 90:
            return "PITCHER_FRIENDLY"
        elif self.runs_factor < 95:
            return "SLIGHTLY_PITCHER"
        return "NEUTRAL"
    
    def get_expected_total_adjustment(self) -> float:
        """Adjustment to expected total based on park"""
        base = (self.runs_factor - 100) / 100
        return base * 1.5  # Scale to runs


@dataclass
class WeatherConditions:
    """Weather for game"""
    temperature: int = 72
    wind_speed: int = 5
    wind_direction: str = "out"  # out, in, left, right, varies
    humidity: int = 50
    precipitation_chance: int = 0
    is_dome: bool = False
    
    def get_total_adjustment(self) -> float:
        """Calculate total adjustment from weather"""
        if self.is_dome:
            return 0
        
        adjustment = 0
        
        # Temperature
        if self.temperature > 85:
            adjustment += 0.5
        elif self.temperature < 50:
            adjustment -= 0.5
        
        # Wind
        if self.wind_direction == "out" and self.wind_speed > 10:
            adjustment += self.wind_speed * 0.08
        elif self.wind_direction == "in" and self.wind_speed > 10:
            adjustment -= self.wind_speed * 0.08
        
        # Humidity (higher = ball doesn't carry)
        if self.humidity > 80:
            adjustment -= 0.3
        elif self.humidity < 30:
            adjustment += 0.2
        
        return adjustment


@dataclass
class UmpireStats:
    """Home plate umpire tendencies"""
    name: str
    games_called: int = 0
    avg_total: float = 8.5
    over_rate: float = 0.50
    k_per_game: float = 15.0
    bb_per_game: float = 6.0
    home_team_wrpct: float = 0.50
    
    def get_total_bias(self) -> str:
        """Over/under/under tendency"""
        if self.over_rate > 0.55:
            return "OVER_FRIENDLY"
        elif self.over_rate < 0.45:
            return "UNDER_FRIENDLY"
        return "NEUTRAL"


class MLBComprehensiveAnalyzer:
    """Full MLB trend analysis with all variables"""
    
    def __init__(self):
        self.ballparks = self._load_ballpark_factors()
        self.umpires = self._load_umpire_data()
        self.historical_matchups = {}
    
    def _load_ballpark_factors(self) -> Dict[str, BallparkFactors]:
        """Load ballpark factors"""
        parks = {
            'Coors Field': BallparkFactors('Coors Field', runs_factor=118, hr_factor=112, 
                                           left_field=347, center_field=415, altitude=True),
            'Fenway Park': BallparkFactors('Fenway Park', runs_factor=106, hr_factor=96,
                                          left_field=310, right_field=302),
            'Yankee Stadium': BallparkFactors('Yankee Stadium', runs_factor=102, hr_factor=112,
                                             right_field=314),
            'Minute Maid Park': BallparkFactors('Minute Maid Park', runs_factor=99, hr_factor=103),
            'Wrigley Field': BallparkFactors('Wrigley Field', runs_factor=102, hr_factor=104,
                                             wind_sensitive=True),
            'Oracle Park': BallparkFactors('Oracle Park', runs_factor=92, hr_factor=88),
            'Dodger Stadium': BallparkFactors('Dodger Stadium', runs_factor=98, hr_factor=104),
            'T-Mobile Park': BallparkFactors('T-Mobile Park', runs_factor=94, hr_factor=95),
            'Petco Park': BallparkFactors('Petco Park', runs_factor=92, hr_factor=88),
            'Tropicana Field': BallparkFactors('Tropicana Field', runs_factor=96, hr_factor=99, roof="dome"),
            'Rogers Centre': BallparkFactors('Rogers Centre', runs_factor=102, hr_factor=106, roof="retractable"),
            'Camden Yards': BallparkFactors('Camden Yards', runs_factor=101, hr_factor=108),
            'Truist Park': BallparkFactors('Truist Park', runs_factor=99, hr_factor=99),
            'Citizens Bank Park': BallparkFactors('Citizens Bank Park', runs_factor=102, hr_factor=111),
            'Citi Field': BallparkFactors('Citi Field', runs_factor=96, hr_factor=96),
        }
        return parks
    
    def _load_umpire_data(self) -> Dict[str, UmpireStats]:
        """Load umpire tendencies"""
        # Simplified - would load from database
        return {}
    
    def analyze_game(self, game: Dict) -> Dict:
        """Comprehensive single game analysis"""
        
        result = {
            'game_id': game.get('game_id'),
            'matchup': f"{game.get('away_team')} @ {game.get('home_team')}",
            'analysis_timestamp': datetime.datetime.now().isoformat(),
            'trends': [],
            'pitching_analysis': {},
            'hitting_analysis': {},
            'situational_analysis': {},
            'weather_analysis': {},
            'total_analysis': {},
            'runline_analysis': {},
            'moneyline_analysis': {},
            'f5_analysis': {},
            'recommended_plays': []
        }
        
        # Get pitcher data
        home_pitcher = game.get('home_pitcher', {})
        away_pitcher = game.get('away_pitcher', {})
        
        home_pitcher_stats = PitcherStats(
            name=home_pitcher.get('name', 'TBD'),
            team=game.get('home_team'),
            era=home_pitcher.get('era', 4.50),
            whip=home_pitcher.get('whip', 1.35),
            k_per_9=home_pitcher.get('k_per_9', 8.0),
            bb_per_9=home_pitcher.get('bb_per_9', 3.0),
            days_rest=home_pitcher.get('days_rest', 4),
            is_home=True
        )
        
        away_pitcher_stats = PitcherStats(
            name=away_pitcher.get('name', 'TBD'),
            team=game.get('away_team'),
            era=away_pitcher.get('era', 4.50),
            whip=away_pitcher.get('whip', 1.35),
            k_per_9=away_pitcher.get('k_per_9', 8.0),
            bb_per_9=away_pitcher.get('bb_per_9', 3.0),
            days_rest=away_pitcher.get('days_rest', 4),
            is_home=False
        )
        
        # Get hitting data
        home_hitting = game.get('home_hitting', {})
        away_hitting = game.get('away_hitting', {})
        
        home_hitting_stats = HittingStats(
            team=game.get('home_team'),
            runs_per_game=home_hitting.get('rpg', 4.5),
            ops=home_hitting.get('ops', 0.730),
            last_7_rpg=home_hitting.get('last_7_rpg', 4.5),
            last_7_ops=home_hitting.get('last_7_ops', 0.730),
            wrc_plus=home_hitting.get('wrc_plus', 100)
        )
        
        away_hitting_stats = HittingStats(
            team=game.get('away_team'),
            runs_per_game=away_hitting.get('rpg', 4.5),
            ops=away_hitting.get('ops', 0.730),
            last_7_rpg=away_hitting.get('last_7_rpg', 4.5),
            last_7_ops=away_hitting.get('last_7_ops', 0.730),
            wrc_plus=away_hitting.get('wrc_plus', 100)
        )
        
        # Get situational data
        ballpark = self.ballparks.get(game.get('venue', ''), BallparkFactors('Unknown'))
        weather = game.get('weather', WeatherConditions())
        umpire = game.get('umpire', UmpireStats('Unknown'))
        
        # Run all analyses
        result['pitching_analysis'] = self._analyze_pitching(
            home_pitcher_stats, away_pitcher_stats, game
        )
        
        result['hitting_analysis'] = self._analyze_hitting(
            home_hitting_stats, away_hitting_stats, game
        )
        
        result['situational_analysis'] = self._analyze_situational(
            game, ballpark, weather, umpire
        )
        
        result['total_analysis'] = self._analyze_total(
            home_pitcher_stats, away_pitcher_stats,
            home_hitting_stats, away_hitting_stats,
            ballpark, weather, umpire, game
        )
        
        result['runline_analysis'] = self._analyze_runline(
            home_pitcher_stats, away_pitcher_stats,
            home_hitting_stats, away_hitting_stats,
            ballpark, game
        )
        
        result['f5_analysis'] = self._analyze_first_five(
            home_pitcher_stats, away_pitcher_stats,
            home_hitting_stats, away_hitting_stats,
            game
        )
        
        result['trends'] = self._compile_all_trends(result)
        result['recommended_plays'] = self._generate_recommendations(result)
        
        return result
    
    def _analyze_pitching(self, home_p: PitcherStats, away_p: PitcherStats, 
                         game: Dict) -> Dict:
        """Deep pitching analysis"""
        analysis = {
            'home_pitcher': {},
            'away_pitcher': {},
            'matchup_advantage': None,
            'bullpen_concern': False
        }
        
        # Home pitcher
        home_trust = home_p.get_trust_score()
        home_fatigue = home_p.get_fatigue_score()
        
        analysis['home_pitcher'] = {
            'name': home_p.name,
            'trust_score': home_trust,
            'fatigue_score': home_fatigue,
            'era': home_p.era,
            'whip': home_p.whip,
            'assessment': self._assess_pitcher(home_trust, home_fatigue)
        }
        
        # Away pitcher
        away_trust = away_p.get_trust_score()
        away_fatigue = away_p.get_fatigue_score()
        
        analysis['away_pitcher'] = {
            'name': away_p.name,
            'trust_score': away_trust,
            'fatigue_score': away_fatigue,
            'era': away_p.era,
            'whip': away_p.whip,
            'assessment': self._assess_pitcher(away_trust, away_fatigue)
        }
        
        # Matchup comparison
        trust_diff = home_trust - away_trust
        if trust_diff > 15:
            analysis['matchup_advantage'] = f"{game.get('home_team')} (pitching)"
            analysis['advantage_magnitude'] = 'strong'
        elif trust_diff > 5:
            analysis['matchup_advantage'] = f"{game.get('home_team')} (pitching)"
            analysis['advantage_magnitude'] = 'moderate'
        elif trust_diff < -15:
            analysis['matchup_advantage'] = f"{game.get('away_team')} (pitching)"
            analysis['advantage_magnitude'] = 'strong'
        elif trust_diff < -5:
            analysis['matchup_advantage'] = f"{game.get('away_team')} (pitching)"
            analysis['advantage_magnitude'] = 'moderate'
        else:
            analysis['matchup_advantage'] = 'Even'
            analysis['advantage_magnitude'] = 'neutral'
        
        return analysis
    
    def _assess_pitcher(self, trust: float, fatigue: float) -> str:
        """Get pitcher assessment"""
        if trust > 75 and fatigue < 30:
            return "ELITE - Trustworthy"
        elif trust > 65 and fatigue < 40:
            return "SOLID - Reliable"
        elif trust > 55 and fatigue < 50:
            return "AVERAGE - Proceed with caution"
        elif fatigue > 60:
            return "FATIGUED - Vulnerable"
        elif trust < 45:
            return "BELOW AVERAGE - Target for offense"
        return "DECENT - Monitor closely"
    
    def _analyze_hitting(self, home_h: HittingStats, away_h: HittingStats,
                        game: Dict) -> Dict:
        """Hitting analysis"""
        analysis = {
            'home_team': {},
            'away_team': {},
            'hot_cold_analysis': {}
        }
        
        home_form = home_h.get_form_rating()
        away_form = away_h.get_form_rating()
        
        analysis['home_team'] = {
            'season_ops': home_h.ops,
            'last_7_ops': home_h.last_7_ops,
            'season_rpg': home_h.runs_per_game,
            'last_7_rpg': home_h.last_7_rpg,
            'form': home_form.value,
            'wrc_plus': home_h.wrc_plus
        }
        
        analysis['away_team'] = {
            'season_ops': away_h.ops,
            'last_7_ops': away_h.last_7_ops,
            'season_rpg': away_h.runs_per_game,
            'last_7_rpg': away_h.last_7_rpg,
            'form': away_form.value,
            'wrc_plus': away_h.wrc_plus
        }
        
        # Hot vs cold matchup
        if home_form in [HittingForm.HOT, HittingForm.GOOD] and away_form in [HittingForm.COLD, HittingForm.ICE_COLD]:
            analysis['hot_cold_analysis'] = f"{game.get('home_team')} HOT vs {game.get('away_team')} COLD"
        elif away_form in [HittingForm.HOT, HittingForm.GOOD] and home_form in [HittingForm.COLD, HittingForm.ICE_COLD]:
            analysis['hot_cold_analysis'] = f"{game.get('away_team')} HOT vs {game.get('home_team')} COLD"
        
        return analysis
    
    def _analyze_situational(self, game: Dict, ballpark: BallparkFactors,
                            weather: WeatherConditions, umpire: UmpireStats) -> Dict:
        """Situational factors analysis"""
        analysis = {
            'ballpark': {
                'name': ballpark.park_name,
                'scoring_environment': ballpark.get_scoring_environment(),
                'runs_factor': ballpark.runs_factor,
                'hr_factor': ballpark.hr_factor
            },
            'weather': {
                'temperature': weather.temperature,
                'wind_speed': weather.wind_speed,
                'wind_direction': weather.wind_direction,
                'total_adjustment': weather.get_total_adjustment()
            },
            'umpire': {
                'name': umpire.name,
                'bias': umpire.get_total_bias() if hasattr(umpire, 'over_rate') else 'Unknown'
            },
            'schedule': {
                'is_getaway_day': game.get('is_getaway_day', False),
                'is_doubleheader': game.get('is_doubleheader', False),
                'day_after_night': game.get('day_after_night', False)
            }
        }
        
        return analysis
    
    def _analyze_total(self, home_p: PitcherStats, away_p: PitcherStats,
                      home_h: HittingStats, away_h: HittingStats,
                      ballpark: BallparkFactors, weather: WeatherConditions,
                      umpire: UmpireStats, game: Dict) -> Dict:
        """Comprehensive total analysis"""
        
        # Base expected total
        league_avg_total = 8.5
        
        # Pitcher adjustments
        pitcher_diff = (home_p.era + away_p.era) / 2 - 4.50
        pitcher_adjustment = pitcher_diff * 1.8  # Scale to runs
        
        # Hitting adjustments
        hitting_diff = (home_h.last_7_rpg + away_h.last_7_rpg) / 2 - 4.5
        hitting_adjustment = hitting_diff * 0.9
        
        # Park adjustment
        park_adjustment = ballpark.get_expected_total_adjustment()
        
        # Weather adjustment
        weather_adjustment = weather.get_total_adjustment()
        
        # Umpire adjustment
        umpire_adjustment = 0
        if hasattr(umpire, 'over_rate'):
            if umpire.over_rate > 0.55:
                umpire_adjustment = 0.3
            elif umpire.over_rate < 0.45:
                umpire_adjustment = -0.3
        
        # Calculate expected total
        expected_total = (league_avg_total + pitcher_adjustment + hitting_adjustment + 
                         park_adjustment + weather_adjustment + umpire_adjustment)
        
        # Market total
        market_total = game.get('total', expected_total)
        
        # Edge calculation
        edge = expected_total - market_total
        
        # Confidence based on data quality
        confidence = self._calculate_total_confidence(
            home_p, away_p, home_h, away_h, weather
        )
        
        analysis = {
            'market_total': market_total,
            'expected_total': round(expected_total, 1),
            'components': {
                'base': league_avg_total,
                'pitching': round(pitcher_adjustment, 2),
                'hitting': round(hitting_adjustment, 2),
                'park': round(park_adjustment, 2),
                'weather': round(weather_adjustment, 2),
                'umpire': round(umpire_adjustment, 2)
            },
            'edge': round(edge, 2),
            'confidence': confidence,
            'recommendation': self._total_recommendation(edge, confidence)
        }
        
        return analysis
    
    def _calculate_total_confidence(self, home_p: PitcherStats, away_p: PitcherStats,
                                   home_h: HittingStats, away_h: HittingStats,
                                   weather: WeatherConditions) -> int:
        """Calculate confidence in total projection (0-100)"""
        confidence = 50  # Base
        
        # Pitcher data quality
        if home_p.era > 0 and away_p.era > 0:
            confidence += 15
        
        # Recent form data
        if home_h.last_7_ops > 0 and away_h.last_7_ops > 0:
            confidence += 15
        
        # Weather certainty
        if not weather.is_dome and weather.precipitation_chance < 20:
            confidence += 10
        
        return min(95, confidence)
    
    def _total_recommendation(self, edge: float, confidence: int) -> str:
        """Generate total recommendation"""
        if abs(edge) < 0.3 or confidence < 40:
            return "NO PLAY - Insufficient edge or confidence"
        
        strength = "STRONG" if abs(edge) > 0.7 else "MODERATE" if abs(edge) > 0.4 else "WEAK"
        direction = "OVER" if edge > 0 else "UNDER"
        
        return f"{strength} {direction} (Edge: {edge:+.1f}, Conf: {confidence})"
    
    def _analyze_runline(self, home_p: PitcherStats, away_p: PitcherStats,
                        home_h: HittingStats, away_h: HittingStats,
                        ballpark: BallparkFactors, game: Dict) -> Dict:
        """Run line analysis"""
        
        # Calculate expected margin
        home_advantage = 0.4  # Home field
        
        # Pitching advantage
        pitching_adv = (away_p.era - home_p.era) * 0.9
        
        # Hitting advantage
        hitting_adv = (home_h.last_7_rpg - away_h.last_7_rpg) * 0.85
        
        expected_margin = home_advantage + pitching_adv + hitting_adv
        
        # Market runline (typically -1.5 for favorite)
        market_spread = game.get('runline', 1.5)
        
        analysis = {
            'expected_margin': round(expected_margin, 2),
            'market_runline': market_spread,
            'components': {
                'home_field': home_advantage,
                'pitching': round(pitching_adv, 2),
                'hitting': round(hitting_adv, 2)
            },
            'recommendation': self._runline_recommendation(expected_margin, market_spread)
        }
        
        return analysis
    
    def _runline_recommendation(self, expected_margin: float, market_spread: float) -> str:
        """Generate runline recommendation"""
        if expected_margin > 1.5:
            return f"PLAY HOME RL (Exp margin: +{expected_margin:.1f})"
        elif expected_margin < -1.5:
            return f"PLAY AWAY RL (Exp margin: {expected_margin:.1f})"
        elif abs(expected_margin) < 1:
            return "AVOID RL - Too close to call"
        return "WEAK EDGE - Small RL play"
    
    def _analyze_first_five(self, home_p: PitcherStats, away_p: PitcherStats,
                           home_h: HittingStats, away_h: HittingStats,
                           game: Dict) -> Dict:
        """First 5 innings analysis"""
        
        # Focus on starting pitchers early
        f5_expected = self._calculate_f5_total(home_p, away_p, home_h, away_h)
        
        analysis = {
            'f5_expected_total': round(f5_expected, 1),
            'home_pitcher_f5_era': round(home_p.era * 0.95, 2),  # Slight boost early
            'away_pitcher_f5_era': round(away_p.era * 0.95, 2),
            'recommendation': self._f5_recommendation(f5_expected, game.get('f5_total', 4.5))
        }
        
        return analysis
    
    def _calculate_f5_total(self, home_p: PitcherStats, away_p: PitcherStats,
                           home_h: HittingStats, away_h: HittingStats) -> float:
        """Calculate expected F5 total"""
        # Starters typically pitch 5-6 innings
        f5_weight = 0.55  # 55% of game scoring happens in F5
        
        base = 4.5  # League avg F5 total
        
        # Adjust for starters
        pitcher_impact = ((home_p.era + away_p.era) / 2 - 4.50) * 0.6
        
        # Hitting impact
        hitting_impact = ((home_h.last_7_rpg + away_h.last_7_rpg) / 2 - 4.5) * 0.5
        
        return base + pitcher_impact + hitting_impact
    
    def _f5_recommendation(self, expected: float, market: float) -> str:
        """F5 recommendation"""
        edge = expected - market
        if abs(edge) > 0.4:
            direction = "OVER" if edge > 0 else "UNDER"
            return f"PLAY F5 {direction} (Edge: {edge:+.1f})"
        return "NO F5 PLAY"
    
    def _compile_all_trends(self, analysis: Dict) -> List[Dict]:
        """Compile all detected trends"""
        trends = []
        
        # Pitching trends
        home_p = analysis['pitching_analysis'].get('home_pitcher', {})
        away_p = analysis['pitching_analysis'].get('away_pitcher', {})
        
        if home_p.get('fatigue_score', 0) > 50:
            trends.append({
                'category': 'PITCHING_FATIGUE',
                'description': f"Home pitcher showing fatigue ({home_p['fatigue_score']}/100)",
                'impact': 'HIGH',
                'recommendation': 'LEAN OVER or FADE HOME'
            })
        
        if away_p.get('trust_score', 50) > 75:
            trends.append({
                'category': 'ACE_PITCHER',
                'description': f"Road ace on mound ({away_p['trust_score']}/100 trust)",
                'impact': 'HIGH',
                'recommendation': 'LEAN UNDER or FADE HOME RUNLINE'
            })
        
        # Hitting trends
        home_h = analysis['hitting_analysis'].get('home_team', {})
        away_h = analysis['hitting_analysis'].get('away_team', {})
        
        home_form = home_h.get('form', 'average')
        away_form = away_h.get('form', 'average')
        
        if home_form == 'hot':
            trends.append({
                'category': 'HOT_OFFENSE',
                'description': f"Home team hot at plate (Last 7 OPS: {home_h.get('last_7_ops', 0):.3f})",
                'impact': 'MEDIUM',
                'recommendation': 'LEAN OVER'
            })
        
        # Total edge
        total = analysis.get('total_analysis', {})
        if abs(total.get('edge', 0)) > 0.4:
            direction = "OVER" if total['edge'] > 0 else "UNDER"
            trends.append({
                'category': 'TOTAL_EDGE',
                'description': f"Total projection: {total.get('expected_total')} vs market {total.get('market_total')}",
                'impact': 'HIGH' if abs(total['edge']) > 0.7 else 'MEDIUM',
                'recommendation': f"PLAY {direction}",
                'edge': total['edge'],
                'confidence': total.get('confidence')
            })
        
        return trends
    
    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate final recommended plays"""
        plays = []
        
        # Check total edge
        total = analysis.get('total_analysis', {})
        if abs(total.get('edge', 0)) > 0.5 and total.get('confidence', 0) > 50:
            plays.append({
                'type': 'TOTAL',
                'play': f"{'OVER' if total['edge'] > 0 else 'UNDER'} {total['market_total']}",
                'edge': total['edge'],
                'confidence': total['confidence'],
                'rationale': f"Projected {total['expected_total']} runs"
            })
        
        # Check runline
        runline = analysis.get('runline_analysis', {})
        if abs(runline.get('expected_margin', 0)) > 1.5:
            plays.append({
                'type': 'RUNLINE',
                'play': 'HOME -1.5' if runline['expected_margin'] > 0 else 'AWAY +1.5',
                'edge': abs(runline['expected_margin']) - 1.5,
                'confidence': 60,
                'rationale': f"Expected margin: {runline['expected_margin']:+.1f}"
            })
        
        return plays


def generate_mlb_daily_report(games: List[Dict]) -> str:
    """Generate full daily MLB report"""
    analyzer = MLBComprehensiveAnalyzer()
    
    report_lines = [
        "=" * 100,
        "HPQT MLB COMPREHENSIVE DAILY ANALYSIS",
        f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
        f"Games Analyzed: {len(games)}",
        "=" * 100,
        ""
    ]
    
    for game in games:
        result = analyzer.analyze_game(game)
        
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"GAME: {result['matchup']}")
        report_lines.append(f"{'='*80}")
        
        # Pitching
        pitching = result['pitching_analysis']
        report_lines.append(f"\n--- PITCHING ---")
        report_lines.append(f"Home: {pitching['home_pitcher'].get('name')} - {pitching['home_pitcher'].get('assessment')}")
        report_lines.append(f"      Trust: {pitching['home_pitcher'].get('trust_score')}/100 | Fatigue: {pitching['home_pitcher'].get('fatigue_score')}/100")
        report_lines.append(f"Road: {pitching['away_pitcher'].get('name')} - {pitching['away_pitcher'].get('assessment')}")
        report_lines.append(f"      Trust: {pitching['away_pitcher'].get('trust_score')}/100 | Fatigue: {pitching['away_pitcher'].get('fatigue_score')}/100")
        report_lines.append(f"Advantage: {pitching.get('matchup_advantage')} ({pitching.get('advantage_magnitude')})")
        
        # Hitting
        hitting = result['hitting_analysis']
        report_lines.append(f"\n--- HITTING ---")
        report_lines.append(f"Home: {hitting['home_team'].get('form').upper()} | Last 7: {hitting['home_team'].get('last_7_ops'):.3f} OPS")
        report_lines.append(f"Road: {hitting['away_team'].get('form').upper()} | Last 7: {hitting['away_team'].get('last_7_ops'):.3f} OPS")
        
        # Total
        total = result['total_analysis']
        report_lines.append(f"\n--- TOTAL ANALYSIS ---")
        report_lines.append(f"Market: {total.get('market_total')} | Projected: {total.get('expected_total')}")
        report_lines.append(f"Components: {total.get('components')}")
        report_lines.append(f"Edge: {total.get('edge'):+.1f} | Confidence: {total.get('confidence')}/100")
        report_lines.append(f"Recommendation: {total.get('recommendation')}")
        
        # Runline
        rl = result['runline_analysis']
        report_lines.append(f"\n--- RUNLINE ---")
        report_lines.append(f"Expected Margin: {rl.get('expected_margin'):+.2f}")
        report_lines.append(f"Recommendation: {rl.get('recommendation')}")
        
        # First 5
        f5 = result['f5_analysis']
        report_lines.append(f"\n--- FIRST 5 INNINGS ---")
        report_lines.append(f"Expected F5 Total: {f5.get('f5_expected_total')}")
        report_lines.append(f"Recommendation: {f5.get('recommendation')}")
        
        # Recommended plays
        report_lines.append(f"\n--- RECOMMENDED PLAYS ---")
        if result['recommended_plays']:
            for play in result['recommended_plays']:
                report_lines.append(f"  * {play['type']}: {play['play']} (Edge: {play['edge']:+.2f}, Conf: {play['confidence']})")
                report_lines.append(f"    Rationale: {play['rationale']}")
        else:
            report_lines.append("  No plays meet criteria")
    
    return "\n".join(report_lines)


# Test
if __name__ == '__main__':
    test_games = [
        {
            'game_id': 'MLB_001',
            'home_team': 'Dodgers',
            'away_team': 'Giants',
            'venue': 'Dodger Stadium',
            'total': 8.0,
            'runline': 1.5,
            'f5_total': 4.5,
            'home_pitcher': {
                'name': 'Kershaw',
                'era': 3.20,
                'whip': 1.05,
                'k_per_9': 9.5,
                'days_rest': 5
            },
            'away_pitcher': {
                'name': 'Webb',
                'era': 3.45,
                'whip': 1.15,
                'k_per_9': 8.8,
                'days_rest': 4
            },
            'home_hitting': {
                'rpg': 5.2,
                'ops': 0.780,
                'last_7_rpg': 5.8,
                'last_7_ops': 0.820,
                'wrc_plus': 115
            },
            'away_hitting': {
                'rpg': 4.1,
                'ops': 0.700,
                'last_7_rpg': 3.5,
                'last_7_ops': 0.650,
                'wrc_plus': 92
            },
            'weather': {
                'temperature': 72,
                'wind_speed': 5,
                'wind_direction': 'out'
            }
        }
    ]
    
    print(generate_mlb_daily_report(test_games))
