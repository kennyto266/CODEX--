//! Technical Indicators Usage Example
//! Demonstrates how to use the technical indicators module

use quant_core::indicators::*;
use quant_core::types::OHLCV;

fn main() {
    // Generate sample data (100 data points)
    let data = generate_sample_data(100);
    
    // Extract price arrays
    let close_prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    let high_prices: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low_prices: Vec<f64> = data.iter().map(|d| d.low).collect();
    let volumes: Vec<u64> = data.iter().map(|d| d.volume as u64).collect();
    
    println!("=== Technical Indicators Example ===\n");
    
    // 1. Simple Moving Average
    let sma_20 = sma(&close_prices, 20);
    println!("SMA(20) - Last 5 values:");
    for i in (95..100).filter(|i| *i < sma_20.len()) {
        println!("  Day {}: {:.2}", i+1, sma_20[i]);
    }
    println!();
    
    // 2. RSI
    let rsi_14 = rsi(&close_prices, 14);
    let rsi_signals = rsi_signals(&rsi_14, 30.0, 70.0);
    println!("RSI(14) - Last 5 values with signals:");
    for i in (95..100).filter(|i| *i < rsi_14.len()) {
        let signal = match rsi_signals[i] {
            1 => "BUY",
            -1 => "SELL",
            _ => "HOLD",
        };
        println!("  Day {}: {:.2} - {}", i+1, rsi_14[i], signal);
    }
    println!();
    
    // 3. MACD
    let (macd_line, signal_line, histogram) = macd(&close_prices, 12, 26, 9);
    let macd_signals = macd_signals(&macd_line, &signal_line);
    println!("MACD(12,26,9) - Last 5 values with signals:");
    for i in (95..100).filter(|i| *i < macd_line.len()) {
        let signal = match macd_signals[i] {
            1 => "BUY",
            -1 => "SELL",
            _ => "HOLD",
        };
        println!("  Day {}: MACD={:.3}, Signal={:.3}, Hist={:.3} - {}", 
                 i+1, macd_line[i], signal_line[i], histogram[i], signal);
    }
    println!();
    
    // 4. Bollinger Bands
    let (bb_upper, bb_middle, bb_lower) = bollinger_bands(&close_prices, 20, 2.0);
    let bb_signals = bollinger_signals(&close_prices, &bb_upper, &bb_lower);
    println!("Bollinger Bands(20, 2σ) - Last 5 values:");
    for i in (95..100).filter(|i| *i < bb_upper.len()) {
        let signal = match bb_signals[i] {
            1 => "BUY",
            -1 => "SELL",
            _ => "HOLD",
        };
        println!("  Day {}: Close={:.2}, Upper={:.2}, Middle={:.2}, Lower={:.2} - {}", 
                 i+1, close_prices[i], bb_upper[i], bb_middle[i], bb_lower[i], signal);
    }
    println!();
    
    // 5. ATR (for volatility)
    let atr_14 = atr(&high_prices, &low_prices, &close_prices, 14);
    println!("ATR(14) - Last 5 values:");
    for i in (95..100).filter(|i| *i < atr_14.len()) {
        println!("  Day {}: {:.2} (volatility)", i+1, atr_14[i]);
    }
    println!();
    
    // 6. Calculate all indicators at once (parallel)
    println!("=== Parallel Calculation (All Indicators) ===");
    let all_indicators = calculate_all_indicators(&data);
    println!("Calculated {} indicator sets", all_indicators.len());
    for (name, values) in &all_indicators {
        if let Some(last_value) = values.last() {
            println!("  {}: {:.2}", name, last_value.value);
        }
    }
}

fn generate_sample_data(len: usize) -> Vec<OHLCV> {
    let mut data = Vec::with_capacity(len);
    let base_price = 100.0;
    
    for i in 0..len {
        let timestamp = (i as u64) * 86400;
        // Simulate price with trend and noise
        let trend = (i as f64) * 0.1;
        let noise = (i as f64).sin() * 2.0 + (i as f64 / 10.0).cos() * 1.5;
        let price = base_price + trend + noise;
        
        data.push(OHLCV {
            timestamp,
            open: price,
            high: price + 1.5,
            low: price - 1.5,
            close: price,
            volume: 1000.0 + (i as f64 * 10.0),
        });
    }
    
    data
}
