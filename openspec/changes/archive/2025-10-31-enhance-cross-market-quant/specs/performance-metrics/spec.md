# Performance Metrics Specification

This specification defines the requirements for comprehensive performance measurement.

## ADDED Requirements

### Signal Statistics
The system SHALL calculate signal trigger rates and effectiveness.

#### Scenario: Calculate signal statistics
Given: 100 trading days with 25 signals
When: Calling SignalStatistics.calculate()
Then: Return trigger_rate=0.25, win_rate=0.64

### Cross-Market Attribution
The system SHALL perform return attribution across markets.

#### Scenario: Brinson attribution analysis
Given: Portfolio returns and benchmark returns
When: Calling ReturnAttribution.brinson_analysis()
Then: Return allocation_effect, selection_effect, interaction_effect

### Risk-Adjusted Returns
The system SHALL calculate risk-adjusted performance metrics.

#### Scenario: Calculate all risk metrics
Given: Portfolio return series
When: Calling RiskAdjustedReturns.calculate_all()
Then: Return sharpe_ratio, sortino_ratio, calmar_ratio
