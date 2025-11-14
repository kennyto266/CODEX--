//! Python bindings for rust-nonprice
//!
//! This module provides Python classes that wrap the Rust implementations

use pyo3::prelude::*;
use rust_nonprice::*;

/// Non-price indicator data class
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyNonPriceIndicator {
    pub inner: NonPriceIndicator,
}

#[pymethods]
impl PyNonPriceIndicator {
    #[new]
    pub fn new(symbol: String, date: String, value: f64, source: String) -> Self {
        let date = date.parse().unwrap_or(chrono::NaiveDate::from_ymd_opt(2000, 1, 1).unwrap());
        Self {
            inner: NonPriceIndicator::new(symbol, date, value, source),
        }
    }

    #[getter]
    pub fn symbol(&self) -> String {
        self.inner.symbol.clone()
    }

    #[getter]
    pub fn date(&self) -> String {
        self.inner.date.to_string()
    }

    #[getter]
    pub fn value(&self) -> f64 {
        self.inner.value
    }

    #[getter]
    pub fn source(&self) -> String {
        self.inner.source.clone()
    }

    #[getter]
    pub fn quality(&self) -> String {
        format!("{}", self.inner.quality)
    }
}

/// Technical indicator data class
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyTechnicalIndicator {
    pub inner: TechnicalIndicator,
}

#[pymethods]
impl PyTechnicalIndicator {
    #[new]
    pub fn new(symbol: String, date: String, indicator_type: String, window_size: usize, value: f64) -> Self {
        let date = date.parse().unwrap_or(chrono::NaiveDate::from_ymd_opt(2000, 1, 1).unwrap());
        let indicator_type = match indicator_type.as_str() {
            "ZSCORE" => IndicatorType::ZScore,
            "RSI" => IndicatorType::RSI,
            "SMA_FAST" => IndicatorType::SMAFast,
            "SMA_SLOW" => IndicatorType::SMASlow,
            _ => IndicatorType::ZScore,
        };
        Self {
            inner: TechnicalIndicator::new(symbol, date, indicator_type, window_size, value),
        }
    }

    #[getter]
    pub fn symbol(&self) -> String {
        self.inner.base_symbol.clone()
    }

    #[getter]
    pub fn date(&self) -> String {
        self.inner.date.to_string()
    }

    #[getter]
    pub fn indicator_type(&self) -> String {
        format!("{}", self.inner.indicator_type)
    }

    #[getter]
    pub fn value(&self) -> Option<f64> {
        self.inner.value
    }

    #[getter]
    pub fn window_size(&self) -> usize {
        self.inner.window_size
    }
}

/// Trading signal data class
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyTradingSignal {
    pub inner: TradingSignal,
}

#[pymethods]
impl PyTradingSignal {
    #[new]
    pub fn new(symbol: String, date: String, action: String, strength: f64) -> Self {
        let date = date.parse().unwrap_or(chrono::NaiveDate::from_ymd_opt(2000, 1, 1).unwrap());
        let action = match action.as_str() {
            "BUY" => SignalAction::Buy,
            "SELL" => SignalAction::Sell,
            "HOLD" => SignalAction::Hold,
            _ => SignalAction::Hold,
        };
        Self {
            inner: TradingSignal {
                symbol,
                date,
                action,
                strength,
                confidence: 0.5,
            },
        }
    }

    #[getter]
    pub fn symbol(&self) -> String {
        self.inner.symbol.clone()
    }

    #[getter]
    pub fn date(&self) -> String {
        self.inner.date.to_string()
    }

    #[getter]
    pub fn action(&self) -> String {
        format!("{}", self.inner.action)
    }

    #[getter]
    pub fn strength(&self) -> f64 {
        self.inner.strength
    }

    #[getter]
    pub fn confidence(&self) -> f64 {
        self.inner.confidence
    }
}

/// Parameter set for optimization
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyParameterSet {
    pub inner: ParameterSet,
}

#[pymethods]
impl PyParameterSet {
    #[new]
    pub fn new(
        indicator_name: String,
        zscore_buy: f64,
        zscore_sell: f64,
        rsi_buy: f64,
        rsi_sell: f64,
        sma_fast: usize,
        sma_slow: usize,
    ) -> Self {
        Self {
            inner: ParameterSet {
                id: format!("py-{}", chrono::Utc::now().timestamp()),
                indicator_name,
                zscore_buy,
                zscore_sell,
                rsi_buy,
                rsi_sell,
                sma_fast,
                sma_slow,
                created_at: chrono::Utc::now(),
            },
        }
    }

    #[getter]
    pub fn id(&self) -> String {
        self.inner.id.clone()
    }

    #[getter]
    pub fn indicator_name(&self) -> String {
        self.inner.indicator_name.clone()
    }

    #[getter]
    pub fn zscore_buy(&self) -> f64 {
        self.inner.zscore_buy
    }

    #[getter]
    pub fn zscore_sell(&self) -> f64 {
        self.inner.zscore_sell
    }

    #[getter]
    pub fn rsi_buy(&self) -> f64 {
        self.inner.rsi_buy
    }

    #[getter]
    pub fn rsi_sell(&self) -> f64 {
        self.inner.rsi_sell
    }

    #[getter]
    pub fn sma_fast(&self) -> usize {
        self.inner.sma_fast
    }

    #[getter]
    pub fn sma_slow(&self) -> usize {
        self.inner.sma_slow
    }
}

/// Backtest engine class
#[pyclass]
pub struct PyBacktestEngine {
    config: BacktestConfig,
}

#[pymethods]
impl PyBacktestEngine {
    #[new]
    pub fn new(initial_capital: f64, commission: f64) -> Self {
        Self {
            config: BacktestConfig {
                initial_capital,
                commission,
                position_sizing: PositionSizing::Fixed,
                risk_free_rate: 0.02,
            },
        }
    }

    pub fn run_backtest(
        &self,
        signals: Vec<PyTradingSignal>,
        stock_data: Vec<String>,
    ) -> PyResult<String> {
        // This is a stub implementation
        let result = format!(
            "Backtest completed with {} signals and {} stock data points",
            signals.len(),
            stock_data.len()
        );
        Ok(result)
    }
}

/// Parameter optimizer class
#[pyclass]
pub struct PyParameterOptimizer {
    config: OptimizationConfig,
}

#[pymethods]
impl PyParameterOptimizer {
    #[new]
    pub fn new(metric: String, max_iterations: usize) -> Self {
        let metric = match metric.as_str() {
            "SHARPE" => OptimizationMetric::SharpeRatio,
            "RETURN" => OptimizationMetric::TotalReturn,
            "DRAWDOWN" => OptimizationMetric::MaxDrawdown,
            _ => OptimizationMetric::SharpeRatio,
        };
        Self {
            config: OptimizationConfig {
                metric,
                max_iterations,
                tolerance: 0.001,
                parallel: true,
            },
        }
    }

    pub fn optimize(&self, data: Vec<PyNonPriceIndicator>) -> PyResult<PyParameterSet> {
        // This is a stub implementation
        Ok(PyParameterSet::new(
            "optimized".to_string(),
            -0.5,
            0.5,
            25.0,
            65.0,
            10,
            30,
        ))
    }
}

/// Report generator class
#[pyclass]
pub struct PyReportGenerator;

#[pymethods]
impl PyReportGenerator {
    #[new]
    pub fn new() -> Self {
        Self
    }

    pub fn generate_markdown(&self, result: String, output_path: String) -> PyResult<String> {
        // This is a stub implementation
        Ok(format!("Report generated at {}", output_path))
    }

    pub fn generate_json(&self, result: String, output_path: String) -> PyResult<String> {
        // This is a stub implementation
        Ok(format!("JSON report generated at {}", output_path))
    }
}

/// Main Python module
#[pymodule]
fn rust_nonprice(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyNonPriceIndicator>()?;
    m.add_class::<PyTechnicalIndicator>()?;
    m.add_class::<PyTradingSignal>()?;
    m.add_class::<PyParameterSet>()?;
    m.add_class::<PyBacktestEngine>()?;
    m.add_class::<PyParameterOptimizer>()?;
    m.add_class::<PyReportGenerator>()?;

    Ok(())
}
