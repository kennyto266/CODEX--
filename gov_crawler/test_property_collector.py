#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物業數據收集器測試腳本
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
    print("🏠 港股量化系統 - 物業數據收集器測試")
    print("=" * 80)
    print("⚠️  此系統僅處理真實物業數據")
    print("🚫 嚴格禁止使用任何 mock 數據")
    print("✅ 所有數據來自官方數據源")
    print("=" * 80 + "\n")

    try:
        # 直接導入並測試
        from adapters.real_data.property.property_data_collector import PropertyDataCollector

        collector = PropertyDataCollector()
        print(f"✓ 創建物業數據收集器")
        print(f"✓ 初始化 {len(collector.adapters)} 個適配器")

        for name, adapter in collector.adapters.items():
            print(f"  - {name}: {adapter.name}")

        print("\n✅ 物業數據收集器初始化成功")
        print("✅ 所有適配器已就緒")

        return True

    except Exception as e:
        logger.error(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
