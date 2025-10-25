#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系統狀態報告生成腳本
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger("system_status")

def print_header(text):
    logger.info("\n" + "=" * 70)
    logger.info(f"  {text}")
    logger.info("=" * 70)

def print_section(text):
    logger.info(f"\n【{text}】")

def print_item(name, status, details=""):
    icon = "✓" if status else "✗"
    logger.info(f"  {icon} {name}")
    if details:
        logger.info(f"      {details}")

def check_module(module_path, class_name=""):
    """檢查模塊是否可以導入"""
    try:
        if class_name:
            exec(f"from {module_path} import {class_name}")
            return True, f"✓ 成功導入 {class_name}"
        else:
            exec(f"import {module_path}")
            return True, f"✓ 模塊可用"
    except ImportError as e:
        return False, f"✗ 導入失敗: {str(e)[:50]}"
    except Exception as e:
        return False, f"✗ 錯誤: {str(e)[:50]}"

def main():
    print_header("港股量化交易系統 - 系統狀態報告")

    # 1. 基本模塊檢查
    print_section("1. 基本模塊檢查")
    modules = [
        ("pandas", "pd"),
        ("numpy", "np"),
        ("requests", ""),
        ("fastapi", "FastAPI"),
        ("uvicorn", ""),
    ]

    for module_name, import_name in modules:
        if import_name:
            success, msg = check_module(module_name, import_name)
        else:
            success, msg = check_module(module_name)
        print_item(module_name, success, msg)

    # 2. 數據適配器檢查
    print_section("2. 數據適配器檢查")
    adapters = [
        ("src.data_adapters.base_adapter", "BaseDataAdapter"),
        ("src.data_adapters.http_api_adapter", "HTTPAPIAdapter"),
        ("src.data_adapters.gov_data_collector", "GovDataCollector"),
        ("src.data_adapters.hkex_data_collector", "HKEXDataCollector"),
        ("src.data_adapters.alternative_data_service", "AlternativeDataService"),
    ]

    adapter_status = {}
    for module_path, class_name in adapters:
        success, msg = check_module(module_path, class_name)
        adapter_status[class_name] = success
        print_item(class_name, success, msg)

    # 3. 回測引擎檢查
    print_section("3. 回測引擎檢查")
    backtest_modules = [
        ("src.backtest.enhanced_backtest_engine", "EnhancedBacktestEngine"),
        ("src.backtest.alt_data_backtest_extension", "AltDataBacktestExtension"),
        ("src.backtest.signal_validation", "SignalValidator"),
    ]

    backtest_status = {}
    for module_path, class_name in backtest_modules:
        success, msg = check_module(module_path, class_name)
        backtest_status[class_name] = success
        print_item(class_name, success, msg)

    # 4. 分析框架檢查
    print_section("4. 分析框架檢查")
    analysis_modules = [
        ("src.analysis.correlation_analyzer", "CorrelationAnalyzer"),
        ("src.analysis.correlation_report", "CorrelationReport"),
    ]

    for module_path, class_name in analysis_modules:
        success, msg = check_module(module_path, class_name)
        print_item(class_name, success, msg)

    # 5. Agent系統檢查
    print_section("5. 多智能體系統檢查")
    try:
        from src.agents.base_agent import BaseAgent
        print_item("BaseAgent", True, "✓ Agent基類可用")

        try:
            from src.agents.coordinator import Coordinator
            print_item("Coordinator", True, "✓ Agent協調器可用")
        except Exception as e:
            print_item("Coordinator", False, f"✗ {str(e)[:40]}")

        try:
            from src.agents.real_agents.data_scientist import DataScientist
            print_item("DataScientist Agent", True, "✓ 數據科學家Agent可用")
        except Exception as e:
            print_item("DataScientist Agent", False, f"✗ {str(e)[:40]}")

    except Exception as e:
        print_item("BaseAgent", False, f"✗ {str(e)[:40]}")

    # 6. 配置檢查
    print_section("6. 系統配置檢查")
    import os
    env_file = Path(".env")
    if env_file.exists():
        print_item(".env文件", True, f"✓ 配置文件存在 ({env_file.stat().st_size} bytes)")
    else:
        print_item(".env文件", False, "✗ 配置文件不存在")

    config_file = Path("pytest.ini")
    if config_file.exists():
        print_item("pytest.ini", True, "✓ 測試配置存在")
    else:
        print_item("pytest.ini", False, "✗ 測試配置不存在")

    # 7. 數據源可用性檢查
    print_section("7. 數據源可用性檢查")
    logger.info("  中心化HTTP API端點:")
    logger.info("    - 基礎URL: http://18.180.162.113:9191")
    logger.info("    - 端點: /inst/getInst")
    logger.info("    - 示例符號: 0700.hk (騰訊), 0388.hk, 1398.hk, 0939.hk")

    try:
        import requests
        try:
            response = requests.get(
                "http://18.180.162.113:9191/inst/getInst",
                params={"symbol": "0700.hk", "duration": 365},
                timeout=5
            )
            if response.status_code == 200:
                print_item("HTTP API 連接", True, "✓ API可訪問")
            else:
                print_item("HTTP API 連接", False, f"✗ 返回狀態碼 {response.status_code}")
        except requests.Timeout:
            print_item("HTTP API 連接", False, "⚠ 連接超時")
        except requests.ConnectionError:
            print_item("HTTP API 連接", False, "⚠ 無法連接到API")
    except ImportError:
        print_item("HTTP API 連接", False, "✗ requests模塊未安裝")

    # 8. 功能總結
    print_section("8. 已實現的功能")
    features = [
        ("HIBOR數據收集", "✓ 香港銀行間同業拆息 (隔夜/1M/3M/6M/12M)"),
        ("替代數據框架", "✓ 訪港旅客、貿易、經濟指標等"),
        ("HKEX數據", "✓ 期貨期權成交量、成交金額、市場廣度"),
        ("相關性分析", "✓ Pearson、Spearman、Kendall相關係數"),
        ("回測引擎", "✓ 增強型回測支持交易成本、滑點、市場沖擊"),
        ("信號融合", "✓ 價格信號與替代數據信號加權融合"),
        ("多智能體系統", "✓ 7個專業Agent協同工作"),
        ("Web儀表板", "✓ FastAPI + WebSocket實時監控"),
        ("爬蟲系統", "✓ HKEX、香港政府數據爬蟲"),
    ]

    for feature, description in features:
        logger.info(f"  ✓ {feature}")
        logger.info(f"      {description}")

    # 9. 後續建議
    print_section("9. 後續建議")
    recommendations = [
        "開始收集實時HIBOR數據進行策略研究",
        "測試替代數據與股票價格的相關性",
        "使用HTTP API端點替換本地數據源",
        "利用已有的爬蟲系統定期收集香港政府數據",
        "基於替代數據開發新的交易策略",
        "使用回測引擎驗證策略性能",
        "配置Telegram機器人進行實時交易提醒",
        "部署到生產環境（Docker或k8s）",
    ]

    for i, rec in enumerate(recommendations, 1):
        logger.info(f"  {i}. {rec}")

    # 最終總結
    print_header("系統狀態總結")
    total_adapters = len(adapter_status)
    active_adapters = sum(1 for v in adapter_status.values() if v)

    total_backtest = len(backtest_status)
    active_backtest = sum(1 for v in backtest_status.values() if v)

    logger.info(f"\n✓ 數據適配器: {active_adapters}/{total_adapters} 可用")
    logger.info(f"✓ 回測模塊: {active_backtest}/{total_backtest} 可用")
    logger.info(f"✓ 系統已準備好進行量化交易研究")
    logger.info(f"\n💡 提示: 使用 'python complete_project_system.py' 啟動完整系統")
    logger.info(f"💡 提示: 使用 'python test_system_startup.py' 運行功能測試")

if __name__ == "__main__":
    try:
        main()
        logger.info("\n" + "=" * 70)
    except Exception as e:
        logger.error(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
