#!/usr/bin/env python3
"""
天氣服務測試腳本
"""

import asyncio
import sys
import os

# 設置路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'telegram_bot'))

async def test_weather_service():
    """測試天氣服務"""
    print("=" * 50)
    print("Telegram Bot 天氣服務測試")
    print("=" * 50)

    try:
        from weather_service import weather_service
        print("[1/3] 導入天氣服務... OK")

        # 獲取天氣數據
        data = await weather_service.get_current_weather()
        print("[2/3] 獲取天氣數據... OK")

        if data:
            # 格式化消息
            message = weather_service.format_weather_message(data, "香港島")
            print("[3/3] 格式化天氣消息... OK")

            print("\n" + "=" * 50)
            print("天氣報告預覽:")
            print("=" * 50)
            print(message[:800])  # 顯示前800字符
            if len(message) > 800:
                print("\n... (內容已截斷)")
            print("=" * 50)

            print(f"\n✅ 測試成功!")
            print(f"   數據源: {data.get('source', '未知')}")
            print(f"   時間: {data.get('timestamp', '未知')}")
            print(f"   溫度: {data.get('temperature', 'N/A')}°C")

        else:
            print("\n❌ 無法獲取天氣數據")

    except ImportError as e:
        print(f"\n❌ 導入錯誤: {e}")
        print("   請確保所有依賴已安裝")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_weather_service())
