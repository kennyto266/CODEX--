#[cfg(test)]
mod tests {
    use crate::backtest::metrics::*;

    #[test]
    fn test_calculate_metrics_basic() {
        let trades = vec![
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
        ];
        let equity_curve = vec![100000.0, 101000.0, 102500.0, 103000.0, 102000.0, 105000.0];
        
        let metrics = calculate_metrics(&trades, &equity_curve, 0.0).unwrap();
        
        assert!(metrics.total_return > 0.0);
        assert!(metrics.annualized_return > 0.0);
        assert!(metrics.trade_count == 2);
        assert!(metrics.win_rate >= 0.0 && metrics.win_rate <= 1.0);
        assert!(metrics.max_drawdown >= 0.0);
    }

    #[test]
    fn test_calculate_sharpe_ratio() {
        let returns = vec![0.01, -0.02, 0.015, -0.01, 0.02, 0.025];
        let volatility = 0.15;
        let sharpe = calculate_sharpe_ratio(&returns, 0.02, volatility);
        assert!(sharpe.is_finite());
    }

    #[test]
    fn test_calculate_max_drawdown() {
        let equity_curve = vec![100000.0, 110000.0, 105000.0, 95000.0, 105000.0, 90000.0];
        let max_dd = calculate_max_drawdown(&equity_curve);
        assert!(max_dd >= 0.0);
        assert!(max_dd <= 1.0);
    }
}
