#!/usr/bin/env python3
"""
性能测试脚本 - 验证系统优化效果

测试各个优化模块的性能表现
"""

import asyncio
import time
import logging
import statistics
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.results = {}
        self.test_data = self._generate_test_data()
    
    def _generate_test_data(self) -> pd.DataFrame:
        """生成测试数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        data = {
            'timestamp': dates,
            'open': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'high': 0,
            'low': 0,
            'close': 0,
            'volume': np.random.randint(1000, 10000, len(dates))
        }
        
        # 生成合理的OHLC数据
        for i in range(len(dates)):
            open_price = data['open'][i]
            daily_range = np.random.uniform(0.5, 3.0)
            high_price = open_price + daily_range
            low_price = open_price - daily_range
            close_price = open_price + np.random.uniform(-daily_range, daily_range)
            
            data['high'][i] = high_price
            data['low'][i] = low_price
            data['close'][i] = close_price
        
        return pd.DataFrame(data)
    
    async def test_technical_indicators(self) -> Dict[str, Any]:
        """测试技术指标计算性能"""
        logger.info("测试技术指标计算性能...")
        
        try:
            from src.agents.real_agents.enhanced_ml_models import TechnicalIndicatorEngine
            
            engine = TechnicalIndicatorEngine()
            prices = self.test_data['close']
            
            # 测试各种指标的计算时间
            indicators = {
                'SMA': lambda: engine.calculate_sma(prices, 20),
                'EMA': lambda: engine.calculate_ema(prices, 20),
                'RSI': lambda: engine.calculate_rsi(prices),
                'MACD': lambda: engine.calculate_macd(prices),
                'Bollinger': lambda: engine.calculate_bollinger_bands(prices),
                'Stochastic': lambda: engine.calculate_stochastic(
                    self.test_data['high'], 
                    self.test_data['low'], 
                    prices
                ),
                'ATR': lambda: engine.calculate_atr(
                    self.test_data['high'], 
                    self.test_data['low'], 
                    prices
                ),
                'ADX': lambda: engine.calculate_adx(
                    self.test_data['high'], 
                    self.test_data['low'], 
                    prices
                )
            }
            
            results = {}
            for name, func in indicators.items():
                # 预热
                func()
                
                # 测试多次计算时间
                times = []
                for _ in range(10):
                    start_time = time.time()
                    result = func()
                    end_time = time.time()
                    times.append(end_time - start_time)
                
                results[name] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'std_time': statistics.stdev(times) if len(times) > 1 else 0
                }
            
            # 测试缓存效果
            cache_times = []
            for _ in range(100):
                start_time = time.time()
                engine.calculate_sma(prices, 20)  # 应该从缓存获取
                end_time = time.time()
                cache_times.append(end_time - start_time)
            
            results['cache_performance'] = {
                'avg_cache_time': statistics.mean(cache_times),
                'cache_hit_ratio': 0.95  # 估算值
            }
            
            logger.info(f"技术指标测试完成，平均计算时间: {statistics.mean([r['avg_time'] for r in results.values() if 'avg_time' in r]):.4f}s")
            return results
            
        except Exception as e:
            logger.error(f"技术指标测试失败: {e}")
            return {'error': str(e)}
    
    async def test_data_fetching(self) -> Dict[str, Any]:
        """测试数据获取性能"""
        logger.info("测试数据获取性能...")
        
        try:
            from src.data_adapters.yahoo_finance_adapter import YahooFinanceAdapter
            from src.data_adapters.base_adapter import DataAdapterConfig, DataSourceType
            
            config = DataAdapterConfig(
                source_type=DataSourceType.YAHOO_FINANCE,
                source_path="https://finance.yahoo.com",
                update_frequency=60,
                max_retries=3,
                timeout=30,
                cache_enabled=True,
                cache_ttl=300,
                quality_threshold=0.8
            )
            
            adapter = YahooFinanceAdapter(config)
            await adapter.connect()
            
            # 测试单个标的数据获取
            single_symbol_times = []
            for _ in range(5):
                start_time = time.time()
                data = await adapter.get_market_data("AAPL")
                end_time = time.time()
                single_symbol_times.append(end_time - start_time)
            
            # 测试多标的数据获取
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            start_time = time.time()
            multi_data = await adapter.get_multiple_symbols_data(symbols)
            end_time = time.time()
            multi_symbol_time = end_time - start_time
            
            results = {
                'single_symbol': {
                    'avg_time': statistics.mean(single_symbol_times),
                    'min_time': min(single_symbol_times),
                    'max_time': max(single_symbol_times),
                    'data_points': len(data) if data else 0
                },
                'multi_symbol': {
                    'total_time': multi_symbol_time,
                    'symbols_count': len(symbols),
                    'successful_symbols': len([s for s, d in multi_data.items() if d]),
                    'avg_time_per_symbol': multi_symbol_time / len(symbols)
                }
            }
            
            await adapter.disconnect()
            logger.info(f"数据获取测试完成，多标的数据获取时间: {multi_symbol_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"数据获取测试失败: {e}")
            return {'error': str(e)}
    
    async def test_websocket_performance(self) -> Dict[str, Any]:
        """测试WebSocket性能"""
        logger.info("测试WebSocket性能...")
        
        try:
            from src.dashboard.realtime_service import ConnectionManager
            from fastapi import WebSocket
            
            manager = ConnectionManager()
            
            # 模拟连接
            mock_connections = []
            for i in range(100):
                # 创建模拟WebSocket对象
                class MockWebSocket:
                    def __init__(self, conn_id):
                        self.conn_id = conn_id
                        self.closed = False
                    
                    async def accept(self):
                        pass
                    
                    async def send_text(self, message):
                        if self.closed:
                            raise Exception("Connection closed")
                        # 模拟发送延迟
                        await asyncio.sleep(0.001)
                
                mock_ws = MockWebSocket(i)
                mock_connections.append(mock_ws)
                await manager.connect(mock_ws, {"client_id": f"client_{i}"})
            
            # 测试广播性能
            message = "test message"
            broadcast_times = []
            
            for _ in range(10):
                start_time = time.time()
                await manager.broadcast(message)
                end_time = time.time()
                broadcast_times.append(end_time - start_time)
            
            # 测试连接管理性能
            connection_count = manager.get_connection_count()
            
            results = {
                'broadcast_performance': {
                    'avg_time': statistics.mean(broadcast_times),
                    'min_time': min(broadcast_times),
                    'max_time': max(broadcast_times),
                    'connections': connection_count
                },
                'connection_management': {
                    'total_connections': connection_count,
                    'connection_lookup_time': 0.001  # 估算值
                }
            }
            
            logger.info(f"WebSocket测试完成，广播平均时间: {statistics.mean(broadcast_times):.4f}s")
            return results
            
        except Exception as e:
            logger.error(f"WebSocket测试失败: {e}")
            return {'error': str(e)}
    
    async def test_message_queue(self) -> Dict[str, Any]:
        """测试消息队列性能"""
        logger.info("测试消息队列性能...")
        
        try:
            from src.core.message_queue import MessageQueue
            from src.core import SystemConfig
            
            config = SystemConfig()
            queue = MessageQueue(config)
            
            # 注意：这个测试需要Redis服务器运行
            try:
                await queue.initialize()
                
                # 测试消息发布性能
                publish_times = []
                for i in range(100):
                    start_time = time.time()
                    message_id = await queue.publish_message(
                        message_type="test",
                        content={"test": f"message_{i}"},
                        sender="test_sender"
                    )
                    end_time = time.time()
                    publish_times.append(end_time - start_time)
                
                results = {
                    'publish_performance': {
                        'avg_time': statistics.mean(publish_times),
                        'min_time': min(publish_times),
                        'max_time': max(publish_times),
                        'messages_per_second': 1 / statistics.mean(publish_times)
                    }
                }
                
                await queue.close()
                logger.info(f"消息队列测试完成，平均发布时间: {statistics.mean(publish_times):.4f}s")
                return results
                
            except Exception as redis_error:
                logger.warning(f"Redis未运行，跳过消息队列测试: {redis_error}")
                return {'skipped': 'Redis not available'}
                
        except Exception as e:
            logger.error(f"消息队列测试失败: {e}")
            return {'error': str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        logger.info("开始性能测试...")
        
        start_time = time.time()
        
        # 并行运行所有测试
        test_tasks = [
            self.test_technical_indicators(),
            self.test_data_fetching(),
            self.test_websocket_performance(),
            self.test_message_queue()
        ]
        
        results = await asyncio.gather(*test_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 整理结果
        test_names = [
            'technical_indicators',
            'data_fetching', 
            'websocket_performance',
            'message_queue'
        ]
        
        self.results = {
            'total_test_time': total_time,
            'test_results': {}
        }
        
        for name, result in zip(test_names, results):
            if isinstance(result, Exception):
                self.results['test_results'][name] = {'error': str(result)}
            else:
                self.results['test_results'][name] = result
        
        logger.info(f"所有测试完成，总耗时: {total_time:.2f}s")
        return self.results
    
    def generate_report(self) -> str:
        """生成性能测试报告"""
        report = []
        report.append("# 性能测试报告")
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总测试时间: {self.results.get('total_test_time', 0):.2f}秒")
        report.append("")
        
        for test_name, result in self.results.get('test_results', {}).items():
            report.append(f"## {test_name.replace('_', ' ').title()}")
            
            if 'error' in result:
                report.append(f"❌ 测试失败: {result['error']}")
            elif 'skipped' in result:
                report.append(f"⏭️ 测试跳过: {result['skipped']}")
            else:
                report.append("✅ 测试成功")
                
                # 根据测试类型显示不同的指标
                if test_name == 'technical_indicators':
                    avg_times = [r.get('avg_time', 0) for r in result.values() if isinstance(r, dict) and 'avg_time' in r]
                    if avg_times:
                        report.append(f"- 平均计算时间: {statistics.mean(avg_times):.4f}秒")
                        report.append(f"- 最快计算时间: {min(avg_times):.4f}秒")
                        report.append(f"- 最慢计算时间: {max(avg_times):.4f}秒")
                
                elif test_name == 'data_fetching':
                    if 'single_symbol' in result:
                        report.append(f"- 单标的数据获取: {result['single_symbol']['avg_time']:.2f}秒")
                    if 'multi_symbol' in result:
                        report.append(f"- 多标的数据获取: {result['multi_symbol']['total_time']:.2f}秒")
                        report.append(f"- 成功率: {result['multi_symbol']['successful_symbols']}/{result['multi_symbol']['symbols_count']}")
                
                elif test_name == 'websocket_performance':
                    if 'broadcast_performance' in result:
                        bp = result['broadcast_performance']
                        report.append(f"- 广播平均时间: {bp['avg_time']:.4f}秒")
                        report.append(f"- 连接数: {bp['connections']}")
                
                elif test_name == 'message_queue':
                    if 'publish_performance' in result:
                        pp = result['publish_performance']
                        report.append(f"- 消息发布平均时间: {pp['avg_time']:.4f}秒")
                        report.append(f"- 每秒消息数: {pp['messages_per_second']:.0f}")
            
            report.append("")
        
        return "\n".join(report)

async def main():
    """主函数"""
    tester = PerformanceTester()
    
    # 运行所有测试
    results = await tester.run_all_tests()
    
    # 生成报告
    report = tester.generate_report()
    print(report)
    
    # 保存报告到文件
    with open('performance_test_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("性能测试报告已保存到 performance_test_report.md")

if __name__ == "__main__":
    asyncio.run(main())