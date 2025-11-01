#!/usr/bin/env python3
"""
GOV 爬蟲系統 - 主程序
香港政府開放數據爬蟲，為量化交易系統收集替代數據
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# 添加源代碼路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, setup_logging, create_directories, ProgressTracker
from src.api_handler import DataGovHKAPI
from src.data_processor import DataProcessor
from src.storage_manager import StorageManager


class GovCrawler:
    """主爬蟲類"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化爬蟲

        Args:
            config_path: 配置文件路徑
        """
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config['crawler'])

        # 創建目錄
        storage_dirs = {
            'raw_data_dir': self.config['storage']['raw_data_dir'],
            'processed_data_dir': self.config['storage']['processed_data_dir'],
            'metadata_dir': self.config['storage']['metadata_dir'],
            'archive_dir': self.config['storage']['archive_dir']
        }
        create_directories(storage_dirs)

        # 初始化各個模塊
        self.api = DataGovHKAPI(self.config)
        self.processor = DataProcessor()
        self.storage = StorageManager(self.config)

        self.logger.info("=" * 60)
        self.logger.info("GOV 爬蟲系統啟動")
        self.logger.info("=" * 60)

    def crawl_finance_data(self) -> bool:
        """
        爬取財經數據

        Returns:
            成功狀態
        """
        if not self.config['datasets']['finance']['enabled']:
            self.logger.info("財經數據爬蟲已禁用")
            return False

        self.logger.info("=" * 60)
        self.logger.info("開始爬取財經數據...")
        self.logger.info("=" * 60)

        try:
            # 爬取財經數據
            finance_data = self.api.crawl_finance_data()
            if finance_data:
                # 保存原始數據
                self.storage.save_raw_data("finance", finance_data)

                # 處理數據
                for resource in finance_data.get('resources', []):
                    try:
                        df = self.processor.process_finance_data(resource)
                        if df is not None and not df.empty:
                            resource_name = resource.get('name', 'unknown')
                            self.storage.save_processed_data(f"finance_{resource_name}", df, format='csv')
                            self.storage.save_processed_data(f"finance_{resource_name}", df, format='json')

                            # 保存元信息
                            metadata = {
                                'dataset_name': f'finance_{resource_name}',
                                'total_records': len(df),
                                'data_quality': self.processor.validate_data_quality(df),
                                'columns': list(df.columns) if hasattr(df, 'columns') else []
                            }
                            self.storage.save_metadata(f"finance_{resource_name}", metadata)
                    except Exception as e:
                        self.logger.warning(f"無法處理財經資源: {e}")
                        continue

            self.logger.info("✓ 財經數據爬取完成")
            return True

        except Exception as e:
            self.logger.error(f"✗ 財經數據爬取失敗: {e}")
            return False

    def crawl_property_data(self) -> bool:
        """
        爬取物業市場數據

        Returns:
            成功狀態
        """
        if not self.config['datasets']['real_estate']['enabled']:
            self.logger.info("房產數據爬蟲已禁用")
            return False

        self.logger.info("=" * 60)
        self.logger.info("開始爬取物業市場數據...")
        self.logger.info("=" * 60)

        try:
            # 爬取地產數據
            property_data = self.api.crawl_real_estate_data()
            if property_data:
                # 保存原始數據
                self.storage.save_raw_data("real_estate", property_data)

                # 處理數據
                for resource in property_data.get('resources', []):
                    try:
                        df = self.processor.process_property_data(resource)
                        if df is not None and not df.empty:
                            resource_name = resource.get('name', 'unknown')
                            self.storage.save_processed_data(f"property_{resource_name}", df, format='csv')
                            self.storage.save_processed_data(f"property_{resource_name}", df, format='json')

                            # 保存元信息
                            metadata = {
                                'dataset_name': f'property_{resource_name}',
                                'total_records': len(df),
                                'data_quality': self.processor.validate_data_quality(df),
                                'columns': list(df.columns) if hasattr(df, 'columns') else []
                            }
                            self.storage.save_metadata(f"property_{resource_name}", metadata)
                    except Exception as e:
                        self.logger.warning(f"無法處理地產資源: {e}")
                        continue

            self.logger.info("✓ 物業市場數據爬取完成")
            return True

        except Exception as e:
            self.logger.error(f"✗ 物業市場數據爬取失敗: {e}")
            return False

    def crawl_retail_data(self) -> bool:
        """
        爬取零售業數據

        Returns:
            成功狀態
        """
        if not self.config['datasets']['business']['enabled']:
            self.logger.info("工商業數據爬蟲已禁用")
            return False

        self.logger.info("=" * 60)
        self.logger.info("開始爬取工商業數據...")
        self.logger.info("=" * 60)

        try:
            # 爬取工商業數據
            business_data = self.api.crawl_business_data()
            if business_data:
                # 保存原始數據
                self.storage.save_raw_data("business", business_data)

                # 處理數據
                for resource in business_data.get('resources', []):
                    try:
                        df = self.processor.process_retail_data(resource)
                        if df is not None and not df.empty:
                            resource_name = resource.get('name', 'unknown')
                            self.storage.save_processed_data(f"business_{resource_name}", df, format='csv')
                            self.storage.save_processed_data(f"business_{resource_name}", df, format='json')

                            # 保存元信息
                            metadata = {
                                'dataset_name': f'business_{resource_name}',
                                'total_records': len(df),
                                'data_quality': self.processor.validate_data_quality(df),
                                'columns': list(df.columns) if hasattr(df, 'columns') else []
                            }
                            self.storage.save_metadata(f"business_{resource_name}", metadata)
                    except Exception as e:
                        self.logger.warning(f"無法處理工商業資源: {e}")
                        continue

            self.logger.info("✓ 工商業數據爬取完成")
            return True

        except Exception as e:
            self.logger.error(f"✗ 工商業數據爬取失敗: {e}")
            return False

    def crawl_traffic_data(self) -> bool:
        """
        爬取交通數據

        Returns:
            成功狀態
        """
        if not self.config['datasets']['transport']['enabled']:
            self.logger.info("運輸數據爬蟲已禁用")
            return False

        self.logger.info("=" * 60)
        self.logger.info("開始爬取交通數據...")
        self.logger.info("=" * 60)

        try:
            # 爬取運輸數據
            transport_data = self.api.crawl_transport_data()
            if transport_data:
                # 保存原始數據
                self.storage.save_raw_data("transport", transport_data)

                # 處理數據
                for resource in transport_data.get('resources', []):
                    try:
                        df = self.processor.process_traffic_data(resource)
                        if df is not None and not df.empty:
                            resource_name = resource.get('name', 'unknown')
                            self.storage.save_processed_data(f"transport_{resource_name}", df, format='csv')
                            self.storage.save_processed_data(f"transport_{resource_name}", df, format='json')

                            # 保存元信息
                            metadata = {
                                'dataset_name': f'transport_{resource_name}',
                                'total_records': len(df),
                                'data_quality': self.processor.validate_data_quality(df),
                                'columns': list(df.columns) if hasattr(df, 'columns') else []
                            }
                            self.storage.save_metadata(f"transport_{resource_name}", metadata)
                    except Exception as e:
                        self.logger.warning(f"無法處理運輸資源: {e}")
                        continue

            self.logger.info("✓ 交通數據爬取完成")
            return True

        except Exception as e:
            self.logger.error(f"✗ 交通數據爬取失敗: {e}")
            return False

    def crawl_all(self) -> dict:
        """
        爬取所有數據

        Returns:
            爬取結果字典
        """
        results = {
            'finance': self.crawl_finance_data(),
            'property': self.crawl_property_data(),
            'retail': self.crawl_retail_data(),
            'traffic': self.crawl_traffic_data()
        }
        return results

    def show_statistics(self) -> None:
        """顯示統計信息"""
        self.logger.info("=" * 60)
        self.logger.info("存儲統計信息")
        self.logger.info("=" * 60)

        stats = self.storage.get_storage_stats()
        for key, value in stats.items():
            if key == 'total_size_bytes':
                # 轉換為易讀格式
                size = value / (1024 * 1024)
                self.logger.info(f"{key}: {size:.2f} MB")
            else:
                self.logger.info(f"{key}: {value}")

        # 列出最近的文件
        self.logger.info("\n最近的原始數據文件:")
        raw_files = self.storage.list_files('raw', limit=5)
        for f in raw_files:
            self.logger.info(f"  - {f}")

        self.logger.info("\n最近的處理數據文件:")
        processed_files = self.storage.list_files('processed', limit=5)
        for f in processed_files:
            self.logger.info(f"  - {f}")

    def cleanup(self) -> None:
        """清理過期數據"""
        self.logger.info("=" * 60)
        self.logger.info("清理過期數據...")
        self.logger.info("=" * 60)

        archived = self.storage.archive_old_data(days_old=30)
        self.logger.info(f"存檔了 {archived} 個舊文件")

        deleted = self.storage.cleanup_old_data(days_old=90)
        self.logger.info(f"刪除了 {deleted} 個過期文件")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='GOV 爬蟲系統 - 香港政府開放數據爬蟲',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main_crawler.py                    # 運行所有爬蟲
  python main_crawler.py --dataset finance  # 只運行財經爬蟲
  python main_crawler.py --stats            # 顯示統計信息
  python main_crawler.py --cleanup          # 清理過期數據
        """
    )

    parser.add_argument('--config', default='config.yaml',
                       help='配置文件路徑 (默認: config.yaml)')
    parser.add_argument('--dataset', choices=['finance', 'property', 'retail', 'traffic'],
                       help='運行特定的數據集爬蟲')
    parser.add_argument('--stats', action='store_true',
                       help='顯示存儲統計信息')
    parser.add_argument('--cleanup', action='store_true',
                       help='清理過期數據')

    args = parser.parse_args()

    try:
        # 初始化爬蟲
        crawler = GovCrawler(config_path=args.config)

        # 根據參數執行操作
        if args.cleanup:
            crawler.cleanup()
        elif args.stats:
            crawler.show_statistics()
        elif args.dataset:
            if args.dataset == 'finance':
                crawler.crawl_finance_data()
            elif args.dataset == 'property':
                crawler.crawl_property_data()
            elif args.dataset == 'retail':
                crawler.crawl_retail_data()
            elif args.dataset == 'traffic':
                crawler.crawl_traffic_data()
        else:
            # 爬取所有數據
            results = crawler.crawl_all()

            # 顯示結果
            crawler.logger.info("=" * 60)
            crawler.logger.info("爬取結果總結")
            crawler.logger.info("=" * 60)
            for dataset, success in results.items():
                status = "✓ 成功" if success else "✗ 失敗"
                crawler.logger.info(f"{dataset}: {status}")

            # 顯示統計
            crawler.show_statistics()

        crawler.logger.info("=" * 60)
        crawler.logger.info("GOV 爬蟲系統完成")
        crawler.logger.info("=" * 60)

    except KeyboardInterrupt:
        print("\n\n程序被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"發生錯誤: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
