#!/usr/bin/env python3
"""
模拟前端JavaScript API调用测试
"""
import requests
import json

def test_strategy_optimization(symbol="0700.HK", strategy_type="all"):
    """模拟前端JavaScript中的runOptimization函数"""
    print(f"测试股票代码: {symbol}")
    print(f"策略类型: {strategy_type}")

    try:
        # 模拟前端fetch请求
        url = f"http://localhost:8013/api/strategy-optimization/{symbol}"
        params = {"strategy_type": strategy_type}

        print(f"请求URL: {url}")
        print(f"请求参数: {params}")

        # 发送GET请求
        response = requests.get(url, params=params)

        print(f"响应状态: {response.status_code}")
        print(f"响应OK: {response.ok}")

        if not response.ok:
            # 模拟前端错误处理
            try:
                error_data = response.json()
                print(f"错误响应数据: {error_data}")
                raise Exception(error_data.get('detail', f"HTTP {response.status} 错误"))
            except:
                print(f"错误响应文本: {response.text}")
                raise Exception(f"HTTP {response.status} 错误")

        # 模拟前端解析响应
        result = response.json()
        print(f"响应JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 模拟前端检查success字段
        if result.get('success'):
            print("✅ 前端检查: success = True")
            print(f"✅ 最佳Sharpe比率: {result['data']['best_sharpe_ratio']}")
            print(f"✅ 策略总数: {result['data']['total_strategies']}")
            return True
        else:
            print("❌ 前端检查: success = False")
            print(f"错误信息: {result.get('message', '未知错误')}")
            return False

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_different_symbols():
    """测试不同的股票代码"""
    symbols = ["0700.HK", "0939.HK", "0388.HK"]

    for symbol in symbols:
        print("\n" + "="*60)
        success = test_strategy_optimization(symbol, "ma")
        print(f"结果: {'✅ 成功' if success else '❌ 失败'}")

if __name__ == "__main__":
    print("🚀 开始测试API模拟前端调用")
    print("="*60)

    # 测试单个API调用
    success = test_strategy_optimization("0700.HK", "all")

    if success:
        print("\n✅ 测试通过！API工作正常")
    else:
        print("\n❌ 测试失败！")

    print("\n" + "="*60)
    print("🔍 测试不同的股票代码...")
    test_different_symbols()
