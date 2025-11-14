//! 演示程序：完整的非价格数据技术指标系统
//!
//! 此程序演示如何使用 Rust Non-Price 系统：
//! 1. 创建模拟 HIBOR 数据
//! 2. 计算技术指标
//! 3. 生成交易信号
//! 4. 优化参数
//! 5. 回测并显示结果

use chrono::NaiveDate;
use std::path::Path;
use std::fs::File;
use std::io::Write;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("{}", "=".repeat(80));
    println!("🎯 Rust 非价格数据技术指标系统 - 完整演示");
    println!("{}", "=".repeat(80));
    println!();

    // 步骤 1: 生成模拟 HIBOR 数据
    println!("📊 步骤 1: 生成模拟 HIBOR 数据...");
    let hibor_data = generate_hibor_data(100);
    println!("   ✅ 生成了 {} 个 HIBOR 数据点", hibor_data.len());

    // 保存到 CSV
    let csv_path = "demo_hibor_data.csv";
    save_hibor_to_csv(&hibor_data, csv_path)?;
    println!("   💾 数据已保存到: {}", csv_path);
    println!();

    // 步骤 2: 加载数据
    println!("📥 步骤 2: 加载数据...");
    let indicators = rust_nonprice::load_nonprice_csv(Path::new(csv_path))?;
    println!("   ✅ 成功加载 {} 个指标", indicators.len());
    println!();

    // 步骤 3: 计算技术指标
    println!("🧮 步骤 3: 计算技术指标...");
    let technical_indicators = rust_nonprice::calculate_all(&indicators)?;
    println!("   ✅ 计算完成，共 {} 个技术指标", technical_indicators.len());
    println!("      - Z-Score 指标: {} 个", technical_indicators.iter().filter(|i| i.indicator_type == rust_nonprice::IndicatorType::ZScore).count());
    println!("      - RSI 指标: {} 个", technical_indicators.iter().filter(|i| i.indicator_type == rust_nonprice::IndicatorType::RSI).count());
    println!("      - SMA 指标: {} 个", technical_indicators.iter().filter(|i| i.indicator_type == rust_nonprice::IndicatorType::SMAFast).count());
    println!();

    // 步骤 4: 创建默认参数
    println!("⚙️  步骤 4: 创建参数配置...");
    let parameters = rust_nonprice::ParameterSet::default();
    println!("   ✅ 参数配置:");
    println!("      - Z-Score 买入阈值: {}", parameters.zscore_buy);
    println!("      - Z-Score 卖出阈值: {}", parameters.zscore_sell);
    println!("      - RSI 买入阈值: {}", parameters.rsi_buy);
    println!("      - RSI 卖出阈值: {}", parameters.rsi_sell);
    println!();

    // 步骤 5: 生成交易信号
    println!("📈 步骤 5: 生成交易信号...");
    let signals = rust_nonprice::generate_signals(&technical_indicators, &parameters)?;
    println!("   ✅ 生成了 {} 个交易信号", signals.len());
    let buy_signals = signals.iter().filter(|s| s.action == rust_nonprice::SignalAction::Buy).count();
    let sell_signals = signals.iter().filter(|s| s.action == rust_nonprice::SignalAction::Sell).count();
    let hold_signals = signals.iter().filter(|s| s.action == rust_nonprice::SignalAction::Hold).count();
    println!("      - 买入信号: {} 个", buy_signals);
    println!("      - 卖出信号: {} 个", sell_signals);
    println!("      - 持有信号: {} 个", hold_signals);
    println!();

    // 步骤 6: 生成模拟股票数据
    println!("📊 步骤 6: 生成模拟股票数据 (用于回测)...");
    let stock_data = generate_stock_data(100);
    let stock_csv = "demo_stock_data.csv";
    save_stock_to_csv(&stock_data, stock_csv)?;
    println!("   ✅ 生成了 {} 个股票数据点", stock_data.len());
    println!();

    // 步骤 7: 加载股票数据
    let stock_indicators = rust_nonprice::load_stock_prices(Path::new(stock_csv), "0700.HK")?;
    println!("   ✅ 加载股票数据: {} 个数据点", stock_indicators.len());
    println!();

    // 步骤 8: 运行回测
    println!("🔄 步骤 8: 运行回测...");
    let backtest_config = rust_nonprice::BacktestConfig::default();
    let backtest_result = rust_nonprice::run_backtest(&signals, &stock_indicators, &backtest_config)?;
    println!("   ✅ 回测完成！");
    println!();
    println!("📊 回测结果摘要:");
    println!("   {}", backtest_result.summary());
    println!();

    // 步骤 9: 参数优化（简化版）
    println!("🔧 步骤 9: 参数优化 (100 个组合)...");
    let mut opt_config = rust_nonprice::OptimizationConfig::default();
    opt_config.max_combinations = Some(100);
    let opt_result = rust_nonprice::optimize(&technical_indicators, &stock_indicators, &opt_config)?;
    println!("   ✅ 优化完成！");
    println!("   📈 最优参数:");
    println!("      - Z-Score 买入: {}", opt_result.best_parameters.zscore_buy);
    println!("      - Z-Score 卖出: {}", opt_result.best_parameters.zscore_sell);
    println!("      - 最优 Sharpe 比率: {:.4}", opt_result.best_sharpe);
    println!("      - 总收益率: {:.2}%", opt_result.best_return);
    println!("      - 最大回撤: {:.2}%", opt_result.best_drawdown);
    println!("   ⏱️  执行时间: {} 毫秒", opt_result.execution_time_ms);
    println!();

    // 步骤 10: 生成报告
    println!("📝 步骤 10: 生成报告...");
    let report_path = "demo_backtest_report.md";
    rust_nonprice::generate_markdown_report(&backtest_result, Path::new(report_path))?;
    println!("   ✅ 报告已生成: {}", report_path);
    println!();

    println!("{}", "=".repeat(80));
    println!("🎉 演示完成！系统运行成功！");
    println!("{}", "=".repeat(80));
    println!();
    println!("💡 提示: 可以查看以下文件了解更多详情:");
    println!("   - {}: HIBOR 数据", csv_path);
    println!("   - {}: 股票数据", stock_csv);
    println!("   - {}: 回测报告", report_path);
    println!();

    Ok(())
}

/// 生成模拟 HIBOR 数据
fn generate_hibor_data(count: usize) -> Vec<rust_nonprice::NonPriceIndicator> {
    let mut data = Vec::new();
    let start_date = NaiveDate::from_ymd_opt(2023, 1, 1).unwrap();

    for i in 0..count {
        let date = start_date + chrono::Duration::days(i as i64);
        // 模拟 HIBOR 波动：基础值 2.5%，带随机波动
        let base_value = 2.5;
        let trend = (i as f64 * 0.01).sin() * 0.3; // 趋势
        let noise = (i as f64 * 0.3).sin() * 0.2; // 噪声
        let value = base_value + trend + noise;

        data.push(rust_nonprice::NonPriceIndicator::new(
            "HIBOR_1M".to_string(),
            date,
            value,
            "DEMO".to_string(),
        ));
    }

    data
}

/// 保存 HIBOR 数据到 CSV
fn save_hibor_to_csv(data: &[rust_nonprice::NonPriceIndicator], path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut file = File::create(path)?;
    writeln!(file, "symbol,date,value,source")?;
    for indicator in data {
        writeln!(file, "{},{},{:.4},{}", indicator.symbol, indicator.date, indicator.value, indicator.source)?;
    }
    Ok(())
}

/// 生成模拟股票数据
fn generate_stock_data(count: usize) -> Vec<rust_nonprice::OHLCV> {
    let mut data = Vec::new();
    let start_date = NaiveDate::from_ymd_opt(2023, 1, 1).unwrap();
    let mut price = 100.0;

    for i in 0..count {
        let date = start_date + chrono::Duration::days(i as i64);
        // 模拟股价波动 - 使用确定性模式替代随机数
        let noise = ((i * 17) as f64 % 100) / 100.0 - 0.5; // 伪随机
        let change = (i as f64 * 0.05).sin() * 2.0 + noise * 1.0;
        price = (price + change).max(50.0); // 最低 50 元

        let open_noise = ((i * 23) as f64 % 100) / 100.0 - 0.5;
        let high_noise = ((i * 29) as f64 % 100) / 100.0;
        let low_noise = ((i * 31) as f64 % 100) / 100.0;
        let volume_base = 1000000 + (i as u64 * 12345) % 500000;

        let open = price + open_noise * 2.0;
        let close = price;
        let high = open.max(close) + high_noise * 2.0;
        let low = open.min(close) - low_noise * 2.0;
        let volume = volume_base;

        data.push(rust_nonprice::OHLCV::new(
            "0700.HK".to_string(),
            date,
            open,
            high,
            low,
            close,
            volume,
        ));
    }

    data
}

/// 保存股票数据到 CSV
fn save_stock_to_csv(data: &[rust_nonprice::OHLCV], path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut file = File::create(path)?;
    writeln!(file, "date,open,high,low,close,volume")?;
    for ohlcv in data {
        writeln!(file, "{},{:.2},{:.2},{:.2},{:.2},{}",
                 ohlcv.date, ohlcv.open, ohlcv.high, ohlcv.low, ohlcv.close, ohlcv.volume)?;
    }
    Ok(())
}
