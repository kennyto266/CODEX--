# Specification: Dashboard Performance Analytics

**Capability ID**: `dashboard-performance-analytics`

## ADDED Requirements

### Requirement: Detailed Performance Metrics

The system SHALL show comprehensive performance analytics

#### Scenario: User views performance dashboard
```
When: User on Performance tab
Then: Shows Sharpe ratio, Sortino, annual return, etc.
```

### Requirement: Equity Curve Visualization

The system SHALL plot equity curve with drawdown overlay

#### Scenario: User analyzes equity curve
```
When: User views equity chart
Then: Line chart shows growth, drawdown areas in red
```

### Requirement: Monthly Returns Heatmap

The system SHALL display a heatmap of monthly returns (color-coded)

#### Scenario: User identifies best/worst months
```
When: User views heatmap
Then: Green for positive, red for negative months
