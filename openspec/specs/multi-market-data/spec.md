# Multi-Market Data Adapter Specification

This specification defines the requirements for implementing multi-market data adapters that support FX, commodity, and bond data with cross-market correlation calculation.

## Requirements

### FX Data Adapter
The system SHALL provide adapters for FX data including USD/CNH, EUR/USD, etc.

#### Scenario: Fetching USD/CNH data
Given: System needs USD/CNH daily data
When: Calling FXAdapter.fetch_data("USD_CNH", "2024-01-01", "2024-12-31")
Then: Return DataFrame with columns: Date, Open, High, Low, Close, Volume

### Commodity Data Adapter
The system SHALL provide adapters for commodity data including Gold, Oil, etc.

#### Scenario: Fetching Gold futures data
Given: System needs Gold futures data
When: Calling CommodityAdapter.fetch_data("GOLD", "2024-01-01", "2024-12-31")
Then: Return DataFrame with OHLCV data

### Bond Data Adapter
The system SHALL provide adapters for bond yield data.

#### Scenario: Fetching US 10Y yield
Given: System needs US 10Y Treasury yield
When: Calling BondAdapter.fetch_data("US_10Y", "2024-01-01", "2024-12-31")
Then: Return DataFrame with Date and Yield columns
