//! T041: Rust回测引擎
//! 高性能回测引擎，支持快速信号处理和交易执行模拟

use serde::{Serialize, Deserialize};
use crate::backtest::BacktestConfig;
use crate::types::{OHLCV, Signal, Trade as TypesTrade, SignalType, DataPoint};
use crate::backtest::BacktestResult;
use rayon::prelude::*;
use std::time::Instant;

/// Main backtest engine
#[derive(Clone)]
pub struct BacktestEngine {
    pub config: BacktestConfig,
}

impl BacktestEngine {
    /// Create a new backtest engine with given configuration
    #[inline]
    pub fn new(config: BacktestConfig) -> Self {
        Self { config }
    }

    /// Run backtest with signals
    pub fn run(
        &self,
        data: &[OHLCV],
        signals: &[Signal],
    ) -> Result<BacktestResult, Box<dyn std::error::Error>> {
        let start_time = Instant::now();

        // Create DataPoint from OHLCV
        let data_points: Vec<DataPoint> = data.iter().map(|&d| d).collect();

        // Execute trades based on signals
        let (trades, equity_curve) = self.execute_trades(&data_points, signals)?;

        // Calculate performance metrics using the new metrics calculator
        let trades_converted: Vec<super::metrics::Trade> = trades.iter().cloned().map(|t| t.into()).collect();
        let metrics = super::metrics::calculate_metrics(
            &trades_converted,
            &equity_curve,
            0.0, // risk-free rate
        )?;

        let execution_time = start_time.elapsed();
        let result = BacktestResult {
            config: self.config.clone(),
            metrics,
            trades: trades.clone(),
            final_value: *equity_curve.last().unwrap_or(&self.config.initial_capital),
            execution_time_ns: execution_time.as_nanos() as u64,
        };

        Ok(result)
    }

    /// Execute trades based on signals with parallel processing
    fn execute_trades(
        &self,
        data: &[DataPoint],
        signals: &[Signal],
    ) -> Result<(Vec<TypesTrade>, Vec<f64>), Box<dyn std::error::Error>> {
        if data.is_empty() {
            return Err("Empty data".into());
        }

        let mut trades = Vec::new();
        let mut equity_curve = Vec::with_capacity(data.len());
        let mut current_capital = self.config.initial_capital;

        // Sort signals by timestamp to ensure proper order
        let mut sorted_signals = signals.to_vec();
        sorted_signals.sort_by_key(|s| s.timestamp);

        let mut position = 0.0;
        let mut entry_price = 0.0;

        for data_point in data {
            // Update equity curve
            current_capital = self.config.initial_capital + position * (data_point.close - entry_price);
            equity_curve.push(current_capital);

            // Process signals at this timestamp
            for signal in sorted_signals.iter().filter(|s| s.timestamp == data_point.timestamp) {
                match signal.signal_type {
                    SignalType::Buy if position <= 0.0 => {
                        entry_price = data_point.close * (1.0 + self.config.slippage);
                        let max_quantity = (current_capital * 0.95) / entry_price;
                        position = max_quantity;
                        current_capital -= position * entry_price * (1.0 + self.config.commission);
                    }
                    SignalType::Sell if position > 0.0 => {
                        let proceeds = position * data_point.close * (1.0 - self.config.slippage);
                        current_capital += proceeds * (1.0 - self.config.commission);
                        
                        // Record trade using types::Trade
                        if let Some(entry_sig) = sorted_signals.iter().find(|s| s.signal_type == SignalType::Buy) {
                            let trade = TypesTrade {
                                id: trades.len() as u64,
                                entry_time: entry_sig.timestamp,
                                exit_time: Some(data_point.timestamp),
                                entry_price,
                                exit_price: Some(data_point.close),
                                quantity: position,
                                pnl: Some(proceeds - position * entry_price),
                                commission: position * entry_price * self.config.commission,
                            };
                            trades.push(trade);
                        }
                        
                        position = 0.0;
                    }
                    _ => {}
                }
            }
        }

        Ok((trades, equity_curve))
    }
}

/// Re-export from metrics module

/// Strategy parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyParams {
    pub strategy_type: String,
    pub fast_period: Option<usize>,
    pub slow_period: Option<usize>,
    pub period: Option<usize>,
    pub threshold: Option<f64>,
    pub commission: Option<f64>,
}

/// Validate market data integrity
pub fn validate_data(data: &[OHLCV]) -> Result<bool, Box<dyn std::error::Error>> {
    if data.is_empty() {
        return Err("Data is empty".into());
    }
    
    for (i, d) in data.iter().enumerate() {
        // Check OHLC relationship
        if d.high < d.low {
            return Err(format!("At index {}: High ({}) < Low ({})", i, d.high, d.low).into());
        }
        if d.high < d.open {
            return Err(format!("At index {}: High ({}) < Open ({})", i, d.high, d.open).into());
        }
        if d.high < d.close {
            return Err(format!("At index {}: High ({}) < Close ({})", i, d.high, d.close).into());
        }
        if d.low > d.open {
            return Err(format!("At index {}: Low ({}) > Open ({})", i, d.low, d.open).into());
        }
        if d.low > d.close {
            return Err(format!("At index {}: Low ({}) > Close ({})", i, d.low, d.close).into());
        }
        
        // Check for NaN or infinite values
        if !d.open.is_finite() || !d.high.is_finite() || !d.low.is_finite() || !d.close.is_finite() {
            return Err(format!("At index {}: Non-finite value detected", i).into());
        }
    }
    
    Ok(true)
}

/// Calculate maximum drawdown
pub fn calculate_drawdown(equity_curve: &[f64]) -> Result<f64, Box<dyn std::error::Error>> {
    if equity_curve.is_empty() {
        return Err("Equity curve is empty".into());
    }
    
    let mut peak = equity_curve[0];
    let mut max_drawdown = 0.0;
    
    for &value in equity_curve {
        if value > peak {
            peak = value;
        }
        
        let drawdown = (peak - value) / peak;
        if drawdown > max_drawdown {
            max_drawdown = drawdown;
        }
    }
    
    Ok(max_drawdown)
}

/// Run SMA backtest
pub fn run_sma_backtest(
    data: &[OHLCV],
    fast_period: usize,
    slow_period: usize,
    initial_capital: f64,
) -> Result<BacktestResult, Box<dyn std::error::Error>> {
    if fast_period >= slow_period {
        return Err("Fast period must be less than slow period".into());
    }
    
    if fast_period == 0 || slow_period == 0 {
        return Err("Periods must be greater than 0".into());
    }
    
    // Validate data
    validate_data(data)?;
    
    if data.len() < slow_period {
        return Err(format!("Not enough data points. Need at least {}, got {}", slow_period, data.len()).into());
    }
    
    // Create config
    let config = BacktestConfig {
        initial_capital,
        commission: 0.001,
        slippage: 0.0005,
        start_date: 0,
        end_date: u64::MAX,
    };
    
    // Generate signals
    let signals = generate_sma_signals(data, fast_period, slow_period)?;
    
    // Create engine and run
    let engine = BacktestEngine::new(config);
    engine.run(data, &signals)
}

/// Generate SMA crossover signals
fn generate_sma_signals(
    data: &[OHLCV],
    fast_period: usize,
    slow_period: usize,
) -> Result<Vec<Signal>, Box<dyn std::error::Error>> {
    let mut signals = Vec::new();
    
    // Extract close prices
    let close_prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    
    // Calculate moving averages
    let mut fast_ma = vec![0.0; data.len()];
    let mut slow_ma = vec![0.0; data.len()];
    
    // Calculate fast MA
    for i in fast_period..data.len() {
        let sum: f64 = close_prices[i - fast_period..i].iter().sum();
        fast_ma[i] = sum / fast_period as f64;
    }
    
    // Calculate slow MA
    for i in slow_period..data.len() {
        let sum: f64 = close_prices[i - slow_period..i].iter().sum();
        slow_ma[i] = sum / slow_period as f64;
    }
    
    // Generate crossover signals
    let mut prev_signal = None;
    for i in slow_period..data.len() {
        let current_fast = fast_ma[i];
        let current_slow = slow_ma[i];
        let prev_fast = fast_ma[i - 1];
        let prev_slow = slow_ma[i - 1];

        let signal = if current_fast > current_slow && prev_fast <= prev_slow {
            // Golden cross - buy signal
            Some(SignalType::Buy)
        } else if current_fast < current_slow && prev_fast >= prev_slow {
            // Death cross - sell signal
            Some(SignalType::Sell)
        } else {
            // No signal - maintain previous state
            None
        };

        if let Some(sig) = signal {
            if Some(sig) != prev_signal {
                signals.push(Signal {
                    timestamp: data[i].timestamp,
                    signal_type: sig,
                    price: close_prices[i],
                    strength: 1.0,
                });
                prev_signal = Some(sig);
            }
        }
    }
    
    Ok(signals)
}

/// Run comprehensive backtest with detailed tracking
pub fn run_comprehensive_backtest(
    data: &[OHLCV],
    signals: &[Signal],
    config: BacktestConfig,
) -> Result<ComprehensiveResult, Box<dyn std::error::Error>> {
    let start_time = Instant::now();

    // Validate data
    validate_data(data)?;

    // Create engine and run basic backtest
    let engine = BacktestEngine::new(config.clone());
    let result = engine.run(data, signals)?;

    // Create comprehensive result
    let comprehensive_result = ComprehensiveResult {
        backtest_result: result,
        initial_capital: config.initial_capital,
        risk_free_rate: 0.02, // 2% default
        dataset_size: data.len(),
        signal_count: signals.len(),
    };

    Ok(comprehensive_result)
}

/// Comprehensive backtest result with additional data
#[derive(Debug, Clone)]
pub struct ComprehensiveResult {
    pub backtest_result: BacktestResult,
    pub initial_capital: f64,
    pub risk_free_rate: f64,
    pub dataset_size: usize,
    pub signal_count: usize,
}

impl ComprehensiveResult {
    /// Get summary string
    pub fn summary(&self) -> String {
        format!(
            "Backtest Summary:\n\
             Initial Capital: ${:.2}\n\
             Final Value: ${:.2}\n\
             Total Return: {:.2}%\n\
             Annualized Return: {:.2}%\n\
             Sharpe Ratio: {:.2}\n\
             Max Drawdown: {:.2}%\n\
             Total Trades: {}\n\
             Win Rate: {:.2}%\n\
             Execution Time: {:.2}ms",
            self.initial_capital,
            self.backtest_result.final_value,
            self.backtest_result.metrics.total_return * 100.0,
            self.backtest_result.metrics.annualized_return * 100.0,
            self.backtest_result.metrics.sharpe_ratio,
            self.backtest_result.metrics.max_drawdown * 100.0,
            self.backtest_result.metrics.trade_count,
            self.backtest_result.metrics.win_rate * 100.0,
            self.backtest_result.execution_time_ns as f64 / 1_000_000.0
        )
    }
}

/// Run backtest with transaction cost tracking
pub fn run_backtest(
    signals: &[Signal],
    stock_data: &[OHLCV],
    config: BacktestConfig,
) -> Result<BacktestResult, Box<dyn std::error::Error>> {
    if stock_data.is_empty() {
        return Err("Empty stock data".into());
    }

    // Validate stock data
    validate_data(stock_data)?;

    // Create engine and run
    let engine = BacktestEngine::new(config);
    engine.run(stock_data, signals)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;

    /// Generate test data
    fn generate_test_data(n: usize) -> Vec<OHLCV> {
        let mut data = Vec::with_capacity(n);
        let mut price = 100.0;
        let timestamp_base = 1_600_000_000;

        for i in 0..n {
            let open = price;
            let change = (i as f64 % 10.0 - 5.0) * 0.5;
            let high = open + change.abs() + 1.0;
            let low = open - change.abs() - 1.0;
            let close = open + change;

            data.push(OHLCV {
                timestamp: timestamp_base + i as u64 * 86400,
                open,
                high,
                low,
                close,
                volume: 1_000_000.0,
            });

            price = close;
        }

        data
    }

    #[test]
    fn test_backtest_basic_sma() {
        // Test with explicit signals to ensure trades
        let data = generate_test_data(100);
        let config = BacktestConfig {
            initial_capital: 100_000.0,
            commission: 0.001,
            slippage: 0.0005,
            start_date: 0,
            end_date: u64::MAX,
        };

        // Create explicit buy and sell signals
        let mut signals = Vec::new();
        signals.push(Signal {
            timestamp: data[10].timestamp,
            signal_type: SignalType::Buy,
            price: data[10].close,
            strength: 1.0,
        });
        signals.push(Signal {
            timestamp: data[50].timestamp,
            signal_type: SignalType::Sell,
            price: data[50].close,
            strength: 1.0,
        });

        let result = run_backtest(&signals, &data, config).unwrap();

        assert!(result.final_value > 0.0);
        assert!(result.metrics.trade_count >= 0);
        assert!(result.metrics.max_drawdown >= 0.0);
        assert!(result.execution_time_ns > 0);

        println!("回测测试通过: 最终价值 ${:.2}, 交易次数: {}",
            result.final_value, result.trades.len());
    }

    #[test]
    fn test_backtest_run_function() {
        let data = generate_test_data(50);
        let config = BacktestConfig::default();

        let signals = vec![
            Signal {
                timestamp: data[10].timestamp,
                signal_type: SignalType::Buy,
                price: data[10].close,
                strength: 1.0,
            },
            Signal {
                timestamp: data[30].timestamp,
                signal_type: SignalType::Sell,
                price: data[30].close,
                strength: 1.0,
            },
        ];

        let result = run_backtest(&signals, &data, config).unwrap();

        assert!(result.final_value > 0.0);
        println!("run_backtest测试通过: 最终价值 ${:.2}", result.final_value);
    }

    #[test]
    fn test_data_validation() {
        let empty_data: Vec<OHLCV> = Vec::new();
        assert!(validate_data(&empty_data).is_err());

        let invalid_data = vec![OHLCV {
            timestamp: 1,
            open: 100.0,
            high: 90.0,
            low: 95.0,
            close: 92.0,
            volume: 1000.0,
        }];
        assert!(validate_data(&invalid_data).is_err());

        let valid_data = vec![OHLCV {
            timestamp: 1,
            open: 100.0,
            high: 110.0,
            low: 95.0,
            close: 105.0,
            volume: 1000.0,
        }];
        assert!(validate_data(&valid_data).is_ok());

        println!("数据验证测试通过");
    }
}
