# Data Model: Rust Non-Price Data Technical Indicators System

**Date**: 2025-11-10
**Feature**: Non-price data to technical indicators conversion system
**Source**: `/specs/1-rust-nonprice-implementation/spec.md`

## Overview

This document defines the data model for the Rust non-price data processing system, including core data structures, validation rules, state transitions, and relationships between entities.

---

## Core Entities

### 1. NonPriceIndicator

**Purpose**: Represents raw economic/macro data points (HIBOR, visitor count, etc.)

**Fields**:
```rust
pub struct NonPriceIndicator {
    pub symbol: String,              // Identifier (e.g., "HIBOR_Overnight_%")
    pub date: NaiveDate,             // Observation date
    pub value: f64,                  // Numeric value
    pub quality: DataQuality,        // Data quality flag
    pub source: String,              // Data source (e.g., "HKMA", "CensusDept")
    pub metadata: HashMap<String, String>, // Additional context
}
```

**Validation Rules**:
- `value` must be finite (not NaN, not ±∞)
- `date` must be within reasonable range (1900-2100)
- `symbol` must match allowed pattern: `[A-Z_]+` (uppercase with underscores)
- Required fields: symbol, date, value

**State Transitions**:
- NEW → VALIDATED (when validation passes)
- NEW → REJECTED (when validation fails with reason)
- VALIDATED → PROCESSED (after indicator calculation)

**Example**:
```json
{
  "symbol": "HIBOR_Overnight_%",
  "date": "2023-06-15",
  "value": 4.25,
  "quality": "GOOD",
  "source": "HKMA",
  "metadata": {
    "currency": "HKD",
    "tenor": "Overnight"
  }
}
```

---

### 2. TechnicalIndicator

**Purpose**: Calculated values derived from NonPriceIndicator

**Fields**:
```rust
pub struct TechnicalIndicator {
    pub base_symbol: String,         // Reference to NonPriceIndicator.symbol
    pub date: NaiveDate,             // Calculation date
    pub indicator_type: IndicatorType, // ZSCORE, RSI, SMA_FAST, SMA_SLOW
    pub value: Option<f64>,          // Calculated value (None if insufficient data)
    pub window_size: usize,          // Rolling window used
    pub calculation_date: DateTime<Utc>, // When calculated
    pub is_valid: bool,              // Whether calculation succeeded
}
```

**IndicatorType Enum**:
```rust
pub enum IndicatorType {
    ZSCORE,
    RSI,
    SMA_FAST,    // 10-day default
    SMA_SLOW,    // 30-day default
}
```

**Validation Rules**:
- For ZSCORE: window_size must be ≥ 20
- For RSI: window_size must be ≥ 14
- For SMA: window_size must be ≥ 1
- `value` is null if insufficient data in window
- `is_valid` = false if calculation error occurred

**State Transitions**:
- CALCULATING → READY (successful calculation)
- CALCULATING → FAILED (error in calculation)

**Example**:
```json
{
  "base_symbol": "HIBOR_Overnight_%",
  "date": "2023-06-15",
  "indicator_type": "ZSCORE",
  "value": 0.85,
  "window_size": 20,
  "calculation_date": "2023-06-15T10:30:00Z",
  "is_valid": true
}
```

---

### 3. TradingSignal

**Purpose**: Generated decision (BUY/SELL/HOLD) based on technical indicators

**Fields**:
```rust
pub struct TradingSignal {
    pub symbol: String,              // Stock symbol (e.g., "0700.HK")
    pub date: NaiveDate,             // Signal date
    pub action: SignalAction,        // BUY, SELL, HOLD
    pub confidence: f64,             // 0.0 to 1.0 (indicator agreement)
    pub source_indicators: Vec<String>, // Which indicators contributed
    pub reasoning: String,           // Human-readable explanation
    pub parameters: HashMap<String, f64>, // Thresholds used
}
```

**SignalAction Enum**:
```rust
pub enum SignalAction {
    BUY,
    SELL,
    HOLD,
}
```

**Validation Rules**:
- `confidence` must be between 0.0 and 1.0
- `date` must align with trading calendar (skip weekends/holidays)
- `source_indicators` cannot be empty
- Required fields: symbol, date, action, confidence, source_indicators

**State Transitions**:
- GENERATING → EMITTED (signal created)
- EMITTED → APPLIED (used in backtest)
- EMITTED → IGNORED (invalid/filtered out)

**Example**:
```json
{
  "symbol": "0700.HK",
  "date": "2023-06-15",
  "action": "BUY",
  "confidence": 0.75,
  "source_indicators": ["HIBOR_Overnight_%_ZSCORE", "Visitor_Count_RSI"],
  "reasoning": "Z-Score below -0.5 threshold ( BUY signal) and RSI oversold",
  "parameters": {
    "zscore_buy_threshold": -0.5,
    "rsi_buy_threshold": 25.0
  }
}
```

---

### 4. ParameterSet

**Purpose**: Collection of threshold values for signal generation

**Fields**:
```rust
pub struct ParameterSet {
    pub id: String,                  // Unique identifier
    pub indicator_name: String,      // Which indicator this applies to
    pub zscore_buy: f64,             // Z-Score buy threshold (e.g., -0.5)
    pub zscore_sell: f64,            // Z-Score sell threshold (e.g., 0.5)
    pub rsi_buy: f64,                // RSI buy threshold (e.g., 25.0)
    pub rsi_sell: f64,               // RSI sell threshold (e.g., 65.0)
    pub sma_fast: usize,             // SMA fast period (e.g., 10)
    pub sma_slow: usize,             // SMA slow period (e.g., 30)
    pub created_at: DateTime<Utc>,
}
```

**Validation Rules**:
- `zscore_buy` < 0.0 (buy when Z-Score is low)
- `zscore_sell` > 0.0 (sell when Z-Score is high)
- `rsi_buy` < `rsi_sell` (e.g., 25 < 65)
- `sma_fast` < `sma_slow` (e.g., 10 < 30)
- All parameters within allowed ranges (from spec)

**State Transitions**:
- CREATED → TESTED (backtested)
- TESTED → OPTIMIZED (scored, part of optimization)

**Example**:
```json
{
  "id": "params_001",
  "indicator_name": "HIBOR_Overnight_%",
  "zscore_buy": -0.5,
  "zscore_sell": 0.5,
  "rsi_buy": 25.0,
  "rsi_sell": 65.0,
  "sma_fast": 10,
  "sma_slow": 30,
  "created_at": "2023-06-15T10:30:00Z"
}
```

---

### 5. BacktestResult

**Purpose**: Performance metrics and trade history from backtesting

**Fields**:
```rust
pub struct BacktestResult {
    pub id: String,                  // Unique backtest ID
    pub symbol: String,              // Stock symbol tested
    pub start_date: NaiveDate,       // Test start
    pub end_date: NaiveDate,         // Test end
    pub initial_capital: f64,        // Starting amount (e.g., 100,000)
    pub final_value: f64,            // Ending portfolio value
    pub total_return_pct: f64,       // Total return percentage
    pub annual_return_pct: f64,      // Annualized return
    pub sharpe_ratio: f64,           // Sharpe ratio (risk-adjusted)
    pub max_drawdown_pct: f64,       // Maximum drawdown
    pub win_rate_pct: f64,           // Win rate percentage
    pub total_trades: usize,         // Number of executed trades
    pub winning_trades: usize,       // Number of winning trades
    pub losing_trades: usize,        // Number of losing trades
    pub execution_time_ms: u64,      // Backtest runtime
    pub parameters: ParameterSet,    // Parameters used
    pub trades: Vec<Trade>,          // Individual trade records
    pub equity_curve: Vec<(NaiveDate, f64)>, // Portfolio value over time
}
```

**Validation Rules**:
- `final_value` ≥ 0.0
- `total_trades` = `winning_trades` + `losing_trades`
- `sharpe_ratio` can be negative (losing strategy)
- `max_drawdown_pct` is negative value (e.g., -15.5)
- `equity_curve` must have at least 2 points (start and end)

**State Transitions**:
- RUNNING → COMPLETED (successful backtest)
- RUNNING → FAILED (error during backtest)
- COMPLETED → RANKED (included in optimization results)

**Example**:
```json
{
  "id": "backtest_001",
  "symbol": "0700.HK",
  "start_date": "2022-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000.0,
  "final_value": 178045.36,
  "total_return_pct": 78.05,
  "annual_return_pct": 17.83,
  "sharpe_ratio": 0.70,
  "max_drawdown_pct": -51.25,
  "win_rate_pct": 51.27,
  "total_trades": 612,
  "winning_trades": 314,
  "losing_trades": 298,
  "execution_time_ms": 4250
}
```

---

### 6. Trade

**Purpose**: Individual executed trade within backtest

**Fields**:
```rust
pub struct Trade {
    pub id: String,                  // Trade ID
    pub entry_date: NaiveDate,       // Buy date
    pub exit_date: NaiveDate,        // Sell date
    pub entry_price: f64,            // Buy price
    pub exit_price: f64,             // Sell price
    pub quantity: f64,               // Shares traded
    pub entry_signal: SignalAction,  // Signal that triggered entry
    pub exit_signal: SignalAction,   // Signal that triggered exit
    pub pnl: f64,                    // Profit/loss
    pub commission: f64,             // Transaction cost
    pub hold_days: i32,              // Days held (negative for short sells)
}
```

**Validation Rules**:
- `exit_date` ≥ `entry_date`
- `quantity` > 0.0 (long-only in current spec)
- `pnl` = (`exit_price` - `entry_price`) * `quantity` - `commission`
- `hold_days` = (`exit_date` - `entry_date`).num_days()

**State Transitions**:
- OPEN → CLOSED (when position closed)
- OPEN → CANCELED (if signal reversed before execution)

**Example**:
```json
{
  "id": "trade_001",
  "entry_date": "2023-03-15",
  "exit_date": "2023-03-28",
  "entry_price": 345.50,
  "exit_price": 358.20,
  "quantity": 100.0,
  "entry_signal": "BUY",
  "exit_signal": "SELL",
  "pnl": 1170.0,
  "commission": 35.0,
  "hold_days": 13
}
```

---

## Entity Relationships

```
NonPriceIndicator
    ↓ (calculates)
TechnicalIndicator
    ↓ (generates)
TradingSignal
    ↓ (applied in)
BacktestResult
    ↓ (contains)
Trade
    ↑ (uses)
ParameterSet
```

**Relationship Cardinalities**:
- One `NonPriceIndicator` → Many `TechnicalIndicator` (one per indicator type)
- One `TechnicalIndicator` → One `NonPriceIndicator` (back-reference)
- One `ParameterSet` → Many `BacktestResult` (same params, different data)
- One `BacktestResult` → Many `Trade`
- One `TradingSignal` → Zero or One `Trade` (signal may not execute if ignored)

---

## Data Flow

```
Input Data (CSV/Parquet)
    ↓
NonPriceIndicator
    ↓
DataValidator
    ↓
TechnicalIndicator Calculator
    ↓
Signal Generator
    ↓ (with ParameterSet)
TradingSignal
    ↓
Backtest Engine
    ↓
BacktestResult
    ↓
Report Generator (Markdown/JSON)
```

**State Machine**:

```
┌──────────────┐
│   NEW DATA   │
└──────┬───────┘
       │ validate()
       ▼
┌──────────────┐      ┌──────────────┐
│   VALIDATED  │      │   REJECTED   │
└──────┬───────┘      │               │
       │ calculate()  └───────────────┘
       ▼
┌──────────────┐
│ INDICATORS   │
└──────┬───────┘
       │ generate()
       ▼
┌──────────────┐      ┌──────────────┐
│   SIGNALS    │      │    FAILED    │
└──────┬───────┘      │               │
       │ backtest()  └───────────────┘
       ▼
┌──────────────┐
│   RESULTS    │
└──────────────┘
```

---

## Validation Rules Summary

| Entity | Rule | Severity | Description |
|--------|------|----------|-------------|
| NonPriceIndicator | value is finite | ERROR | Must be valid number |
| NonPriceIndicator | date in range | ERROR | 1900-2100 |
| TechnicalIndicator | window_size ≥ required | ERROR | ZSCORE≥20, RSI≥14 |
| TechnicalIndicator | value is null if insufficient data | WARN | Expected behavior |
| TradingSignal | confidence 0.0-1.0 | ERROR | Must be probability |
| TradingSignal | source_indicators not empty | ERROR | At least one source |
| ParameterSet | zscore_buy < 0 | ERROR | Buy when low |
| ParameterSet | zscore_sell > 0 | ERROR | Sell when high |
| ParameterSet | rsi_buy < rsi_sell | ERROR | Standard definition |
| ParameterSet | sma_fast < sma_slow | ERROR | Must cross |
| BacktestResult | final_value ≥ 0 | ERROR | No negative portfolio |
| BacktestResult | total_trades = wins + losses | ERROR | Must balance |
| Trade | exit_date ≥ entry_date | ERROR | Time flows forward |
| Trade | quantity > 0 | ERROR | Long-only |

---

## Serialization

**Format**: JSON for interchange, binary formats for storage

**Example: Complete Pipeline**
```json
{
  "input": {
    "symbol": "HIBOR_Overnight_%",
    "date": "2023-06-15",
    "value": 4.25
  },
  "technical_indicators": [
    {
      "base_symbol": "HIBOR_Overnight_%",
      "date": "2023-06-15",
      "indicator_type": "ZSCORE",
      "value": 0.85,
      "window_size": 20
    }
  ],
  "trading_signal": {
    "symbol": "0700.HK",
    "date": "2023-06-15",
    "action": "BUY",
    "confidence": 0.75,
    "source_indicators": ["HIBOR_Overnight_%_ZSCORE"]
  },
  "backtest_result": {
    "total_return_pct": 78.05,
    "sharpe_ratio": 0.70,
    "max_drawdown_pct": -51.25
  }
}
```

---

**Data Model Completed**: 2025-11-10
**Status**: ✅ Complete - Ready for API contract design
