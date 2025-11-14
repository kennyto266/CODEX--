"""
Sprint 4 集成示例
展示协程池 + Protocol Buffers + 背压控制的完整使用
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
import json

from src.utils.performance_utils import (
    initialize_performance_system,
    execute_with_pool,
    rate_limited_execute,
    serialize_and_send,
    receive_and_deserialize,
    batch_process,
    high_throughput_processor,
    get_performance_stats,
    benchmark_throughput,
    cleanup_performance_system
)
from src.serialization.protobuf_serializer import (
    MessageSchema,
    create_stock_data_schema,
    create_trade_signal_schema
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_usage():
    """演示基本使用方法"""
    logger.info("=" * 60)
    logger.info("Demo 1: 基本使用方法")
    logger.info("=" * 60)

    # 初始化性能系统
    await initialize_performance_system()

    # 1. 使用协程池执行任务
    async def sample_task(x: int, y: int) -> int:
        await asyncio.sleep(0.1)
        return x + y

    result = await execute_with_pool(sample_task, 10, 20)
    logger.info(f"协程池执行结果: {result}")

    # 2. 使用速率限制执行任务
    async def api_call(url: str) -> str:
        await asyncio.sleep(0.1)
        return f"Response from {url}"

    result = await rate_limited_execute(
        api_call,
        "http://api.example.com/data",
        resource_id="api_calls"
    )
    logger.info(f"速率限制执行结果: {result}")

    # 3. 序列化数据
    stock_data = {
        'symbol': '0700.HK',
        'timestamp': int(time.time()),
        'open': 100.5,
        'high': 105.0,
        'low': 99.0,
        'close': 103.5,
        'volume': 1000000
    }

    # 注册schema
    serializer = await get_serializer()
    stock_schema = create_stock_data_schema()
    serializer.register_schema(stock_schema)

    # 序列化
    serialized = await serialize_and_send(stock_data, "StockData", compress=True)
    logger.info(f"序列化后大小: {len(serialized)} bytes")

    # 反序列化
    deserialized = await receive_and_deserialize(serialized, "StockData", decompress=True)
    logger.info(f"反序列化结果: {deserialized['symbol']}")

    logger.info("✓ 基本使用演示完成\n")


async def demo_batch_processing():
    """演示批量处理"""
    logger.info("=" * 60)
    logger.info("Demo 2: 批量处理")
    logger.info("=" * 60)

    # 模拟处理大量股票数据
    async def process_stock_data(symbol_data: tuple):
        symbol, timestamp = symbol_data
        await asyncio.sleep(0.01)  # 模拟处理时间
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'price': 100.0 + (timestamp % 10),
            'volume': 1000000 + (timestamp % 100000)
        }

    # 生成测试数据
    symbols = ['0700.HK', '0388.HK', '1398.HK', '0939.HK', '3988.HK']
    test_data = [(symbol, int(time.time()) + i) for i, symbol in enumerate(symbols * 20)]

    logger.info(f"准备处理 {len(test_data)} 条数据...")

    start = time.time()
    results = await batch_process(test_data, process_stock_data, batch_size=50)
    duration = time.time() - start

    logger.info(f"完成处理: {len(results)} 条数据")
    logger.info(f"处理时间: {duration:.2f} 秒")
    logger.info(f"吞吐量: {len(results)/duration:.2f} ops/sec")
    logger.info(f"示例结果: {results[0]}")

    logger.info("✓ 批量处理演示完成\n")


async def demo_high_throughput():
    """演示高吞吐量处理"""
    logger.info("=" * 60)
    logger.info("Demo 3: 高吞吐量处理")
    logger.info("=" * 60)

    # 创建输入和输出队列
    input_queue = asyncio.Queue(maxsize=1000)
    output_queue = asyncio.Queue(maxsize=1000)

    # 启动高吞吐量处理器
    processor_task = asyncio.create_task(
        high_throughput_processor(
            input_queue,
            lambda x: x * 2,
            output_queue,
            max_concurrent=100,
            resource_id="high_throughput"
        )
    )

    # 生产数据
    logger.info("生产数据中...")
    for i in range(100):
        await input_queue.put(i)

    # 等待处理完成
    await input_queue.join()

    # 获取结果
    results = []
    while not output_queue.empty():
        results.append(await output_queue.get())

    logger.info(f"处理了 {len(results)} 条数据")
    logger.info(f"前10个结果: {results[:10]}")

    # 取消处理器任务
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass

    logger.info("✓ 高吞吐量处理演示完成\n")


async def demo_performance_monitoring():
    """演示性能监控"""
    logger.info("=" * 60)
    logger.info("Demo 4: 性能监控")
    logger.info("=" * 60)

    # 执行一些任务
    async def monitor_task(n):
        await asyncio.sleep(0.05)
        return n * 2

    # 批量提交任务
    for batch in range(3):
        logger.info(f"执行第 {batch + 1} 批任务...")
        await batch_process(
            list(range(20)),
            monitor_task,
            batch_size=20
        )

        # 获取性能统计
        stats = await get_performance_stats()

        # 打印协程池统计
        pool_stats = stats.get('coroutine_pool', {})
        logger.info(
            f"协程池 - 工作者: {pool_stats.get('total_workers', 0)}/"
            f"{pool_stats.get('active_workers', 0)}, "
            f"队列: {pool_stats.get('queue_size', 0)}/"
            f"{pool_stats.get('queue_max_size', 0)}"
        )

        # 打印背压统计
        bp_stats = stats.get('backpressure', {})
        if 'resource_stats' in bp_stats:
            for resource, stat in bp_stats['resource_stats'].items():
                logger.info(
                    f"背压 - {resource}: "
                    f"{stat.get('requests_in_window', 0)} requests"
                )

        await asyncio.sleep(0.5)

    logger.info("✓ 性能监控演示完成\n")


async def demo_benchmark():
    """演示基准测试"""
    logger.info("=" * 60)
    logger.info("Demo 5: 基准测试")
    logger.info("=" * 60)

    # 定义基准测试任务
    async def benchmark_task():
        # 模拟一些计算
        result = sum(i * i for i in range(100))
        return result

    # 运行基准测试
    logger.info("运行吞吐量基准测试...")
    results = await benchmark_throughput(
        benchmark_task,
        iterations=1000,
        concurrency=100
    )

    logger.info("基准测试结果:")
    logger.info(f"  总时间: {results['total_duration']:.2f} 秒")
    logger.info(f"  吞吐量: {results['throughput']:.2f} ops/sec")
    logger.info(f"  平均延迟: {results['avg_latency']*1000:.2f} ms")
    logger.info(f"  完成: {results['completed']}")
    logger.info(f"  失败: {results['failed']}")

    logger.info("✓ 基准测试演示完成\n")


async def demo_real_world_scenario():
    """演示真实场景：股票数据处理流水线"""
    logger.info("=" * 60)
    logger.info("Demo 6: 真实场景 - 股票数据处理流水线")
    logger.info("=" * 60)

    # 创建schema
    stock_schema = create_stock_data_schema()
    trade_signal_schema = create_trade_signal_schema()

    serializer = await get_serializer()
    serializer.register_schema(stock_schema)
    serializer.register_schema(trade_signal_schema)

    async def fetch_stock_data(symbol: str) -> Dict:
        """获取股票数据"""
        await asyncio.sleep(0.05)  # 模拟API调用
        return {
            'symbol': symbol,
            'timestamp': int(time.time()),
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.5,
            'volume': 1000000
        }

    async def analyze_signals(stock_data: Dict) -> Dict:
        """分析交易信号"""
        await asyncio.sleep(0.02)
        # 简单的信号生成
        price_change = stock_data['close'] - stock_data['open']
        action = 'BUY' if price_change > 0 else 'SELL'
        return {
            'symbol': stock_data['symbol'],
            'action': action,
            'price': stock_data['close'],
            'quantity': 1000,
            'timestamp': stock_data['timestamp'],
            'strategy': 'PRICE_CHANGE',
            'confidence': 0.8
        }

    async def send_signal(signal: Dict) -> bool:
        """发送交易信号"""
        # 序列化信号
        serialized = await serialize_and_send(signal, "TradeSignal", compress=True)
        logger.debug(f"发送信号: {signal['symbol']} {signal['action']} (大小: {len(serialized)} bytes)")
        return True

    # 模拟股票列表
    symbols = ['0700.HK', '0388.HK', '1398.HK', '0939.HK', '3988.HK']

    logger.info("启动处理流水线...")

    # 阶段1: 获取数据
    logger.info("阶段1: 获取股票数据...")
    start = time.time()
    stock_data_list = await batch_process(symbols, fetch_stock_data, batch_size=len(symbols))
    logger.info(f"获取 {len(stock_data_list)} 只股票数据")

    # 阶段2: 分析信号
    logger.info("阶段2: 分析交易信号...")
    signals = await batch_process(stock_data_list, analyze_signals, batch_size=len(stock_data_list))
    logger.info(f"生成 {len(signals)} 个交易信号")

    # 阶段3: 发送信号（速率限制）
    logger.info("阶段3: 发送交易信号...")
    for signal in signals:
        await rate_limited_execute(
            send_signal,
            signal,
            resource_id="signal_sender",
            priority=5
        )
    logger.info("所有信号已发送")

    # 统计
    duration = time.time() - start
    logger.info(f"\n流水线完成统计:")
    logger.info(f"  总时间: {duration:.2f} 秒")
    logger.info(f"  吞吐量: {len(signals)/duration:.2f} signals/sec")
    logger.info(f"  数据量: {len(stock_data_list)} 条")
    logger.info(f"  信号量: {len(signals)} 个")

    # 显示示例信号
    logger.info(f"\n示例交易信号:")
    logger.info(f"  {json.dumps(signals[0], indent=2, default=str)}")

    logger.info("✓ 真实场景演示完成\n")


async def main():
    """主函数"""
    logger.info("🚀 Sprint 4 性能优化 - 完整演示")
    logger.info("演示协程池 + Protocol Buffers + 背压控制的集成使用\n")

    try:
        # 演示各个功能
        await demo_basic_usage()
        await asyncio.sleep(1)

        await demo_batch_processing()
        await asyncio.sleep(1)

        await demo_high_throughput()
        await asyncio.sleep(1)

        await demo_performance_monitoring()
        await asyncio.sleep(1)

        await demo_benchmark()
        await asyncio.sleep(1)

        await demo_real_world_scenario()

        # 最终性能报告
        logger.info("=" * 60)
        logger.info("最终性能报告")
        logger.info("=" * 60)

        stats = await get_performance_stats()
        logger.info(json.dumps(stats, indent=2, default=str))

        logger.info("\n✅ 所有演示完成!")
        logger.info("✓ 协程池管理 - 动态扩缩容")
        logger.info("✓ 背压控制 - 速率限制和熔断器")
        logger.info("✓ Protocol Buffers - 高效序列化")
        logger.info("✓ 性能优化 - 200K msg/s 目标")

    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}", exc_info=True)

    finally:
        # 清理资源
        logger.info("\n清理性能系统...")
        await cleanup_performance_system()
        logger.info("清理完成!")


if __name__ == "__main__":
    asyncio.run(main())
