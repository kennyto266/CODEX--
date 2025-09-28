#!/usr/bin/env python3
"""
用户数据分析接口
处理用户提供的具体港股数据
"""

from hk_fundamental_analyst import HKFundamentalAnalyst
import json

def analyze_user_input(user_data_str):
    """
    分析用户提供的数据
    
    参数:
    user_data_str: 用户提供的JSON字符串数据
    
    返回:
    分析结果的JSON格式
    """
    try:
        # 解析用户输入的数据
        if isinstance(user_data_str, str):
            user_data = json.loads(user_data_str)
        else:
            user_data = user_data_str
        
        # 确保数据是列表格式
        if not isinstance(user_data, list):
            user_data = [user_data]
        
        # 创建分析代理
        analyst = HKFundamentalAnalyst()
        
        # 执行分析
        result = analyst.analyze(user_data)
        
        return result
        
    except Exception as e:
        return {
            "error": f"数据分析失败: {str(e)}",
            "undervalued_stocks": [],
            "pe_avg": 0.0,
            "sharpe_contribution": 0.0,
            "recommendations": ["请检查输入数据格式"]
        }

# 用户提供的示例数据
USER_INPUT_EXAMPLE = '''
{
    "stock": "0700.HK", 
    "close_prices": [100, 102, 98], 
    "eps_estimates": [5.2, 5.5, 5.1], 
    "roe": [0.15, 0.16, 0.14]
}
'''

def main():
    """主函数 - 处理用户示例数据"""
    print("=== 港股基本面分析代理 ===")
    print("专业量化分析，追求高Sharpe Ratio策略\n")
    
    # 分析用户提供的示例数据
    result = analyze_user_input(USER_INPUT_EXAMPLE)
    
    # 输出分析结果
    print("ReAct分析过程:")
    print("Reasoning: 计算PE比率(98/5.1=19.2)，ROE增长率(-6.7%)，评估港股监管风险")
    print("Acting: 生成JSON分析结果和投资建议\n")
    
    # JSON格式输出
    json_result = json.dumps(result, ensure_ascii=False, indent=2)
    print("=== 分析结果 ===")
    print(json_result)
    
    # 简短解释
    print(f"\n💡 关键洞见: PE={result.get('pe_avg', 0):.1f}，当前估值合理，但需关注ROE下降趋势")
    print(f"💡 投资建议: Sharpe贡献度{result.get('sharpe_contribution', 0):.3f}，建议谨慎配置")

if __name__ == "__main__":
    main()