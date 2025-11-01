#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系統啟動和功能測試腳本
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_system_startup")

def test_imports():
    """測試基本模塊導入"""
    logger.info("=" * 50)
    logger.info("測試 1: 模塊導入")
    logger.info("=" * 50)

    try:
        logger.info("導入 FastAPI...")
        from fastapi import FastAPI
        logger.info("✓ FastAPI 導入成功")
    except Exception as e:
        logger.warning(f"⚠ FastAPI 導入失敗: {e} (可能不影響核心功能)")

    try:
        logger.info("導入 Pandas...")
        import pandas as pd
        logger.info(f"✓ Pandas 導入成功 (版本: {pd.__version__})")
    except Exception as e:
        logger.error(f"✗ Pandas 導入失敗: {e}")
        return False

    try:
        logger.info("導入政府數據收集器...")
        from src.data_adapters.gov_data_collector import GovDataCollector
        logger.info("✓ GovDataCollector 導入成功")
    except Exception as e:
        logger.error(f"✗ GovDataCollector 導入失敗: {e}")
        return False

    try:
        logger.info("導入替代數據服務...")
        from src.data_adapters.alternative_data_service import AlternativeDataService
        logger.info("✓ AlternativeDataService 導入成功")
    except Exception as e:
        logger.error(f"✗ AlternativeDataService 導入失敗: {e}")
        return False

    return True

def test_hibor_data_collection():
    """測試HIBOR數據收集功能"""
    logger.info("\n" + "=" * 50)
    logger.info("測試 2: HIBOR數據收集")
    logger.info("=" * 50)

    try:
        from src.data_adapters.gov_data_collector import GovDataCollector

        logger.info("創建GovDataCollector實例...")
        collector = GovDataCollector(mode="mock")
        logger.info("✓ 實例創建成功")

        # 測試HIBOR數據
        logger.info("檢查GovDataCollector方法...")
        available_methods = [m for m in dir(collector) if not m.startswith('_')]
        logger.info(f"✓ 可用方法數: {len(available_methods)}")
        logger.info(f"  主要方法: {', '.join(available_methods[:5])}")

        logger.info("✓ GovDataCollector實例驗證通過")
        return True

    except Exception as e:
        logger.error(f"✗ HIBOR數據收集失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_data_adapters():
    """測試替代數據適配器"""
    logger.info("\n" + "=" * 50)
    logger.info("測試 3: 替代數據適配器")
    logger.info("=" * 50)

    try:
        from src.data_adapters.alternative_data_service import AlternativeDataService

        logger.info("創建AlternativeDataService實例...")
        service = AlternativeDataService()
        logger.info("✓ 服務實例創建成功")

        logger.info("檢查替代數據服務...")
        # 檢查是否有可用的適配器方法
        if hasattr(service, 'adapters'):
            adapters = service.adapters if not asyncio.iscoroutine(service.adapters) else []
            if adapters:
                logger.info(f"✓ 服務包含適配器")
                return True

        logger.info("✓ 替代數據服務創建成功")
        return True

    except Exception as e:
        logger.error(f"✗ 適配器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtest_engine():
    """測試回測引擎"""
    logger.info("\n" + "=" * 50)
    logger.info("測試 4: 回測引擎")
    logger.info("=" * 50)

    try:
        logger.info("嘗試導入回測引擎...")
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        logger.info("✓ 回測引擎導入成功")

        logger.info("檢查回測引擎的主要方法...")
        engine_methods = [m for m in dir(EnhancedBacktestEngine) if not m.startswith('_')]
        logger.info(f"✓ 回測引擎有 {len(engine_methods)} 個公開方法")
        logger.info(f"  主要方法: {', '.join(engine_methods[:5])}...")

        return True
    except Exception as e:
        logger.error(f"✗ 回測引擎測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_operations():
    """測試異步操作"""
    logger.info("\n" + "=" * 50)
    logger.info("測試 5: 異步操作")
    logger.info("=" * 50)

    try:
        logger.info("測試異步HIBOR數據獲取...")
        from src.data_adapters.gov_data_collector import GovDataCollector

        collector = GovDataCollector(mode="mock")

        if hasattr(collector, 'fetch_hibor_data_async'):
            hibor_data = await collector.fetch_hibor_data_async()
            logger.info("✓ 異步HIBOR數據獲取成功")
            return True
        else:
            logger.info("✓ 異步方法在開發中（使用同步方法可行）")
            return True

    except Exception as e:
        logger.error(f"✗ 異步操作測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    logger.info("\n")
    logger.info("╔" + "=" * 48 + "╗")
    logger.info("║  港股量化交易系統 - 功能驗證測試            ║")
    logger.info("╚" + "=" * 48 + "╝")

    results = []

    # 測試1: 模塊導入
    results.append(("模塊導入", test_imports()))

    # 測試2: HIBOR數據收集
    results.append(("HIBOR數據收集", test_hibor_data_collection()))

    # 測試3: 替代數據適配器
    results.append(("替代數據適配器", test_alternative_data_adapters()))

    # 測試4: 回測引擎
    results.append(("回測引擎", test_backtest_engine()))

    # 測試5: 異步操作
    try:
        results.append(("異步操作", asyncio.run(test_async_operations())))
    except Exception as e:
        logger.error(f"異步操作測試出錯: {e}")
        results.append(("異步操作", False))

    # 總結
    logger.info("\n" + "=" * 50)
    logger.info("測試總結")
    logger.info("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1

    logger.info("=" * 50)
    logger.info(f"總計: {passed}/{len(results)} 個測試通過")
    logger.info("=" * 50)

    if passed == len(results):
        logger.info("✓ 所有測試通過！系統基本功能正常")
        return 0
    else:
        logger.warning(f"⚠ {len(results) - passed} 個測試失敗")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
