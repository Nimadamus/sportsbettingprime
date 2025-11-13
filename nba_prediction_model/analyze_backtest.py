"""Quick analysis of backtest prediction quality"""
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error

# Load predictions
df = pd.read_csv('nba_prediction_model/data/outputs/backtest_predictions.csv')

# Analyze prediction accuracy
spread_mae = mean_absolute_error(df['actual_spread'], df['predicted_spread'])
total_mae = mean_absolute_error(df['actual_total'], df['predicted_total'])

# Correlation
spread_corr = df[['predicted_spread', 'actual_spread']].corr().iloc[0, 1]
total_corr = df[['predicted_total', 'actual_total']].corr().iloc[0, 1]

# Direction accuracy
df['spread_direction_correct'] = ((df['predicted_spread'] > 0) == (df['actual_spread'] > 0))
direction_acc = df['spread_direction_correct'].mean()

# Model vs simulated Vegas
df['beat_vegas_spread'] = np.abs(df['predicted_spread'] - df['actual_spread']) < np.abs(df['vegas_spread'] - df['actual_spread'])
beat_vegas = df['beat_vegas_spread'].mean()

print('='*60)
print('WALK-FORWARD BACKTEST - PREDICTION QUALITY')
print('='*60)
print(f'Total predictions: {len(df)}')
print(f'')
print(f'Spread Prediction:')
print(f'  MAE: {spread_mae:.2f} points')
print(f'  Correlation: {spread_corr:.3f}')
print(f'  Direction accuracy: {direction_acc:.1%}')
print(f'  Beat simulated Vegas: {beat_vegas:.1%}')
print(f'')
print(f'Total Prediction:')
print(f'  MAE: {total_mae:.2f} points')
print(f'  Correlation: {total_corr:.3f}')
print(f'')
print(f'CRITICAL FINDINGS:')
print(f'  - 71% win rate from betting simulation is FAKE')
print(f'  - Simulated Vegas lines are too easy to beat')
print(f'  - Real Vegas lines needed for honest assessment')
print(f'  - MAE of {spread_mae:.1f} is the real metric to trust')
print('='*60)
