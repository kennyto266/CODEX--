# Specification: Correlation Analysis and Alternative Data Integration

## ADDED Requirements

### Requirement: Correlation Analysis Module

The system SHALL calculate statistical correlations between alternative data indicators and stock returns.

#### Capability
- System SHALL compute Pearson correlation coefficients
- System SHALL calculate Sharpe ratios with alternative data
- System SHALL compute rolling correlation for time-varying relationships
- System SHALL detect leading/lagging indicators
- System SHALL generate correlation heatmaps

#### Scenario: Calculate Correlation Between HIBOR and Bank Stocks
```
Given: Daily HIBOR rates and daily returns for 0939.HK (CCB), 1398.HK (ICBC)
When: CorrelationAnalyzer.calculate_correlation_matrix(alt_data, returns)
Then:
  - Calculates Pearson correlation: corr(HIBOR_change, stock_return)
  - Result matrix:
    Indicator           | 0939.HK | 1398.HK | 2388.HK (Bank of HK)
    HIBOR_Overnight_Chg | -0.65   | -0.68   | -0.62
    HIBOR_3M_Chg        | -0.58   | -0.61   | -0.55
  - Negative correlation: Higher rates → lower bank stock returns
  - Statistical significance: p-values < 0.05 for all
  - Results stored for reporting and visualization
```

#### Scenario: Identifying Leading Indicators
```
Given: Visitor arrivals and tourism/retail stocks (1113.HK Cheung Kong, 2333.HK Aeon)
When: CorrelationAnalyzer.identify_leading_indicators(visitor_data, stock_returns, max_lag=20)
Then:
  - Tests correlation at various lags: 0, 1, 5, 10, 20 days
  - Discovers peak correlation at lag = +3 days
  - Interpretation: Visitor arrivals 3 days BEFORE stock price moves
  - Suggests visitor data is leading indicator for retail stocks
  - Lag analysis helps build predictive trading signals
  - Report: "Visitor arrivals lead 1113.HK returns by 3 days (corr=0.42)"
```

---

### Requirement: Sharpe Ratio Calculation with Alternative Data

The system SHALL calculate risk-adjusted returns and compare strategies with alternative data.

#### Capability
- System SHALL compute traditional Sharpe ratio: (return - rf) / std_dev
- System SHALL compute multi-factor Sharpe with alternative data signals
- System SHALL provide comparison metrics for performance improvement
- System SHALL support configurable risk-free rate

#### Scenario: Comparing Sharpe Ratios
```
Given: Backtest results for price-only strategy vs price+HIBOR strategy
When: AnalysisModule calculates Sharpe ratios
Then:
  - Price-only strategy:
    Annual Return: 12.5%
    Volatility: 18.2%
    Sharpe Ratio = (12.5% - 2.0%) / 18.2% = 0.58

  - Price + HIBOR strategy:
    Annual Return: 15.8%
    Volatility: 16.5%
    Sharpe Ratio = (15.8% - 2.0%) / 16.5% = 0.84

  - Improvement: +45% higher Sharpe ratio (0.58 → 0.84)
  - Lower volatility + higher returns with alt data signals
```

---

### Requirement: Rolling Correlation Analysis

The system SHALL calculate time-varying correlation to identify regime changes.

#### Capability
- System SHALL compute rolling window correlation (configurable window)
- System SHALL analyze correlation stability over time
- System SHALL detect regime changes (high vs low correlation)
- System SHALL visualize correlation trends

#### Scenario: Detecting Correlation Regime Change
```
Given: 60-day rolling correlation between property stocks and real estate index
When: CorrelationAnalyzer.calculate_rolling_correlation(alt_data, prices, window=60)
Then:
  - Q1 2024: Correlation = 0.75 (strong positive)
  - Q2 2024: Correlation = 0.71 (slightly weaker)
  - Q3 2024: Correlation = 0.45 (weakening significantly)
  - Q4 2024: Correlation = 0.25 (decoupling)

  - Dashboard shows rolling correlation chart
  - Alerts when correlation drops below 0.5 threshold
  - Strategy may need adjustment: alt data signal reliability declining
  - Consider adding hedge or new indicator
```

---

### Requirement: Correlation Report Generation

The system SHALL generate comprehensive analysis reports for stakeholders.

#### Capability
- System SHALL compute summary statistics for each indicator
- System SHALL generate visual heatmaps and correlation matrices
- System SHALL identify top correlations and anti-correlations
- System SHALL calculate statistical significance and confidence intervals
- System SHALL provide recommendations for signal usage

#### Scenario: Generating Correlation Report for Fund Meeting
```
Given: Alternative data analysis for 10 stocks over 2024
When: CorrelationAnalyzer.generate_correlation_report()
Then:
  - Report output:

    ALTERNATIVE DATA CORRELATION ANALYSIS REPORT
    ============================================
    Period: 2024-01-01 to 2024-10-18
    Universe: 10 Hong Kong stocks

    KEY FINDINGS:

    1. HIBOR Correlations:
       - Strongest correlation: HIBOR↑ → Bank stocks↓ (corr = -0.68)
       - Weakest correlation: HIBOR↑ → Tech stocks (corr = -0.12)
       - Statistical significance: All p-values < 0.05

    2. Visitor Arrivals Correlations:
       - Strong with retail/tourism: corr = 0.55
       - Leads stock returns by 3 days
       - Useful for short-term signals

    3. HKEX Futures Correlations:
       - High corr with index stocks (corr = 0.82)
       - Lower corr with defensive stocks (corr = 0.25)

    RECOMMENDATIONS:
    - Use HIBOR for bank stock strategies
    - Use visitor arrivals for tourism sector
    - Combine HKEX futures for market-wide views

    NEXT STEPS:
    - Backtest with recommended indicators
    - Monitor correlation stability quarterly

  - Report exported as PDF/HTML
  - Shared with portfolio managers
```

---

### Requirement: Dashboard Correlation Visualization

The system SHALL display correlation analysis in web dashboard.

#### Capability
- System SHALL display interactive correlation heatmap
- System SHALL show time series charts: alt data vs stock price
- System SHALL display rolling correlation charts
- System SHALL provide summary statistics tables
- System SHALL enable filtering by sector, stock, indicator

#### Scenario: Dashboard: Exploring HIBOR-Bank Stock Correlation
```
Given: User opens Alternative Data dashboard
When: User selects "HIBOR" and stocks "0939.HK, 1398.HK, 2388.HK"
Then:
  - Dashboard displays:

    Panel 1: Correlation Heatmap
    ┌────────────┬──────┬──────┬──────┐
    │ Indicator  │0939.HK│1398.HK│2388.HK│
    ├────────────┼──────┼──────┼──────┤
    │HIBOR_ON   │ -0.65│ -0.68│ -0.62│
    │HIBOR_3M   │ -0.58│ -0.61│ -0.55│
    │HIBOR_6M   │ -0.52│ -0.55│ -0.48│
    └────────────┴──────┴──────┴──────┘

    Panel 2: Time Series Chart
    - X-axis: Date
    - Y1-axis (left): HIBOR rate (%)
    - Y2-axis (right): Stock return (%)
    - Overlay trend lines showing negative relationship

    Panel 3: Rolling Correlation (60-day window)
    - Shows how correlation changes over time
    - Highlights periods of decoupling

    Panel 4: Statistics
    - Mean correlation: -0.62
    - Min/Max range: [-0.75, -0.45]
    - p-value: < 0.001 (highly significant)
    - Sample size: 200 trading days
```

---

## MODIFIED Requirements

### Requirement: Backtest Engine Reporting

The system SHALL extend reporting to include alternative data impact analysis.

#### Capability
- System SHALL report performance metrics with and without alt data
- System SHALL calculate correlation contribution to returns
- System SHALL compute signal quality metrics
- System SHALL summarize alternative data signal performance

#### Scenario: Backtest Report with Alternative Data Analysis
```
Given: Backtest completed with price + HIBOR signals
When: BacktestEngine.generate_report()
Then:
  - Standard metrics (Sharpe, drawdown, etc.)
  - Additional section: ALTERNATIVE DATA ANALYSIS

    Alternative Data Impact:
    - HIBOR signal accuracy: 62% (correctly predicted direction)
    - Signal frequency: 35 signals over 200 days
    - Win rate on HIBOR signals: 58%
    - Contribution to total Sharpe: +0.18 (from +0.58 to +0.76)

    Signal Distribution:
    - Buy signals from HIBOR: 18 (15 profitable, 3 loss)
    - Sell signals from HIBOR: 17 (10 profitable, 7 loss)

    Top Periods:
    - HIBOR most effective: Q1 2024 (correlation highest)
    - HIBOR least effective: Q3 2024 (correlation breaking down)
```
