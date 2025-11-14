#!/usr/bin/env python3
"""
FRED API密钥测试脚本
用于验证FRED API密钥是否正常工作并获取宏观经济数据

运行前请先设置环境变量:
export FRED_API_KEY="your_api_key_here"

然后运行:
python test_fred_api.py
"""

import os
import sys
import requests
import json
from datetime import datetime

# 检查API密钥
FRED_API_KEY = os.environ.get('FRED_API_KEY')
if not FRED_API_KEY:
    print("❌ 错误: 未找到FRED_API_KEY环境变量")
    print("\n请先设置API密钥:")
    print("export FRED_API_KEY='your_api_key_here'")
    sys.exit(1)

print("=" * 70)
print("FRED API 密钥测试")
print("=" * 70)
print(f"API密钥: {FRED_API_KEY[:10]}...{FRED_API_KEY[-10:]}")
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# FRED API基础配置
BASE_URL = "https://api.stlouisfed.org/fred"

# 要测试的核心经济指标
TEST_SERIES = {
    'GDPC1': {
        'name': '实际GDP (季度)',
        'description': 'Real Gross Domestic Product',
        'category': 'GDP数据'
    },
    'CPIAUCSL': {
        'name': '消费者价格指数',
        'description': 'Consumer Price Index for All Urban Consumers',
        'category': '通胀数据'
    },
    'UNRATE': {
        'name': '失业率',
        'description': 'Unemployment Rate',
        'category': '就业数据'
    },
    'FEDFUNDS': {
        'name': '联邦基金利率',
        'description': 'Federal Funds Rate',
        'category': '利率数据'
    },
    'PAYEMS': {
        'name': '非农就业',
        'description': 'All Employees: Total Nonfarm',
        'category': '就业数据'
    },
    'INDPRO': {
        'name': '工业生产指数',
        'description': 'Industrial Production Index',
        'category': '工业数据'
    }
}

def get_series_data(series_id, series_info):
    """获取指定系列的最新数据"""
    url = f"{BASE_URL}/series/observations"
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': 1,
        'sort_order': 'desc'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'observations' in data and data['observations']:
            latest = data['observations'][0]
            return {
                'status': 'success',
                'series_id': series_id,
                'name': series_info['name'],
                'description': series_info['description'],
                'category': series_info['category'],
                'date': latest['date'],
                'value': latest['value'],
                'message': '数据获取成功'
            }
        else:
            return {
                'status': 'error',
                'series_id': series_id,
                'name': series_info['name'],
                'message': 'API返回空数据'
            }

    except requests.exceptions.Timeout:
        return {
            'status': 'error',
            'series_id': series_id,
            'name': series_info['name'],
            'message': '请求超时 (10秒)'
        }
    except requests.exceptions.HTTPError as e:
        return {
            'status': 'error',
            'series_id': series_id,
            'name': series_info['name'],
            'message': f'HTTP错误: {response.status_code}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'series_id': series_id,
            'name': series_info['name'],
            'message': f'未知错误: {str(e)[:50]}'
        }

def main():
    """主测试函数"""
    results = []
    success_count = 0
    error_count = 0

    print("开始测试FRED API...")
    print(f"将测试 {len(TEST_SERIES)} 个核心经济指标\n")

    # 逐个测试每个指标
    for i, (series_id, series_info) in enumerate(TEST_SERIES.items(), 1):
        print(f"[{i}/{len(TEST_SERIES)}] 测试 {series_info['name']} ({series_id})")
        print("-" * 70)

        result = get_series_data(series_id, series_info)
        results.append(result)

        if result['status'] == 'success':
            success_count += 1
            print(f"✅ 成功!")
            print(f"   指标: {result['name']}")
            print(f"   类别: {result['category']}")
            print(f"   最新日期: {result['date']}")
            print(f"   最新值: {result['value']}")
        else:
            error_count += 1
            print(f"❌ 失败: {result['message']}")

        print()

    # 输出总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总测试指标: {len(TEST_SERIES)}")
    print(f"成功: {success_count} ✅")
    print(f"失败: {error_count} ❌")
    print(f"成功率: {(success_count/len(TEST_SERIES)*100):.1f}%")
    print()

    if success_count > 0:
        print("✅ FRED API密钥工作正常!")
        print(f"已成功获取 {success_count} 个宏观经济指标")
        print()

        # 按类别分组显示成功的数据
        categories = {}
        for result in results:
            if result['status'] == 'success':
                cat = result['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(result)

        print("成功获取的指标类别:")
        for category, items in categories.items():
            print(f"\n  📊 {category}:")
            for item in items:
                print(f"    • {item['name']} ({item['series_id']}): {item['value']}")

        print("\n" + "=" * 70)
        print("覆盖率提升分析")
        print("=" * 70)
        print(f"新增真实数据点: +{success_count} 个")
        print(f"覆盖率提升: +{(success_count/162*100):.2f}%")
        print(f"从22.2% → {(22.2 + success_count/162*100):.1f}%")
        print()
        print("🎯 继续申请其他API密钥 (IEX Cloud, Finnhub)")
        print("   预计总覆盖率可达: 30%+")

    else:
        print("❌ FRED API密钥测试失败")
        print("请检查:")
        print("  1. API密钥是否正确")
        print("  2. 网络连接是否正常")
        print("  3. 是否超过请求频率限制")

    print("\n" + "=" * 70)

    # 保存测试结果到文件
    with open('fred_api_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'api_key_prefix': f"{FRED_API_KEY[:10]}...{FRED_API_KEY[-10:]}",
            'total_tests': len(TEST_SERIES),
            'success_count': success_count,
            'error_count': error_count,
            'success_rate': success_count/len(TEST_SERIES)*100,
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"测试结果已保存到: fred_api_test_results.json")

if __name__ == "__main__":
    main()
