# Specification: Dashboard Trading Interface

**Capability ID**: `dashboard-trading-interface`

## ADDED Requirements

### Requirement: Order Placement

The system SHALL allow users to place buy/sell orders directly from dashboard

#### Scenario: User places a buy order
```
When: User enters symbol, quantity, and clicks "Buy"
Then: Order submitted to execution engine
  And: Confirmation shows in UI
```

### Requirement: Position Management

The system SHALL allow users to view open positions and manage them

#### Scenario: User closes a position
```
When: User views open positions and clicks "Close"
Then: Exit order placed at market price
```

### Requirement: Trade History

The system SHALL allow users to view all filled trades with P&L

#### Scenario: User reviews trades
```
When: User views TradeHistory
Then: Shows entry date, exit date, P&L for each trade
```

## API Endpoints

- `POST /api/trading/order`
- `GET /api/trading/positions`
- `GET /api/trading/orders`
- `GET /api/trading/history`
- `WS /ws/orders`
