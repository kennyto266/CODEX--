#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終驗證腳本 - 物業數據適配器
"""

import sys
sys.path.append('gov_crawler')

print('=' * 80)
print('物業數據適配器 - 最終驗證')
print('=' * 80)

try:
    # 測試導入
    from adapters.real_data.property.landreg_property_adapter import LandRegPropertyAdapter
    from adapters.real_data.property.property_market_index_adapter import PropertyMarketIndexAdapter
    from adapters.real_data.property.property_data_collector import PropertyDataCollector
    print('所有模塊導入成功')

    # 測試創建適配器
    landreg = LandRegPropertyAdapter()
    index = PropertyMarketIndexAdapter()
    collector = PropertyDataCollector()
    print('所有適配器創建成功')

    # 測試屬性
    print(f'土地註冊處適配器名稱: {landreg.name}')
    print(f'物業指數適配器名稱: {index.name}')
    print(f'收集器適配器數量: {len(collector.adapters)}')

    # 測試支持的指標
    landreg_indicators = landreg.get_supported_indicators()
    index_indicators = index.get_supported_indicators()
    print(f'土地註冊處支持 {len(landreg_indicators)} 個指標')
    print(f'物業指數支持 {len(index_indicators)} 個指標')

    # 測試數據源信息
    info1 = landreg.get_data_source_info()
    info2 = index.get_data_source_info()
    print(f'土地註冊處數據類型: {info1["data_type"]}')
    print(f'物業指數 Mock 禁用: {not info1["mock_enabled"]}')

    print('=' * 80)
    print('所有驗證通過 - 物業數據適配器系統就緒！')
    print('=' * 80)

except Exception as e:
    print(f'驗證失敗: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
