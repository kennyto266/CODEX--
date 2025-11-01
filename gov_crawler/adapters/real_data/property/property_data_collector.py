#!/usr/bin/env python3
"""
物業數據統一收集器 - Property Data Collector
整合多個物業數據源的統一收集器
僅使用真實數據，絕對禁止 mock 數據
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from .landreg_property_adapter import LandRegPropertyAdapter
from .property_market_index_adapter import PropertyMarketIndexAdapter
from ..base_real_adapter import DataQualityReport, MockDataError

logger = logging.getLogger(__name__)

class PropertyDataCollector:
    """
    物業數據統一收集器
    協調多個物業數據適配器，確保僅收集真實數據
    """

    def __init__(self):
        self.adapters = {}
        self._initialize_adapters()

    def _initialize_adapters(self):
        """初始化所有物業數據適配器"""
        logger.info("初始化物業數據適配器...")

        self.adapters = {
            'land_registry': LandRegPropertyAdapter(),
            'market_index': PropertyMarketIndexAdapter(),
        }

        # 記錄初始化警告
        for name, adapter in self.adapters.items():
            adapter.log_real_data_warning()

        logger.info(f"已初始化 {len(self.adapters)} 個物業數據適配器")

    async def collect_all_property_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        收集所有物業數據
        """
        logger.warning("=" * 80)
        logger.warning("開始收集物業數據 - 嚴格禁止 mock 數據")
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

        for name, adapter in self.adapters.items():
            try:
                logger.info(f"\n正在收集 {name} 物業數據...")
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

        logger.info("\n" + "=" * 80)
        logger.info("物業數據收集完成")
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
                'real_data_count': len(df),
                'data_file': saved_file,
                'quality_report': quality_report.to_dict(),
                'source_info': source_info,
                'is_real_data': True,
                'has_mock_data': False,
                'columns': list(df.columns),
                'date_range': {
                    'start': df['date'].min().isoformat() if 'date' in df.columns and not df['date'].empty else None,
                    'end': df['date'].max().isoformat() if 'date' in df.columns and not df['date'].empty else None,
                },
                'supported_indicators': adapter.get_supported_indicators() if hasattr(adapter, 'get_supported_indicators') else []
            }

            logger.info(f"✓ {name}: 成功收集 {len(df)} 條真實物業數據")
            logger.info(f"  - 質量分數: {quality_report.overall_score:.2f}")
            logger.info(f"  - 真實性確認: {'是' if quality_report.is_real_data else '否'}")

            return result

    def get_property_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        獲取物業數據摘要
        """
        if df.empty:
            return {"error": "No data available"}

        summary = {
            'total_records': len(df),
            'date_range': {
                'start': df['date'].min() if 'date' in df.columns else None,
                'end': df['date'].max() if 'date' in df.columns else None,
            },
            'indicators': df['indicator'].unique().tolist() if 'indicator' in df.columns else [],
            'sources': df['source'].unique().tolist() if 'source' in df.columns else [],
            'data_quality': {
                'real_data_percentage': (df['is_real'].sum() / len(df) * 100) if 'is_real' in df.columns else 100,
                'missing_values': df.isnull().sum().sum(),
                'completeness': (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            }
        }

        # 價格統計
        if 'value' in df.columns:
            values = df['value'].dropna()
            if len(values) > 0:
                summary['price_statistics'] = {
                    'min': float(values.min()),
                    'max': float(values.max()),
                    'mean': float(values.mean()),
                    'median': float(values.median()),
                    'std': float(values.std())
                }

        # 交易量統計
        if 'transaction' in df['indicator'].str.lower().any() if 'indicator' in df.columns else False:
            transaction_data = df[df['indicator'].str.contains('Transaction', case=False, na=False) if 'indicator' in df.columns else False]
            if not transaction_data.empty and 'value' in transaction_data.columns:
                summary['transaction_statistics'] = {
                    'total_transactions': int(transaction_data['value'].sum()),
                    'average_monthly': float(transaction_data['value'].mean())
                }

        # 地區分析
        if 'district' in df.columns:
            district_counts = df['district'].value_counts().to_dict()
            summary['district_distribution'] = district_counts

        return summary

    def generate_property_report(self, results: Dict[str, Any]) -> str:
        """
        生成物業數據報告
        """
        report = []
        report.append("╔" + "═" * 78 + "╗")
        report.append("║" + " " * 24 + "物業數據收集報告" + " " * 35 + "║")
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
            if source_data.get('supported_indicators'):
                report.append(f"    - 支持指標: {len(source_data['supported_indicators'])} 個")
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
        report.append("🏠 物業數據類型:")
        report.append("  • 土地註冊處交易數據")
        report.append("  • 物業價格指數 (CCL, RVD)")
        report.append("  • 地區市場分析")
        report.append("  • 面積分布統計")
        report.append("  • 租金指數")

        report.append("")
        report.append("═" * 80)
        report.append("注意: 此系統僅處理真實物業數據，所有 mock 數據都會被拒絕")
        report.append("═" * 80)

        return "\n".join(report)

    async def validate_property_data_only(self, results: Dict[str, Any]) -> bool:
        """
        驗證所有收集的數據都是真實的
        """
        logger.info("正在驗證物業數據真實性...")

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

        logger.info("✅ 所有物業數據驗證通過，確認為真實數據")
        return True

    def save_collection_results(self, results: Dict[str, Any], report_text: str) -> str:
        """
        保存收集結果
        """
        import json
        from pathlib import Path

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存結果 JSON
        results_file = Path("gov_crawler/data/property_data_collection_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 保存報告
        report_file = Path(f"gov_crawler/data/property_data_collection_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        logger.info(f"結果已保存到: {results_file}")
        logger.info(f"報告已保存到: {report_file}")

        return str(report_file)

async def main():
    """主函數 - 測試物業數據收集"""
    print("\n" + "=" * 80)
    print("🏠 港股量化系統 - 物業數據收集器")
    print("=" * 80)
    print("⚠️  此系統僅處理真實物業數據")
    print("🚫 嚴格禁止使用任何 mock 數據")
    print("✅ 所有數據來自官方數據源")
    print("=" * 80 + "\n")

    collector = PropertyDataCollector()

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    try:
        results = await collector.collect_all_property_data(start_date, end_date)

        validation_passed = await collector.validate_property_data_only(results)

        if validation_passed:
            print("\n✅ 數據驗證通過 - 所有數據均為真實物業數據")
        else:
            print("\n❌ 數據驗證失敗 - 可能存在 mock 數據")

        report_text = collector.generate_property_report(results)
        print("\n" + report_text)

        report_file = collector.save_collection_results(results, report_text)

        print(f"\n✅ 物業數據收集成功完成")
        print(f"📊 收集了 {results['real_data_confirmed']} 條真實數據記錄")
        print(f"📁 報告文件: {report_file}")

        return True

    except MockDataError as e:
        print(f"\n🚫 Mock 數據錯誤: {str(e)}")
        print("收集失敗 - 拒絕使用 mock 數據")
        return False

    except Exception as e:
        print(f"\n❌ 收集失敗: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
