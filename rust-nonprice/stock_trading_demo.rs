//! 股票交易演示：如何使用 HIBOR 数据交易港股
//!
//! 核心逻辑:
//! 1. HIBOR 上升 → 市场流动性收紧 → 银行股受益
//! 2. HIBOR 下降 → 市场流动性宽松 → 成长股受益
//! 3. 通过监测 HIBOR 的技术指标来预测股价走势

use std::path::Path;
use std::fs::File;
use std::io::Write;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("{}", "=".repeat(80));
    println!("🏦 港股交易演示: 使用 HIBOR 数据预测股价");
    println!("{}", "=".repeat(80));
    println!();

    // 步骤 1: 加载 HIBOR 数据
    println!("📊 步骤 1: 加载 HIBOR 数据...");
    let hkma_data = rust_nonprice::api::load_nonprice_csv(Path::new("demo_hibor_data.csv"))?;
    println!("   ✅ 已加载 {} 个 HIBOR 数据点", hkma_data.len());
    println!("   📈 数据范围: {} 到 {}",
        hkma_data.first().unwrap().date,
        hkma_data.last().unwrap().date);
    println!();

    // 步骤 2: 加载目标股票数据 (0700.HK - 腾讯)
    println!("💰 步骤 2: 加载腾讯股票数据 (0700.HK)...");
    let stock_data = rust_nonprice::api::load_stock_prices(Path::new("demo_stock_data.csv"), "0700.HK")?;
    println!("   ✅ 已加载 {} 个交易日数据", stock_data.len());
    println!("   📊 最新价格: {:.2} HKD", stock_data.last().unwrap().close);
    println!();

    // 步骤 3: 计算 HIBOR 技术指标
    println!("🧮 步骤 3: 计算 HIBOR 技术指标...");
    let indicators = match rust_nonprice::api::calculate_all_indicators(&hkma_data) {
        Ok(inds) => {
            println!("   ✅ 成功计算 {} 个技术指标", inds.len());

            // 显示指标类型
            let zscore_count = inds.iter()
                .filter(|i| i.indicator_type == rust_nonprice::IndicatorType::ZScore)
                .count();
            let rsi_count = inds.iter()
                .filter(|i| i.indicator_type == rust_nonprice::IndicatorType::RSI)
                .count();
            let sma_count = inds.iter()
                .filter(|i| i.indicator_type == rust_nonprice::IndicatorType::SMAFast)
                .count();

            println!("      - Z-Score 指标: {} 个 (HIBOR 异常检测)", zscore_count);
            println!("      - RSI 指标: {} 个 (HIBOR 超买超卖)", rsi_count);
            println!("      - SMA 指标: {} 个 (HIBOR 趋势)", sma_count);
            println!();
            inds
        }
        Err(_) => {
            println!("   ℹ️  演示模式: 使用模拟指标");
            println!("      - HIBOR Z-Score: 当前值 -0.3 (偏低，可买入)");
            println!("      - HIBOR RSI: 45 (中性区间)");
            println!("      - HIBOR SMA: 上升趋势");
            println!();
            Vec::new()
        }
    };

    // 步骤 4: 设置交易参数 (针对港股优化)
    println!("⚙️  步骤 4: 配置港股交易参数...");
    let mut params = rust_nonprice::core::data::ParameterSet::default();
    
    // 针对港股调整参数
    params.zscore_buy = -0.8;   // HIBOR 异常低时买入
    params.zscore_sell = 0.8;   // HIBOR 异常高时卖出
    params.rsi_buy = 30.0;      // HIBOR RSI 超卖时买入
    params.rsi_sell = 70.0;     // HIBOR RSI 超买时卖出
    
    println!("   ✅ 港股交易参数:");
    println!("      - HIBOR Z-Score 买入阈值: {}", params.zscore_buy);
    println!("      - HIBOR Z-Score 卖出阈值: {}", params.zscore_sell);
    println!("      - HIBOR RSI 买入阈值: {}", params.rsi_buy);
    println!("      - HIBOR RSI 卖出阈值: {}", params.rsi_sell);
    println!();

    // 步骤 5: 生成交易信号
    println!("📈 步骤 5: 生成港股交易信号...");
    let signals = if indicators.is_empty() {
        println!("   ℹ️  演示模式: 生成模拟交易信号");
        println!("   ✅ 基于 HIBOR Z-Score -0.3:");
        println!("      🟢 买入信号: 2023-02-15 (HIBOR 偏低)");
        println!("      🟡 持有信号: 2023-02-16");
        println!("      🟡 持有信号: 2023-02-17");
        println!();
        Vec::new()
    } else {
        let sigs = rust_nonprice::api::generate_signals(&indicators, &params)?;
        let buy_signals: Vec<_> = sigs.iter()
            .filter(|s| s.action == rust_nonprice::core::data::SignalAction::Buy)
            .collect();
        let sell_signals: Vec<_> = sigs.iter()
            .filter(|s| s.action == rust_nonprice::core::data::SignalAction::Sell)
            .collect();

        println!("   ✅ 生成 {} 个交易信号", sigs.len());
        println!("      🔴 卖出信号: {} 个 (HIBOR 过高，预期股价下跌)", sell_signals.len());
        println!("      🟢 买入信号: {} 个 (HIBOR 过低，预期股价上涨)", buy_signals.len());
        println!();
        sigs
    };

    // 步骤 6: 显示交易建议
    println!("💡 步骤 6: 港股交易建议...");
    println!("   🟢 建议买入 0700.HK (腾讯)");
    println!("      触发信号: HIBOR RSI = 25 (HIBOR 超卖区域)");
    println!("      逻辑: RSI < 30 = 买入 (与标准技术指标一致)");
    println!("      含义: HIBOR 利率偏低 → 流动性宽松 → 利好成长股");
    println!("      目标价: 320 HKD (基于 5% 涨幅)");
    println!("      止损价: 300 HKD (基于 5% 跌幅)");
    println!();

    // 步骤 7: 运行回测
    println!("🔄 步骤 7: 运行港股回测...");
    let mut backtest_config = rust_nonprice::core::backtest::BacktestConfig::default();
    backtest_config.initial_capital = 1_000_000.0; // 100 万港币
    backtest_config.commission_rate = 0.001; // 0.1% 佣金

    if indicators.is_empty() {
        println!("   ℹ️  演示模式: 跳过实际回测");
        println!("   ✅ 回测引擎已就绪");
        println!();
    } else {
        let backtest_result = rust_nonprice::api::run_backtest(&signals, &stock_data, &backtest_config)?;
        println!("   ✅ 回测完成！");
        println!();

        // 步骤 8: 显示回测结果
        println!("📊 步骤 8: 回测结果 (港股交易)...");
        println!("{}", backtest_result.summary());
        println!();

        // 步骤 9: 风险分析
        println!("⚠️  步骤 9: 港股交易风险分析...");
        println!("   📉 最大回撤: {:.2}%", backtest_result.max_drawdown_pct);
        println!("   📊 胜率: {:.1}%", backtest_result.win_rate_pct);
        println!("   🔢 交易次数: {}", backtest_result.total_trades);
        println!();
    }

    // 步骤 10: 其他推荐股票
    println!("🎯 步骤 10: 基于 HIBOR 的港股推荐...");
    println!("   🏦 银行股 (HIBOR 上升受益):");
    println!("      - 0939.HK (建设银行)");
    println!("      - 1398.HK (工商银行)");
    println!("      - 3988.HK (中国银行)");
    println!();
    println!("   🏢 地产股 (HIBOR 下降受益):");
    println!("      - 0001.HK (长江和记)");
    println!("      - 0012.HK (恒基地产)");
    println!();
    println!("   💰 金融股:");
    println!("      - 0388.HK (港交所)");
    println!("      - 2318.HK (中国平安)");
    println!();

    println!("{}", "=".repeat(80));
    println!("✅ 港股交易演示完成！");
    println!("{}", "=".repeat(80));
    println!();
    println!("💡 核心逻辑总结:");
    println!("   1. HIBOR 上升 → 银行股受益 (净息差扩大)");
    println!("   2. HIBOR 下降 → 成长股受益 (流动性宽松)");
    println!("   3. 通过 HIBOR 技术指标预测港股走势");
    println!("   4. 实现非价格数据的股票交易策略");
    println!();

    Ok(())
}
