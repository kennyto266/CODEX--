# Enhanced Backtest Engine Specification

This specification defines the requirements for enhancing the backtest engine with cross-market capabilities.

## MODIFIED Requirements

### Fixed Holding Period Management
The system SHALL support fixed holding periods (14 days as per 阿程 Strategy).

#### Scenario: 14-day holding period
Given: Signal triggered on day 1
When: Running backtest with holding_period=14
Then: Position holds for exactly 14 days

### Multi-Asset Portfolio Support
The system SHALL support multiple assets in portfolio backtesting.

#### Scenario: Multi-asset backtest
Given: 3 assets (HSI, Gold, USD/CNH)
When: Running MultiAssetBacktest
Then: Return portfolio returns with asset contributions

### Enhanced Transaction Cost Model
The system SHALL include comprehensive transaction costs.

#### Scenario: Calculate total cost
Given: Trade amount = 1M, commission = 0.02%, slippage = 0.01%
When: Calculating transaction cost
Then: Return breakdown: fixed + commission + slippage + market impact
