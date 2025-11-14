//! 综合技术指标测试
#[cfg(test)]
mod tests {
    use quant_core::indicators::*;
    use quant_core::types::OHLCV;

    fn generate_test_data(len: usize) -> Vec<OHLCV> {
        let mut data = Vec::with_capacity(len);
        let base_price = 100.0;
        for i in 0..len {
            let timestamp = (i as u64) * 86400;
            let noise = (i as f64).sin() * 2.0;
            let price = base_price + noise;
            data.push(OHLCV {
                timestamp,
                open: price,
                high: price + 1.0,
                low: price - 1.0,
                close: price,
                volume: 1000.0,
            });
        }
        data
    }

    #[test]
    fn test_sma_calculation() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
        let result = sma(&prices, 5);
        assert_eq!(result.len(), 10);
        assert!((result[4] - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_ema_calculation() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ema(&prices, 3);
        assert_eq!(result.len(), 5);
        assert_eq!(result[0], 1.0);
    }

    #[test]
    fn test_rsi_calculation() {
        let prices = vec![1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 4.0, 3.0, 2.0];
        let result = rsi(&prices, 5);
        assert_eq!(result.len(), 10);
        for rsi_val in &result {
            assert!(*rsi_val >= 0.0);
            assert!(*rsi_val <= 100.0);
        }
    }

    #[test]
    fn test_macd_calculation() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5];
        let (macd_line, signal_line, histogram) = macd(&prices, 3, 6, 3);
        assert_eq!(macd_line.len(), 12);
        assert_eq!(signal_line.len(), 12);
        assert_eq!(histogram.len(), 12);
    }

    #[test]
    fn test_bollinger_bands() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5];
        let (upper, middle, lower) = bollinger_bands(&prices, 5, 2.0);
        assert_eq!(upper.len(), 10);
        assert_eq!(middle.len(), 10);
        assert_eq!(lower.len(), 10);
    }

    #[test]
    fn test_all_indicators_with_real_data() {
        let data = generate_test_data(100);
        let close_prices: Vec<f64> = data.iter().map(|d| d.close).collect();
        let high_prices: Vec<f64> = data.iter().map(|d| d.high).collect();
        let low_prices: Vec<f64> = data.iter().map(|d| d.low).collect();
        let volumes: Vec<u64> = data.iter().map(|d| d.volume as u64).collect();
        
        let sma_20 = sma(&close_prices, 20);
        assert_eq!(sma_20.len(), 100);
        
        let rsi_14 = rsi(&close_prices, 14);
        assert_eq!(rsi_14.len(), 100);
        
        let (_macd, _signal, _histogram) = macd(&close_prices, 12, 26, 9);
        
        let atr_14 = atr(&high_prices, &low_prices, &close_prices, 14);
        assert_eq!(atr_14.len(), 100);
        
        let obv_values = obv(&close_prices, &volumes);
        assert_eq!(obv_values.len(), 100);
    }

    #[test]
    fn test_edge_cases() {
        let empty: Vec<f64> = vec![];
        assert!(sma(&empty, 5).is_empty());
        assert!(rsi(&empty, 5).is_empty());
        
        let single = vec![100.0];
        let sma_single = sma(&single, 5);
        assert_eq!(sma_single.len(), 1);
    }
}
