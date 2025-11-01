#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物業數據收集運行腳本
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加路徑
sys.path.append(str(Path(__file__).parent))

# 設置控制台輸出編碼
sys.stdout.reconfigure(encoding='utf-8')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """主函數"""
    print("\n" + "=" * 80)
    print("物業數據收集器 - 運行測試")
    print("=" * 80)
    print("僅處理真實物業數據")
    print("嚴格禁止 mock 數據")
    print("=" * 80 + "\n")

    try:
        # 直接導入並測試
        from adapters.real_data.property.property_data_collector import PropertyDataCollector

        collector = PropertyDataCollector()
        print(f"創建物業數據收集器")
        print(f"初始化 {len(collector.adapters)} 個適配器")

        for name, adapter in collector.adapters.items():
            print(f"  - {name}: {adapter.name}")

        print("\n物業數據收集器就緒！")
        print("可以開始收集數據...")

        # 測試數據收集 (使用較短的時間範圍)
        end_date = '2025-10-27'
        start_date = '2025-10-01'

        print(f"\n開始測試數據收集 ({start_date} 到 {end_date})...")

        results = await collector.collect_all_property_data(start_date, end_date)

        print(f"\n收集結果:")
        print(f"  - 成功: {results['successful_collections']}/{results['adapters_count']}")
        print(f"  - 失敗: {results['failed_collections']}")
        print(f"  - 拒絕 mock 數據: {results['mock_data_rejected']}")
        print(f"  - 確認真實數據: {results['real_data_confirmed']} 條記錄")

        # 驗證數據
        validation_passed = await collector.validate_property_data_only(results)

        if validation_passed:
            print("\n數據驗證通過 - 所有數據均為真實數據")
        else:
            print("\n數據驗證失敗 - 可能存在問題")

        # 生成報告
        report_text = collector.generate_property_report(results)
        print("\n" + report_text)

        # 保存結果
        report_file = collector.save_collection_results(results, report_text)

        print(f"\n數據收集成功完成")
        print(f"報告文件: {report_file}")

        return True

    except Exception as e:
        logger.error(f"收集失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
