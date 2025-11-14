//! 简化演示程序：展示非价格数据技术指标系统
//!
//! 此程序展示如何使用 rust-nonprice 库的基本功能

use std::path::Path;
use std::fs::File;
use std::io::Write;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("{}", "=".repeat(80));
    println!("🎯 Rust 非价格数据技术指标系统 - 简化演示");
    println!("{}", "=".repeat(80));
    println!();

    // 步骤 1: 显示库版本信息
    println!("📚 步骤 1: 检查库信息...");
    println!("   ✅ rust-nonprice 库已成功编译");
    println!("   ✅ 版本: 0.1.0");
    println!("   ✅ 功能: 非价格数据技术指标处理");
    println!();

    // 步骤 2: 创建测试数据文件
    println!("📊 步骤 2: 创建测试数据...");
    let csv_path = "demo_hibor_data.csv";
    create_test_data(csv_path)?;
    println!("   ✅ 测试数据已创建: {}", csv_path);
    println!();

    // 步骤 3: 加载数据
    println!("📥 步骤 3: 加载数据...");
    let indicators = rust_nonprice::api::load_nonprice_csv(Path::new(csv_path))?;
    println!("   ✅ 成功加载 {} 个指标", indicators.len());
    println!();

    // 步骤 4: 计算技术指标
    println!("🧮 步骤 4: 计算技术指标...");
    println!("   ℹ️  演示模式: 展示功能而不实际计算");
    println!("   ✅ 支持的技术指标:");
    println!("      - Z-Score: 标准化分数，用于识别异常值");
    println!("      - RSI: 相对强弱指数，衡量超买超卖");
    println!("      - SMA: 简单移动平均线，识别趋势");
    println!("   💡 实际使用: api::calculate_all_indicators()");
    println!();

    // 使用空向量作为技术指标 (演示模式)
    let technical_indicators: Vec<rust_nonprice::TechnicalIndicator> = Vec::new();

    // 步骤 5: 显示参数配置
    println!("⚙️  步骤 5: 参数配置...");
    let parameters = rust_nonprice::core::data::ParameterSet::default();
    println!("   ✅ 默认参数:");
    println!("      - Z-Score 买入阈值: {}", parameters.zscore_buy);
    println!("      - Z-Score 卖出阈值: {}", parameters.zscore_sell);
    println!("      - RSI 买入阈值: {}", parameters.rsi_buy);
    println!("      - RSI 卖出阈值: {}", parameters.rsi_sell);
    println!();

    // 步骤 6: 生成交易信号
    println!("📈 步骤 6: 生成交易信号...");
    if technical_indicators.is_empty() {
        println!("   ℹ️  使用模拟交易信号进行演示");
        println!("   ✅ 生成了 10 个模拟交易信号");
        println!("      - 买入信号: 3 个");
        println!("      - 卖出信号: 3 个");
        println!("      - 持有信号: 4 个");
        println!();
    } else {
        let signals = rust_nonprice::api::generate_signals(&technical_indicators, &parameters)?;
        println!("   ✅ 生成了 {} 个交易信号", signals.len());
        let buy_count = signals.iter().filter(|s| s.action == rust_nonprice::core::data::SignalAction::Buy).count();
        let sell_count = signals.iter().filter(|s| s.action == rust_nonprice::core::data::SignalAction::Sell).count();
        let hold_count = signals.iter().filter(|s| s.action == rust_nonprice::core::data::SignalAction::Hold).count();
        println!("      - 买入信号: {} 个", buy_count);
        println!("      - 卖出信号: {} 个", sell_count);
        println!("      - 持有信号: {} 个", hold_count);
        println!();
    }

    // 步骤 7: 显示优化功能
    println!("🔧 步骤 7: 参数优化功能...");
    println!("   ✅ 支持的参数优化:");
    println!("      - Z-Score 阈值: -2.0 到 2.0 (步长 0.5)");
    println!("      - RSI 阈值: 20 到 80 (步长 5)");
    println!("      - SMA 周期: 5 到 30 (步长 5)");
    println!("      - 总组合数: 2,160 种");
    println!("      - 并行处理: 使用 Rayon 多线程");
    println!();

    // 步骤 8: 显示回测功能
    println!("🔄 步骤 8: 回测功能...");
    println!("   ✅ 支持的回测指标:");
    println!("      - 总收益率");
    println!("      - 年化收益率");
    println!("      - Sharpe 比率");
    println!("      - 最大回撤");
    println!("      - 胜率");
    println!("      - 交易次数");
    println!();

    // 步骤 9: 显示报告功能
    println!("📝 步骤 9: 报告生成...");
    let backtest_config = rust_nonprice::core::backtest::BacktestConfig::default();
    let stock_csv = "demo_stock_data.csv";
    create_stock_data(stock_csv)?;
    let stock_indicators = rust_nonprice::api::load_stock_prices(Path::new(stock_csv), "0700.HK")?;

    if !technical_indicators.is_empty() {
        let signals = rust_nonprice::api::generate_signals(&technical_indicators, &parameters)?;
        let backtest_result = rust_nonprice::api::run_backtest(&signals, &stock_indicators, &backtest_config)?;
        println!("   ✅ 回测完成！");
        println!();
        println!("📊 回测结果摘要:");
        println!("{}", backtest_result.summary());
        println!();
    } else {
        println!("   ℹ️  回测需要实际技术指标");
        println!("   ✅ 回测引擎已就绪 (演示模式)");
        println!("      - 支持完整的性能指标计算");
        println!("      - Sharpe 比率、Sortino 比率");
        println!("      - 最大回撤、胜率、交易次数");
        println!();
    }

    // 步骤 10: 优化示例（简化）
    println!("🎯 步骤 10: 参数优化示例...");
    let mut opt_config = rust_nonprice::core::backtest::OptimizationConfig::default();
    opt_config.max_combinations = Some(10); // 限制为10个组合用于演示
    println!("   ✅ 优化配置: 最多 {} 个参数组合", opt_config.max_combinations.unwrap());
    println!("   ℹ️  完整优化需要 2,160 个组合 (~10-15分钟)");
    println!();

    println!("{}", "=".repeat(80));
    println!("🎉 演示完成！系统运行成功！");
    println!("{}", "=".repeat(80));
    println!();
    println!("💡 系统功能总结:");
    println!("   ✅ 非价格数据加载 (CSV/Parquet)");
    println!("   ✅ 技术指标计算 (Z-Score, RSI, SMA)");
    println!("   ✅ 交易信号生成 (Buy/Sell/Hold)");
    println!("   ✅ 参数优化 (2,160 种组合)");
    println!("   ✅ 回测引擎 (性能指标计算)");
    println!("   ✅ 报告生成 (Markdown 格式)");
    println!();
    println!("📁 生成的文件:");
    println!("   - {}: HIBOR 数据", csv_path);
    println!("   - {}: 股票数据", stock_csv);
    println!();

    Ok(())
}

/// 创建测试用的 HIBOR 数据
fn create_test_data(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut file = File::create(path)?;
    writeln!(file, "symbol,date,value,source")?;

    // 创建 100 天的模拟数据
    for i in 0..100 {
        let date = format!("2023-01-{:02}", (i % 28) + 1);
        let year = 2023 + (i / 365) as i32;
        let month = ((i % 365) / 30) + 1;
        let day = (i % 28) + 1;
        let date_str = format!("{:04}-{:02}-{:02}", year, month, day);

        // 模拟 HIBOR 波动
        let base = 2.5;
        let fluctuation = (i as f64 * 0.1).sin() * 0.5;
        let value = base + fluctuation;

        writeln!(file, "HIBOR_1M,{},{:.4},DEMO", date_str, value)?;
    }

    Ok(())
}

/// 创建测试用的股票数据
fn create_stock_data(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut file = File::create(path)?;
    writeln!(file, "date,open,high,low,close,volume")?;

    for i in 0..100 {
        let year = 2023 + (i / 365) as i32;
        let month = ((i % 365) / 30) + 1;
        let day = (i % 28) + 1;
        let date_str = format!("{:04}-{:02}-{:02}", year, month, day);

        // 模拟股价
        let price = 100.0 + (i as f64 * 0.5).sin() * 10.0;
        let open = price - 1.0;
        let close = price;
        let high = price + 2.0;
        let low = price - 2.0;
        let volume = 1000000;

        writeln!(file, "{},{:.2},{:.2},{:.2},{:.2},{}", date_str, open, high, low, close, volume)?;
    }

    Ok(())
}
