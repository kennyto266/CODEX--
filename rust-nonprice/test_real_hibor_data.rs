//! 测试真实 HIBOR 数据加载
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("\n{}", "=".repeat(80));
    println!("📊 测试真实 HIBOR 数据加载");
    println!("{}", "=".repeat(80));
    
    // 加载真实 HIBOR 数据
    println!("\n1. 加载真实 HIBOR 数据...");
    let hkma_data = rust_nonprice::api::load_nonprice_csv(Path::new("../real_hibor_data.csv"))?;
    println!("   ✅ 成功加载 {} 个数据点", hkma_data.len());
    
    // 显示数据范围
    println!("\n2. 数据范围:");
    println!("   起始: {}", hkma_data.first().unwrap().date);
    println!("   结束: {}", hkma_data.last().unwrap().date);
    
    // 统计各期限数据
    let tenors = ["HIBOR_Overnight", "HIBOR_1M", "HIBOR_3M", "HIBOR_6M", "HIBOR_12M"];
    println!("\n3. 各期限数据统计:");
    for tenor in &tenors {
        let count = hkma_data.iter().filter(|d| d.symbol == *tenor).count();
        println!("   {}: {} 个数据点", tenor, count);
    }
    
    // 计算技术指标
    println!("\n4. 计算技术指标...");
    let indicators = rust_nonprice::api::calculate_all_indicators(&hkma_data)?;
    println!("   ✅ 计算完成，共 {} 个指标", indicators.len());
    
    // 显示最新 HIBOR 隔夜利率
    let overnight_latest = hkma_data.iter()
        .filter(|d| d.symbol == "HIBOR_Overnight")
        .last()
        .unwrap();
    println!("\n5. 最新 HIBOR 隔夜利率:");
    println!("   日期: {}", overnight_latest.date);
    println!("   利率: {:.4f}%", overnight_latest.value);
    
    // 显示 HIBOR RSI 交易信号
    println!("\n6. HIBOR RSI 交易信号:");
    println!("   根据技术指标分析:");
    println!("   - HIBOR RSI < 30: 买入信号 (利率低，流动性宽松)");
    println!("   - HIBOR RSI > 70: 卖出信号 (利率高，流动性收紧)");
    
    println!("\n{}", "=".repeat(80));
    println!("✅ 真实 HIBOR 数据测试完成！");
    println!("{}", "=".repeat(80));
    
    Ok(())
}
