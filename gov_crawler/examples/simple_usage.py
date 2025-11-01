#!/usr/bin/env python3
"""
GOV 爬蟲 - 簡單使用示例
"""

import sys
from pathlib import Path

# 添加源代碼路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, setup_logging
from src.api_handler import DataGovHKAPI
from src.data_processor import DataProcessor
from src.storage_manager import StorageManager


def example_1_basic_crawl():
    """示例 1: 基本爬蟲使用"""
    print("=" * 60)
    print("示例 1: 基本爬蟲使用")
    print("=" * 60)

    # 加載配置
    config = load_config('config.yaml')
    logger = setup_logging(config['crawler'])

    # 初始化 API
    api = DataGovHKAPI(config)

    # 爬取 GDP 數據
    print("\n正在爬取 GDP 數據...")
    gdp_data = api.fetch_gdp_data()

    if gdp_data:
        print(f"✓ 成功爬取 {gdp_data['total_count']} 條記錄")
        print(f"  資源 ID: {gdp_data['resource_id']}")
        print(f"  時間戳: {gdp_data['timestamp']}")

        # 顯示前 3 條記錄
        print("\n前 3 條記錄:")
        for i, record in enumerate(gdp_data['records'][:3]):
            print(f"  {i+1}. {record}")
    else:
        print("✗ 爬蟲失敗")

    api.close()


def example_2_process_data():
    """示例 2: 數據處理"""
    print("\n" + "=" * 60)
    print("示例 2: 數據處理")
    print("=" * 60)

    # 加載配置
    config = load_config('config.yaml')
    logger = setup_logging(config['crawler'])

    # 初始化
    api = DataGovHKAPI(config)
    processor = DataProcessor()

    # 爬取並處理 GDP 數據
    print("\n正在爬取並處理 GDP 數據...")
    gdp_data = api.fetch_gdp_data()

    if gdp_data:
        df = processor.process_finance_data(gdp_data)

        if not df.empty:
            print(f"✓ 處理完成，共 {len(df)} 行")
            print(f"  列: {list(df.columns)}")
            print(f"\n數據預覽:")
            print(df.head())

            # 計算統計
            stats = processor.calculate_statistics(df)
            print(f"\n統計信息:")
            print(f"  行數: {stats['row_count']}")
            print(f"  列數: {stats['column_count']}")
            print(f"  缺失值: {sum(stats['missing_values'].values())}")

            # 驗證質量
            quality = processor.validate_data_quality(df)
            print(f"\n數據質量:")
            print(f"  有效: {quality['is_valid']}")
            print(f"  缺失值比例: {quality['missing_values_ratio']:.2%}")
            print(f"  重複行: {quality['duplicate_rows']}")
        else:
            print("✗ 數據處理失敗")
    else:
        print("✗ 數據爬蟲失敗")

    api.close()


def example_3_storage():
    """示例 3: 數據存儲"""
    print("\n" + "=" * 60)
    print("示例 3: 數據存儲")
    print("=" * 60)

    # 加載配置
    config = load_config('config.yaml')
    logger = setup_logging(config['crawler'])

    # 初始化
    api = DataGovHKAPI(config)
    processor = DataProcessor()
    storage = StorageManager(config)

    # 爬取、處理、存儲
    print("\n正在爬取 GDP 數據...")
    gdp_data = api.fetch_gdp_data()

    if gdp_data:
        # 保存原始數據
        print("  保存原始數據...")
        raw_file = storage.save_raw_data('gdp_example', gdp_data)
        print(f"  ✓ 已保存: {raw_file}")

        # 處理數據
        print("  處理數據...")
        df = processor.process_finance_data(gdp_data)

        if not df.empty:
            # 保存處理後的數據
            print("  保存處理後的數據...")
            csv_file = storage.save_processed_data('gdp_example', df, format='csv')
            json_file = storage.save_processed_data('gdp_example', df, format='json')
            print(f"  ✓ CSV: {csv_file}")
            print(f"  ✓ JSON: {json_file}")

            # 保存元信息
            print("  保存元信息...")
            metadata = {
                'dataset_name': 'gdp_example',
                'total_records': len(df),
                'source': 'gov.hk',
                'columns': list(df.columns)
            }
            meta_file = storage.save_metadata('gdp_example', metadata)
            print(f"  ✓ 元信息: {meta_file}")

            # 顯示存儲統計
            print("\n存儲統計:")
            stats = storage.get_storage_stats()
            for key, value in stats.items():
                if key == 'total_size_bytes':
                    size_mb = value / (1024 * 1024)
                    print(f"  {key}: {size_mb:.2f} MB")
                else:
                    print(f"  {key}: {value}")
    else:
        print("✗ 爬蟲失敗")

    api.close()


def example_4_search_datasets():
    """示例 4: 搜索數據集"""
    print("\n" + "=" * 60)
    print("示例 4: 搜索數據集")
    print("=" * 60)

    # 加載配置
    config = load_config('config.yaml')
    logger = setup_logging(config['crawler'])

    # 初始化 API
    api = DataGovHKAPI(config)

    # 搜索與房產相關的數據集
    print("\n搜索 '房產' 相關的數據集...")
    results = api.search_datasets('房產')

    if results:
        print(f"✓ 找到 {len(results)} 個數據集\n")
        for i, dataset in enumerate(results[:5], 1):
            print(f"{i}. {dataset.get('title', 'N/A')}")
            print(f"   組織: {dataset.get('organization', {}).get('title', 'N/A')}")
            print(f"   資源數: {len(dataset.get('resources', []))}")
    else:
        print("✗ 未找到相關數據集")

    api.close()


def example_5_load_and_analyze():
    """示例 5: 加載和分析存儲的數據"""
    print("\n" + "=" * 60)
    print("示例 5: 加載和分析存儲的數據")
    print("=" * 60)

    # 加載配置
    config = load_config('config.yaml')
    logger = setup_logging(config['crawler'])

    # 初始化存儲管理器
    storage = StorageManager(config)

    # 加載元信息
    print("\n正在加載存儲的數據...")
    metadata = storage.load_metadata('gdp_example')

    if metadata:
        print(f"✓ 找到元信息")
        print(f"  數據集: {metadata.get('dataset_name')}")
        print(f"  記錄數: {metadata.get('total_records')}")
        print(f"  列: {metadata.get('columns')}")

        # 加載處理後的數據
        print("\n正在加載處理後的數據...")
        df = storage.load_processed_data('gdp_example', format='csv')

        if df is not None:
            print(f"✓ 成功加載 {len(df)} 行數據")
            print(f"\n數據預覽:")
            print(df.head(3))
        else:
            print("✗ 未找到處理後的數據")
    else:
        print("✗ 未找到元信息")

    # 列出所有可用文件
    print("\n可用的原始數據文件:")
    raw_files = storage.list_files('raw', limit=10)
    for f in raw_files:
        print(f"  - {f}")

    print("\n可用的處理數據文件:")
    processed_files = storage.list_files('processed', limit=10)
    for f in processed_files:
        print(f"  - {f}")


def main():
    """主函數"""
    print("""
╔══════════════════════════════════════════════════════════╗
║          GOV 爬蟲 - 使用示例                            ║
╚══════════════════════════════════════════════════════════╝

請選擇要運行的示例:
1. 基本爬蟲使用
2. 數據處理
3. 數據存儲
4. 搜索數據集
5. 加載和分析存儲的數據
6. 運行所有示例
0. 退出
    """)

    choice = input("請輸入選項 (0-6): ").strip()

    try:
        if choice == '1':
            example_1_basic_crawl()
        elif choice == '2':
            example_2_process_data()
        elif choice == '3':
            example_3_storage()
        elif choice == '4':
            example_4_search_datasets()
        elif choice == '5':
            example_5_load_and_analyze()
        elif choice == '6':
            example_1_basic_crawl()
            example_2_process_data()
            example_3_storage()
            example_4_search_datasets()
            example_5_load_and_analyze()
        elif choice == '0':
            print("退出")
            return
        else:
            print("無效選項")
            return

        print("\n✓ 示例執行完成")

    except KeyboardInterrupt:
        print("\n\n程序被中斷")
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
