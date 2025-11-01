## ADDED Requirements

### Requirement: System MUST support portfolio viewing
The system SHALL allow users to view detailed portfolio information using `/portfolio` command.

#### Scenario: View portfolio
- **WHEN** user executes `/portfolio` command
- **THEN** system MUST display portfolio containing:
  - Stock holdings list (stock code, name, quantity, cost price, current price, P&L)
  - Total market value
  - Total P&L and P&L rate
  - Each stock's weight

#### Scenario: View empty portfolio
- **WHEN** user executes `/portfolio` but portfolio is empty
- **THEN** system MUST display prompt suggesting user to add holdings

### Requirement: System MUST support adding portfolio positions
The system SHALL allow users to add positions via `/portfolio add <stock_code> <quantity> <cost_price>` command.

#### Scenario: Add valid position
- **WHEN** user executes `/portfolio add 0700.HK 100 350.0`
- **THEN** system MUST validate stock code, quantity and price, then add to portfolio

#### Scenario: Add invalid stock code
- **WHEN** user executes `/portfolio add INVALID 100 350.0`
- **THEN** system MUST return error message indicating invalid stock code

#### Scenario: Add invalid parameters
- **WHEN** user executes `/portfolio add 0700.HK abc 350.0`
- **THEN** system MUST return error message indicating parameter format error

### Requirement: System MUST support removing portfolio positions
The system SHALL allow users to delete positions via `/portfolio remove <stock_code>` command.

#### Scenario: Delete existing position
- **WHEN** user executes `/portfolio remove 0700.HK`
- **THEN** system MUST remove the position from portfolio

#### Scenario: Delete non-existent position
- **WHEN** user executes `/portfolio remove 9999.HK` (non-existent stock)
- **THEN** system MUST return error message indicating position doesn't exist

### Requirement: System MUST persist portfolio data
The system SHALL persist portfolio data to storage so data is not lost after Bot restart.

#### Scenario: Data persists after restart
- **WHEN** Bot is shut down and restarted
- **THEN** system MUST restore portfolio data from file or database

### Requirement: System MUST format portfolio display
The system SHALL display portfolio information in readable format with Markdown support.

#### Scenario: Format holdings list
- **WHEN** displaying portfolio
- **THEN** system MUST display holdings in table format using emojis and Markdown for readability

### Requirement: System MUST update with real-time prices
The system SHALL use real-time or latest market prices to calculate market value and P&L.

#### Scenario: Use real-time price calculation
- **WHEN** user views portfolio
- **THEN** system MUST fetch real-time prices from market data API and calculate latest market value and P&L
