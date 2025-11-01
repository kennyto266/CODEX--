# Cross-Market Strategy Framework Specification

This specification defines the requirements for implementing cross-market trading strategies.

## ADDED Requirements

### USD/CNH → HSI Strategy
The system SHALL implement 阿程 Strategy 12 logic using USD/CNH to predict HSI movements.

#### Scenario: USD/CNH strength triggers HSI short
Given: USD/CNH 4-day cumulative return = 0.005 (0.5%)
When: Running FXHsiStrategy.generate_signals()
Then: Return SELL signal for HSI

### Commodity → Stock Strategy
The system SHALL implement commodity-driven stock strategies.

#### Scenario: Gold price increase triggers gold stock buy
Given: Gold 4-day cumulative return = 0.03 (3%)
When: Running CommodityStockStrategy.generate_signals()
Then: Return BUY signal for gold mining stocks

### Multi-Strategy Portfolio
The system SHALL combine multiple strategies with dynamic weights.

#### Scenario: Combine strategy signals
Given: Multiple strategy signals with different strengths
When: Calling StrategyPortfolio.combine_signals()
Then: Return combined signal with vote results
