# Specification: Dashboard Strategy Management

**Capability ID**: `dashboard-strategy-management`

## ADDED Requirements

### Requirement: Strategy Browsing

The system SHALL allow users to browse available strategies and their parameters

#### Scenario: User selects a strategy
```
When: User views strategy list
Then: Shows MA, RSI, MACD, KDJ with parameters
```

### Requirement: Strategy Performance

The system SHALL display historical performance for each strategy

#### Scenario: User compares strategies
```
When: User clicks "Compare"
Then: Shows side-by-side Sharpe ratios, max drawdown
```

### Requirement: Custom Strategy Configuration

The system SHALL allow users to save custom parameter sets

#### Scenario: User saves optimized parameters
```
When: User enters custom parameters and clicks "Save"
Then: Configuration stored in database
