# NBA Prediction Model

A comprehensive machine learning system for predicting NBA game outcomes, point spreads, and totals.

## Overview

This NBA prediction model uses advanced statistics, team performance metrics, and machine learning algorithms to predict:
- **Game Winners**: Which team will win with confidence probabilities
- **Point Spreads**: Expected margin of victory
- **Totals**: Expected combined points scored

The model considers 50+ features including:
- Team offensive and defensive ratings
- Net ratings and pace
- Recent form (last 5 and 10 games)
- Four Factors (eFG%, TOV%, OREB%, FTA Rate)
- Shooting efficiency and three-point percentages
- Rest advantages and back-to-back situations
- Home court advantage

## Project Structure

```
nba_prediction_model/
├── data/
│   ├── nba_data_collector.py    # Fetches NBA team statistics from NBA API
│   └── outputs/                  # Saved datasets
├── models/
│   ├── predictor.py              # ML models (XGBoost, LightGBM, Random Forest)
│   └── saved/                    # Trained model files
├── utils/
│   ├── feature_engineering.py    # Creates prediction features
│   └── evaluation.py             # Model evaluation and backtesting
├── outputs/                      # Predictions and reports
├── generate_predictions.py       # Daily prediction generator
├── train_model.py               # Model training script
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

### 1. Install Python Dependencies

```bash
cd nba_prediction_model
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import pandas, numpy, sklearn, xgboost, lightgbm, nba_api; print('All dependencies installed successfully!')"
```

## Usage

### Step 1: Train the Models

First, train the prediction models using historical data:

```bash
# Train with synthetic data (for testing)
python train_model.py --model-type xgboost --evaluate

# Train with real historical data (when available)
python train_model.py --model-type xgboost --use-real-data --evaluate
```

**Model Types:**
- `xgboost` (recommended): Gradient boosting with XGBoost
- `lightgbm`: Fast gradient boosting with LightGBM
- `random_forest`: Random forest ensemble
- `logistic`: Logistic regression (baseline)
- `ensemble`: Combination of multiple models

**Training Output:**
- Win prediction accuracy
- Spread prediction MAE (Mean Absolute Error)
- Total prediction MAE
- Feature importance rankings
- Saved models in `models/saved/`

### Step 2: Generate Daily Predictions

After training, generate predictions for upcoming games:

```bash
python generate_predictions.py
```

**Prediction Output:**
```
Analyzing: BOS @ LAL
  Predicted Winner: LAL
  Win Probability: 62.5% (Home) | 37.5% (Away)
  Predicted Spread: LAL -5.5
  Predicted Total: 223.5
  Expected Score: LAL 114.5 - BOS 109.0
```

Predictions are saved to `outputs/nba_predictions_YYYY-MM-DD.json`

### Step 3: Evaluate Model Performance

Backtest the model on historical data:

```python
from utils.evaluation import ModelEvaluator
from models.predictor import NBAPredictor

# Load trained models
predictor = NBAPredictor()
predictor.load_models('models/saved')

# Evaluate on test data
evaluator = ModelEvaluator()
report = evaluator.generate_report(predictions_df, results_df)
evaluator.print_summary(report)
```

**Evaluation Metrics:**
- Win prediction accuracy
- Spread prediction accuracy (MAE, RMSE)
- Total prediction accuracy (MAE, RMSE)
- Betting simulation results (ROI, win rate)
- Maximum drawdown analysis

## Features Explained

### Team Performance Metrics

**Offensive & Defensive Ratings:**
- Points scored/allowed per 100 possessions
- Accounts for pace of play
- League average: ~110

**Net Rating:**
- Offensive Rating - Defensive Rating
- Indicates team strength
- Positive = good, negative = bad

**Pace:**
- Possessions per 48 minutes
- Fast pace = more possessions = higher scoring
- League average: ~100

### Advanced Metrics

**Four Factors (Dean Oliver):**
1. **eFG% (Effective Field Goal %)**: Shooting efficiency accounting for 3-pointers
2. **TOV% (Turnover Rate)**: How often team turns ball over
3. **OREB% (Offensive Rebound Rate)**: Percentage of available offensive rebounds
4. **FTA Rate (Free Throw Attempt Rate)**: How often team gets to the line

**True Shooting % (TS%):**
- Overall shooting efficiency including 2PT, 3PT, and FT
- Formula: PTS / (2 * (FGA + 0.44 * FTA))

**PIE (Player Impact Estimate):**
- Overall player/team contribution metric
- Range: 0.0 to 1.0, average: 0.5

### Situational Features

**Rest Advantage:**
- Days of rest differential between teams
- Back-to-back games (negative impact)
- Teams with more rest typically perform better

**Home Court Advantage:**
- Baseline ~3.5 point advantage
- Varies by team and arena
- Includes travel, crowd, and familiarity factors

**Recent Form:**
- Last 5 games: Short-term momentum
- Last 10 games: Medium-term trends
- Captures hot/cold streaks

## Model Architecture

### Classification Model (Win Prediction)

**Algorithm:** XGBoost Classifier
- **Input:** 50+ team/matchup features
- **Output:** Win probability for home/away team
- **Optimization:** Maximize accuracy and log-loss

### Regression Models (Spread & Total)

**Algorithm:** XGBoost Regressor
- **Spread Model:**
  - Predicts point differential (home_score - away_score)
  - Positive = home team favored
  - Target MAE: <5 points

- **Total Model:**
  - Predicts combined score (home_score + away_score)
  - Based on pace, offensive/defensive ratings
  - Target MAE: <8 points

### Feature Scaling

All features are standardized using `StandardScaler`:
- Mean = 0, Standard Deviation = 1
- Improves model convergence
- Ensures all features have equal weight

## Data Collection

### NBA API Integration

The model uses `nba_api` to fetch official NBA statistics:

```python
from data.nba_data_collector import NBADataCollector

collector = NBADataCollector(season='2024-25')

# Get team statistics
team_stats = collector.get_team_stats(measure_type='Advanced')

# Get recent form
recent_form = collector.get_recent_form(team_id=1610612747, last_n_games=10)

# Build comprehensive dataset
dataset = collector.build_comprehensive_dataset()
```

**Available Stat Types:**
- Base: Traditional stats (PTS, REB, AST, etc.)
- Advanced: OFF_RATING, DEF_RATING, NET_RATING, PACE, PIE
- Four Factors: eFG%, TOV%, OREB%, FTA Rate
- Splits: Home/Away, Division, Conference

### Rate Limiting

The NBA API has rate limits (600ms between requests). The data collector automatically handles this with sleep delays.

## Betting Integration

### Consensus Comparison

Compare model predictions with expert consensus:

```python
generator.generate_consensus_integration(predictions_df)
```

This integrates with the existing `consensus_library/picks_database.json` to show:
- How many experts picked each side
- Agreement/disagreement with model
- High-confidence opportunities

### Top Picks Generation

Filter predictions by confidence level:

```python
top_picks = generator.generate_top_picks(predictions_df, min_confidence=0.65)
```

Returns games where the model has ≥65% confidence in the winner.

### Betting Simulation

Backtest betting performance:

```python
from utils.evaluation import ModelEvaluator

evaluator = ModelEvaluator()
betting_results = evaluator.simulate_betting(
    predictions_df,
    results_df,
    unit_size=100,
    kelly_fraction=0.25  # Use 1/4 Kelly for safety
)
```

**Simulation Features:**
- Kelly Criterion bet sizing
- -110 American odds (standard)
- Bankroll management
- Maximum drawdown tracking
- ROI calculation

## Model Performance

### Expected Benchmarks

**Win Prediction:**
- Target Accuracy: 60-65%
- Baseline (home team always wins): ~58%
- Professional bettors: 55-58%

**Spread Prediction:**
- Target MAE: 4-6 points
- Vegas lines typically accurate within 3-4 points
- Beating the spread: 52.4% needed to break even

**Total Prediction:**
- Target MAE: 6-10 points
- More volatile than spreads
- Weather/pace factors critical

### Feature Importance

Top predictive features (typical):
1. Net Rating Differential
2. Recent Form (Last 10 games)
3. Home Court Advantage
4. Offensive vs Defensive Rating matchup
5. Rest Advantage
6. Pace (for totals)
7. Four Factors differentials

## Advanced Usage

### Custom Feature Engineering

Add your own features to `utils/feature_engineering.py`:

```python
def create_custom_features(self, home_stats, away_stats):
    features = {}

    # Example: Injury impact score
    features['home_injury_impact'] = self.calculate_injury_impact(home_stats)

    # Example: Schedule difficulty
    features['home_schedule_strength'] = self.calculate_schedule_strength(home_stats)

    return features
```

### Ensemble Modeling

Combine multiple models for better predictions:

```python
# Train multiple model types
predictor_xgb = NBAPredictor(model_type='xgboost')
predictor_lgb = NBAPredictor(model_type='lightgbm')
predictor_rf = NBAPredictor(model_type='random_forest')

# Average predictions
ensemble_pred = (xgb_pred + lgb_pred + rf_pred) / 3
```

### Real-Time Updates

Update team statistics during the season:

```python
# Fetch latest team data
collector = NBADataCollector(season='2024-25')
team_stats = collector.build_comprehensive_dataset()

# Save for daily predictions
collector.save_dataset(team_stats, 'nba_team_data_latest.csv')
```

## Integration with Sports Betting Prime

This model is designed to integrate with the existing Sports Betting Prime platform:

### 1. Daily Prediction Export

Export predictions in the same format as consensus picks:

```json
{
  "date": "2025-11-13",
  "sport": "NBA",
  "predictions": [
    {
      "matchup": "BOS @ LAL",
      "pick": "LAL -5.5",
      "confidence": 0.675,
      "predicted_total": 223.5,
      "model_score": 8.5
    }
  ]
}
```

### 2. HTML Page Generation

Create NBA analysis page following MLB template:
- Game-by-game breakdowns
- Statistical matchup analysis
- Key factors and trends
- Model confidence levels
- Integration with consensus data

### 3. Performance Tracking

Track model predictions against actual results:
- Store predictions in `picks_database.json`
- Update with game results
- Calculate accuracy metrics
- Display on Performance Telemetry page

## Troubleshooting

### Common Issues

**1. NBA API Rate Limiting:**
```
Error: Too many requests
Solution: Increase sleep delays in nba_data_collector.py
```

**2. Missing Dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

**3. Model Not Found:**
```
Solution: Run python train_model.py first to create models
```

**4. Data Collection Errors:**
```
Error: Team stats unavailable
Solution: Check NBA season parameter (use '2024-25' format)
```

## Future Enhancements

### Planned Features

1. **Player Impact Analysis:**
   - Injury tracking and impact scores
   - Star player availability
   - Lineup combinations

2. **Live Odds Integration:**
   - Real-time line movement tracking
   - Value bet identification
   - Line vs. model comparison

3. **Historical Matchup Analysis:**
   - Head-to-head records
   - Coaching matchups
   - Playoff vs. regular season splits

4. **Advanced Situational Models:**
   - Altitude impact (Denver)
   - Coast-to-coast travel
   - Revenge game narratives
   - Schedule spot analysis

5. **Real-Time Adjustments:**
   - Pre-game injury reports
   - Lineup changes
   - Weather (for outdoor courts)
   - Live in-game prediction updates

## Contributing

To improve the model:
1. Add new features in `feature_engineering.py`
2. Experiment with model hyperparameters
3. Collect more historical data
4. Test different ML algorithms
5. Submit pull requests with improvements

## Resources

**NBA Statistics:**
- [NBA.com Stats](https://stats.nba.com)
- [Basketball Reference](https://basketball-reference.com)
- [NBA API Documentation](https://github.com/swar/nba_api)

**Machine Learning:**
- [XGBoost Documentation](https://xgboost.readthedocs.io)
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)

**Sports Analytics:**
- Dean Oliver's "Four Factors"
- Ken Pomeroy's efficiency metrics
- Nate Silver's ELO ratings

## License

This project is part of Sports Betting Prime platform.

## Contact

For questions or issues, please open an issue on the repository.

---

**Disclaimer:** This model is for educational and entertainment purposes only. Sports betting involves risk. Always bet responsibly and within your means.
