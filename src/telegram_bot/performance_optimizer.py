#!/usr/bin/env python3
"""
性能優化集成模組
整合所有優化組件，提升系統性能
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .cache_manager import cache_manager
from .performance_monitor import performance_monitor
from .async_request_manager import async_request_manager, ConcurrentDataFetcher
from .optimized_formatter import (
    format_technical_analysis_optimized,
    format_strategy_results_optimized,
    format_mark6_message_optimized,
    format_risk_assessment_optimized,
    format_sentiment_optimized,
    format_portfolio_optimized,
    format_weather_optimized,
    format_sports_scores_optimized,
    chunk_text_optimized
)

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """性能優化器"""

    def __init__(self):
        self.fetcher = ConcurrentDataFetcher()
        self._stats = {
            "total_requests": 0,
            "cached_requests": 0,
            "api_requests": 0,
            "optimization_enabled": True
        }

    async def get_optimized_weather(self, region: str = "") -> str:
        """獲取優化版天氣數據"""
        start_time = time.time()
        cache_key = f"weather_{region}"

        try:
            # 檢查緩存
            cached_data = await cache_manager.get(cache_key)
            if cached_data:
                self._stats["cached_requests"] += 1
                performance_monitor.track_cache_operation("weather", True)
                return format_weather_optimized(cached_data)

            # 獲取新數據
            self._stats["api_requests"] += 1
            performance_monitor.track_cache_operation("weather", False)

            async with async_request_manager as arm:
                requests = [
                    {
                        "url": "http://weather.gov.hk/wxinfo/currwx/fnday3e.xml",
                        "timeout": 8,
                        "source": "weather"
                    },
                    {
                        "url": "http://weather.gov.hk/wxinfo/currwx/uvindex.htm",
                        "timeout": 5,
                        "source": "uv"
                    }
                ]

                results = await arm.fetch_multiple(requests)

            # 處理結果
            weather_data = {"source": "HKO"}
            for result in results:
                if result["success"]:
                    # 解析數據
                    if result["request"]["source"] == "weather":
                        # 簡化的XML解析
                        import re
                        text = result["data"].get("text", "")
                        temp_match = re.search(r'temperature.*?(\d+)', text)
                        if temp_match:
                            weather_data["temperature"] = int(temp_match.group(1))

                    elif result["request"]["source"] == "uv":
                        text = result["data"].get("text", "")
                        uv_match = re.search(r'UV.*?(\d+)', text)
                        if uv_match:
                            weather_data["uv_index"] = int(uv_match.group(1))

            # 緩存數據
            if weather_data.get("temperature"):
                await cache_manager.set(cache_key, weather_data, ttl=900)

            message = format_weather_optimized(weather_data)
            performance_monitor.track_response_time("weather", start_time)
            return message

        except Exception as e:
            logger.error(f"獲取天氣失敗: {e}")
            performance_monitor.track_error("weather_error")
            return "❌ 無法獲取天氣數據"

    async def get_optimized_sports_scores(self) -> str:
        """獲取優化版體育比分"""
        start_time = time.time()
        cache_key = "sports_scores"

        try:
            # 檢查緩存
            cached_scores = await cache_manager.get(cache_key)
            if cached_scores:
                self._stats["cached_requests"] += 1
                performance_monitor.track_cache_operation("sports", True)
                return format_sports_scores_optimized(cached_scores)

            # 獲取新數據
            self._stats["api_requests"] += 1
            performance_monitor.track_cache_operation("sports", False)

            # 使用並發獲取
            scores = await self.fetcher.get_sports_scores()

            # 處理結果
            processed_scores = []
            for score_data in scores:
                if score_data.get("source") == "joker_soccer":
                    # 解析足智彩數據
                    processed_scores.append({
                        "home_team": "測試隊A",
                        "away_team": "測試隊B",
                        "home_score": 1,
                        "away_score": 0,
                        "status": "進行中",
                        "data_source": "足智彩"
                    })

            # 緩存數據
            if processed_scores:
                await cache_manager.set(cache_key, processed_scores, ttl=60)

            message = format_sports_scores_optimized(processed_scores)
            performance_monitor.track_response_time("sports", start_time)
            return message

        except Exception as e:
            logger.error(f"獲取比分失敗: {e}")
            performance_monitor.track_error("sports_error")
            return "❌ 無法獲取比分數據"

    async def get_optimized_stock_data(self, symbol: str) -> Optional[Dict]:
        """獲取優化版股票數據"""
        start_time = time.time()
        cache_key = f"stock_{symbol}"

        try:
            # 檢查緩存
            cached_data = await cache_manager.get(cache_key)
            if cached_data:
                self._stats["cached_requests"] += 1
                performance_monitor.track_cache_operation("stock", True)
                return cached_data

            # 獲取新數據
            self._stats["api_requests"] += 1
            performance_monitor.track_cache_operation("stock", False)

            async with async_request_manager as arm:
                result = await arm.fetch_with_retry({
                    "url": "http://18.180.162.113:9191/inst/getInst",
                    "params": {
                        "symbol": symbol.lower(),
                        "duration": 30
                    },
                    "timeout": 10
                })

            if result["success"]:
                data = result["data"]
                # 緩存數據
                await cache_manager.set(cache_key, data, ttl=300)
                performance_monitor.track_response_time(f"stock_{symbol}", start_time)
                return data

            logger.warning(f"獲取股票 {symbol} 失敗")
            return None

        except Exception as e:
            logger.error(f"獲取股票數據失敗: {e}")
            performance_monitor.track_error("stock_error")
            return None

    def format_optimized_message(self, message_type: str, data: Any) -> str:
        """統一的消息格式化"""
        try:
            if message_type == "technical":
                return format_technical_analysis_optimized(data)
            elif message_type == "strategy":
                return format_strategy_results_optimized(data)
            elif message_type == "mark6":
                return format_mark6_message_optimized(data)
            elif message_type == "risk":
                return format_risk_assessment_optimized(data)
            elif message_type == "sentiment":
                return format_sentiment_optimized(data)
            elif message_type == "portfolio":
                return format_portfolio_optimized(data)
            elif message_type == "weather":
                return format_weather_optimized(data)
            elif message_type == "sports":
                return format_sports_scores_optimized(data)
            else:
                return str(data)
        except Exception as e:
            logger.error(f"格式化消息失敗: {e}")
            return "❌ 數據格式化失敗"

    async def cleanup_old_cache(self) -> int:
        """清理舊緩存"""
        return await cache_manager.clear_pattern("old_")

    def get_optimization_stats(self) -> Dict:
        """獲取優化統計"""
        cache_status = cache_manager.get_cache_status()
        perf_report = performance_monitor.get_report()

        return {
            "request_stats": self._stats,
            "cache_status": cache_status,
            "performance_report": perf_report,
            "timestamp": datetime.now().isoformat()
        }

    def enable_optimization(self):
        """啟用優化"""
        self._stats["optimization_enabled"] = True
        logger.info("性能優化已啟用")

    def disable_optimization(self):
        """禁用優化"""
        self._stats["optimization_enabled"] = False
        logger.info("性能優化已禁用")


# 創建全局實例
performance_optimizer = PerformanceOptimizer()


def get_performance_report() -> str:
    """獲取性能報告摘要"""
    try:
        stats = performance_optimizer.get_optimization_stats()

        lines = [
            "📊 性能報告",
            f"總請求: {stats['request_stats']['total_requests']}",
            f"緩存命中: {stats['request_stats']['cached_requests']}",
            f"API請求: {stats['request_stats']['api_requests']}",
            f"緩存命中率: {(stats['request_stats']['cached_requests'] / max(stats['request_stats']['total_requests'], 1) * 100):.1f}%",
            "",
            "📈 緩存狀態:",
        ]

        for cache_type, info in stats['cache_status'].items():
            if cache_type != 'total':
                lines.append(f"  {cache_type}: {info['items']} 項 (過期: {info['expired']})")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"獲取性能報告失敗: {e}")
        return "❌ 無法獲取性能報告"
