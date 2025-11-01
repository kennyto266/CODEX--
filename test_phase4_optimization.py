#!/usr/bin/env python3
"""
Phase 4 性能優化測試腳本
驗證所有優化功能
"""

import sys
import asyncio
import time

sys.path.insert(0, '/c/Users/Penguin8n/CODEX--/CODEX--/src')
sys.path.insert(0, '/c/Users/Penguin8n/CODEX--/CODEX--/src/telegram_bot')

print("Phase 4 性能優化測試")
print("=" * 60)

# 測試1: 緩存管理
print("\n測試 1: 緩存管理...")
try:
    from cache_manager import cache_manager
    print(f"[PASS] 緩存管理器: {type(cache_manager).__name__}")
    
    # 測試緩存
    import asyncio
    asyncio.run(cache_manager.set("test", {"value": "test"}, 10))
    result = asyncio.run(cache_manager.get("test"))
    if result and result.get("value") == "test":
        print("[PASS] 緩存設置和獲取正常工作")
    else:
        print("[FAIL] 緩存功能異常")
except Exception as e:
    print(f"[FAIL] 緩存管理錯誤: {e}")

# 測試2: 性能監控
print("\n測試 2: 性能監控...")
try:
    from performance_monitor import performance_monitor
    print(f"[PASS] 性能監控器: {type(performance_monitor).__name__}")
    
    # 測試追蹤
    start = time.time()
    time.sleep(0.1)
    performance_monitor.track_command("test_cmd", start)
    
    report = performance_monitor.get_report()
    if "commands" in report:
        print("[PASS] 性能追蹤正常工作")
    else:
        print("[FAIL] 性能追蹤異常")
except Exception as e:
    print(f"[FAIL] 性能監控錯誤: {e}")

# 測試3: 異步請求管理
print("\n測試 3: 異步請求管理...")
try:
    from async_request_manager import async_request_manager
    print(f"[PASS] 異步請求管理: {type(async_request_manager).__name__}")
    
    # 測試會話
    if hasattr(async_request_manager, 'init_session'):
        print("[PASS] 異步請求管理包含init_session方法")
    else:
        print("[FAIL] 缺少init_session方法")
except Exception as e:
    print(f"[FAIL] 異步請求管理錯誤: {e}")

# 測試4: 優化格式化
print("\n測試 4: 優化格式化...")
try:
    from optimized_formatter import format_weather_optimized, format_mark6_message_optimized
    
    # 測試天氣格式化
    weather_data = {"temperature": 25, "humidity": 60, "weather": "晴天"}
    weather_msg = format_weather_optimized(weather_data)
    print(f"[PASS] 天氣格式化: {len(weather_msg)} 字符")
    
    # 測試Mark6格式化
    mark6_data = {"draw_no": "12345", "estimated_prize": "28000000"}
    mark6_msg = format_mark6_message_optimized(mark6_data)
    print(f"[PASS] Mark6格式化: {len(mark6_msg)} 字符")
    
    if len(weather_msg) < 400 and len(mark6_msg) < 200:
        print("[PASS] 響應格式已優化")
    else:
        print("[WARNING] 響應格式可能需要進一步優化")
        
except Exception as e:
    print(f"[FAIL] 格式化錯誤: {e}")

# 測試5: 性能優化器
print("\n測試 5: 性能優化器...")
try:
    from performance_optimizer import performance_optimizer
    print(f"[PASS] 性能優化器: {type(performance_optimizer).__name__}")
    
    # 測試統計
    stats = performance_optimizer.get_optimization_stats()
    if "request_stats" in stats:
        print("[PASS] 優化統計正常工作")
    else:
        print("[FAIL] 優化統計異常")
except Exception as e:
    print(f"[FAIL] 性能優化器錯誤: {e}")

# 測試6: 集成測試
print("\n測試 6: 集成測試...")
try:
    # 測試緩存和性能監控的整合
    from cache_manager import cache_manager
    from performance_monitor import performance_monitor
    
    async def test_integration():
        start = time.time()
        await cache_manager.set("integration_test", {"test": "data"}, 60)
        data = await cache_manager.get("integration_test")
        performance_monitor.track_command("integration_test", start)
        return data is not None
    
    result = asyncio.run(test_integration())
    if result:
        print("[PASS] 緩存和性能監控集成正常")
    else:
        print("[FAIL] 集成測試失敗")
        
except Exception as e:
    print(f"[FAIL] 集成測試錯誤: {e}")

print("\n" + "=" * 60)
print("Phase 4 性能優化測試完成")
print("=" * 60)
