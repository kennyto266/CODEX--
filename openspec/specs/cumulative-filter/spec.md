# Cumulative Return Filter Specification

This specification defines the requirements for implementing cumulative return filtering inspired by 阿程 Strategy 12.

## Requirements

### Cumulative Return Calculation
The system SHALL calculate multi-day cumulative returns with configurable window (default 4 days).

#### Scenario: Calculate 4-day cumulative return
Given: Price series [6.78, 6.79, 6.80, 6.81, 6.82]
When: Calling calculate_cumulative_return(prices, window=4)
Then: Return cumulative returns [NaN, NaN, NaN, 0.0044, 0.0044]

### Signal Filtering
The system SHALL filter signals based on cumulative return threshold (default ±0.4%).

#### Scenario: Trigger sell signal
Given: 4-day cumulative return = 0.005 (0.5%)
When: Calling filter_signals(cumulative_returns, threshold=0.004, signal_type='short')
Then: Return signal -1 (sell)

### Dynamic Threshold Adjustment
The system SHALL adjust thresholds based on market volatility.

#### Scenario: Adjust threshold for high volatility
Given: Market volatility = 0.008 (high)
When: Calling filter_signals with dynamic threshold
Then: Use adjusted threshold = base_threshold * volatility_factor
