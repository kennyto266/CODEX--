"""
Phase 8: Enhanced Features - 数据增强模块使用示例 (T194-T198)
=============================================================

展示如何使用5个数据增强模块：
- T194: 基本面数据集成
- T195: 期权数据支持
- T196: 期货合约支持
- T197: 多数据源融合
- T198: 实时数据流

Author: Claude Code
Date: 2025-11-09
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any

# 导入数据模块
from src.data.fundamental import (
    FundamentalDataIntegrator,
    FinancialStatement,
    FinancialStatementType,
    get_fundamental_data,
    calculate_financial_health_score
)

from src.data.options_data import (
    OptionsDataManager,
    OptionContract,
    OptionType,
    get_option_chain,
    calculate_implied_volatility
)

from src.data.futures_data import (
    FuturesDataManager,
    FuturesContract,
    get_futures_contracts,
    calculate_futures_fair_value
)

from src.data.fusion import (
    DataFusionEngine,
    DataSource,
    DataSourcePriority,
    DataType,
    fuse_multi_source_data
)

from src.data.streaming import (
    RealtimeStreamManager,
    StreamEvent,
    StreamEventType,
    StreamEventProcessor,
    create_price_alert
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 示例1: 基本面数据集成 (T194)
# ============================================================================

async def example_fundamental_data():
    """基本面数据集成示例"""
    print("\n" + "="*70)
    print("示例1: 基本面数据集成 (T194)")
    print("="*70)

    # 创建基本面数据集成器
    integrator = FundamentalDataIntegrator(
        cache_size=1000,
        cache_ttl=3600.0
    )

    # 注册数据源 (模拟)
    class MockFundamentalSource:
        async def get_financial_statements(self, symbol, statement_type, start_date, end_date):
            return [
                FinancialStatement(
                    symbol=symbol,
                    report_date=date.today(),
                    statement_type=statement_type,
                    total_assets=Decimal('1000000000'),
                    total_liabilities=Decimal('500000000'),
                    shareholders_equity=Decimal('500000000'),
                    revenue=Decimal('200000000'),
                    net_income=Decimal('50000000')
                )
            ]

        async def get_valuation_metrics(self, symbol, as_of_date):
            from src.data.fundamental import ValuationMetrics
            return ValuationMetrics(
                symbol=symbol,
                report_date=as_of_date,
                pe_ratio=Decimal('20.0'),
                pb_ratio=Decimal('2.0'),
                roe=Decimal('0.1')
            )

    integrator.register_data_source("mock_fundamental", MockFundamentalSource())

    # 获取财务报表
    print("\n1. 获取财务报表:")
    statements = await integrator.get_financial_statements(
        symbol="0700.HK",
        statement_type=FinancialStatementType.BALANCE_SHEET,
        years=2
    )
    for stmt in statements:
        print(f"   日期: {stmt.report_date}")
        print(f"   总资产: {stmt.total_assets:,}")
        print(f"   股东权益: {stmt.shareholders_equity:,}")

    # 获取估值指标
    print("\n2. 获取估值指标:")
    metrics = await integrator.get_valuation_metrics("0700.HK")
    if metrics:
        print(f"   市盈率: {metrics.pe_ratio}")
        print(f"   市净率: {metrics.pb_ratio}")
        print(f"   净资产收益率: {metrics.roe}")

    # 计算财务比率
    print("\n3. 计算财务比率:")
    ratios = await integrator.calculate_financial_ratios("0700.HK")
    for ratio, value in ratios.items():
        print(f"   {ratio}: {value}%")

    # 计算财务健康评分
    print("\n4. 计算财务健康评分:")
    health_score = await calculate_financial_health_score("0700.HK")
    print(f"   健康评分: {health_score:.2f}/100")

    # 获取综合基本面数据
    print("\n5. 获取综合基本面数据:")
    fundamentals = await integrator.get_comprehensive_fundamentals("0700.HK")
    for key, value in fundamentals.items():
        print(f"   {key}: {'有数据' if value else '无数据'}")

    print("\n基本面数据集成示例完成!\n")


# ============================================================================
# 示例2: 期权数据支持 (T195)
# ============================================================================

async def example_options_data():
    """期权数据支持示例"""
    print("\n" + "="*70)
    print("示例2: 期权数据支持 (T195)")
    print("="*70)

    # 创建期权数据管理器
    manager = OptionsDataManager(
        cache_size=1000,
        cache_ttl=300.0,
        risk_free_rate=0.03
    )

    # 创建期权合约
    print("\n1. 创建期权合约:")
    call_option = OptionContract(
        symbol="0700.HK",
        option_symbol="0700.HK.C2403.400",
        expiration_date=date(2024, 3, 31),
        strike_price=Decimal('400'),
        option_type=OptionType.CALL,
        last_price=Decimal('15')
    )
    print(f"   合约代码: {call_option.option_symbol}")
    print(f"   行权价: {call_option.strike_price}")
    print(f"   期权类型: {call_option.option_type.value}")

    # 计算隐含波动率
    print("\n2. 计算隐含波动率:")
    iv = await manager.get_implied_volatility(
        option=call_option,
        underlying_price=Decimal('395'),
        time_to_expiration=30 / 365
    )
    print(f"   隐含波动率: {iv:.2%}")

    # 计算Greeks
    print("\n3. 计算Greeks:")
    greeks = await manager.calculate_greeks(
        option=call_option,
        underlying_price=Decimal('395'),
        time_to_expiration=30 / 365
    )
    for greek, value in greeks.items():
        print(f"   {greek}: {value:.4f}")

    # 期权策略分析
    print("\n4. 期权策略分析:")
    strategy = await manager.analyze_option_strategy(
        strategy_type="covered_call",
        symbol="0700.HK",
        underlying_price=Decimal('395'),
        call_strike=Decimal('400'),
        call_premium=Decimal('15')
    )
    print(f"   策略类型: {strategy['strategy_type']}")
    print(f"   最大盈利: {strategy['max_profit']}")
    print(f"   最大亏损: {strategy['max_loss']}")
    print(f"   盈亏平衡点: {strategy['breakeven']}")

    # 使用便捷函数
    print("\n5. 便捷函数计算隐含波动率:")
    iv_calc = await calculate_implied_volatility(
        option_price=15.0,
        underlying_price=395.0,
        strike_price=400.0,
        time_to_expiration=30/365,
        risk_free_rate=0.03,
        option_type="CALL"
    )
    print(f"   隐含波动率: {iv_calc:.2%}")

    print("\n期权数据支持示例完成!\n")


# ============================================================================
# 示例3: 期货数据支持 (T196)
# ============================================================================

async def example_futures_data():
    """期货数据支持示例"""
    print("\n" + "="*70)
    print("示例3: 期货数据支持 (T196)")
    print("="*70)

    # 创建期货数据管理器
    manager = FuturesDataManager(
        cache_size=1000,
        cache_ttl=300.0
    )

    # 创建期货合约
    print("\n1. 创建期货合约:")
    contract = FuturesContract(
        symbol="HSI2024M",
        underlying="HSI",
        contract_month="2024-03",
        expiration_date=date(2024, 3, 31),
        last_price=Decimal('20000'),
        volume=10000,
        open_interest=5000
    )
    print(f"   合约代码: {contract.symbol}")
    print(f"   标的资产: {contract.underlying}")
    print(f"   最新价: {contract.last_price}")
    print(f"   成交量: {contract.volume}")

    # 计算持有成本
    print("\n2. 计算持有成本:")
    carry_model = await manager.calculate_cost_of_carry(
        futures_symbol="HSI2024M",
        spot_price=Decimal('20000'),
        time_to_expiration=0.25,
        dividend_yield=Decimal('0.02'),
        risk_free_rate=Decimal('0.03'),
        convenience_yield=Decimal('0.01')
    )
    print(f"   无风险利率: {carry_model.risk_free_rate:.2%}")
    print(f"   融资利率: {carry_model.financing_rate:.2%}")
    print(f"   隐含期货价格: {carry_model.implied_futures_price:.2f}")

    # 分析基差
    print("\n3. 分析基差:")
    basis = await manager.analyze_basis(
        futures_symbol="HSI2024M",
        spot_symbol="HSI",
        as_of_date=date.today()
    )
    if basis:
        print(f"   期货价格: {basis.futures_price}")
        print(f"   现货价格: {basis.spot_price}")
        print(f"   基差: {basis.basis}")
        print(f"   基差百分比: {basis.basis_percent:.2%}")

    # 展期策略
    print("\n4. 展期策略:")
    roll_strategy = await manager.get_roll_strategy(
        underlying="HSI",
        strategy_type="calendar_spread"
    )
    if roll_strategy:
        print(f"   当前合约: {roll_strategy.current_contract}")
        print(f"   下一合约: {roll_strategy.next_contract}")
        print(f"   展期成本: {roll_strategy.roll_cost}")

    # 日历价差分析
    print("\n5. 日历价差分析:")
    spread_analysis = await manager.analyze_calendar_spread(
        front_month="HSI2024M",
        deferred_month="HSI2024J",
        as_of_date=date.today()
    )
    if spread_analysis:
        print(f"   近月价格: {spread_analysis['front_price']}")
        print(f"   远月价格: {spread_analysis['deferred_price']}")
        print(f"   价差: {spread_analysis['spread']}")
        print(f"   价差百分比: {spread_analysis['spread_percent']:.2%}")

    # 使用便捷函数
    print("\n6. 便捷函数计算期货公允价值:")
    fair_value = await calculate_futures_fair_value(
        spot_price=20000,
        days_to_expiry=90,
        dividend_yield=0.02,
        risk_free_rate=0.03
    )
    print(f"   公允价值: {fair_value:.2f}")

    print("\n期货数据支持示例完成!\n")


# ============================================================================
# 示例4: 多数据源融合 (T197)
# ============================================================================

async def example_data_fusion():
    """多数据源融合示例"""
    print("\n" + "="*70)
    print("示例4: 多数据源融合 (T197)")
    print("="*70)

    # 创建数据融合引擎
    engine = DataFusionEngine(
        cache_size=2000,
        cache_ttl=300.0,
        max_workers=4
    )

    # 模拟数据源
    class MockDataSource1:
        async def get_data(self, symbol, data_type, start_time, end_time):
            # 模拟数据1 - 有延迟但数据质量高
            import random
            await asyncio.sleep(0.1)  # 模拟网络延迟
            base_price = 100
            return [
                {
                    "timestamp": start_time + timedelta(minutes=i),
                    "price": base_price + random.uniform(-2, 2),
                    "volume": 1000 + random.randint(-100, 100)
                }
                for i in range(5)
            ]

    class MockDataSource2:
        async def get_data(self, symbol, data_type, start_time, end_time):
            # 模拟数据2 - 无延迟但数据有噪音
            import random
            return [
                {
                    "timestamp": start_time + timedelta(minutes=i),
                    "price": 100 + random.uniform(-1, 3),  # 更大噪音
                    "volume": 1000 + random.randint(-200, 200)
                }
                for i in range(5)
            ]

    # 注册数据源
    print("\n1. 注册数据源:")
    engine.register_data_source(
        name="source1",
        source_type="YAHOO",
        fetcher=MockDataSource1(),
        priority=DataSourcePriority.HIGH,
        reliability_score=0.95
    )
    engine.register_data_source(
        name="source2",
        source_type="ALPHA_VANTAGE",
        fetcher=MockDataSource2(),
        priority=DataSourcePriority.MEDIUM,
        reliability_score=0.85
    )
    print("   ✓ 已注册2个数据源")

    # 融合多源数据
    print("\n2. 融合多源数据:")
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()

    results = await engine.fuse_data(
        symbol="0700.HK",
        data_type=DataType.OHLCV,
        start_time=start_time,
        end_time=end_time,
        resolution="PRIORITY"  # 使用优先级策略
    )

    print(f"   融合了 {len(results)} 个数据点")

    for i, result in enumerate(results[:3]):  # 只显示前3个
        print(f"   数据点 {i+1}:")
        print(f"     时间: {result.timestamp}")
        print(f"     数据: {result.merged_data}")
        print(f"     质量评分: {result.quality_score:.2f}")
        print(f"     使用的数据源: {result.sources_used}")

    # 比较数据源质量
    print("\n3. 比较数据源质量:")
    comparison = await engine.compare_sources(
        symbol="0700.HK",
        data_type=DataType.OHLCV,
        start_time=start_time,
        end_time=end_time
    )
    print(comparison.to_string())

    # 使用便捷函数
    print("\n4. 便捷函数融合数据:")
    fusion_results = await fuse_multi_source_data(
        symbol="0700.HK",
        data_type=DataType.OHLCV,
        start_time=start_time,
        end_time=end_time
    )
    print(f"   融合了 {len(fusion_results)} 个数据点")

    print("\n多数据源融合示例完成!\n")


# ============================================================================
# 示例5: 实时数据流 (T198)
# ============================================================================

async def example_streaming_data():
    """实时数据流示例"""
    print("\n" + "="*70)
    print("示例5: 实时数据流 (T198)")
    print("="*70)

    # 创建实时流管理器
    manager = RealtimeStreamManager(
        buffer_size=10000,
        buffer_age=3600,
        reconnect_attempts=5
    )

    # 创建事件处理器
    processor = StreamEventProcessor(manager)

    # 统计数据
    tick_count = 0
    trade_count = 0

    # 注册事件处理器
    print("\n1. 注册事件处理器:")

    def on_tick(event: StreamEvent):
        nonlocal tick_count
        tick_count += 1
        if tick_count <= 3:  # 只打印前3个
            print(f"   逐笔成交: {event.symbol} - 价格: {event.data.get('price')}")

    def on_trade(event: StreamEvent):
        nonlocal trade_count
        trade_count += 1
        if trade_count <= 3:  # 只打印前3个
            print(f"   成交: {event.symbol} - 成交量: {event.data.get('volume')}")

    processor.on_tick(on_tick)
    processor.on_trade(on_trade)

    print("   ✓ 已注册逐笔成交和成交事件处理器")

    # 模拟发布事件
    print("\n2. 模拟实时数据流:")

    for i in range(5):
        # 发布逐笔成交事件
        tick_event = StreamEvent(
            event_type=StreamEventType.TICK,
            symbol="0700.HK",
            timestamp=datetime.now(),
            data={
                "price": 395.0 + i * 0.5,
                "volume": 100 + i * 10
            },
            source="simulated"
        )
        await manager.publish_event(tick_event)

        # 发布成交事件
        trade_event = StreamEvent(
            event_type=StreamEventType.TRADE,
            symbol="0700.HK",
            timestamp=datetime.now(),
            data={
                "price": 395.0 + i * 0.5,
                "volume": 1000 + i * 100
            },
            source="simulated"
        )
        await manager.publish_event(trade_event)

        await asyncio.sleep(0.1)

    # 获取缓冲区统计
    print("\n3. 缓冲区统计:")
    buffer_stats = manager.get_buffer_stats()
    for key, value in buffer_stats.items():
        print(f"   {key}: {value}")

    # 获取连接统计
    print("\n4. 连接统计:")
    conn_stats = manager.get_connection_stats()
    for key, value in conn_stats.items():
        print(f"   {key}: {value}")

    # 测试价格告警
    print("\n5. 价格告警测试:")
    alert_event = StreamEvent(
        event_type=StreamEventType.TICK,
        symbol="0700.HK",
        timestamp=datetime.now(),
        data={"price": 400.0},
        source="simulated"
    )

    triggered = create_price_alert(
        symbol="0700.HK",
        target_price=399.0,
        direction="above",
        event=alert_event
    )
    print(f"   价格告警触发: {triggered}")

    print("\n实时数据流示例完成!\n")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "#"*70)
    print("# Phase 8: Enhanced Features - 数据增强模块使用示例 (T194-T198)")
    print("#"*70)

    try:
        # 运行所有示例
        await example_fundamental_data()
        await asyncio.sleep(0.5)

        await example_options_data()
        await asyncio.sleep(0.5)

        await example_futures_data()
        await asyncio.sleep(0.5)

        await example_data_fusion()
        await asyncio.sleep(0.5)

        await example_streaming_data()

        print("\n" + "#"*70)
        print("# 所有示例运行完成!")
        print("#"*70 + "\n")

    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
