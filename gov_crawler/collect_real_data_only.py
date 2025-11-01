#!/usr/bin/env python3
"""
真實數據統一收集器 - Real Data Only Collector
絕對不使用 mock 數據，僅收集來自官方數據源的真實數據

這個腳本將：
1. 從真實的 HKMA、C&SD 等官方數據源收集數據
2. 驗證所有數據都是真實的（非 mock）
3. 生成數據質量報告
4. 將真實數據保存到量化交易系統

警告: 任何使用 mock 數據的行為都會被拒絕並記錄錯誤
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import json

# 添加適配器路徑
sys.path.append(str(Path(__file__).parent / 'adapters' / 'real_data'))

from hibor.hkma_hibor_adapter import HKMAHiborAdapter
from economic.csd_economic_adapter import CSDEconomicAdapter
from property.landreg_property_adapter import LandRegPropertyAdapter
from property.property_market_index_adapter import PropertyMarketIndexAdapter
from base_real_adapter import DataQualityReport, MockDataError

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gov_crawler/logs/real_data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealDataOnlyCollector:
    """
    真實數據收集器 - 拒絕所有 mock 數據
    """

    def __init__(self):
        self.adapters = {}
        self.collection_results = {}
        self.real_data_count = 0
        self.mock_data_attempts = 0

        # 初始化適配器
        self._initialize_adapters()

    def _initialize_adapters(self):
        """初始化所有真實數據適配器"""
        logger.info("初始化真實數據適配器...")

        # 只能使用真實數據適配器
        self.adapters = {
            'hibor': HKMAHiborAdapter(),
            'economic': CSDEconomicAdapter(),
            'property_landreg': LandRegPropertyAdapter(),
            'property_index': PropertyMarketIndexAdapter(),
        }

        # 記錄初始化警告
        for name, adapter in self.adapters.items():
            adapter.log_real_data_warning()

        logger.info(f"已初始化 {len(self.adapters)} 個真實數據適配器")

    async def collect_all_real_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        收集所有真實數據
        """
        logger.warning("=" * 80)
        logger.warning("開始收集真實數據 - 嚴格禁止 mock 數據")
        logger.warning("=" * 80)

        results = {
            'collection_time': datetime.now().isoformat(),
            'start_date': start_date,
            'end_date': end_date,
            'adapters_count': len(self.adapters),
            'successful_collections': 0,
            'failed_collections': 0,
            'total_records': 0,
            'real_data_confirmed': 0,
            'mock_data_rejected': 0,
            'data_sources': {},
            'quality_reports': {},
            'errors': []
        }

        async with RealDataAdapter('temp', 'temp') as temp:  # 創建 session context
            for name, adapter in self.adapters.items():
                try:
                    logger.info(f"\n正在收集 {name} 真實數據...")
                    result = await self._collect_from_adapter(adapter, name, start_date, end_date)
                    results['data_sources'][name] = result
                    results['successful_collections'] += 1
                    results['total_records'] += len(result.get('data', []))
                    results['real_data_confirmed'] += result.get('real_data_count', 0)

                except MockDataError as e:
                    logger.error(f"🚫 {name}: Mock 數據錯誤 - {str(e)}")
                    results['mock_data_rejected'] += 1
                    results['errors'].append(f"{name}: {str(e)}")

                except Exception as e:
                    logger.error(f"❌ {name}: 收集失敗 - {str(e)}")
                    results['failed_collections'] += 1
                    results['errors'].append(f"{name}: {str(e)}")

        # 驗證總體數據質量
        if results['mock_data_rejected'] > 0:
            logger.error("🚨 檢測到 mock 數據嘗試！已拒絕所有 mock 數據")
            logger.error("數據質量無法保證，建議檢查數據源")

        logger.info("\n" + "=" * 80)
        logger.info("真實數據收集完成")
        logger.info(f"成功: {results['successful_collections']}/{len(self.adapters)}")
        logger.info(f"失敗: {results['failed_collections']}")
        logger.info(f"拒絕 mock 數據: {results['mock_data_rejected']}")
        logger.info(f"確認真實數據: {results['real_data_confirmed']} 條記錄")
        logger.info("=" * 80)

        return results

    async def _collect_from_adapter(self, adapter, name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        從單個適配器收集數據
        """
        async with adapter:
            # 測試連接
            connection_ok = await adapter.test_connection()
            if not connection_ok:
                raise ConnectionError(f"無法連接到 {name} 數據源")

            # 獲取真實數據
            df, quality_report = await adapter.collect_and_validate(start_date, end_date)

            if df.empty:
                raise ValueError(f"{name}: 未獲取到任何數據")

            # 強制驗證真實數據
            is_real = await adapter.validate_data_is_real(df)
            if not is_real:
                raise MockDataError(f"{name}: 數據驗證失敗 - 可能包含 mock 數據")

            # 保存數據
            saved_file = adapter.save_data_with_quality(df, quality_report)

            # 獲取數據源信息
            source_info = adapter.get_data_source_info()

            result = {
                'name': name,
                'success': True,
                'records_count': len(df),
                'real_data_count': len(df),  # 所有數據都應該是真實的
                'data_file': saved_file,
                'quality_report': quality_report.to_dict(),
                'source_info': source_info,
                'is_real_data': True,
                'has_mock_data': False,
                'columns': list(df.columns),
                'date_range': {
                    'start': df['date'].min().isoformat() if 'date' in df.columns else None,
                    'end': df['date'].max().isoformat() if 'date' in df.columns else None,
                }
            }

            logger.info(f"✓ {name}: 成功收集 {len(df)} 條真實數據")
            logger.info(f"  - 質量分數: {quality_report.overall_score:.2f}")
            logger.info(f"  - 真實性確認: {'是' if quality_report.is_real_data else '否'}")

            return result

    def generate_collection_report(self, results: Dict[str, Any]) -> str:
        """
        生成收集報告
        """
        report = []
        report.append("╔" + "═" * 78 + "╗")
        report.append("║" + " " * 20 + "真實數據收集報告" + " " * 35 + "║")
        report.append("╚" + "═" * 78 + "╝")
        report.append("")

        # 基本信息
        report.append(f"📅 收集時間: {results['collection_time']}")
        report.append(f"📊 時間範圍: {results['start_date']} 到 {results['end_date']}")
        report.append(f"🔢 適配器數量: {results['adapters_count']}")
        report.append("")

        # 收集結果
        report.append("📈 收集結果:")
        report.append(f"  ✓ 成功: {results['successful_collections']}/{results['adapters_count']}")
        report.append(f"  ✗ 失敗: {results['failed_collections']}")
        report.append(f"  🚫 拒絕 mock 數據: {results['mock_data_rejected']}")
        report.append(f"  ✅ 確認真實數據: {results['real_data_confirmed']} 條記錄")
        report.append("")

        # 詳細結果
        report.append("📋 詳細結果:")
        for name, source_data in results['data_sources'].items():
            status = "✅" if source_data['success'] else "❌"
            report.append(f"  {status} {name}:")
            report.append(f"    - 記錄數量: {source_data['records_count']}")
            report.append(f"    - 真實數據: {source_data['real_data_count']}")
            report.append(f"    - 質量分數: {source_data['quality_report']['overall_score']:.2f}")
            report.append(f"    - 數據文件: {source_data['data_file']}")

        # 錯誤列表
        if results['errors']:
            report.append("")
            report.append("⚠️ 錯誤列表:")
            for error in results['errors']:
                report.append(f"  - {error}")

        # 數據質量評估
        report.append("")
        report.append("📊 數據質量評估:")
        if results['mock_data_rejected'] == 0:
            report.append("  ✅ 所有數據均為真實數據")
            report.append("  ✅ 無 mock 數據檢測")
            report.append("  ✅ 數據質量可接受")
        else:
            report.append("  ⚠️ 發現 mock 數據嘗試")
            report.append("  ⚠️ 數據質量存在風險")

        report.append("")
        report.append("═" * 80)
        report.append("注意: 此系統僅處理真實數據，所有 mock 數據都會被拒絕")
        report.append("═" * 80)

        return "\n".join(report)

    async def validate_real_data_only(self, results: Dict[str, Any]) -> bool:
        """
        驗證所有收集的數據都是真實的
        """
        logger.info("正在驗證數據真實性...")

        # 檢查是否有 mock 數據被拒絕
        if results['mock_data_rejected'] > 0:
            logger.error("驗證失敗: 檢測到 mock 數據嘗試")
            return False

        # 檢查每個數據源
        for name, source_data in results['data_sources'].items():
            if not source_data.get('is_real_data', False):
                logger.error(f"驗證失敗: {name} 數據不是真實的")
                return False

            if source_data.get('has_mock_data', False):
                logger.error(f"驗證失敗: {name} 包含 mock 數據")
                return False

            # 檢查質量報告
            quality_report = source_data.get('quality_report', {})
            if not quality_report.get('is_real_data', False):
                logger.error(f"驗證失敗: {name} 質量報告顯示非真實數據")
                return False

        logger.info("✅ 所有數據驗證通過，確認為真實數據")
        return True

    def save_collection_results(self, results: Dict[str, Any], report_text: str) -> str:
        """
        保存收集結果
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存結果 JSON
        results_file = Path("gov_crawler/data/real_data_collection_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 保存報告
        report_file = Path(f"gov_crawler/data/real_data_collection_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        logger.info(f"結果已保存到: {results_file}")
        logger.info(f"報告已保存到: {report_file}")

        return str(report_file)

    def disable_mock_data_mode(self):
        """
        禁用 mock 數據模式 - 強制使用真實數據
        """
        logger.warning("=" * 80)
        logger.warning("🚨 MOCK 數據模式已禁用")
        logger.warning("=" * 80)
        logger.warning("此系統僅接受真實數據源，任何 mock 數據將被拒絕")
        logger.warning("違規行為將被記錄並導致收集失敗")
        logger.warning("=" * 80)

async def main():
    """主函數"""
    print("\n" + "=" * 80)
    print("🔴 港股量化交易系統 - 真實數據收集器")
    print("=" * 80)
    print("⚠️  警告: 此系統僅處理真實數據")
    print("🚫 禁止使用任何 mock 數據")
    print("✅ 僅從官方數據源收集數據")
    print("=" * 80 + "\n")

    # 創建收集器
    collector = RealDataOnlyCollector()

    # 禁用 mock 數據模式
    collector.disable_mock_data_mode()

    # 設定收集時間範圍
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    try:
        # 收集真實數據
        results = await collector.collect_all_real_data(start_date, end_date)

        # 驗證真實數據
        validation_passed = await collector.validate_real_data_only(results)

        if not validation_passed:
            logger.error("❌ 數據驗證失敗 - 存在 mock 數據")
            return False

        # 生成報告
        report_text = collector.generate_collection_report(results)
        print("\n" + report_text)

        # 保存結果
        report_file = collector.save_collection_results(results, report_text)

        # 返回成功
        logger.info(f"\n✅ 真實數據收集成功完成")
        logger.info(f"📊 收集了 {results['real_data_confirmed']} 條真實數據記錄")
        logger.info(f"📁 報告文件: {report_file}")

        return True

    except MockDataError as e:
        logger.error(f"🚫 Mock 數據錯誤: {str(e)}")
        logger.error("收集失敗 - 拒絕使用 mock 數據")
        return False

    except Exception as e:
        logger.error(f"❌ 收集失敗: {str(e)}")
        logger.error("請檢查數據源連接和配置")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
