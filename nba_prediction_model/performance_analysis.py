"""
Comprehensive Performance Analysis
Advanced metrics for betting model validation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json


class PerformanceAnalyzer:
    """
    Advanced performance metrics for betting models
    """

    def __init__(self, bets_df):
        """
        Initialize analyzer with betting history

        Args:
            bets_df: DataFrame with bet-by-bet results
        """
        self.bets = bets_df
        self.metrics = {}

    def calculate_sharpe_ratio(self, risk_free_rate=0.04):
        """
        Calculate Sharpe Ratio (risk-adjusted returns)

        Sharpe = (Return - RiskFreeRate) / StdDev

        Professional sports bettors target Sharpe > 1.0

        Args:
            risk_free_rate: Annual risk-free rate (default 4%)

        Returns:
            Sharpe ratio
        """
        if len(self.bets) == 0:
            return 0

        # Calculate returns per bet
        self.bets['return_pct'] = self.bets['profit'] / self.bets['bet_size']

        mean_return = self.bets['return_pct'].mean()
        std_return = self.bets['return_pct'].std()

        if std_return == 0:
            return 0

        # Adjust risk-free rate to per-bet basis
        # Assuming ~200 bets per season, ~3 bets per day
        risk_free_per_bet = risk_free_rate / 200

        sharpe = (mean_return - risk_free_per_bet) / std_return

        return sharpe

    def calculate_sortino_ratio(self, target_return=0, risk_free_rate=0.04):
        """
        Calculate Sortino Ratio (downside risk-adjusted returns)

        Only considers downside volatility (losses), not upside

        Args:
            target_return: Minimum acceptable return
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio
        """
        if len(self.bets) == 0:
            return 0

        self.bets['return_pct'] = self.bets['profit'] / self.bets['bet_size']

        mean_return = self.bets['return_pct'].mean()

        # Calculate downside deviation (only negative returns)
        downside_returns = self.bets[self.bets['return_pct'] < target_return]['return_pct']

        if len(downside_returns) == 0:
            return np.inf  # No downside!

        downside_std = np.sqrt(((downside_returns - target_return) ** 2).mean())

        if downside_std == 0:
            return 0

        risk_free_per_bet = risk_free_rate / 200
        sortino = (mean_return - risk_free_per_bet) / downside_std

        return sortino

    def calculate_calmar_ratio(self):
        """
        Calculate Calmar Ratio (return / max drawdown)

        Measures return relative to worst drawdown

        Professional target: > 0.5

        Returns:
            Calmar ratio
        """
        if len(self.bets) == 0:
            return 0

        # Calculate cumulative returns
        self.bets['cumulative_return'] = (self.bets['profit'].cumsum() /
                                         self.bets.iloc[0]['bet_size'])

        # Calculate max drawdown
        self.bets['peak'] = self.bets['cumulative_return'].cummax()
        self.bets['drawdown_pct'] = ((self.bets['peak'] - self.bets['cumulative_return']) /
                                     (self.bets['peak'].abs() + 1)) * 100

        max_drawdown = self.bets['drawdown_pct'].max()

        if max_drawdown == 0:
            return np.inf

        # Total return
        total_return_pct = self.bets['cumulative_return'].iloc[-1] * 100

        calmar = total_return_pct / max_drawdown

        return calmar

    def analyze_streaks(self):
        """
        Analyze winning and losing streaks

        Returns:
            Dictionary with streak statistics
        """
        if len(self.bets) == 0:
            return {}

        wins = (self.bets['outcome'] == 'WIN').astype(int)

        # Calculate streaks
        streaks = []
        current_streak = 0
        streak_type = None

        for win in wins:
            if win == 1:
                if streak_type == 'win':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streaks.append({'type': streak_type, 'length': current_streak})
                    current_streak = 1
                    streak_type = 'win'
            else:
                if streak_type == 'loss':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streaks.append({'type': streak_type, 'length': current_streak})
                    current_streak = 1
                    streak_type = 'loss'

        # Add final streak
        if current_streak > 0:
            streaks.append({'type': streak_type, 'length': current_streak})

        streaks_df = pd.DataFrame(streaks)

        win_streaks = streaks_df[streaks_df['type'] == 'win']['length']
        loss_streaks = streaks_df[streaks_df['type'] == 'loss']['length']

        return {
            'longest_win_streak': int(win_streaks.max()) if len(win_streaks) > 0 else 0,
            'longest_loss_streak': int(loss_streaks.max()) if len(loss_streaks) > 0 else 0,
            'avg_win_streak': float(win_streaks.mean()) if len(win_streaks) > 0 else 0,
            'avg_loss_streak': float(loss_streaks.mean()) if len(loss_streaks) > 0 else 0,
            'total_streaks': len(streaks)
        }

    def analyze_edge_threshold(self):
        """
        Analyze performance by edge threshold

        Determines optimal minimum edge for placing bets

        Returns:
            DataFrame with performance by edge threshold
        """
        if len(self.bets) == 0:
            return pd.DataFrame()

        thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
        results = []

        for threshold in thresholds:
            filtered_bets = self.bets[self.bets['edge'] >= threshold]

            if len(filtered_bets) > 0:
                wins = len(filtered_bets[filtered_bets['outcome'] == 'WIN'])
                total = len(filtered_bets)
                win_rate = wins / total
                total_profit = filtered_bets['profit'].sum()
                roi = (total_profit / filtered_bets['bet_size'].sum()) * 100

                results.append({
                    'edge_threshold': threshold,
                    'total_bets': total,
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'roi_percent': roi
                })

        return pd.DataFrame(results)

    def analyze_by_bet_type(self):
        """
        Compare performance between spread and total bets

        Returns:
            Dictionary with performance by bet type
        """
        results = {}

        for bet_type in self.bets['bet_type'].unique():
            type_bets = self.bets[self.bets['bet_type'] == bet_type]

            if len(type_bets) > 0:
                wins = len(type_bets[type_bets['outcome'] == 'WIN'])
                win_rate = wins / len(type_bets)
                total_profit = type_bets['profit'].sum()
                avg_bet = type_bets['bet_size'].mean()
                roi = (total_profit / type_bets['bet_size'].sum()) * 100

                results[bet_type] = {
                    'total_bets': len(type_bets),
                    'wins': wins,
                    'losses': len(type_bets) - wins,
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'avg_bet_size': avg_bet,
                    'roi_percent': roi
                }

        return results

    def analyze_by_month(self):
        """
        Analyze performance by month

        Returns:
            DataFrame with monthly performance
        """
        if len(self.bets) == 0:
            return pd.DataFrame()

        self.bets['month'] = pd.to_datetime(self.bets['game_date']).dt.to_period('M')

        monthly = self.bets.groupby('month').agg({
            'bet_size': ['count', 'sum'],
            'profit': 'sum',
            'outcome': lambda x: (x == 'WIN').sum()
        }).reset_index()

        monthly.columns = ['month', 'total_bets', 'total_wagered', 'profit', 'wins']
        monthly['win_rate'] = monthly['wins'] / monthly['total_bets']
        monthly['roi_percent'] = (monthly['profit'] / monthly['total_wagered']) * 100

        return monthly

    def calculate_kelly_optimal(self):
        """
        Calculate optimal Kelly fraction based on historical performance

        Kelly = (p * b - q) / b
        where p = win probability, q = loss probability, b = odds

        Returns:
            Optimal Kelly fraction
        """
        if len(self.bets) == 0:
            return 0

        # Calculate historical win probability
        p = (self.bets['outcome'] == 'WIN').mean()
        q = 1 - p

        # Assuming -110 odds (b = 0.909)
        b = 0.909

        kelly = (p * b - q) / b

        # Fractional Kelly (1/4 Kelly is common for safety)
        safe_kelly = kelly / 4

        return {
            'full_kelly': kelly,
            'quarter_kelly': safe_kelly,
            'historical_win_rate': p,
            'recommended': safe_kelly if safe_kelly > 0 else 0
        }

    def generate_comprehensive_report(self):
        """
        Generate complete performance analysis

        Returns:
            Dictionary with all metrics
        """
        print("\n" + "="*60)
        print("COMPREHENSIVE PERFORMANCE ANALYSIS")
        print("="*60)

        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_bets': len(self.bets)
        }

        if len(self.bets) == 0:
            print("No bets to analyze")
            return report

        # Basic metrics
        wins = len(self.bets[self.bets['outcome'] == 'WIN'])
        losses = len(self.bets[self.bets['outcome'] == 'LOSS'])
        win_rate = wins / len(self.bets)
        total_profit = self.bets['profit'].sum()
        total_wagered = self.bets['bet_size'].sum()
        roi = (total_profit / total_wagered) * 100

        report['basic_metrics'] = {
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_wagered': total_wagered,
            'roi_percent': roi,
            'breakeven_rate': 0.524  # Need 52.4% at -110 odds
        }

        print(f"\nBasic Metrics:")
        print(f"  Total Bets: {len(self.bets)}")
        print(f"  Win Rate: {win_rate:.1%} ({wins}W-{losses}L)")
        print(f"  ROI: {roi:.2f}%")
        print(f"  Total Profit: ${total_profit:,.2f}")

        # Risk-adjusted metrics
        sharpe = self.calculate_sharpe_ratio()
        sortino = self.calculate_sortino_ratio()
        calmar = self.calculate_calmar_ratio()

        report['risk_adjusted'] = {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar
        }

        print(f"\nRisk-Adjusted Metrics:")
        print(f"  Sharpe Ratio: {sharpe:.3f} (target: >1.0)")
        print(f"  Sortino Ratio: {sortino:.3f} (target: >1.5)")
        print(f"  Calmar Ratio: {calmar:.3f} (target: >0.5)")

        # Streaks
        streaks = self.analyze_streaks()
        report['streaks'] = streaks

        print(f"\nStreak Analysis:")
        print(f"  Longest Win Streak: {streaks['longest_win_streak']}")
        print(f"  Longest Loss Streak: {streaks['longest_loss_streak']}")
        print(f"  Avg Win Streak: {streaks['avg_win_streak']:.1f}")
        print(f"  Avg Loss Streak: {streaks['avg_loss_streak']:.1f}")

        # Edge threshold analysis
        edge_analysis = self.analyze_edge_threshold()
        if not edge_analysis.empty:
            report['edge_analysis'] = edge_analysis.to_dict('records')

            print(f"\nOptimal Edge Threshold:")
            best_roi_row = edge_analysis.loc[edge_analysis['roi_percent'].idxmax()]
            print(f"  Best ROI at {best_roi_row['edge_threshold']:.1f} point edge")
            print(f"  ROI: {best_roi_row['roi_percent']:.2f}%")
            print(f"  Bets: {best_roi_row['total_bets']}")

        # Bet type analysis
        by_type = self.analyze_by_bet_type()
        report['by_bet_type'] = by_type

        print(f"\nPerformance by Bet Type:")
        for bet_type, stats in by_type.items():
            print(f"  {bet_type.upper()}:")
            print(f"    Win Rate: {stats['win_rate']:.1%}")
            print(f"    ROI: {stats['roi_percent']:.2f}%")
            print(f"    Profit: ${stats['total_profit']:,.2f}")

        # Kelly sizing
        kelly = self.calculate_kelly_optimal()
        report['kelly_criterion'] = kelly

        print(f"\nKelly Criterion Analysis:")
        print(f"  Historical Win Rate: {kelly['historical_win_rate']:.1%}")
        print(f"  Full Kelly: {kelly['full_kelly']:.3f}")
        print(f"  Quarter Kelly (recommended): {kelly['quarter_kelly']:.3f}")

        # Monthly performance
        monthly = self.analyze_by_month()
        if not monthly.empty:
            report['monthly_performance'] = monthly.to_dict('records')

            print(f"\nMonthly Performance:")
            for _, row in monthly.iterrows():
                print(f"  {row['month']}: {row['win_rate']:.1%} WR, ${row['profit']:,.0f} profit")

        print("="*60)

        return report


def main():
    """Run comprehensive analysis on backtest results"""
    print("="*60)
    print("PERFORMANCE ANALYSIS")
    print("="*60)

    # Load backtest results
    try:
        bets_df = pd.read_csv('nba_prediction_model/data/outputs/backtest_bets.csv')
        print(f"Loaded {len(bets_df)} bets from backtest")
    except FileNotFoundError:
        print("ERROR: No backtest results found")
        print("Run backtest.py first")
        return

    # Analyze
    analyzer = PerformanceAnalyzer(bets_df)
    report = analyzer.generate_comprehensive_report()

    # Save report
    output_path = 'nba_prediction_model/data/outputs/performance_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nAnalysis saved: {output_path}")


if __name__ == "__main__":
    main()
