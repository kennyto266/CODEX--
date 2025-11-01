# Specification: Dashboard Alternative Data

**Capability ID**: `dashboard-alternative-data`

## ADDED Requirements

### Requirement: Alternative Data Browsing

The system SHALL allow users to view alternative data sources (HIBOR, property, etc.)

#### Scenario: User views HIBOR rates
```
When: User selects HIBOR from data sources
Then: Shows time series chart of HIBOR rates
```

### Requirement: Correlation Analysis

The system SHALL calculate and display correlation with portfolio returns

#### Scenario: User checks correlation
```
When: User selects 2+ data sources
Then: Shows correlation matrix heatmap
