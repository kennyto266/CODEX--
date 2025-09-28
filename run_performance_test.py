#!/usr/bin/env python3
"""
快速性能测试启动脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    """运行性能测试"""
    try:
        from performance_test import PerformanceTester
        
        print("🚀 启动港股量化交易AI Agent系统性能测试...")
        print("=" * 60)
        
        tester = PerformanceTester()
        results = await tester.run_all_tests()
        
        print("\n📊 性能测试结果:")
        print("=" * 60)
        
        # 显示关键指标
        for test_name, result in results.get('test_results', {}).items():
            print(f"\n🔍 {test_name.replace('_', ' ').title()}:")
            
            if 'error' in result:
                print(f"   ❌ 错误: {result['error']}")
            elif 'skipped' in result:
                print(f"   ⏭️ 跳过: {result['skipped']}")
            else:
                print("   ✅ 测试通过")
                
                # 显示关键性能指标
                if test_name == 'technical_indicators':
                    avg_times = [r.get('avg_time', 0) for r in result.values() 
                               if isinstance(r, dict) and 'avg_time' in r]
                    if avg_times:
                        print(f"   📈 平均计算时间: {min(avg_times):.4f}s")
                
                elif test_name == 'data_fetching':
                    if 'multi_symbol' in result:
                        total_time = result['multi_symbol']['total_time']
                        symbols = result['multi_symbol']['symbols_count']
                        print(f"   📊 多标的数据获取: {total_time:.2f}s ({symbols}个标的)")
                
                elif test_name == 'websocket_performance':
                    if 'broadcast_performance' in result:
                        bp = result['broadcast_performance']
                        print(f"   🌐 WebSocket广播: {bp['avg_time']:.4f}s ({bp['connections']}连接)")
        
        print(f"\n⏱️ 总测试时间: {results.get('total_test_time', 0):.2f}秒")
        print("\n✅ 性能测试完成！详细报告已保存到 performance_test_report.md")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖包已安装：pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())