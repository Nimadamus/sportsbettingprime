#!/usr/bin/env python3
"""
Handicapping Program Query Tool (HPQT)
======================================
A comprehensive query interface for sports handicapping data analysis.

Features:
- Query consensus picks from covers_contest_picks.csv
- Filter by sport, game, confidence level
- Sharp consensus analysis
- Historical trend queries
- Live data validation and logging
"""

import os
import sys
import json
import logging
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import argparse

# Environment and dependency checking
REQUIRED_PACKAGES = ['sqlite3', 'csv', 'json', 'logging', 'datetime', 'pathlib', 'typing', 'dataclasses', 'enum']
OPTIONAL_PACKAGES = ['pandas', 'numpy', 'colorama']

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

@dataclass
class QueryResult:
    """Standard query result container"""
    success: bool
    data: Any
    message: str
    execution_time: float
    query_type: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'data': self.data if isinstance(self.data, (dict, list)) else str(self.data),
            'message': self.message,
            'execution_time': self.execution_time,
            'query_type': self.query_type,
            'timestamp': self.timestamp.isoformat()
        }

class EnvironmentValidator:
    """Validates the environment and dependencies"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues = []
        self.warnings = []
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks"""
        self.logger.info("=" * 60)
        self.logger.info("ENVIRONMENT VALIDATION STARTING")
        self.logger.info("=" * 60)
        
        # Check Python version
        self._check_python_version()
        
        # Check required packages
        self._check_required_packages()
        
        # Check optional packages
        self._check_optional_packages()
        
        # Check data files
        self._check_data_files()
        
        # Check directory structure
        self._check_directory_structure()
        
        # Check write permissions
        self._check_permissions()
        
        self.logger.info("=" * 60)
        if self.issues:
            self.logger.error(f"VALIDATION FAILED: {len(self.issues)} critical issues found")
            return False, self.issues, self.warnings
        else:
            self.logger.info(f"VALIDATION PASSED: {len(self.warnings)} warnings")
            return True, self.issues, self.warnings
            
    def _check_python_version(self):
        """Check Python version is 3.8+"""
        version = sys.version_info
        self.logger.info(f"Python Version: {version.major}.{version.minor}.{version.micro}")
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.issues.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
            
    def _check_required_packages(self):
        """Verify all required packages are available"""
        self.logger.info("Checking required packages...")
        for package in REQUIRED_PACKAGES:
            try:
                __import__(package)
                self.logger.info(f"  [OK] {package}")
            except ImportError:
                self.issues.append(f"Required package missing: {package}")
                
    def _check_optional_packages(self):
        """Check for optional packages that enhance functionality"""
        self.logger.info("Checking optional packages...")
        for package in OPTIONAL_PACKAGES:
            try:
                __import__(package)
                self.logger.info(f"  [OK] {package} (available)")
            except ImportError:
                self.warnings.append(f"Optional package not installed: {package}")
                self.logger.warning(f"  [MISSING] {package} (not installed)")
                
    def _check_data_files(self):
        """Verify data files exist and are readable"""
        self.logger.info("Checking data files...")
        data_files = [
            'consensus_library/covers_contest_picks.csv',
            'consensus_library/picks_database.json',
        ]
        base_path = Path(__file__).parent
        for file_path in data_files:
            full_path = base_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.logger.info(f"  [OK] {file_path} ({size:,} bytes)")
            else:
                self.warnings.append(f"Data file not found: {file_path}")
                self.logger.warning(f"  [MISSING] {file_path} (not found)")
                
    def _check_directory_structure(self):
        """Verify required directories exist"""
        self.logger.info("Checking directory structure...")
        required_dirs = ['consensus_library', 'scripts', 'daily', 'blog']
        base_path = Path(__file__).parent
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.logger.info(f"  [OK] {dir_name}/")
            else:
                self.warnings.append(f"Directory missing: {dir_name}/")
                self.logger.warning(f"  [MISSING] {dir_name}/ (not found)")
                
    def _check_permissions(self):
        """Check write permissions for logs and cache"""
        self.logger.info("Checking permissions...")
        base_path = Path(__file__).parent
        test_dirs = ['.', 'consensus_library']
        for dir_name in test_dirs:
            dir_path = base_path / dir_name
            try:
                test_file = dir_path / '.permission_test'
                test_file.write_text('test')
                test_file.unlink()
                self.logger.info(f"  [OK] Write access: {dir_name}/")
            except (PermissionError, OSError) as e:
                self.issues.append(f"No write permission for {dir_name}/: {e}")

class HandicappingQueryTool:
    """Main query tool for handicapping data"""
    
    def __init__(self, logger: logging.Logger, base_path: Path = None):
        self.logger = logger
        self.base_path = base_path or Path(__file__).parent
        self.data_cache = {}
        self.db_connection = None
        self.query_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_execution_time': 0.0
        }
        self.logger.info("HandicappingQueryTool initialized")
        
    def initialize_database(self) -> bool:
        """Initialize SQLite database for faster queries"""
        try:
            db_path = self.base_path / 'consensus_library' / 'query_cache.db'
            self.db_connection = sqlite3.connect(str(db_path))
            cursor = self.db_connection.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_type TEXT,
                    query_params TEXT,
                    result_count INTEGER,
                    execution_time REAL,
                    timestamp TEXT,
                    success BOOLEAN
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS picks_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT,
                    sport TEXT,
                    matchup TEXT,
                    pick TEXT,
                    confidence REAL,
                    consensus_count INTEGER,
                    timestamp TEXT
                )
            ''')
            
            self.db_connection.commit()
            self.logger.info("Database initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False
            
    def load_csv_data(self, file_path: str) -> List[Dict]:
        """Load CSV data into memory"""
        cache_key = f"csv:{file_path}"
        if cache_key in self.data_cache:
            self.logger.debug(f"Using cached data for {file_path}")
            return self.data_cache[cache_key]
            
        full_path = self.base_path / file_path
        if not full_path.exists():
            self.logger.error(f"File not found: {full_path}")
            return []
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                self.data_cache[cache_key] = data
                self.logger.info(f"Loaded {len(data)} records from {file_path}")
                return data
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return []
            
    def load_json_data(self, file_path: str) -> Dict:
        """Load JSON data into memory"""
        cache_key = f"json:{file_path}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
            
        full_path = self.base_path / file_path
        if not full_path.exists():
            self.logger.error(f"File not found: {full_path}")
            return {}
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.data_cache[cache_key] = data
                self.logger.info(f"Loaded JSON data from {file_path}")
                return data
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return {}
            
    def query_by_sport(self, sport: str, min_confidence: float = 0.0) -> QueryResult:
        """Query picks by sport type"""
        start_time = datetime.now()
        self.logger.info(f"Query by sport: {sport} (min_confidence: {min_confidence})")
        
        try:
            data = self.load_csv_data('consensus_library/covers_contest_picks.csv')
            if not data:
                return QueryResult(
                    success=False,
                    data=[],
                    message="No data available",
                    execution_time=0,
                    query_type="sport_filter",
                    timestamp=start_time
                )
                
            # Filter by sport (case-insensitive)
            sport_lower = sport.lower()
            results = [
                row for row in data 
                if sport_lower in str(row.get('Sport', '')).lower() or
                   sport_lower in str(row.get('League', '')).lower() or
                   sport_lower in str(row.get('Game', '')).lower()
            ]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(True, execution_time)
            
            return QueryResult(
                success=True,
                data=results,
                message=f"Found {len(results)} picks for {sport}",
                execution_time=execution_time,
                query_type="sport_filter",
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, execution_time)
            self.logger.error(f"Query failed: {e}")
            return QueryResult(
                success=False,
                data=[],
                message=f"Error: {str(e)}",
                execution_time=execution_time,
                query_type="sport_filter",
                timestamp=start_time
            )
            
    def query_by_matchup(self, team1: str, team2: Optional[str] = None) -> QueryResult:
        """Query picks by team matchup"""
        start_time = datetime.now()
        self.logger.info(f"Query by matchup: {team1} vs {team2}")
        
        try:
            data = self.load_csv_data('consensus_library/covers_contest_picks.csv')
            results = []
            
            team1_lower = team1.lower()
            team2_lower = team2.lower() if team2 else None
            
            for row in data:
                game = str(row.get('Game', '')).lower()
                if team1_lower in game:
                    if team2_lower is None or team2_lower in game:
                        results.append(row)
                        
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(True, execution_time)
            
            return QueryResult(
                success=True,
                data=results,
                message=f"Found {len(results)} picks for matchup",
                execution_time=execution_time,
                query_type="matchup_filter",
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, execution_time)
            return QueryResult(
                success=False,
                data=[],
                message=f"Error: {str(e)}",
                execution_time=execution_time,
                query_type="matchup_filter",
                timestamp=start_time
            )
            
    def query_high_confidence(self, threshold: int = 100) -> QueryResult:
        """Query high confidence picks"""
        start_time = datetime.now()
        self.logger.info(f"Query high confidence (threshold: {threshold})")
        
        try:
            data = self.load_csv_data('consensus_library/covers_contest_picks.csv')
            results = []
            
            for row in data:
                try:
                    confidence = int(row.get('Confidence', 0) or row.get('Consensus Count', 0) or 0)
                    if confidence >= threshold:
                        results.append(row)
                except (ValueError, TypeError):
                    continue
                    
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(True, execution_time)
            
            return QueryResult(
                success=True,
                data=results,
                message=f"Found {len(results)} high-confidence picks",
                execution_time=execution_time,
                query_type="confidence_filter",
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, execution_time)
            return QueryResult(
                success=False,
                data=[],
                message=f"Error: {str(e)}",
                execution_time=execution_time,
                query_type="confidence_filter",
                timestamp=start_time
            )
            
    def get_consensus_summary(self) -> QueryResult:
        """Get summary statistics of consensus data"""
        start_time = datetime.now()
        self.logger.info("Generating consensus summary")
        
        try:
            data = self.load_csv_data('consensus_library/covers_contest_picks.csv')
            
            # Calculate statistics
            total_picks = len(data)
            sports = {}
            games = set()
            confidence_values = []
            
            for row in data:
                sport = row.get('Sport', 'Unknown')
                sports[sport] = sports.get(sport, 0) + 1
                games.add(row.get('Game', 'Unknown'))
                try:
                    conf = int(row.get('Confidence', 0) or row.get('Consensus Count', 0) or 0)
                    confidence_values.append(conf)
                except (ValueError, TypeError):
                    pass
                    
            summary = {
                'total_picks': total_picks,
                'unique_games': len(games),
                'sports_breakdown': sports,
                'avg_confidence': sum(confidence_values) / len(confidence_values) if confidence_values else 0,
                'max_confidence': max(confidence_values) if confidence_values else 0
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(True, execution_time)
            
            return QueryResult(
                success=True,
                data=summary,
                message="Consensus summary generated",
                execution_time=execution_time,
                query_type="summary",
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, execution_time)
            return QueryResult(
                success=False,
                data={},
                message=f"Error: {str(e)}",
                execution_time=execution_time,
                query_type="summary",
                timestamp=start_time
            )
            
    def _update_stats(self, success: bool, execution_time: float):
        """Update query statistics"""
        self.query_stats['total_queries'] += 1
        if success:
            self.query_stats['successful_queries'] += 1
        else:
            self.query_stats['failed_queries'] += 1
            
        # Update average execution time
        n = self.query_stats['total_queries']
        old_avg = self.query_stats['avg_execution_time']
        self.query_stats['avg_execution_time'] = ((n - 1) * old_avg + execution_time) / n
        
    def get_stats(self) -> Dict:
        """Get query statistics"""
        return {
            **self.query_stats,
            'cache_size': len(self.data_cache),
            'cache_keys': list(self.data_cache.keys())
        }
        
    def clear_cache(self):
        """Clear data cache"""
        self.data_cache.clear()
        self.logger.info("Data cache cleared")
        
    def close(self):
        """Clean up resources"""
        if self.db_connection:
            self.db_connection.close()
            self.logger.info("Database connection closed")

def setup_logging(log_level: LogLevel = LogLevel.INFO, log_file: str = None) -> logging.Logger:
    """Setup logging with file and console handlers"""
    logger = logging.getLogger('HPQT')
    logger.setLevel(log_level.value)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level.value)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"hpqt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    else:
        log_file = Path(log_file)
        
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

def interactive_mode(tool: HandicappingQueryTool, logger: logging.Logger):
    """Run interactive query mode"""
    print("\n" + "=" * 60)
    print("HANDICAPPING PROGRAM QUERY TOOL - INTERACTIVE MODE")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  sport <sport_name>     - Query by sport (nba, nfl, nhl, etc.)")
    print("  matchup <team1> [team2] - Query by matchup")
    print("  confidence <threshold> - Query high confidence picks")
    print("  summary               - Show consensus summary")
    print("  stats                 - Show query statistics")
    print("  clear                 - Clear data cache")
    print("  help                  - Show this help message")
    print("  quit                  - Exit the tool")
    print("=" * 60 + "\n")
    
    while True:
        try:
            command = input("HPQT> ").strip()
            if not command:
                continue
                
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:]
            
            if cmd == 'quit' or cmd == 'exit':
                print("Exiting...")
                break
                
            elif cmd == 'help':
                print("\nCommands:")
                print("  sport <sport_name>     - Query by sport")
                print("  matchup <team1> [team2] - Query by matchup")
                print("  confidence <threshold> - Query high confidence picks")
                print("  summary               - Show consensus summary")
                print("  stats                 - Show query statistics")
                print("  clear                 - Clear data cache")
                print("  quit                  - Exit the tool\n")
                
            elif cmd == 'sport':
                if not args:
                    print("Error: sport name required")
                    continue
                sport = args[0]
                result = tool.query_by_sport(sport)
                _display_result(result)
                
            elif cmd == 'matchup':
                if len(args) < 1:
                    print("Error: at least one team required")
                    continue
                team1 = args[0]
                team2 = args[1] if len(args) > 1 else None
                result = tool.query_by_matchup(team1, team2)
                _display_result(result)
                
            elif cmd == 'confidence':
                threshold = int(args[0]) if args else 100
                result = tool.query_high_confidence(threshold)
                _display_result(result)
                
            elif cmd == 'summary':
                result = tool.get_consensus_summary()
                _display_result(result)
                
            elif cmd == 'stats':
                stats = tool.get_stats()
                print("\n" + "-" * 40)
                print("QUERY STATISTICS")
                print("-" * 40)
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                print("-" * 40 + "\n")
                
            elif cmd == 'clear':
                tool.clear_cache()
                print("Cache cleared.\n")
                
            else:
                print(f"Unknown command: {cmd}")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"Error: {e}")

def _display_result(result: QueryResult):
    """Display query result in formatted way"""
    print("\n" + "-" * 60)
    print(f"Query Result: {'[SUCCESS]' if result.success else '[FAILED]'}")
    print("-" * 60)
    print(f"Type: {result.query_type}")
    print(f"Message: {result.message}")
    print(f"Execution Time: {result.execution_time:.4f}s")
    print(f"Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result.success and result.data:
        if isinstance(result.data, list):
            print(f"\nResults ({len(result.data)} items):")
            for i, item in enumerate(result.data[:5], 1):
                if isinstance(item, dict):
                    print(f"  {i}. {dict(item)}")
                else:
                    print(f"  {i}. {item}")
            if len(result.data) > 5:
                print(f"  ... and {len(result.data) - 5} more items")
        elif isinstance(result.data, dict):
            print("\nResults:")
            for key, value in result.data.items():
                print(f"  {key}: {value}")
    print("-" * 60 + "\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Handicapping Program Query Tool (HPQT)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python handicapping_query_tool.py --validate
  python handicapping_query_tool.py --interactive
  python handicapping_query_tool.py --sport NBA
  python handicapping_query_tool.py --matchup "Lakers" "Warriors"
  python handicapping_query_tool.py --confidence 150
        '''
    )
    
    parser.add_argument('--validate', action='store_true', help='Run environment validation only')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run interactive mode')
    parser.add_argument('--sport', type=str, help='Query by sport')
    parser.add_argument('--matchup', nargs='+', help='Query by matchup (team1 [team2])')
    parser.add_argument('--confidence', type=int, help='Query high confidence picks')
    parser.add_argument('--summary', action='store_true', help='Show consensus summary')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--log-file', type=str, help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = LogLevel[args.log_level]
    logger = setup_logging(log_level, args.log_file)
    
    # Print banner
    logger.info("=" * 60)
    logger.info("HANDICAPPING PROGRAM QUERY TOOL v1.0")
    logger.info("=" * 60)
    
    # Run validation
    validator = EnvironmentValidator(logger)
    valid, issues, warnings = validator.validate()
    
    if not valid:
        logger.error("Environment validation failed. Please fix the issues above.")
        sys.exit(1)
        
    if args.validate:
        print("\nValidation complete. Environment is ready.")
        sys.exit(0)
        
    # Initialize query tool
    tool = HandicappingQueryTool(logger)
    tool.initialize_database()
    
    # Execute based on arguments
    if args.interactive or len(sys.argv) == 1:
        interactive_mode(tool, logger)
    elif args.sport:
        result = tool.query_by_sport(args.sport)
        _display_result(result)
    elif args.matchup:
        team1 = args.matchup[0]
        team2 = args.matchup[1] if len(args.matchup) > 1 else None
        result = tool.query_by_matchup(team1, team2)
        _display_result(result)
    elif args.confidence:
        result = tool.query_high_confidence(args.confidence)
        _display_result(result)
    elif args.summary:
        result = tool.get_consensus_summary()
        _display_result(result)
    else:
        parser.print_help()
        
    # Cleanup
    tool.close()
    logger.info("HandicappingQueryTool shutdown complete")

if __name__ == '__main__':
    main()
