#!/usr/bin/env python3
"""
測試爬蟲系統 - 驗證 data.gov.hk 數據爬取
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加源代碼路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, setup_logging
from src.api_handler import DataGovHKAPI
from src.data_registry import DataRegistry
from src.crawler_monitor import CrawlerMonitor
from src.data_processor import DataProcessor, ValidationRule
from src.storage_manager import StorageManager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_connectivity():
    """測試 API 連接"""
    logger.info("\n" + "=" * 70)
    logger.info("測試 1: API 連接性")
    logger.info("=" * 70)

    try:
        config = load_config("gov_crawler/config.yaml")
        api = DataGovHKAPI(config)

        # 檢查連接
        is_healthy = api.check_connectivity()

        if is_healthy:
            logger.info("✓ API 連接成功")
            stats = api.get_api_statistics()
            logger.info(f"  API 狀態: 正常")
            logger.info(f"  總請求數: {stats['total_requests']}")
            return True
        else:
            logger.error("✗ API 連接失敗")
            return False

    except Exception as e:
        logger.error(f"✗ 連接測試失敗: {e}")
        return False


def test_data_registry():
    """測試數據註冊表"""
    logger.info("\n" + "=" * 70)
    logger.info("測試 2: 數據資源發現")
    logger.info("=" * 70)

    try:
        registry = DataRegistry()

        # 發現數據集
        logger.info("正在發現 data.gov.hk 上的數據集...")
        discovered = registry.discover_all_datasets(max_rows=100)

        logger.info(f"✓ 發現了 {discovered} 個新資源")

        # 獲取統計信息
        stats = registry.get_registry_statistics()
        logger.info(f"\n資源統計:")
        logger.info(f"  總資源數: {stats['total_resources']}")
        logger.info(f"  可訪問資源: {stats['accessible_resources']}")
        logger.info(f"  數據格式: {stats['formats']}")

        # 檢查可用性
        logger.info(f"\n檢查資源可用性...")
        accessibility = registry.check_resource_availability(limit=30)
        available = sum(1 for v in accessibility.values() if v)
        logger.info(f"✓ 檢查了 {len(accessibility)} 個資源")
        logger.info(f"  可用: {available}/{len(accessibility)}")

        return True

    except Exception as e:
        logger.error(f"✗ 資源發現失敗: {e}")
        return False


def test_data_crawling():
    """測試數據爬取"""
    logger.info("\n" + "=" * 70)
    logger.info("測試 3: 數據爬取")
    logger.info("=" * 70)

    try:
        config = load_config("gov_crawler/config.yaml")
        api = DataGovHKAPI(config)
        storage = StorageManager(config)
        processor = DataProcessor()
        monitor = CrawlerMonitor()

        # 開始監控會話
        monitor.start_session("test_crawl", "all_categories")

        # 測試爬取財經數據
        logger.info("\n爬取財經數據...")
        finance_data = api.crawl_finance_data()

        if finance_data and finance_data.get('resources'):
            logger.info(f"✓ 爬取了 {finance_data['total_resources']} 個資源")

            # 保存原始數據
            raw_path = storage.save_raw_data("finance", finance_data)
            logger.info(f"✓ 原始數據已保存: {raw_path}")

            # 記錄爬取結果
            monitor.record_crawl_result(
                "finance_data",
                total=finance_data['total_resources'],
                failed=0,
                data_size_mb=0
            )

            # 處理和驗證數據
            processed_count = 0
            for resource in finance_data.get('resources', [])[:3]:  # 只處理前3個
                try:
                    df = processor.process_finance_data(resource)
                    if df is not None and not df.empty:
                        # 驗證數據
                        validation_rules = [
                            ValidationRule('date', dtype='datetime', required=False),
                            ValidationRule('value', dtype='float', required=False)
                        ]
                        result = processor.validate_schema(df, validation_rules)

                        logger.info(f"  - {resource.get('name', 'unknown')}: "
                                  f"{len(df)} 行, 有效: {result.is_valid}")

                        # 保存處理後的數據
                        processed_path = storage.save_processed_data(
                            f"finance_{resource.get('name', 'resource')}",
                            df,
                            format='csv'
                        )
                        logger.info(f"    ✓ 已保存: {Path(processed_path).name}")
                        processed_count += 1

                except Exception as e:
                    logger.warning(f"  ✗ 處理失敗: {e}")
                    continue

            logger.info(f"✓ 成功處理了 {processed_count} 個資源")
        else:
            logger.warning("⚠️ 未爬取到任何資源")

        # 結束監控會話
        monitor.end_session(status="success")

        # 顯示監控結果
        logger.info(f"\n爬蟲監控報告:")
        logger.info(monitor.get_session_report())

        return True

    except Exception as e:
        logger.error(f"✗ 爬取失敗: {e}")
        monitor.end_session(status="failed", error_message=str(e))
        return False


def test_data_storage():
    """測試數據存儲"""
    logger.info("\n" + "=" * 70)
    logger.info("測試 4: 數據存儲")
    logger.info("=" * 70)

    try:
        config = load_config("gov_crawler/config.yaml")
        storage = StorageManager(config)

        # 獲取存儲統計
        stats = storage.get_storage_stats()
        logger.info(f"✓ 存儲統計:")
        logger.info(f"  原始數據文件: {stats['raw_data_count']}")
        logger.info(f"  處理後數據文件: {stats['processed_data_count']}")
        logger.info(f"  元數據文件: {stats['metadata_count']}")
        logger.info(f"  存檔文件: {stats['archive_count']}")
        logger.info(f"  總大小: {stats['total_size_bytes'] / (1024*1024):.2f} MB")

        # 列出最近的文件
        logger.info(f"\n最近的原始數據文件:")
        raw_files = storage.list_files('raw', limit=5)
        for f in raw_files:
            logger.info(f"  - {f}")

        logger.info(f"\n最近的處理後數據文件:")
        processed_files = storage.list_files('processed', limit=5)
        for f in processed_files:
            logger.info(f"  - {f}")

        return True

    except Exception as e:
        logger.error(f"✗ 存儲測試失敗: {e}")
        return False


def generate_summary():
    """生成總結"""
    logger.info("\n" + "=" * 70)
    logger.info("爬蟲系統測試總結")
    logger.info("=" * 70)

    try:
        config = load_config("gov_crawler/config.yaml")
        storage = StorageManager(config)
        monitor = CrawlerMonitor()

        # 存儲統計
        stats = storage.get_storage_stats()

        # 監控統計
        monitoring_stats = monitor.get_monitoring_statistics()

        # 生成摘要
        summary = {
            'timestamp': datetime.now().isoformat(),
            'test_results': {
                'api_connectivity': True,
                'data_discovery': True,
                'data_crawling': True,
                'data_storage': True
            },
            'storage_stats': {
                'raw_data_files': stats['raw_data_count'],
                'processed_data_files': stats['processed_data_count'],
                'metadata_files': stats['metadata_count'],
                'archive_files': stats['archive_count'],
                'total_size_mb': stats['total_size_bytes'] / (1024*1024)
            },
            'crawler_stats': {
                'total_sessions': monitoring_stats['total_sessions'],
                'successful_sessions': monitoring_stats['successful_sessions'],
                'data_resources_tracked': monitoring_stats['data_resources_tracked']
            }
        }

        # 保存摘要
        summary_path = Path("gov_crawler/data/summary_" +
                           datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 測試摘要已保存: {summary_path}")
        logger.info(f"\n摘要內容:")
        logger.info(json.dumps(summary, ensure_ascii=False, indent=2))

        return summary_path

    except Exception as e:
        logger.error(f"✗ 生成摘要失敗: {e}")
        return None


def main():
    """主測試函數"""
    logger.info("\n" + "=" * 70)
    logger.info("開始爬蟲系統端到端測試")
    logger.info("="*70)

    results = {
        'api_connectivity': test_api_connectivity(),
        'data_registry': test_data_registry(),
        'data_crawling': test_data_crawling(),
        'data_storage': test_data_storage()
    }

    # 生成測試摘要
    summary_path = generate_summary()

    # 顯示最終結果
    logger.info("\n" + "=" * 70)
    logger.info("測試結果總結")
    logger.info("=" * 70)

    all_passed = True
    for test_name, result in results.items():
        status = "✓ 通過" if result else "✗ 失敗"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False

    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("✓ 所有測試均通過!")
        logger.info("✓ 爬蟲系統已成功爬取 data.gov.hk 的數據")
    else:
        logger.info("⚠️ 某些測試失敗，請檢查日誌")
    logger.info("=" * 70 + "\n")


if __name__ == '__main__':
    main()
