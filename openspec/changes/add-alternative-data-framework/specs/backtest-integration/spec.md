# Specification: Backtest Engine Integration with Alternative Data

## MODIFIED Requirements

### Requirement: Extended Backtest Engine Interface

The system SHALL modify backtest engine to accept and process alternative data signals alongside price-based signals.

#### Capability
- System SHALL Accept alternative data indicators in backtest configuration
- System SHALL Combine alternative data signals with price-based signals
- System SHALL Generate buy/sell signals from alternative data
- System SHALL Report on alternative data signal contribution
- System SHALL Compare performance with/without alternative data

#### Scenario: Backtesting Strategy with HIBOR Signal
```
Given: EnhancedBacktestEngine, price data for 0939.HK, HIBOR rates
When: test_engine.backtest_with_alt_data(
        symbol='0939.HK',
        strategy_class=BankStockHIBORStrategy,
        price_data=price_df,
        alt_data={'hibor_on': hibor_df},
        start_date=date(2024, 1, 1),
        end_date=date(2024, 10, 18),
        initial_capital=100000
      )
Then:
  - Engine loads price data + HIBOR data
  - Engine aligns data to common trading dates
  - For each trading day:
    - Strategy.generate_signals(price_data, alt_data)
    - Signal processing: BUY, SELL, HOLD
    - Position management: Track holdings
    - P&L calculation: Daily profit/loss
  - Returns BacktestResult with metrics:
    - Total return: 15.8%
    - Sharpe ratio: 0.84
    - Alt data signal count: 35
    - Alt data signal win rate: 58%
```

#### Scenario: Comparing Performance With and Without Alternative Data
```
Given: Two backtest runs for same strategy (with and without HIBOR)
When: Analyst reviews both backtest reports
Then:
  - Strategy without HIBOR:
    - Annual return: 12.5%
    - Sharpe ratio: 0.58
    - Max drawdown: -22%

  - Strategy with HIBOR:
    - Annual return: 15.8%
    - Sharpe ratio: 0.84
    - Max drawdown: -18%

  - Analysis shows:
    - +3.3% additional return from HIBOR signals
    - +45% Sharpe improvement
    - -4% lower drawdown (better risk control)
    - HIBOR signals statistically significant contribution
```

---

### Requirement: Strategy Signal Generation with Alternative Data

The system SHALL extend strategy base class to accept alternative data in signal generation.

#### Capability
- System SHALL Modified generate_signals() to accept optional alt_data parameter
- System SHALL Multiple signal sources (price and alternative data)
- System SHALL Signal combination/weighting strategies
- System SHALL Backward compatible with price-only strategies

#### Scenario: Strategy Using Price + HIBOR Signals
```
Given: BankStockHIBORStrategy inherits from Strategy
When: Strategy generates signals for each date
Then:
  - Price-based signal generation:
    - Calculate technical indicators: MA, RSI, MACD
    - Generate signal: BUY if (close > MA50 and RSI < 70)
    - Confidence: price_signal_strength = 0.7

  - Alternative data signal generation:
    - Calculate HIBOR trend: HIBOR_on declining
    - Generate signal: BUY if (HIBOR_change < -0.05 bps)
    - Confidence: alt_signal_strength = 0.8

  - Signal combination:
    - Both agree on BUY: Combined signal strength = (0.7 + 0.8) / 2 = 0.75
    - High confidence → Execute full position
    - Only one agrees: Combined strength = 0.55
    - Lower confidence → Execute reduced position (30%)
    - Disagree: Combined strength = 0.0
    - No trade executed

  - Final output: STRONG_BUY, position_size=100%
```

#### Scenario: Backward Compatibility - Price-Only Strategy
```
Given: Existing strategy inheriting from Strategy (price-only)
When: Strategy.generate_signals(price_data) called without alt_data
Then:
  - Strategy.generate_signals(price_data, alt_data=None) accepted
  - Function uses only price data (alt_data parameter ignored)
  - Backward compatible: Existing strategies work unchanged
  - No modification required to old strategy code
```

---

## ADDED Requirements

### Requirement: Alternative Data Signal Strategies

The system SHALL implement strategies specifically designed to use alternative data signals.

#### Capability
- System SHALL implement AltDataSignalStrategy: multi-signal strategy combining price + alt data
- System SHALL implement CorrelationStrategy: trade high-correlation relationships
- System SHALL implement MacroHedgeStrategy: use macro indicators for portfolio hedging
- System SHALL support configurable signal weighting for different sources

#### Scenario: AltDataSignalStrategy for Bank Stocks
```
Given: Analyst creates strategy to trade 0939.HK using HIBOR + price signals
When: Strategy processes market data
Then:
  - Configuration:
    Strategy: AltDataSignalStrategy
    Symbol: 0939.HK
    Price signals: MA, RSI, MACD (weight=0.5)
    Alt signals: HIBOR_change (weight=0.5)

  - Signal generation for 2024-09-02:
    - Price signals: BUY (RSI=35, oversold)
    - HIBOR signals: BUY (HIBOR down -0.05 bps, favorable)
    - Combined: BUY with high confidence
    - Position: 50% of capital

  - Signal generation for 2024-09-03:
    - Price signals: HOLD (RSI=50)
    - HIBOR signals: BUY (HIBOR still down)
    - Combined: WEAK BUY
    - Position: Add 20% more

  - Strategy flexibly combines multiple signal sources
```

#### Scenario: CorrelationStrategy - Trading Bank Pairs
```
Given: High correlation between HIBOR and bank stocks (corr=-0.65)
When: CorrelationStrategy processes data
Then:
  - Strategy setup:
    - Indicator 1: HIBOR rates (tracking)
    - Indicator 2: 0939.HK price (trading)
    - Expected correlation: -0.65
    - Trade when correlation breaks

  - Daily processing:
    - If HIBOR rising but 0939.HK not falling as expected
      → Indicator out of sync (mean reversion)
      → Signal: SHORT 0939.HK (expecting reversal)

    - If HIBOR falling but 0939.HK not rising as expected
      → Correlation breakdown
      → Signal: LONG 0939.HK (expected bounce)

  - Profitable during regime stability
  - Stop loss when correlation structural changes
```

#### Scenario: MacroHedgeStrategy for Portfolio Protection
```
Given: Portfolio of 10 Hong Kong stocks exposed to macro risks
When: MacroHedgeStrategy runs daily
Then:
  - Macro indicators tracked:
    - HIBOR levels: Interest rate risk
    - Visitor arrivals: Tourism exposure
    - HSI futures: Market beta

  - Hedging logic:
    - If HIBOR rising sharply: Reduce bank stock exposure
    - If visitor arrivals falling: Reduce retail/tourism exposure
    - If HSI futures declining: Reduce portfolio beta via shorts

  - Daily signal:
    - "MACRO_ALERT: Rising HIBOR detected"
    - "Recommendation: Reduce 0939.HK weight by 30%"
    - "Alternative: Buy protective puts on bank ETF"

  - Strategy protects portfolio from macro shocks
```

---

### Requirement: Performance Metrics with Alternative Data

The system SHALL calculate and report alternative data contribution to performance.

#### Capability
- System SHALL calculate signal accuracy: % of correct directional predictions
- System SHALL measure signal contribution: Sharpe impact of each source
- System SHALL track signal frequency: number of signals per period
- System SHALL compute risk-adjusted metrics: alt data adjusted Sharpe

#### Scenario: Computing Signal Accuracy and Contribution
```
Given: Backtest completed with HIBOR signals (35 total signals)
When: BacktestEngine.calculate_metrics_with_alt_data()
Then:
  - Signal Analysis:
    Buy signals: 18
      - Profitable: 15 (83% win rate)
      - Losing: 3 (17% loss rate)
      - Avg profit per winning signal: +2.1%
      - Avg loss per losing signal: -1.5%

    Sell signals: 17
      - Profitable: 10 (59% win rate)
      - Losing: 7 (41% loss rate)
      - Avg profit per winning signal: +1.8%
      - Avg loss per losing signal: -2.2%

  - Overall Metrics:
    - Total signal win rate: 58% (25/43 correct)
    - Signal accuracy comparable to industry standard
    - Avg holding period: 4.2 days

  - Contribution Analysis:
    - Without HIBOR signals: Sharpe = 0.58
    - HIBOR signal contribution: +0.18
    - With HIBOR signals: Sharpe = 0.76
    - Alt data improved Sharpe by 31%
```

---

### Requirement: Alternative Data Signal Validation

The system SHALL ensure alternative data signals are statistically valid and not overfitted.

#### Capability
- System SHALL perform out-of-sample testing for alternative data signals
- System SHALL analyze signal stability across time periods
- System SHALL validate correlations (ensure signals not spurious)
- System SHALL test statistical significance of signals

#### Scenario: Validating HIBOR Signal Stability
```
Given: Backtest run on full 2024 data with HIBOR signals
When: Engine performs out-of-sample validation
Then:
  - In-sample (training): 2024-01-01 to 2024-06-30
    - Sharpe with HIBOR: 0.82
    - Signal win rate: 62%

  - Out-of-sample (test): 2024-07-01 to 2024-10-18
    - Sharpe with HIBOR: 0.76
    - Signal win rate: 55%

  - Validation Results:
    - In-sample vs out-of-sample difference: 6%
    - Acceptable degradation (< 10%)
    - Signal is NOT overfitted
    - HIBOR signals likely generalizable

  - Recommendation: Safe for live trading
```

---

### Requirement: Dashboard Alternative Data Strategy Results

The system SHALL display strategy backtest results with alternative data analysis.

#### Capability
- System SHALL display side-by-side comparison: with/without alt data
- System SHALL visualize signals: price chart with signals overlaid
- System SHALL show performance breakdown: price signals vs alt signals
- System SHALL enable strategy parameter configuration: alt data weights

#### Scenario: Dashboard Strategy Analysis View
```
Given: User opens backtest result for BankStockHIBORStrategy
When: Dashboard loads results
Then:
  - Top Section: Performance Summary
    ┌─────────────────────────────────┐
    │ Strategy: BankStockHIBORStrategy│
    │ Period: 2024-01-01 to 2024-10-18
    │
    │ Metric          │ Without Alt │ With Alt │ Improvement
    │ ────────────────┼─────────────┼──────────┼────────────
    │ Annual Return   │    12.5%    │  15.8%   │   +26%
    │ Sharpe Ratio    │    0.58     │  0.84    │   +45%
    │ Max Drawdown    │   -22%      │  -18%    │   +18%
    │ Win Rate        │    52%      │  58%     │   +12%
    └─────────────────────────────────┘

  - Middle Section: Signal Chart
    - X-axis: Date
    - Price line: 0939.HK closing price
    - BUY signals: Green arrows (18 total)
    - SELL signals: Red arrows (17 total)
    - HIBOR trend: Shaded background (red=rising, green=falling)

  - Bottom Section: Alternative Data Configuration
    - Price signals weight: [Slider 0-1] currently 0.5
    - HIBOR signals weight: [Slider 0-1] currently 0.5
    - [Backtest button to re-run with new weights]

  - Interactive: User can adjust weights and instantly re-optimize
```
