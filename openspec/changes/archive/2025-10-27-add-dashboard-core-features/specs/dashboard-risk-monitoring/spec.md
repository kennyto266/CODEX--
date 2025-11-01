# Specification: Dashboard Risk Monitoring

**Capability ID**: `dashboard-risk-monitoring`

## ADDED Requirements

### Requirement: Portfolio Risk Metrics

The system SHALL display VaR, expected shortfall, and position-level risk

#### Scenario: User checks portfolio risk
```
Given: User on Risk tab
When: Page loads
Then: Shows metrics: VaR (95%), drawdown, position sizes
```

### Requirement: Risk Alerts

The system SHALL provide real-time risk alerts when limits are exceeded

#### Scenario: Portfolio exceeds risk limit
```
When: Position size > risk limit
Then: Alert triggers, shown in red in AlertCenter
```

### Requirement: Stress Testing

The system SHALL allow users to run stress tests on portfolio

#### Scenario: User runs stress test
```
When: User selects stress scenarios and clicks "Run"
Then: Results show portfolio impact under scenarios
```

## API Endpoints

- `GET /api/risk/portfolio`
- `GET /api/risk/var`
- `GET /api/risk/alerts`
- `POST /api/risk/stress-test`
- `WS /ws/risk`
