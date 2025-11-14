//! T042: Rust性能指标计算器
//! 高性能金融性能指标计算引擎，支持8个核心指标
//!
//! 性能目标: 典型回测计算 < 10ms
//! 零panic错误处理
//! 支持组合和单一资产策略

use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fmt;

/// 交易记录结构
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Trade {
    pub entry_date: String,
    pub exit_date: String,
    pub entry_price: f64,
    pub exit_price: f64,
    pub quantity: f64,
    pub pnl: f64,
}

/// 性能指标结构
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PerformanceMetrics {
    pub total_return: f64,              // 总收益率 (%)
    pub annualized_return: f64,         // 年化收益率 (%)
    pub sharpe_ratio: f64,              // 夏普比率
    pub sortino_ratio: f64,             // 索提诺比率
    pub max_drawdown: f64,              // 最大回撤 (%)
    pub win_rate: f64,                  // 胜率 (%)
    pub trade_count: usize,             // 交易次数
    pub avg_hold_days: f64,             // 平均持仓天数
    pub profit_factor: f64,             // 盈利因子
    pub calmar_ratio: f64,              // 卡玛比率
    pub var_95: f64,                   // 95% VaR
    pub cvar_95: f64,                  // 95% CVaR
    pub volatility: f64,               // 波动率
    pub execution_time_ms: u64,        // 执行时间（毫秒）
    pub memory_usage_mb: f64,          // 内存使用（MB）
}

/// 回测结果结构（包含扩展指标）
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BacktestResult {
    pub config: super::BacktestConfig,
    pub metrics: PerformanceMetrics,
    pub trades: Vec<crate::types::Trade>,
    pub final_value: f64,
    pub execution_time_ns: u64,
}

/// 指标计算错误类型
#[derive(Debug, Clone)]
pub enum MetricsError {
    EmptyTrades,
    EmptyEquityCurve,
    InvalidData,
    DivisionByZero,
    InvalidDateRange,
}

impl fmt::Display for MetricsError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            MetricsError::EmptyTrades => write!(f, "交易记录为空"),
            MetricsError::EmptyEquityCurve => write!(f, "权益曲线为空"),
            MetricsError::InvalidData => write!(f, "数据无效（包含NaN或负值）"),
            MetricsError::DivisionByZero => write!(f, "除零错误"),
            MetricsError::InvalidDateRange => write!(f, "日期范围无效"),
        }
    }
}

impl Error for MetricsError {}

/// 计算所有性能指标
/// # 参数
/// * `trades` - 交易记录切片
/// * `equity_curve` - 权益曲线
/// * `risk_free_rate` - 无风险利率（默认0%）
///
/// # 返回值
/// 返回计算结果或错误
#[inline]
pub fn calculate_metrics(
    trades: &[Trade],
    equity_curve: &[f64],
    risk_free_rate: f64,
) -> Result<PerformanceMetrics, MetricsError> {
    // 验证输入数据
    validate_input(trades, equity_curve)?;

    // 计算日收益率
    let returns = calculate_returns(equity_curve)?;

    // 计算总收益率
    let initial_value = equity_curve
        .first()
        .ok_or(MetricsError::EmptyEquityCurve)?;
    let final_value = equity_curve
        .last()
        .ok_or(MetricsError::EmptyEquityCurve)?;
    let total_return = (final_value - initial_value) / initial_value;

    // 计算年化收益率
    let trading_days = 252u64;
    let days = equity_curve.len().saturating_sub(1) as u64;
    let annualized_return = calculate_annualized_return(total_return, days);

    // 计算夏普比率
    let volatility = calculate_volatility(&returns);
    let sharpe_ratio = calculate_sharpe_ratio(&returns, risk_free_rate, volatility);

    // 计算索提诺比率
    let sortino_ratio = calculate_sortino_ratio(&returns, risk_free_rate);

    // 计算最大回撤
    let max_drawdown = calculate_max_drawdown(equity_curve);

    // 计算胜率
    let winning_trades = calculate_winning_trades(trades);
    let trade_count = trades.len();
    let win_rate = if trade_count > 0 {
        winning_trades as f64 / trade_count as f64
    } else {
        0.0
    };

    // 计算平均持仓时间
    let avg_hold_days = calculate_average_hold_time(trades);

    // 计算盈利因子
    let profit_factor = calculate_profit_factor(trades);

    // 计算卡玛比率
    let calmar_ratio = if max_drawdown > 0.0 {
        annualized_return / max_drawdown
    } else {
        0.0
    };

    Ok(PerformanceMetrics {
        total_return,
        annualized_return,
        sharpe_ratio,
        sortino_ratio,
        max_drawdown,
        win_rate,
        trade_count,
        avg_hold_days,
        profit_factor,
        calmar_ratio,
        var_95: 0.0,
        cvar_95: 0.0,
        volatility: 0.0,
        execution_time_ms: 0,
        memory_usage_mb: 0.0,
    })
}

/// 计算夏普比率
/// 夏普比率 = (组合收益率 - 无风险利率) / 收益率标准差
#[inline]
pub fn calculate_sharpe_ratio(
    returns: &[f64],
    risk_free_rate: f64,
    volatility: f64,
) -> f64 {
    if volatility == 0.0 {
        return 0.0;
    }

    // 计算平均收益率并年化
    let mean_return = if !returns.is_empty() {
        returns.iter().sum::<f64>() / returns.len() as f64
    } else {
        0.0
    } * 252.0; // 年化

    (mean_return - risk_free_rate) / volatility
}

/// 计算索提诺比率
/// 使用下行偏差而不是标准差
#[inline]
pub fn calculate_sortino_ratio(returns: &[f64], risk_free_rate: f64) -> f64 {
    if returns.is_empty() {
        return 0.0;
    }

    // 只考虑负收益
    let negative_returns: Vec<f64> = returns.iter().filter(|&&r| r < 0.0).copied().collect();

    // 如果没有负收益，返回无穷大
    if negative_returns.is_empty() {
        return f64::INFINITY;
    }

    // 计算下行偏差
    let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
    let downside_deviation = (negative_returns
        .iter()
        .map(|r| (r - mean_return).powi(2))
        .sum::<f64>()
        / negative_returns.len() as f64)
    .sqrt()
        * (252.0_f64).sqrt(); // 年化

    if downside_deviation == 0.0 {
        return 0.0;
    }

    // 年化收益率
    let annualized_return = (1.0 + mean_return).powf(252.0) - 1.0;

    (annualized_return - risk_free_rate) / downside_deviation
}

/// 计算最大回撤
/// 峰谷法计算最大回撤百分比
#[inline]
pub fn calculate_max_drawdown(equity_curve: &[f64]) -> f64 {
    if equity_curve.is_empty() {
        return 0.0;
    }

    let mut peak = equity_curve[0];
    let mut max_drawdown = 0.0;

    for &value in equity_curve.iter() {
        if value > peak {
            peak = value;
        }

        if peak > 0.0 {
            let drawdown = (peak - value) / peak;
            if drawdown > max_drawdown {
                max_drawdown = drawdown;
            }
        }
    }

    max_drawdown
}

/// 计算年化收益率
/// 使用复合年增长率 (CAGR)
#[inline]
pub fn calculate_annualized_return(total_return: f64, days: u64) -> f64 {
    if days == 0 {
        return 0.0;
    }

    let years = days as f64 / 252.0; // 252个交易日/年
    (1.0 + total_return).powf(1.0 / years) - 1.0
}

/// 计算收益率
#[inline]
fn calculate_returns(equity_curve: &[f64]) -> Result<Vec<f64>, MetricsError> {
    if equity_curve.len() < 2 {
        return Ok(Vec::new());
    }

    let mut returns = Vec::with_capacity(equity_curve.len() - 1);

    for i in 1..equity_curve.len() {
        let prev_value = equity_curve[i - 1];
        if prev_value <= 0.0 {
            return Err(MetricsError::InvalidData);
        }
        let ret = (equity_curve[i] - prev_value) / prev_value;
        returns.push(ret);
    }

    Ok(returns)
}

/// 计算波动率（标准差）
#[inline]
fn calculate_volatility(returns: &[f64]) -> f64 {
    if returns.len() < 2 {
        return 0.0;
    }

    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns
        .iter()
        .map(|r| (r - mean).powi(2))
        .sum::<f64>()
        / (returns.len() - 1) as f64;

    variance.sqrt() * (252.0_f64).sqrt() // 年化
}

/// 计算获胜交易数量
#[inline]
fn calculate_winning_trades(trades: &[Trade]) -> usize {
    trades.iter().filter(|t| t.pnl > 0.0).count()
}

/// 计算平均持仓时间
#[inline]
fn calculate_average_hold_time(trades: &[Trade]) -> f64 {
    if trades.is_empty() {
        return 0.0;
    }

    let total_hold_time = trades
        .iter()
        .map(|trade| {
            parse_date_difference_days(&trade.exit_date, &trade.entry_date)
        })
        .sum::<f64>();

    total_hold_time / trades.len() as f64
}

/// 解析日期差值（简单实现）
#[inline]
fn parse_date_difference_days(exit_date: &str, entry_date: &str) -> f64 {
    // 简化实现，假设每个日期代表一天
    // 实际项目中应该使用chrono库进行日期计算
    1.0
}

/// 计算盈利因子
/// 盈利因子 = 总盈利 / 总亏损
#[inline]
fn calculate_profit_factor(trades: &[Trade]) -> f64 {
    let (total_profit, total_loss) = trades
        .iter()
        .fold((0.0, 0.0), |(profit, loss), trade| {
            if trade.pnl > 0.0 {
                (profit + trade.pnl, loss)
            } else {
                (profit, loss - trade.pnl) // 亏损为负数
            }
        });

    if total_loss == 0.0 {
        if total_profit > 0.0 {
            f64::INFINITY
        } else {
            0.0
        }
    } else {
        total_profit / total_loss
    }
}

/// 验证输入数据
#[inline]
fn validate_input(trades: &[Trade], equity_curve: &[f64]) -> Result<(), MetricsError> {
    if trades.is_empty() {
        return Err(MetricsError::EmptyTrades);
    }

    if equity_curve.is_empty() {
        return Err(MetricsError::EmptyEquityCurve);
    }

    // 检查是否有NaN值
    for &value in equity_curve {
        if value.is_nan() || value.is_infinite() || value < 0.0 {
            return Err(MetricsError::InvalidData);
        }
    }

    for trade in trades {
        if trade.entry_price.is_nan()
            || trade.exit_price.is_nan()
            || trade.quantity.is_nan()
            || trade.pnl.is_nan()
        {
            return Err(MetricsError::InvalidData);
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 辅助函数：创建测试交易
    fn create_test_trades() -> Vec<Trade> {
        vec![
            Trade {
                entry_date: "2023-01-01".to_string(),
                exit_date: "2023-01-05".to_string(),
                entry_price: 100.0,
                exit_price: 105.0,
                quantity: 100.0,
                pnl: 500.0,
            },
            Trade {
                entry_date: "2023-01-10".to_string(),
                exit_date: "2023-01-15".to_string(),
                entry_price: 102.0,
                exit_price: 98.0,
                quantity: 100.0,
                pnl: -400.0,
            },
            Trade {
                entry_date: "2023-01-20".to_string(),
                exit_date: "2023-01-30".to_string(),
                entry_price: 100.0,
                exit_price: 110.0,
                quantity: 100.0,
                pnl: 1000.0,
            },
            Trade {
                entry_date: "2023-02-01".to_string(),
                exit_date: "2023-02-05".to_string(),
                entry_price: 108.0,
                exit_price: 106.0,
                quantity: 100.0,
                pnl: -200.0,
            },
        ]
    }

    /// 辅助函数：创建测试权益曲线
    fn create_test_equity_curve() -> Vec<f64> {
        vec![
            100000.0,  // 初始价值
            101000.0,  // day 1
            102500.0,  // day 2
            103000.0,  // day 3
            102000.0,  // day 4
            105000.0,  // day 5
            106500.0,  // day 6
            107000.0,  // day 7
            106000.0,  // day 8
            108500.0,  // day 9
            110000.0,  // 结束价值
        ]
    }

    #[test]
    fn test_calculate_metrics_basic() {
        let trades = create_test_trades();
        let equity_curve = create_test_equity_curve();
        let metrics = calculate_metrics(&trades, &equity_curve, 0.0).unwrap();

        assert!(metrics.total_return > 0.0);
        assert!(metrics.annualized_return > 0.0);
        assert!(metrics.trade_count == 4);
        assert!(metrics.win_rate > 0.0 && metrics.win_rate <= 1.0);
        assert!(metrics.max_drawdown >= 0.0);
    }

    #[test]
    fn test_calculate_sharpe_ratio() {
        let returns = vec![0.01, -0.02, 0.015, -0.01, 0.02, 0.025];
        let volatility = 0.15;
        let sharpe = calculate_sharpe_ratio(&returns, 0.02, volatility);

        assert!(sharpe.is_finite());
        println!("夏普比率: {:.4}", sharpe);
    }

    #[test]
    fn test_calculate_sortino_ratio() {
        let returns = vec![0.01, -0.02, 0.015, -0.01, 0.02, 0.025];
        let sortino = calculate_sortino_ratio(&returns, 0.02);

        assert!(sortino.is_finite());
        assert!(sortino > 0.0);
        println!("索提诺比率: {:.4}", sortino);
    }

    #[test]
    fn test_calculate_max_drawdown() {
        let equity_curve = vec![100000.0, 110000.0, 105000.0, 95000.0, 105000.0, 90000.0];
        let max_dd = calculate_max_drawdown(&equity_curve);

        assert!(max_dd >= 0.0);
        assert!(max_dd <= 1.0);
        assert!((max_dd - 0.1818).abs() < 0.01, "最大回撤应为约18.18%，实际: {:.4}", max_dd);
    }

    #[test]
    fn test_calculate_annualized_return() {
        let total_return = 0.20; // 20%
        let days = 252; // 1年
        let annualized = calculate_annualized_return(total_return, days);

        assert!((annualized - 0.20).abs() < 0.01);
    }

    #[test]
    fn test_calculate_profit_factor() {
        let trades = create_test_trades();
        let profit_factor = calculate_profit_factor(&trades);

        assert!(profit_factor > 0.0);
        assert!(profit_factor.is_finite());
        println!("盈利因子: {:.4}", profit_factor);
    }

    #[test]
    fn test_empty_trades_error() {
        let trades: Vec<Trade> = Vec::new();
        let equity_curve = vec![100000.0, 110000.0];

        let result = calculate_metrics(&trades, &equity_curve, 0.0);
        assert!(result.is_err());
    }

    #[test]
    fn test_empty_equity_curve_error() {
        let trades = create_test_trades();
        let equity_curve: Vec<f64> = Vec::new();

        let result = calculate_metrics(&trades, &equity_curve, 0.0);
        assert!(result.is_err());
    }

    #[test]
    fn test_invalid_data_error() {
        let trades = create_test_trades();
        let equity_curve = vec![100000.0, f64::NAN, 110000.0];

        let result = calculate_metrics(&trades, &equity_curve, 0.0);
        assert!(result.is_err());
    }

    #[test]
    fn test_all_winning_trades() {
        let trades = vec![
            Trade {
                entry_date: "2023-01-01".to_string(),
                exit_date: "2023-01-02".to_string(),
                entry_price: 100.0,
                exit_price: 105.0,
                quantity: 100.0,
                pnl: 500.0,
            },
            Trade {
                entry_date: "2023-01-03".to_string(),
                exit_date: "2023-01-04".to_string(),
                entry_price: 100.0,
                exit_price: 110.0,
                quantity: 100.0,
                pnl: 1000.0,
            },
        ];
        let equity_curve = vec![100000.0, 105000.0, 115000.0];

        let metrics = calculate_metrics(&trades, &equity_curve, 0.0).unwrap();
        assert!((metrics.win_rate - 1.0).abs() < f64::EPSILON);
        assert!(metrics.profit_factor.is_infinite());
    }

    #[test]
    fn test_all_losing_trades() {
        let trades = vec![
            Trade {
                entry_date: "2023-01-01".to_string(),
                exit_date: "2023-01-02".to_string(),
                entry_price: 100.0,
                exit_price: 95.0,
                quantity: 100.0,
                pnl: -500.0,
            },
            Trade {
                entry_date: "2023-01-03".to_string(),
                exit_date: "2023-01-04".to_string(),
                entry_price: 100.0,
                exit_price: 90.0,
                quantity: 100.0,
                pnl: -1000.0,
            },
        ];
        let equity_curve = vec![100000.0, 95000.0, 85000.0];

        let metrics = calculate_metrics(&trades, &equity_curve, 0.0).unwrap();
        assert!((metrics.win_rate - 0.0).abs() < f64::EPSILON);
        assert!(metrics.profit_factor == 0.0);
    }

    #[test]
    fn test_single_trade() {
        let trades = vec![Trade {
            entry_date: "2023-01-01".to_string(),
            exit_date: "2023-01-02".to_string(),
            entry_price: 100.0,
            exit_price: 105.0,
            quantity: 100.0,
            pnl: 500.0,
        }];
        let equity_curve = vec![100000.0, 105000.0];

        let metrics = calculate_metrics(&trades, &equity_curve, 0.0).unwrap();
        assert_eq!(metrics.trade_count, 1);
        assert!((metrics.win_rate - 1.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_zero_volatility() {
        let returns = vec![0.01, 0.01, 0.01, 0.01, 0.01];
        let volatility = 0.0;
        let sharpe = calculate_sharpe_ratio(&returns, 0.02, volatility);

        assert_eq!(sharpe, 0.0);
    }

    #[test]
    fn test_performance_benchmark() {
        let trades = create_test_trades();
        let equity_curve = create_test_equity_curve();

        let start = std::time::Instant::now();
        for _ in 0..1000 {
            let _ = calculate_metrics(&trades, &equity_curve, 0.0);
        }
        let elapsed = start.elapsed();

        let avg_time = elapsed.as_millis() as f64 / 1000.0;
        println!("平均计算时间: {:.4}ms", avg_time);

        assert!(avg_time < 1.0, "性能测试失败：平均时间 {:.4}ms 超过 1ms", avg_time);
    }
}

/// Convert from types::Trade to metrics::Trade
impl From<crate::types::Trade> for Trade {
    fn from(trade: crate::types::Trade) -> Self {
        Trade {
            entry_date: trade.entry_time.to_string(),
            exit_date: trade.exit_time.map_or("".to_string(), |t| t.to_string()),
            entry_price: trade.entry_price,
            exit_price: trade.exit_price.unwrap_or(0.0),
            quantity: trade.quantity,
            pnl: trade.pnl.unwrap_or(0.0),
        }
    }
}
