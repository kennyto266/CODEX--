//! Core data types for the quantitative trading system

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// OHLCV (Open, High, Low, Close, Volume) data point
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct OHLCV {
    pub timestamp: u64,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}

/// Signal type for trade actions
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SignalType {
    Buy,
    Sell,
    Hold,
}

/// Trading signal
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Signal {
    pub timestamp: u64,
    pub signal_type: SignalType,
    pub price: f64,
    pub strength: f64,
}

/// Trade record
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Trade {
    pub id: u64,
    pub entry_time: u64,
    pub exit_time: Option<u64>,
    pub entry_price: f64,
    pub exit_price: Option<f64>,
    pub quantity: f64,
    pub pnl: Option<f64>,
    pub commission: f64,
}

/// Data point alias for backward compatibility
pub type DataPoint = OHLCV;

/// Market data container
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub points: Vec<OHLCV>,
}

impl MarketData {
    /// Create new market data container
    pub fn new(points: Vec<OHLCV>) -> Self {
        Self { points }
    }

    /// Get data length
    pub fn len(&self) -> usize {
        self.points.len()
    }

    /// Check if data is empty
    pub fn is_empty(&self) -> bool {
        self.points.is_empty()
    }
}
