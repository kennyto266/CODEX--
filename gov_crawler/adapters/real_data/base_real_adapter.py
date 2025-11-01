#!/usr/bin/env python3
"""
真實數據適配器基類 - Real Data Adapter Base
僅支持真實數據源，絕對不使用 mock 數據
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import json
from dataclasses import dataclass, asdict

# 配置日誌
logger = logging.getLogger(__name__)

@dataclass
class DataQualityReport:
    """數據質量報告"""
    source: str
    timestamp: str
    completeness: float  # 0-1 (1 = 100% 完整)
    accuracy: float      # 0-1 (1 = 100% 準確)
    timeliness: float    # 0-1 (1 = 最新數據)
    consistency: float   # 0-1 (1 = 完全一致)
    overall_score: float # 0-1 (加權平均)
    is_real_data: bool   # 必須為 True
    validation_errors: List[str]
    warnings: List[str]

    def is_acceptable(self) -> bool:
        """檢查數據是否可接受（真實數據且質量良好）"""
        return self.is_real_data and self.overall_score >= 0.85

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RealDataAdapter:
    """真實數據適配器基類 - 絕對不生成 mock 數據"""

    def __init__(self, name: str, source_url: str):
        self.name = name
        self.source_url = source_url
        self.session = None
        self.data_dir = Path("gov_crawler/data/real_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.quality_dir = Path("gov_crawler/data/quality_reports")
        self.quality_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'HongKongQuantDataCollector/1.0',
                'Accept': 'application/json, text/csv, */*',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()

    async def fetch_real_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取真實數據 - 必須實現
        這個方法必須從真實的 API 或數據源獲取數據
        絕對不能生成或返回 mock 數據
        """
        raise NotImplementedError(f"{self.name} 必須實現 fetch_real_data 方法")

    async def validate_data_is_real(self, df: pd.DataFrame) -> bool:
        """
        驗證數據是真實的（不是 mock 數據）
        """
        if df is None or df.empty:
            logger.error(f"{self.name}: 無數據")
            return False

        # 檢查是否有 mock 標記
        if 'is_mock' in df.columns and df['is_mock'].any():
            logger.error(f"{self.name}: 檢測到 mock 數據！")
            return False

        # 檢查數據是否包含真實的時間戳
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'], errors='coerce')
            if dates.isna().any():
                logger.error(f"{self.name}: 無效的日期格式")
                return False

            # 檢查數據時間範圍是否合理（不是預設的 mock 範圍）
            min_date = dates.min()
            max_date = dates.max()
            now = datetime.now()

            # 如果所有數據都是昨天的（mock 數據的特徵）
            if (now - max_date).days > 30:
                logger.warning(f"{self.name}: 數據可能過舊，檢查是否為真實數據")

        # 檢查數值範圍是否合理
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            values = df[col].dropna()
            if len(values) == 0:
                continue

            # 檢查是否為常數值（mock 數據特徵）
            if values.nunique() <= 1:
                logger.error(f"{self.name}: 數據列 '{col}' 為常數值，可能是 mock 數據")
                return False

            # 檢查是否為完美的正態分佈或明顯的人工模式
            if len(values) > 10:
                mean_val = values.mean()
                std_val = values.std()
                if std_val == 0:
                    logger.error(f"{self.name}: 數據列 '{col}' 無變化，可能是 mock 數據")
                    return False

                # 如果標準差異常小，標記為可疑
                if abs(std_val / mean_val) < 0.001 and mean_val != 0:
                    logger.warning(f"{self.name}: 數據列 '{col}' 變化過小，請檢查是否為真實數據")

        logger.info(f"{self.name}: 數據驗證通過，確認為真實數據")
        return True

    async def validate_data_quality(self, df: pd.DataFrame, start_date: str, end_date: str) -> DataQualityReport:
        """
        驗證數據質量
        """
        errors = []
        warnings = []
        timestamp = datetime.now().isoformat()

        # 1. 檢查完整性
        completeness = 1.0
        if df.empty:
            completeness = 0.0
            errors.append("數據框為空")
        else:
            missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
            completeness = 1.0 - missing_ratio
            if missing_ratio > 0.1:
                warnings.append(f"缺失數據比例: {missing_ratio:.2%}")

        # 2. 驗證真實性（最重要）
        is_real_data = await self.validate_data_is_real(df)
        if not is_real_data:
            errors.append("數據不是真實數據")

        # 3. 檢查及時性
        timeliness = 1.0
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'], errors='coerce')
            if not dates.empty:
                latest_date = dates.max()
                days_old = (datetime.now() - latest_date).days
                # 根據數據類型設定可接受的最大天數
                if 'hibor' in self.name.lower():
                    max_days = 2  # HIBOR 應為最新
                else:
                    max_days = 30

                if days_old > max_days:
                    timeliness = 0.0
                    errors.append(f"數據過舊: {days_old} 天")
                else:
                    timeliness = max(0, 1.0 - (days_old / max_days))

        # 4. 檢查一致性
        consistency = 1.0
        # 這裡可以添加更多一致性檢查邏輯

        # 計算總體分數（真實性權重最高）
        overall_score = (
            completeness * 0.2 +
            (1.0 if is_real_data else 0.0) * 0.5 +  # 真實性佔 50%
            timeliness * 0.2 +
            consistency * 0.1
        )

        report = DataQualityReport(
            source=self.name,
            timestamp=timestamp,
            completeness=completeness,
            accuracy=1.0 if is_real_data else 0.0,  # 準確性與真實性相關
            timeliness=timeliness,
            consistency=consistency,
            overall_score=overall_score,
            is_real_data=is_real_data,
            validation_errors=errors,
            warnings=warnings
        )

        return report

    def save_data_with_quality(self, df: pd.DataFrame, quality_report: DataQualityReport) -> str:
        """
        保存數據和質量報告
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = self.name.lower().replace(' ', '_')

        # 保存數據
        data_file = self.data_dir / f"{source_name}_{timestamp}.csv"
        df.to_csv(data_file, index=False)

        # 保存質量報告
        quality_file = self.quality_dir / f"{source_name}_quality_{timestamp}.json"
        with open(quality_file, 'w', encoding='utf-8') as f:
            json.dump(quality_report.to_dict(), f, ensure_ascii=False, indent=2)

        # 保存最新版本鏈接
        latest_link = self.data_dir / f"{source_name}_latest.csv"
        latest_link.unlink(missing_ok=True)  # 刪除舊鏈接
        latest_link.symlink_to(data_file.name)  # 創建新鏈接

        logger.info(f"{self.name}: 數據已保存到 {data_file}")
        logger.info(f"{self.name}: 質量報告已保存到 {quality_file}")

        return str(data_file)

    async def collect_and_validate(self, start_date: str, end_date: str) -> Tuple[pd.DataFrame, DataQualityReport]:
        """
        收集數據並進行驗證
        """
        logger.info(f"{self.name}: 開始收集真實數據")
        logger.info(f"{self.name}: 時間範圍: {start_date} 到 {end_date}")

        try:
            # 獲取真實數據
            df = await self.fetch_real_data(start_date, end_date)

            if df is None or df.empty:
                raise ValueError(f"{self.name}: 未能獲取到真實數據")

            # 驗證數據是真實的
            is_real = await self.validate_data_is_real(df)
            if not is_real:
                raise ValueError(f"{self.name}: 驗證失敗 - 數據不是真實的")

            # 驗證數據質量
            quality_report = await self.validate_data_quality(df, start_date, end_date)

            # 如果質量不達標，記錄警告但不拋出錯誤
            if not quality_report.is_acceptable():
                logger.warning(f"{self.name}: 數據質量不達標: {quality_report.overall_score:.2f}")
                for error in quality_report.validation_errors:
                    logger.warning(f"  - {error}")

            return df, quality_report

        except Exception as e:
            logger.error(f"{self.name}: 數據收集失敗: {str(e)}")
            raise

    def get_data_source_info(self) -> Dict[str, Any]:
        """
        獲取數據源信息
        """
        return {
            "name": self.name,
            "source_url": self.source_url,
            "last_update": datetime.now().isoformat(),
            "data_type": "real",  # 明確標記為真實數據
            "mock_enabled": False,  # 絕不使用 mock 數據
        }

    def log_real_data_warning(self):
        """
        記錄真實數據警告
        """
        warning = f"""
        ╔═══════════════════════════════════════════════════════════════╗
        ║                    ⚠️  真實數據警告                             ║
        ║                                                               ║
        ║ {self.name} 適配器                              ║
        ║                                                               ║
        ║ 此適配器僅處理真實數據，絕對不會生成或使用 mock 數據。           ║
        ║                                                               ║
        ║ 真實數據驗證:                                                 ║
        ║ ✓ 數據必須來自官方 API 或數據源                                ║
        ║ ✓ 數據時間戳必須是真實的                                      ║
        ║ ✓ 數據值必須具有合理的變化                                    ║
        ║ ✓ 不得包含任何人工標記或模擬標記                              ║
        ║                                                               ║
        ║ 違規將導致:                                                    ║
        ║ ✗ 交易信號無效                                                ║
        ║ ✗ 量化分析結果錯誤                                            ║
        ║ ✗ 投資決策失誤                                                ║
        ║                                                               ║
        ╚═══════════════════════════════════════════════════════════════╝
        """
        logger.warning(warning)

# 確保所有適配器都繼承此類
class MockDataError(Exception):
    """Mock 數據錯誤 - 使用 mock 數據時拋出"""
    pass

def validate_no_mock_data(func):
    """
    裝飾器：驗證函數不使用 mock 數據
    """
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        if isinstance(result, pd.DataFrame):
            if 'is_mock' in result.columns and result['is_mock'].any():
                raise MockDataError("禁止使用 mock 數據！")
        return result
    return wrapper
