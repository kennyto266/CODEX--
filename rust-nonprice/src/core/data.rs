//! Core data structures and types for the non-price data system
//!
//! This module defines all fundamental data types including:
//! - NonPriceIndicator: Raw economic data
//! - TechnicalIndicator: Calculated indicators
//! - TradingSignal: Generated signals
//! - BacktestResult: Performance metrics
//! - ParameterSet: Configuration parameters

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;

/// Data quality indicator
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DataQuality {
    Good,
    Fair,
    Poor,
    Rejected,
}

impl fmt::Display for DataQuality {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            DataQuality::Good => write!(f, "GOOD"),
            DataQuality::Fair => write!(f, "FAIR"),
            DataQuality::Poor => write!(f, "POOR"),
            DataQuality::Rejected => write!(f, "REJECTED"),
        }
    }
}

/// Technical indicator type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum IndicatorType {
    ZScore,
    RSI,
    SMAFast,
    SMASlow,
}

impl fmt::Display for IndicatorType {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            IndicatorType::ZScore => write!(f, "ZSCORE"),
            IndicatorType::RSI => write!(f, "RSI"),
            IndicatorType::SMAFast => write!(f, "SMA_FAST"),
            IndicatorType::SMASlow => write!(f, "SMA_SLOW"),
        }
    }
}

/// Trading signal action
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SignalAction {
    Buy,
    Sell,
    Hold,
}

impl fmt::Display for SignalAction {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            SignalAction::Buy => write!(f, "BUY"),
            SignalAction::Sell => write!(f, "SELL"),
            SignalAction::Hold => write!(f, "HOLD"),
        }
    }
}

/// Represents raw economic/macro data points (HIBOR, visitor count, etc.)
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NonPriceIndicator {
    pub symbol: String,
    pub date: NaiveDate,
    pub value: f64,
    pub quality: DataQuality,
    pub source: String,
    pub metadata: HashMap<String, String>,
}

impl NonPriceIndicator {
    /// Create a new non-price indicator
    pub fn new(
        symbol: String,
        date: NaiveDate,
        value: f64,
        source: String,
    ) -> Self {
        Self {
            symbol,
            date,
            value,
            quality: DataQuality::Good,
            source,
            metadata: HashMap::new(),
        }
    }

    /// Check if the indicator is valid (has finite value)
    pub fn is_valid(&self) -> bool {
        self.value.is_finite() && !self.value.is_nan()
    }
}

/// Calculated technical indicator derived from NonPriceIndicator
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TechnicalIndicator {
    pub base_symbol: String,
    pub date: NaiveDate,
    pub indicator_type: IndicatorType,
    pub value: Option<f64>,
    pub window_size: usize,
    pub calculation_date: DateTime<Utc>,
    pub is_valid: bool,
}

impl TechnicalIndicator {
    /// Create a new technical indicator
    pub fn new(
        base_symbol: String,
        date: NaiveDate,
        indicator_type: IndicatorType,
        window_size: usize,
    ) -> Self {
        Self {
            base_symbol,
            date,
            indicator_type,
            value: None,
            window_size,
            calculation_date: Utc::now(),
            is_valid: false,
        }
    }

    /// Set the calculated value and mark as valid
    pub fn set_value(&mut self, value: f64) {
        self.value = Some(value);
        self.is_valid = true;
    }
}

/// Generated trading signal (BUY/SELL/HOLD)
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TradingSignal {
    pub symbol: String,
    pub date: NaiveDate,
    pub action: SignalAction,
    pub confidence: f64,
    pub source_indicators: Vec<String>,
    pub reasoning: String,
    pub parameters: HashMap<String, f64>,
}

impl TradingSignal {
    /// Create a new trading signal
    pub fn new(
        symbol: String,
        date: NaiveDate,
        action: SignalAction,
        confidence: f64,
    ) -> Self {
        Self {
            symbol,
            date,
            action,
            confidence,
            source_indicators: Vec::new(),
            reasoning: String::new(),
            parameters: HashMap::new(),
        }
    }
}

/// Collection of threshold values for signal generation
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParameterSet {
    pub id: String,
    pub indicator_name: String,
    pub zscore_buy: f64,
    pub zscore_sell: f64,
    pub rsi_buy: f64,
    pub rsi_sell: f64,
    pub sma_fast: usize,
    pub sma_slow: usize,
    pub created_at: DateTime<Utc>,
}

impl ParameterSet {
    /// Create default parameter set
    pub fn default() -> Self {
        let now = Utc::now();
        Self {
            id: format!("default-{}", now.timestamp()),
            indicator_name: "default".to_string(),
            zscore_buy: -0.5,
            zscore_sell: 0.5,
            rsi_buy: 25.0,
            rsi_sell: 65.0,
            sma_fast: 10,
            sma_slow: 30,
            created_at: now,
        }
    }

    /// Create a new parameter set with custom values
    pub fn new(
        indicator_name: String,
        zscore_buy: f64,
        zscore_sell: f64,
        rsi_buy: f64,
        rsi_sell: f64,
        sma_fast: usize,
        sma_slow: usize,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: format!("{}-{}", indicator_name, now.timestamp()),
            indicator_name,
            zscore_buy,
            zscore_sell,
            rsi_buy,
            rsi_sell,
            sma_fast,
            sma_slow,
            created_at: now,
        }
    }

    /// Validate parameter set constraints
    pub fn validate(&self) -> Result<(), crate::core::error::BacktestError> {
        if self.zscore_buy >= 0.0 {
            return Err(crate::core::error::BacktestError::ValidationError {
                field: "zscore_buy".to_string(),
                reason: "must be negative (buy when low)".to_string(),
            });
        }
        if self.zscore_sell <= 0.0 {
            return Err(crate::core::error::BacktestError::ValidationError {
                field: "zscore_sell".to_string(),
                reason: "must be positive (sell when high)".to_string(),
            });
        }
        if self.rsi_buy >= self.rsi_sell {
            return Err(crate::core::error::BacktestError::ValidationError {
                field: "rsi_buy/rsi_sell".to_string(),
                reason: "rsi_buy must be less than rsi_sell".to_string(),
            });
        }
        if self.sma_fast >= self.sma_slow {
            return Err(crate::core::error::BacktestError::ValidationError {
                field: "sma_fast/sma_slow".to_string(),
                reason: "sma_fast must be less than sma_slow".to_string(),
            });
        }
        Ok(())
    }
}

/// Stock price data for backtesting
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OHLCV {
    pub symbol: String,
    pub date: NaiveDate,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: u64,
}

impl OHLCV {
    /// Create new OHLCV data point
    pub fn new(
        symbol: String,
        date: NaiveDate,
        open: f64,
        high: f64,
        low: f64,
        close: f64,
        volume: u64,
    ) -> Self {
        Self {
            symbol,
            date,
            open,
            high,
            low,
            close,
            volume,
        }
    }

    /// Get adjusted close price (for splits/dividends)
    pub fn adjusted_close(&self) -> f64 {
        self.close
    }

    /// Validate OHLCV data
    pub fn validate(&self) -> Result<(), crate::core::error::BacktestError> {
        if self.high < self.low {
            return Err(crate::core::error::BacktestError::ValidationError {
                field: "high/low".to_string(),
                reason: "high must be >= low".to_string(),
            });
        }
        if self.open < 0.0 || self.close < 0.0 {
            return Err(crate::core::error::BacktestError::ValidationError {
                field: "open/close".to_string(),
                reason: "prices must be non-negative".to_string(),
            });
        }
        Ok(())
    }
}

/// Individual executed trade
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Trade {
    pub id: String,
    pub entry_date: NaiveDate,
    pub exit_date: NaiveDate,
    pub entry_price: f64,
    pub exit_price: f64,
    pub quantity: f64,
    pub entry_signal: SignalAction,
    pub exit_signal: SignalAction,
    pub pnl: f64,
    pub commission: f64,
    pub hold_days: i32,
}

impl Trade {
    /// Create a new trade
    pub fn new(
        id: String,
        entry_date: NaiveDate,
        exit_date: NaiveDate,
        entry_price: f64,
        exit_price: f64,
        quantity: f64,
        entry_signal: SignalAction,
        exit_signal: SignalAction,
    ) -> Self {
        let commission = entry_price * quantity * 0.001; // 0.1% commission
        let pnl = (exit_price - entry_price) * quantity - commission;
        let hold_days = (exit_date - entry_date).num_days() as i32;

        Self {
            id,
            entry_date,
            exit_date,
            entry_price,
            exit_price,
            quantity,
            entry_signal,
            exit_signal,
            pnl,
            commission,
            hold_days,
        }
    }

    /// Check if trade is profitable
    pub fn is_profitable(&self) -> bool {
        self.pnl > 0.0
    }
}

/// Performance metrics and trade history from backtesting
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestResult {
    pub id: String,
    pub symbol: String,
    pub start_date: NaiveDate,
    pub end_date: NaiveDate,
    pub initial_capital: f64,
    pub final_value: f64,
    pub total_return_pct: f64,
    pub annual_return_pct: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown_pct: f64,
    pub win_rate_pct: f64,
    pub total_trades: usize,
    pub winning_trades: usize,
    pub losing_trades: usize,
    pub execution_time_ms: u64,
    pub parameters: ParameterSet,
    pub trades: Vec<Trade>,
    pub equity_curve: Vec<(NaiveDate, f64)>,
}

impl BacktestResult {
    /// Create a new backtest result
    pub fn new(
        id: String,
        symbol: String,
        start_date: NaiveDate,
        end_date: NaiveDate,
        initial_capital: f64,
        parameters: ParameterSet,
    ) -> Self {
        Self {
            id,
            symbol,
            start_date,
            end_date,
            initial_capital,
            final_value: initial_capital,
            total_return_pct: 0.0,
            annual_return_pct: 0.0,
            sharpe_ratio: 0.0,
            max_drawdown_pct: 0.0,
            win_rate_pct: 0.0,
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            execution_time_ms: 0,
            parameters,
            trades: Vec::new(),
            equity_curve: Vec::new(),
        }
    }

    /// Get human-readable summary
    pub fn summary(&self) -> String {
        format!(
            "Backtest Results for {}:\n\
            Period: {} to {}\n\
            Initial Capital: ${:.2}\n\
            Final Value: ${:.2}\n\
            Total Return: {:.2}%\n\
            Annual Return: {:.2}%\n\
            Sharpe Ratio: {:.2}\n\
            Max Drawdown: {:.2}%\n\
            Win Rate: {:.1}%\n\
            Total Trades: {}",
            self.symbol,
            self.start_date,
            self.end_date,
            self.initial_capital,
            self.final_value,
            self.total_return_pct,
            self.annual_return_pct,
            self.sharpe_ratio,
            self.max_drawdown_pct,
            self.win_rate_pct,
            self.total_trades
        )
    }
}
