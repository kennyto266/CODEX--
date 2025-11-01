"""
基礎爬蟲抽象類
為所有體育數據爬蟲提供統一接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import json


logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """基礎爬蟲抽象類"""

    def __init__(self, name: str):
        self.name = name
        self.last_update: Optional[datetime] = None
        self.update_count = 0
        self.error_count = 0

    @abstractmethod
    async def fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        獲取數據的抽象方法
        必須由子類實現

        Returns:
            Dict[str, Any]: 爬取的原始數據
        """
        pass

    @abstractmethod
    async def parse_data(self, raw_data: str) -> Dict[str, Any]:
        """
        解析數據的抽象方法
        必須由子類實現

        Args:
            raw_data: 原始 HTML 或 JSON 數據

        Returns:
            Dict[str, Any]: 解析後的結構化數據
        """
        pass

    async def scrape(self, **kwargs) -> Dict[str, Any]:
        """
        完整的爬取流程：獲取 -> 解析 -> 驗證

        Returns:
            Dict[str, Any]: 最終處理後的數據
        """
        try:
            logger.info(f"[{self.name}] 開始爬取數據...")
            raw_data = await self.fetch_data(**kwargs)

            if not raw_data:
                raise ValueError("未獲取到任何數據")

            logger.info(f"[{self.name}] 數據獲取成功，開始解析...")
            parsed_data = await self.parse_data(raw_data)

            if not parsed_data:
                raise ValueError("數據解析失敗，返回空結果")

            # 驗證數據
            validated_data = await self.validate_data(parsed_data)
            if not validated_data:
                logger.warning(f"[{self.name}] 數據驗證失敗")
                raise ValueError("數據驗證失敗")

            # 更新統計信息
            self.last_update = datetime.now()
            self.update_count += 1
            self.error_count = 0

            logger.info(f"[{self.name}] 爬取完成，數據條目數：{len(validated_data) if isinstance(validated_data, (list, dict)) else 'N/A'}")
            return validated_data

        except Exception as e:
            self.error_count += 1
            logger.error(f"[{self.name}] 爬取失敗：{str(e)}", exc_info=True)
            raise

    async def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證數據完整性
        子類可以重寫此方法以實現特定驗證邏輯

        Args:
            data: 待驗證的數據

        Returns:
            Dict[str, Any]: 驗證後的數據
        """
        # 基本驗證：確保數據不為空
        if not data:
            return None

        # 如果是列表，確保不為空
        if isinstance(data, list) and len(data) == 0:
            logger.warning(f"[{self.name}] 數據列表為空")
            return None

        return data

    def get_stats(self) -> Dict[str, Any]:
        """獲取爬蟲統計信息"""
        return {
            "name": self.name,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "update_count": self.update_count,
            "error_count": self.error_count,
            "success_rate": self.update_count / (self.update_count + self.error_count) if (self.update_count + self.error_count) > 0 else 0
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        stats = self.get_stats()

        # 檢查是否過久未更新 (超過 1 小時)
        is_stale = False
        if self.last_update:
            time_diff = datetime.now() - self.last_update
            is_stale = time_diff.total_seconds() > 3600  # 1小時

        # 檢查錯誤率 (超過 50%)
        high_error_rate = stats["error_count"] > 0 and stats["success_rate"] < 0.5

        status = "healthy"
        issues = []

        if is_stale:
            status = "stale"
            issues.append("數據超過1小時未更新")

        if high_error_rate:
            status = "unhealthy"
            issues.append("錯誤率過高")

        return {
            "status": status,
            "issues": issues,
            "stats": stats
        }
