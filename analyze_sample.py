#!/usr/bin/env python3
"""
港股基本面分析示例
使用用户提供的数据格式进行分析
"""

from hk_fundamental_analyst import HKFundamentalAnalyst
import json

def analyze_user_data():
    """分析用户提供的示例数据"""
    
    # 用户提供的数据格式示例
    input_data = [
        {
            "stock": "0700.HK",  # 腾讯控股
            "close_prices": [100, 102, 98, 105, 103],
            "eps_estimates": [5.2, 5.5, 5.1, 5.8, 5.6],
            "roe": [0.15, 0.16, 0.14, 0.17, 0.16],
            "debt_equity_ratio": 0.28
        },
        {
            "stock": "0005.HK",  # 汇丰控股
            "close_prices": [42, 44, 41, 43, 42.5],
            "eps_estimates": [2.8, 3.1, 2.9, 3.2, 3.0],
            "roe": [0.08, 0.09, 0.07, 0.10, 0.09],
            "debt_equity_ratio": 0.12
        },
        {
            "stock": "1398.HK",  # 工商银行
            "close_prices": [4.2, 4.3, 4.1, 4.4, 4.25],
            "eps_estimates": [0.45, 0.48, 0.46, 0.50, 0.47],
            "roe": [0.11, 0.12, 0.10, 0.13, 0.12],
            "debt_equity_ratio": 0.08
        },
        {
            "stock": "2318.HK",  # 中国平安
            "close_prices": [58, 61, 56, 62, 59],
            "eps_estimates": [8.5, 8.8, 8.2, 9.1, 8.7],
            "roe": [0.18, 0.19, 0.17, 0.20, 0.18],
            "debt_equity_ratio": 0.35
        }
    ]
    
    print("=== 港股基本面分析代理 ===")
    print("目标: 追求高Sharpe Ratio (>1.5) 的交易策略")
    print("专注: 恒生指数成分股分析\n")
    
    # 创建分析代理
    analyst = HKFundamentalAnalyst()
    
    print("Reasoning (推理过程):")
    print("1. 计算关键基本面指标 (PE, ROE, 盈利成长率)")
    print("2. 识别低估股票 (PE < 行业中位数的70%)")
    print("3. 评估风险调整后收益潜力")
    print("4. 考虑港股特殊因素 (中美关系、汇率、监管)\n")
    
    # 执行分析
    print("Acting (执行分析):")
    result = analyst.analyze(input_data)
    
    # 输出JSON结果
    print("=== 分析结果 (JSON格式) ===")
    json_output = json.dumps(result, ensure_ascii=False, indent=2)
    print(json_output)
    
    # 关键洞见
    print("\n=== 关键洞见 ===")
    if result["undervalued_stocks"]:
        best_stock = min(result["undervalued_stocks"], key=lambda x: x["pe_ratio"])
        print(f"💡 最佳投资标的: {best_stock['symbol']} (PE: {best_stock['pe_ratio']})")
    else:
        print("💡 当前市场估值偏高，建议保持谨慎态度")
    
    print(f"💡 市场整体PE水平: {result['pe_avg']}，Sharpe贡献度: {result['sharpe_contribution']}")
    
    return result

if __name__ == "__main__":
    analyze_user_data()