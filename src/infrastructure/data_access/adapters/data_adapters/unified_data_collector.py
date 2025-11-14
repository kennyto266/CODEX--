"""
統一數據收集器
整合 GovDataCollector、HKEXDataCollector 和 KaggleDataCollector
支援多種數據收集方式：網頁抓取、API調用、文件下載
"""

import asyncio
import aiohttp
import pandas as pd
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path

from .unified_base_adapter import UnifiedBaseAdapter

class UnifiedDataCollector(UnifiedBaseAdapter):
    """
    統一數據收集器
    支援多種數據源和收集方式
    """

    SUPPORTED_SOURCES = {
        'gov': 'Government APIs',
        'hkex': 'HKEX Scraping',
        'kaggle': 'Kaggle Datasets',
        'web': 'Web Scraping',
        'api': 'Custom APIs'
    }

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.output_dir = Path(self.config.get('output_dir', './data/collector'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取HTTP會話"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """關閉會話"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def collect_from_api(self, source: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        從API收集數據

        Args:
            source: 數據源名稱
            params: API參數

        Returns:
            收集的數據
        """
        session = await self._get_session()

        try:
            # 示例：政府數據API
            if source == 'gov':
                url = params.get('url')
                if not url:
                    raise ValueError("URL required for gov source")

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'source': source,
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")

            # 示例：自定義API
            elif source == 'api':
                url = params.get('url')
                headers = params.get('headers', {})
                data = params.get('data', {})

                async with session.get(url, headers=headers, params=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'source': source,
                            'data': result,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")

            else:
                raise ValueError(f"Unsupported API source: {source}")

        except Exception as e:
            return {
                'success': False,
                'source': source,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def scrape_web(self, source: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        網頁抓取

        Args:
            source: 抓取源
            params: 抓取參數

        Returns:
            抓取的數據
        """
        # 注意：這裡是簡化實現
        # 實際實現需要使用 BeautifulSoup、Selenium 等
        return {
            'success': False,
            'source': source,
            'error': 'Web scraping not yet implemented',
            'note': 'Install BeautifulSoup/Selenium and implement scraping logic',
            'params': params
        }

    async def download_dataset(self, source: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        下載數據集

        Args:
            source: 數據源
            params: 下載參數

        Returns:
            下載結果
        """
        # 簡化實現 - 實際需要 Kaggle API
        if source == 'kaggle':
            dataset_id = params.get('dataset_id')
            if not dataset_id:
                return {
                    'success': False,
                    'error': 'dataset_id required',
                    'source': source
                }

            # 模擬下載
            return {
                'success': True,
                'source': source,
                'dataset_id': dataset_id,
                'message': 'Dataset download simulated - implement Kaggle API',
                'timestamp': datetime.now().isoformat()
            }

        return {
            'success': False,
            'error': f'Unsupported download source: {source}',
            'source': source
        }

    async def validate_data_quality(self, data: Any, rules: Optional[Dict] = None) -> Dict[str, Any]:
        """
        驗證數據質量

        Args:
            data: 要驗證的數據
            rules: 驗證規則

        Returns:
            驗證結果
        """
        if rules is None:
            rules = {
                'min_rows': 1,
                'required_columns': [],
                'max_null_ratio': 0.1
            }

        issues = []
        score = 100

        # 檢查是否為DataFrame
        if not isinstance(data, pd.DataFrame):
            issues.append("Data is not a DataFrame")
            score -= 30
        else:
            # 檢查行數
            min_rows = rules.get('min_rows', 1)
            if len(data) < min_rows:
                issues.append(f"Data has {len(data)} rows, minimum required: {min_rows}")
                score -= 20

            # 檢查空值比例
            max_null = rules.get('max_null_ratio', 0.1)
            null_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns)) if len(data) > 0 else 1
            if null_ratio > max_null:
                issues.append(f"Null ratio {null_ratio:.2%} exceeds maximum {max_null:.2%}")
                score -= int(null_ratio * 100)

            # 檢查必填列
            required_cols = rules.get('required_columns', [])
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                issues.append(f"Missing required columns: {missing_cols}")
                score -= len(missing_cols) * 10

        return {
            'valid': len(issues) == 0,
            'score': max(0, score),
            'issues': issues,
            'row_count': len(data) if isinstance(data, pd.DataFrame) else 0,
            'column_count': len(data.columns) if isinstance(data, pd.DataFrame) else 0
        }

    async def save_data(self, data: Any, filename: str, format: str = 'json') -> Dict[str, Any]:
        """
        保存數據

        Args:
            data: 要保存的數據
            filename: 文件名
            format: 格式 ('json', 'csv', 'parquet')

        Returns:
            保存結果
        """
        filepath = self.output_dir / filename

        try:
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            elif format == 'csv':
                if isinstance(data, pd.DataFrame):
                    data.to_csv(filepath, index=False)
                else:
                    raise ValueError("Data must be DataFrame for CSV format")

            elif format == 'parquet':
                if isinstance(data, pd.DataFrame):
                    data.to_parquet(filepath, index=False)
                else:
                    raise ValueError("Data must be DataFrame for Parquet format")

            else:
                raise ValueError(f"Unsupported format: {format}")

            return {
                'success': True,
                'filepath': str(filepath),
                'format': format,
                'size': os.path.getsize(filepath) if filepath.exists() else 0
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filepath': str(filepath)
            }

    async def collect_data(self, source: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        統一數據收集入口

        Args:
            source: 數據源
            params: 收集參數

        Returns:
            收集的數據
        """
        method = params.get('method', 'api')

        if method == 'api':
            return await self.collect_from_api(source, params)
        elif method == 'scrape':
            return await self.scrape_web(source, params)
        elif method == 'download':
            return await self.download_dataset(source, params)
        else:
            raise ValueError(f"Unsupported collection method: {method}")

    async def fetch_data(self, params: Dict[str, Any]) -> Any:
        """實現基礎適配器的fetch_data方法"""
        return await self.collect_data(
            params['source'],
            params
        )

    def get_supported_sources(self) -> Dict[str, str]:
        """獲取支持的數據源"""
        return self.SUPPORTED_SOURCES

    def get_data_source_info(self) -> Dict[str, Any]:
        """獲取數據源信息"""
        info = super().get_data_source_info()
        info.update({
            'output_directory': str(self.output_dir),
            'supported_sources': self.SUPPORTED_SOURCES,
            'supported_formats': ['json', 'csv', 'parquet']
        })
        return info
