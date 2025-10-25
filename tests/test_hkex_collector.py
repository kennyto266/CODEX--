#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test HKEX Collector"""

import asyncio
from datetime import date
from src.data_adapters.hkex_data_collector import HKEXDataCollector

async def test_hkex():
    print("\n=== Testing HKEXDataCollector ===\n")

    # Create collector
    collector = HKEXDataCollector(mode='mock')

    # Connect
    connected = await collector.connect()
    print(f"Connected: {connected}")

    # List indicators
    indicators = await collector.list_indicators()
    print(f"\nSupported indicators ({len(indicators)}):")
    for ind in indicators:
        print(f"  - {ind}")

    # Fetch data
    print("\n[Fetching Data]")
    data = await collector.fetch_data('hsi_futures_volume', date(2024, 9, 1), date(2024, 9, 5))
    print(f"Data shape: {data.shape}")
    print(f"First 3 rows:\n{data.head(3)}\n")

    # Get realtime
    print("[Real-time Data]")
    realtime = await collector.get_realtime_data("hsi_implied_volatility")
    print(f"HSI IV: {realtime['value']:.2f}%")

    # Health check
    print("\n[Health Check]")
    health = await collector.health_check()
    print(f"Status: {health['status']}")
    print(f"Is Connected: {health['is_connected']}")
    print(f"Cache Size: {health['cache_size']}")

    # Disconnect
    await collector.disconnect()
    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    asyncio.run(test_hkex())
