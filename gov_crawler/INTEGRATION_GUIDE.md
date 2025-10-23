# GOV 爬蟲 - 量化交易系統集成指南

## 概述

本指南說明如何將 GOV 爬蟲系統與您的港股量化交易系統集成，以獲取替代數據用於策略開發。

## 架構圖

```
┌─────────────────┐
│  GOV Crawler    │
│  (GOV爬蟲)      │
└────────┬────────┘
         │ 下載數據
         ▼
┌─────────────────┐
│   Data/         │
│  processed/     │ ─── 處理後的 CSV/JSON 數據
└────────┬────────┘
         │
         │ 讀取
         ▼
┌─────────────────────────────────────┐
│  Quantitative Trading System        │
│  (量化交易系統)                     │
│                                     │
│  ├─ Data Adapters                  │
│  │  └─ GovDataAdapter (新增)        │
│  ├─ Strategies                     │
│  ├─ Backtest Engine                │
│  └─ Risk Management                │
└─────────────────────────────────────┘
```

## 集成步驟

### 步驟 1: 添加 GOV 適配器

在您的量化系統中創建 `src/data_adapters/gov_data_adapter.py`：

```python
"""
GOV 數據適配器 - 集成香港政府開放數據
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class GovDataAdapter:
    """香港政府開放數據適配器"""

    def __init__(self, data_dir: str = "gov_crawler/data/processed"):
        """
        初始化適配器

        Args:
            data_dir: GOV 爬蟲的數據目錄
        """
        self.data_dir = data_dir
        self._cache = {}
        self._last_updated = {}

    def fetch_gdp_data(self, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        獲取 GDP 數據

        Args:
            force_refresh: 是否強制刷新緩存

        Returns:
            GDP DataFrame
        """
        return self._load_data('gdp', force_refresh)

    def fetch_property_market_data(self, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        獲取物業市場數據

        Args:
            force_refresh: 是否強制刷新緩存

        Returns:
            物業市場 DataFrame
        """
        return self._load_data('property_market', force_refresh)

    def fetch_retail_sales_data(self, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        獲取零售銷售數據

        Args:
            force_refresh: 是否強制刷新緩存

        Returns:
            零售銷售 DataFrame
        """
        return self._load_data('retail_sales', force_refresh)

    def fetch_traffic_data(self, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        獲取交通數據

        Args:
            force_refresh: 是否強制刷新緩存

        Returns:
            交通 DataFrame
        """
        return self._load_data('traffic', force_refresh)

    def _load_data(self, dataset_name: str, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        加載數據（帶緩存）

        Args:
            dataset_name: 數據集名稱
            force_refresh: 是否強制刷新

        Returns:
            DataFrame 或 None
        """
        # 如果不強制刷新且已緩存，返回緩存數據
        if not force_refresh and dataset_name in self._cache:
            logger.info(f"從緩存返回 {dataset_name} 數據")
            return self._cache[dataset_name]

        # 查找最新的 CSV 文件
        files = self._find_latest_file(dataset_name, '.csv')
        if not files:
            logger.warning(f"未找到 {dataset_name} 的數據文件")
            return None

        try:
            df = pd.read_csv(files)
            self._cache[dataset_name] = df
            self._last_updated[dataset_name] = datetime.now()
            logger.info(f"成功加載 {dataset_name}: {len(df)} 行")
            return df
        except Exception as e:
            logger.error(f"加載 {dataset_name} 失敗: {e}")
            return None

    def _find_latest_file(self, prefix: str, extension: str) -> Optional[str]:
        """
        查找最新的文件

        Args:
            prefix: 文件前綴
            extension: 文件擴展名

        Returns:
            文件路徑或 None
        """
        if not os.path.exists(self.data_dir):
            return None

        matching_files = [
            f for f in os.listdir(self.data_dir)
            if f.startswith(prefix) and f.endswith(extension)
        ]

        if not matching_files:
            return None

        latest = sorted(matching_files)[-1]
        return os.path.join(self.data_dir, latest)

    def get_data_info(self) -> Dict[str, Dict]:
        """
        獲取所有可用數據的信息

        Returns:
            數據信息字典
        """
        info = {}
        datasets = ['gdp', 'property_market', 'retail_sales', 'traffic']

        for dataset in datasets:
            file_path = self._find_latest_file(dataset, '.csv')
            if file_path:
                info[dataset] = {
                    'file': file_path,
                    'last_updated': self._last_updated.get(dataset),
                    'is_cached': dataset in self._cache
                }

        return info

    def clear_cache(self) -> None:
        """清空緩存"""
        self._cache.clear()
        self._last_updated.clear()
        logger.info("緩存已清空")
```

### 步驟 2: 集成到數據服務

修改 `src/data_adapters/data_service.py`，添加 GOV 適配器：

```python
# ... 在 DataService 類中添加

from .gov_data_adapter import GovDataAdapter

class DataService:
    def __init__(self):
        # 現有的適配器...
        self.adapters = {
            'yfinance': YahooFinanceAdapter(),
            'alpha_vantage': AlphaVantageAdapter(),
            # 添加 GOV 適配器
            'gov': GovDataAdapter()
        }

    def get_alternative_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        獲取替代數據

        Args:
            data_type: 數據類型 ('gdp', 'property_market', 'retail_sales', 'traffic')

        Returns:
            DataFrame
        """
        gov_adapter = self.adapters.get('gov')
        if not gov_adapter:
            return None

        if data_type == 'gdp':
            return gov_adapter.fetch_gdp_data()
        elif data_type == 'property_market':
            return gov_adapter.fetch_property_market_data()
        elif data_type == 'retail_sales':
            return gov_adapter.fetch_retail_sales_data()
        elif data_type == 'traffic':
            return gov_adapter.fetch_traffic_data()

        return None
```

### 步驟 3: 在策略中使用 GOV 數據

```python
# 示例策略 - 基於經濟指標的股票選擇

from src.data_adapters.data_service import DataService
from src.data_adapters.gov_data_adapter import GovDataAdapter

class MacroEconomicStrategy:
    """宏觀經濟策略"""

    def __init__(self):
        self.gov_adapter = GovDataAdapter()

    def generate_signals(self) -> Dict[str, str]:
        """
        基於政府經濟數據生成交易信號

        Returns:
            信號字典 {symbol: action}
        """
        signals = {}

        # 獲取經濟指標
        gdp_data = self.gov_adapter.fetch_gdp_data()
        retail_data = self.gov_adapter.fetch_retail_sales_data()

        if gdp_data is not None and len(gdp_data) > 1:
            # 分析 GDP 趨勢
            latest_gdp = gdp_data.iloc[-1]
            prev_gdp = gdp_data.iloc[-2]

            gdp_growth = (latest_gdp['value'] - prev_gdp['value']) / prev_gdp['value']

            # GDP 增長 > 2% 時看漲
            if gdp_growth > 0.02:
                signals['0941.HK'] = 'BUY'  # 中國移動
                signals['0939.HK'] = 'BUY'  # 中國建築銀行
            else:
                signals['0941.HK'] = 'SELL'
                signals['0939.HK'] = 'SELL'

        if retail_data is not None and len(retail_data) > 1:
            # 分析零售趨勢
            latest_retail = retail_data.iloc[-1]['value']
            prev_retail = retail_data.iloc[-2]['value']

            retail_growth = (latest_retail - prev_retail) / prev_retail

            # 零售銷售增長時看漲零售股
            if retail_growth > 0.01:
                signals['0939.HK'] = 'BUY'  # 假設看漲

        return signals

    def calculate_position_size(self, symbol: str, action: str) -> float:
        """
        基於經濟狀況計算頭寸大小

        Args:
            symbol: 股票代碼
            action: 交易動作

        Returns:
            頭寸大小比例
        """
        gdp_data = self.gov_adapter.fetch_gdp_data()

        if gdp_data is not None and len(gdp_data) > 0:
            latest_gdp = gdp_data.iloc[-1]['value']
            # 更好的經濟環境 = 更大的頭寸
            return min(0.05 * (latest_gdp / 100), 0.1)

        return 0.05  # 默認 5%
```

### 步驟 4: 在回測中使用

```python
# 在回測腳本中集成 GOV 數據

from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
from src.data_adapters.gov_data_adapter import GovDataAdapter
from src.strategies import MacroEconomicStrategy

# 初始化爬蟲
gov_adapter = GovDataAdapter()

# 獲取替代數據用於分析
gdp_data = gov_adapter.fetch_gdp_data()
property_data = gov_adapter.fetch_property_market_data()
retail_data = gov_adapter.fetch_retail_sales_data()

# 創建策略
strategy = MacroEconomicStrategy()

# 運行回測
engine = EnhancedBacktestEngine()
results = engine.backtest(
    symbols=['0700.HK', '0005.HK', '0941.HK'],
    strategy=strategy,
    start_date='2022-01-01',
    end_date='2024-12-31'
)

print(results)
```

## 數據對齐和特徵工程

### 特徵構建示例

```python
import pandas as pd
from scipy import stats

class GovDataFeatureEngineer:
    """政府數據特徵工程"""

    @staticmethod
    def create_gdp_features(gdp_df: pd.DataFrame, stock_df: pd.DataFrame) -> pd.DataFrame:
        """
        為股票數據創建 GDP 相關特徵

        Args:
            gdp_df: GDP 數據
            stock_df: 股票數據

        Returns:
            增強的股票數據框
        """
        # 按日期對齐
        stock_df = stock_df.copy()
        stock_df['gdp_growth'] = np.nan

        # 填充 GDP 增長率
        for idx, row in stock_df.iterrows():
            date = row['date']
            gdp_row = gdp_df[gdp_df['date'] <= date].tail(1)
            if not gdp_row.empty:
                stock_df.at[idx, 'gdp_growth'] = gdp_row['value'].values[0]

        # 計算 GDP 增長率變化
        stock_df['gdp_momentum'] = stock_df['gdp_growth'].pct_change()

        return stock_df

    @staticmethod
    def create_property_features(property_df: pd.DataFrame, stock_df: pd.DataFrame) -> pd.DataFrame:
        """
        為股票數據創建房產相關特徵

        Args:
            property_df: 房產數據
            stock_df: 股票數據

        Returns:
            增強的股票數據框
        """
        stock_df = stock_df.copy()

        # 創建房產市場指標
        stock_df['property_price_index'] = np.nan
        stock_df['property_transaction_volume'] = np.nan

        for idx, row in stock_df.iterrows():
            date = row['date']
            prop_row = property_df[property_df['date'] <= date].tail(1)
            if not prop_row.empty:
                stock_df.at[idx, 'property_price_index'] = prop_row['price'].values[0]
                stock_df.at[idx, 'property_transaction_volume'] = prop_row['volume'].values[0]

        return stock_df
```

## 性能考慮

### 緩存策略

```python
class CachedGovDataAdapter(GovDataAdapter):
    """帶緩存的 GOV 數據適配器"""

    def __init__(self, cache_ttl: int = 3600):
        """
        初始化

        Args:
            cache_ttl: 緩存過期時間（秒）
        """
        super().__init__()
        self.cache_ttl = cache_ttl

    def fetch_gdp_data(self, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        帶 TTL 的 GDP 數據獲取

        Args:
            force_refresh: 是否強制刷新

        Returns:
            GDP DataFrame
        """
        if 'gdp' in self._cache and not force_refresh:
            last_updated = self._last_updated.get('gdp')
            if last_updated and (datetime.now() - last_updated).total_seconds() < self.cache_ttl:
                return self._cache['gdp']

        return super().fetch_gdp_data(force_refresh)
```

## 定時更新

### 使用 APScheduler

```python
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)

class AutoDataUpdater:
    """自動數據更新器"""

    def __init__(self, data_service):
        self.data_service = data_service
        self.scheduler = BackgroundScheduler()

    def start(self):
        """啟動自動更新"""
        # 每天凌晨 2 點更新 GOV 數據
        self.scheduler.add_job(
            self._update_gov_data,
            'cron',
            hour=2,
            minute=0,
            id='gov_data_update'
        )

        self.scheduler.start()
        logger.info("自動更新已啟動")

    def _update_gov_data(self):
        """更新 GOV 數據"""
        try:
            gov_adapter = self.data_service.adapters.get('gov')
            if gov_adapter:
                gov_adapter.clear_cache()
                gov_adapter.fetch_gdp_data(force_refresh=True)
                gov_adapter.fetch_property_market_data(force_refresh=True)
                gov_adapter.fetch_retail_sales_data(force_refresh=True)
                gov_adapter.fetch_traffic_data(force_refresh=True)
                logger.info("GOV 數據已更新")
        except Exception as e:
            logger.error(f"GOV 數據更新失敗: {e}")

    def stop(self):
        """停止自動更新"""
        self.scheduler.shutdown()
        logger.info("自動更新已停止")
```

## 監控和日誌

```python
import logging

# 配置 GOV 適配器日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gov_adapter.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('gov_adapter')
```

## 常見問題

### Q: 如何確保數據及時性？
A: 使用定時更新機制，在非交易時間（如凌晨）自動更新 GOV 數據。

### Q: 能否同時使用多個數據源？
A: 完全可以。GOV 數據是補充性的，應與您現有的市場數據一起使用。

### Q: 如何處理數據缺失？
A: 使用 pandas 的插值方法：
```python
df['value'].interpolate(method='linear', inplace=True)
```

---

更多詳情請參考 README.md 和 QUICKSTART.md
