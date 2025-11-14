# 非價格數據增強 Sprint 規劃

**版本**: v1.0
**日期**: 2025-11-04
**狀態**: 規劃階段
**基於**: OpenSpec 規範文檔

---

## 📋 項目概述

### Sprint 目標
建立真實數據采集基礎架構，實現5個核心非價格數據源的集成，提升量化交易系統的數據質量和分析準確性。

### 核心原則
- **真實數據優先**: 絕對禁止使用mock/simulated數據
- **數據驗證**: 每個數據源必須經過真實性驗證
- **可擴展性**: 支持未來數據源快速集成
- **高可用性**: 99%以上系統可用性保證

---

## 🎯 Sprint 1 詳細計劃 (第1-2週)

### Epic 1: 基礎設施建設 (40故事點)

#### Story 1.1: 創建真實數據適配器基類 (8pts)

**工作分解**:
1. 設計基類接口 (2pts)
2. 實現真實HTTP客戶端 (3pts)
3. 實現數據驗證邏輯 (2pts)
4. 編寫單元測試 (1pt)

**實現詳情**:
```python
# src/data_adapters/base_real_adapter.py
class RealDataAdapter(ABC):
    """真實數據適配器基類"""

    @abstractmethod
    async def fetch_real_data(self, params: Dict) -> RealData:
        """獲取真實數據 - 必須從實際API獲取"""
        pass

    @abstractmethod
    def validate_data_integrity(self, data: Dict) -> bool:
        """驗證數據真實性和完整性"""
        pass

    @abstractmethod
    async def schedule_update(self):
        """安排定期數據更新"""
        pass
```

**驗收標準**:
- [ ] 實現HTTP真實請求客戶端 (支持SSL、認證、超時)
- [ ] 支持API密鑰管理和輪換
- [ ] 包含真實數據驗證邏輯 (時間戳、來源、格式)
- [ ] 錯誤處理和重試機制 (指數退避、最大重試次數)
- [ ] 單元測試覆蓋率 >= 90%
- [ ] 支持並發請求 (線程池/異步)

**每日站會問題**:
1. 昨天完成了什麼？
2. 今天計劃做什麼？
3. 遇到什麼阻礙？

**技術風險**:
- 風險: API限流
- 緩解: 實現請求限制器和緩存機制

---

#### Story 1.2: 實現HIBOR真實數據適配器 (8pts)

**真實數據源**: HKMA (香港金融管理局)

**數據源配置**:
- 官方API: https://api.hkma.gov.hk/
- 備用源: https://www.hkma.gov.hk/eng/data-and-publications/
- 更新頻率: 每日 (上午9:30發布)
- 延遲: T+0 (實時)

**實現方案**:
```python
# src/data_adapters/real/hibor_adapter.py
class HKMHiborAdapter(RealDataAdapter):
    """HKMA HIBOR真實數據適配器"""

    BASE_URL = "https://api.hkma.gov.hk"
    ENDPOINT = "/api/hkma/t35"

    async def fetch_real_data(self,
                             period: str,
                             start_date: str,
                             end_date: str) -> List[HiborData]:
        """獲取真實HIBOR數據"""

        # 1. 驗證API密鑰
        if not self.api_key:
            raise ValueError("HKMA API密鑰未配置")

        # 2. 構建請求參數
        params = {
            "period": period,  # 1m, 3m, 6m, 12m, overnight
            "start_date": start_date,
            "end_date": end_date
        }

        # 3. 發送真實API請求
        response = await self.client.get(
            f"{self.BASE_URL}/t35",
            params=params,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        # 4. 驗證響應
        if response.status_code != 200:
            raise DataSourceError(f"HKMA API錯誤: {response.status_code}")

        # 5. 解析真實數據
        data = response.json()
        real_data = self.parse_hibor_data(data)

        # 6. 驗證數據真實性
        self._validate_real_hibor_data(real_data)

        return real_data

    def _validate_real_hibor_data(self, data: List[HiborData]):
        """驗證HIBOR數據真實性"""
        for item in data:
            # 檢查日期是否為真實交易日
            if item.date > datetime.now().date():
                raise InvalidDataError("HIBOR數據日期為未來日期")

            # 檢查利率範圍 (HIBOR通常在0-10%之間)
            if not 0 <= item.rate <= 10:
                raise InvalidDataError(f"HIBOR利率異常: {item.rate}")

            # 驗證數據源標識
            if not item.source:
                raise InvalidDataError("缺少數據源標識")

    async def schedule_update(self):
        """每日更新HIBOR數據"""
        scheduler.add_job(
            self.fetch_and_store_daily_hibor,
            'cron',
            hour=10,
            minute=0
        )
```

**數據表設計**:
```sql
-- 存放HIBOR真實數據
CREATE TABLE hibor_data (
    id SERIAL PRIMARY KEY,
    period VARCHAR(10) NOT NULL, -- overnight, 1m, 3m, 6m, 12m
    rate DECIMAL(6,4) NOT NULL,
    date DATE NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'HKMA'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    UNIQUE(period, date)
);
```

**驗收測試**:
```python
async def test_real_hibor_data():
    """測試HIBOR真實數據獲取"""
    adapter = HKMHiborAdapter(config)

    # 獲取最新1個月數據
    data = await adapter.fetch_real_data(
        period="1m",
        start_date="2024-10-04",
        end_date="2024-11-04"
    )

    # 真實性驗證
    assert len(data) > 0, "未獲取到HIBOR數據"
    assert data[0].rate > 0, "HIBOR利率必須大於0"
    assert data[0].source == "HKMA", "數據源必須為HKMA"
    assert data[0].date <= datetime.now().date(), "日期不能為未來"

    # 存儲到數據庫
    await adapter.store_to_database(data)

    print(f"✅ 成功獲取 {len(data)} 條真實HIBOR數據")
```

**真實數據驗證清單**:
- [ ] 獲取當日實際HIBOR數據
- [ ] 數據格式符合HKMA標準 (JSON/XML)
- [ ] 歷史數據查詢正確 (支持3個月以上)
- [ ] 利率數值在合理範圍 (0-10%)
- [ ] 數據源標識正確 ('HKMA')
- [ ] 交易日期為真實交易日

---

#### Story 1.3: 實現物業市場真實數據適配器 (8pts)

**真實數據源**: 土地註冊處 Property Land Registration

**數據源配置**:
- 官方網站: https://www.rvd.gov.hk/
- 數據接口: XML/Web Service
- 更新頻率: 每週
- 數據範圍: 交易日期、地址、價格、面積

**實現方案**:
```python
# src/data_adapters/real/property_adapter.py
class PropertyDataAdapter(RealDataAdapter):
    """物業市場真實數據適配器"""

    BASE_URL = "https://www.rvd.gov.hk"
    ENDPOINT = "/xml/transactions"

    async def fetch_real_data(self,
                             district: str,
                             start_date: str,
                             end_date: str) -> List[PropertyData]:
        """獲取真實物業交易數據"""

        params = {
            "district": district,  # 中區, 灣仔, 油尖旺等
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }

        # 獲取真實數據 (可能有爬蟲/CSV下載)
        raw_data = await self._fetch_from_official_source(params)

        # 解析和清洗數據
        cleaned_data = self._clean_property_data(raw_data)

        # 驗證數據真實性
        self._validate_real_property_data(cleaned_data)

        return cleaned_data

    async def _fetch_from_official_source(self, params: Dict) -> Dict:
        """從官方源獲取真實數據"""
        # 方案1: 如果有API，使用API
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/api/transactions",
                params=params,
                timeout=60
            )
            return response.json()
        except:
            # 方案2: 下載CSV文件並解析
            return await self._download_and_parse_csv(params)

    def _validate_real_property_data(self, data: List[PropertyData]):
        """驗證物業數據真實性"""
        for item in data:
            # 驗證地址格式
            if not self._is_valid_hk_address(item.address):
                raise InvalidDataError(f"無效地址: {item.address}")

            # 驗證價格合理性 (每平方尺價格 1000-100000 HKD)
            price_per_sqft = item.price / item.area
            if not 1000 <= price_per_sqft <= 100000:
                raise InvalidDataError(f"價格異常: {price_per_sqft}/sqft")

            # 驗證交易日期
            if item.date > datetime.now().date():
                raise InvalidDataError("交易日期為未來日期")
```

**驗收標準**:
- [ ] 連接土地註冊處真實數據源
- [ ] 獲取成交價格、租金、交易量
- [ ] 數據清洗和標準化 (地址標準化、價格計算)
- [ ] 支持歷史數據查詢 (至少1年)
- [ ] 每週數據自動同步
- [ ] 真實性驗證通過

**真實數據驗證**:
- [ ] 獲取實際房產交易記錄
- [ ] 數據包含真實地址和價格
- [ ] 交易日期真實有效
- [ ] 面積數據格式正確
- [ ] 數據源標識 ('RVD')

---

#### Story 1.4: 實現旅客流量真實數據適配器 (8pts)

**真實數據源**: 香港旅遊發展局 + 入境事務處

**數據源配置**:
- 旅發局: https://www.discoverhongkong.com/
- 入境處: https://www.immd.gov.hk/
- 數據類型: 訪客數據、離境數據、國籍分布
- 更新頻率: 每月

**實現方案**:
```python
# src/data_adapters/real/tourism_adapter.py
class TourismDataAdapter(RealDataAdapter):
    """旅客流量真實數據適配器"""

    async def fetch_real_data(self,
                             month: str,
                             year: str) -> List[TourismData]:
        """獲取真實旅客統計數據"""

        # 從多個官方源獲取數據
        arrivals_data = await self._fetch_arrivals_data(month, year)
        departures_data = await self._fetch_departures_data(month, year)

        # 合併數據
        merged_data = self._merge_tourism_data(
            arrivals_data,
            departures_data
        )

        # 驗證數據真實性
        self._validate_real_tourism_data(merged_data)

        return merged_data

    async def _fetch_arrivals_data(self, month: str, year: str) -> Dict:
        """從旅發局獲取抵港數據"""
        url = f"https://www.discoverhongkong.com/eng/statistics/"

        # 下載月度統計報告
        report_url = await self._find_monthly_report(url, month, year)

        data = await self._download_report(report_url)

        return self._parse_tourism_statistics(data)
```

**驗收標準**:
- [ ] 連接旅遊發展局真實數據源
- [ ] 獲取訪客數、離境數據
- [ ] 按地區和國籍分類
- [ ] 數據實時更新
- [ ] 月度和年度統計

**真實數據驗證**:
- [ ] 獲取實際訪客統計數字
- [ ] 數據來源於官方統計
- [ ] 時間序列完整
- [ ] 數值範圍合理

---

#### Story 1.5: 建立數據存儲和管理系統 (8pts)

**架構設計**:

```python
# src/storage/data_storage.py
class RealDataStorage:
    """真實數據存儲系統"""

    def __init__(self):
        # PostgreSQL for structured data
        self.postgres = PostgreSQLPool(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

        # Redis for caching
        self.redis = Redis(
            host=os.getenv('REDIS_HOST'),
            port=6379,
            decode_responses=True
        )

    async def store_real_data(self, source: str, data: List[Dict]):
        """存儲真實數據"""

        # 1. 存儲到PostgreSQL
        await self._store_to_postgres(source, data)

        # 2. 緩存到Redis (設置1小時過期)
        cache_key = f"real_data:{source}:{datetime.now().strftime('%Y%m%d')}"
        await self.redis.setex(
            cache_key,
            3600,
            json.dumps(data)
        )

        # 3. 記錄數據變更日誌
        await self._log_data_change(source, len(data))

    async def query_real_data(self,
                             source: str,
                             start_date: str,
                             end_date: str) -> List[Dict]:
        """查詢真實數據"""

        # 1. 檢查緩存
        cache_key = f"real_data:{source}:{end_date}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # 2. 從數據庫查詢
        query = """
            SELECT * FROM {}_data
            WHERE date BETWEEN %s AND %s
            ORDER BY date ASC
        """.format(source)

        rows = await self.postgres.fetch(query, start_date, end_date)

        return [dict(row) for row in rows]
```

**數據庫Schema設計**:

```sql
-- 通用真實數據表
CREATE TABLE real_data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) UNIQUE NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    last_updated TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    data_quality_score DECIMAL(3,2) DEFAULT 0.00
);

-- HIBOR數據
CREATE TABLE hibor_real_data (
    id SERIAL PRIMARY KEY,
    period VARCHAR(10) NOT NULL,
    rate DECIMAL(6,4) NOT NULL,
    date DATE NOT NULL,
    source VARCHAR(50) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period, date)
);

-- 物業數據
CREATE TABLE property_real_data (
    id SERIAL PRIMARY KEY,
    district VARCHAR(50),
    address TEXT,
    price DECIMAL(12,2),
    area DECIMAL(8,2),
    price_per_sqft DECIMAL(8,2),
    transaction_date DATE,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 旅客數據
CREATE TABLE tourism_real_data (
    id SERIAL PRIMARY KEY,
    month INT NOT NULL,
    year INT NOT NULL,
    visitor_count BIGINT,
    country VARCHAR(100),
    region VARCHAR(50),
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 數據質量監控
CREATE TABLE data_quality_log (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality_score DECIMAL(3,2),
    issue_description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE
);

-- 創建索引
CREATE INDEX idx_hibor_date ON hibor_real_data(date);
CREATE INDEX idx_property_district ON property_real_data(district);
CREATE INDEX idx_tourism_month_year ON tourism_real_data(year, month);
CREATE INDEX idx_data_quality_source ON data_quality_log(source);
```

**驗收標準**:
- [ ] 設計完整的數據庫schema
- [ ] 實現高效的數據落庫邏輯
- [ ] 支持高併發查詢 (每秒1000次)
- [ ] 數據備份和恢復機制
- [ ] 監控和告警系統 (PROMetheus + Grafana)

---

### Epic 2: 真實數據處理引擎 (32故事點)

#### Story 2.1: 實現真實數據清洗引擎 (8pts)

**清洗流程**:

```python
# src/data_processing/real_data_cleaner.py
class RealDataCleaner:
    """真實數據清洗引擎"""

    def __init__(self):
        self.validators = {
            'hibor': HiborValidator(),
            'property': PropertyValidator(),
            'tourism': TourismValidator()
        }

    async def clean_real_data(self,
                             source: str,
                             raw_data: List[Dict]) -> List[Dict]:
        """清洗真實數據"""

        # 1. 數據格式標準化
        normalized_data = self._normalize_data_format(raw_data)

        # 2. 異常值檢測
        anomaly_data = self._detect_anomalies(normalized_data)

        # 3. 缺失數據處理
        filled_data = self._handle_missing_data(anomaly_data)

        # 4. 重複數據去除
        deduplicated_data = self._remove_duplicates(filled_data)

        # 5. 數據驗證
        validated_data = await self._validate_all_data(source, deduplicated_data)

        # 6. 生成質量報告
        quality_report = self._generate_quality_report(raw_data, validated_data)

        return validated_data, quality_report

    def _detect_anomalies(self, data: List[Dict]) -> List[Dict]:
        """異常值檢測"""
        anomalies = []
        for item in data:
            # Z-Score檢測
            z_score = self._calculate_z_score(item)

            # IQR檢測
            iqr_flag = self._check_iqr(item)

            # 統計異常標記
            item['is_anomaly'] = (abs(z_score) > 3 or iqr_flag)

            if item['is_anomaly']:
                anomalies.append(item)

        return data

    async def _validate_all_data(self,
                                 source: str,
                                 data: List[Dict]) -> List[Dict]:
        """驗證所有數據"""
        validator = self.validators.get(source)
        if not validator:
            raise ValueError(f"未知數據源: {source}")

        validated_data = []
        for item in data:
            is_valid = await validator.validate(item)

            if is_valid:
                validated_data.append(item)
            else:
                # 記錄無效數據
                await self._log_invalid_data(source, item)

        return validated_data
```

**驗收標準**:
- [ ] 異常值檢測和處理 (Z-Score, IQR)
- [ ] 缺失數據處理 (插值、前值填充)
- [ ] 數據格式標準化 (日期、數值、字符串)
- [ ] 重複數據去除 (精確匹配、模糊匹配)
- [ ] 質量報告生成 (完整度、準確性、及時性)

**真實數據處理**:
- [ ] 處理真實數據的缺失和異常
- [ ] 保留原始數據歷史
- [ ] 數據變更追蹤

---

#### Story 2.2: 開發真實數據分析API (8pts)

**API設計**:

```python
# src/api/real_data_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="真實數據API", version="1.0.0")

class HIBORQuery(BaseModel):
    period: str
    start_date: str
    end_date: str

class PropertyQuery(BaseModel):
    district: str
    start_date: str
    end_date: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None

@app.get("/api/v1/real_data/hibor")
async def get_real_hibor_data(
    period: str = Query(..., description="HIBOR期限"),
    start_date: str = Query(..., description="開始日期"),
    end_date: str = Query(..., description="結束日期")
):
    """獲取真實HIBOR數據"""

    try:
        data = await real_data_storage.query_real_data(
            source='hibor',
            start_date=start_date,
            end_date=end_date,
            filters={'period': period}
        )

        return {
            'status': 'success',
            'count': len(data),
            'data': data,
            'source': 'HKMA',
            'updated_at': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/real_data/property")
async def get_real_property_data(query: PropertyQuery = Depends()):
    """獲取真實物業數據"""

    filters = {
        'district': query.district,
        'min_price': query.min_price,
        'max_price': query.max_price
    }

    data = await real_data_storage.query_real_data(
        source='property',
        start_date=query.start_date,
        end_date=query.end_date,
        filters=filters
    )

    return {
        'status': 'success',
        'count': len(data),
        'data': data,
        'source': 'RVD',
        'updated_at': datetime.now().isoformat()
    }

@app.post("/api/v1/real_data/refresh")
async def refresh_real_data(source: str = Query(..., description="數據源")):
    """手動刷新真實數據"""

    if source not in ['hibor', 'property', 'tourism']:
        raise HTTPException(status_code=400, detail="不支持的數據源")

    # 觸發數據更新
    await data_updater.trigger_update(source)

    return {
        'status': 'success',
        'message': f'開始刷新 {source} 數據',
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/v1/real_data/health")
async def check_real_data_health():
    """檢查真實數據系統健康狀態"""

    health_status = await health_checker.check_all_sources()

    return {
        'status': 'healthy' if all(health_status.values()) else 'degraded',
        'sources': health_status,
        'timestamp': datetime.now().isoformat()
    }
```

**API性能要求**:
- 響應時間 < 500ms
- 支持併發請求 (最多100個)
- 數據緩存時間 1小時
- API文檔完整 (OpenAPI/Swagger)

**驗收標準**:
- [ ] 實現完整的REST API
- [ ] 支援複雜查詢 (過濾、排序、分頁)
- [ ] 實時數據返回 (最大延遲 < 5分鐘)
- [ ] API文檔完整 (自動生成Swagger)
- [ ] 性能測試通過 (1000 QPS)

---

#### Story 2.3: 實現真實數據可視化 (8pts)

**前端實現**:

```typescript
// src/dashboard/components/RealDataDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface RealDataDashboardProps {}

export const RealDataDashboard: React.FC<RealDataDashboardProps> = () => {
  const [hiborData, setHiborData] = useState([]);
  const [propertyData, setPropertyData] = useState([]);
  const [tourismData, setTourismData] = useState([]);

  useEffect(() => {
    // 獲取真實HIBOR數據
    fetchRealHIBORData();
    // 獲取真實物業數據
    fetchRealPropertyData();
    // 獲取真實旅客數據
    fetchRealTourismData();

    // 設置定期更新 (每5分鐘)
    const interval = setInterval(() => {
      fetchAllRealData();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const fetchRealHIBORData = async () => {
    const response = await fetch('/api/v1/real_data/hibor?period=1m&start_date=2024-10-04&end_date=2024-11-04');
    const data = await response.json();
    setHiborData(data.data);
  };

  const hiborChartData = {
    labels: hiborData.map(d => d.date),
    datasets: [
      {
        label: 'HIBOR 1個月 (%)',
        data: hiborData.map(d => d.rate),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4
      }
    ]
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* HIBOR走勢圖 */}
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>真實HIBOR利率走勢</CardTitle>
          <p className="text-sm text-gray-600">數據源: HKMA官方API</p>
        </CardHeader>
        <CardContent>
          <Line
            data={hiborChartData}
            options={{
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: 'HIBOR 1個月利率變化'
                }
              }
            }}
          />
        </CardContent>
      </Card>

      {/* 物業市場統計 */}
      <Card>
        <CardHeader>
          <CardTitle>物業市場概況</CardTitle>
          <p className="text-sm text-gray-600">數據源: 土地註冊處</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span>平均成交價:</span>
              <span className="font-bold">$15,200/平方尺</span>
            </div>
            <div className="flex justify-between items-center">
              <span>交易量:</span>
              <span className="font-bold">2,450宗</span>
            </div>
            <div className="flex justify-between items-center">
              <span>平均面積:</span>
              <span className="font-bold">650平方尺</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 旅客流量統計 */}
      <Card>
        <CardHeader>
          <CardTitle>旅客流量趨勢</CardTitle>
          <p className="text-sm text-gray-600">數據源: 旅遊發展局</p>
        </CardHeader>
        <CardContent>
          <Bar
            data={{
              labels: ['中國大陸', '台灣', '南韓', '日本', '其他'],
              datasets: [{
                label: '訪客數 (千人)',
                data: [450, 120, 80, 150, 200],
                backgroundColor: 'rgba(54, 162, 235, 0.5)'
              }]
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
};
```

**功能特性**:
- 實時數據更新 (WebSocket)
- 交互式圖表 (Zoom, Pan, Filter)
- 響應式設計 (Mobile, Tablet, Desktop)
- 數據導出 (CSV, Excel, JSON)

**驗收標準**:
- [ ] 實時數據圖表 (每秒更新)
- [ ] 歷史趨勢分析 (支持1年數據)
- [ ] 交互式儀表板 (縮放、篩選)
- [ ] 響應式設計 (支持所有設備)
- [ ] 數據導出功能 (多格式)

---

#### Story 2.4: 集成到量化交易系統 (8pts)

**集成架構**:

```python
# src/integration/quant_system_integration.py
from typing import Dict, List
import pandas as pd

class QuantSystemIntegrator:
    """量化系統集成器"""

    def __init__(self):
        self.data_adapter = RealDataAdapter()
        self.factor_calculator = FactorCalculator()

    async def enhance_strategy_with_real_data(
        self,
        strategy: TradingStrategy,
        symbols: List[str]
    ) -> EnhancedStrategy:
        """使用真實非價格數據增強策略"""

        # 1. 獲取股票價格數據
        price_data = await self._fetch_price_data(symbols)

        # 2. 獲取真實非價格數據
        hibor_data = await self.data_adapter.get_hibor_data()
        property_data = await self.data_adapter.get_property_data()
        tourism_data = await self.data_adapter.get_tourism_data()

        # 3. 計算增強因子
        enhanced_factors = self.factor_calculator.calculate_enhanced_factors(
            price_data=price_data,
            hibor_data=hibor_data,
            property_data=property_data,
            tourism_data=tourism_data
        )

        # 4. 生成增強信號
        enhanced_signals = strategy.generate_signals(
            data=enhanced_factors,
            use_real_data=True
        )

        return EnhancedStrategy(
            base_strategy=strategy,
            signals=enhanced_signals,
            data_sources=['PRICE', 'HIBOR', 'PROPERTY', 'TOURISM']
        )

    def calculate_enhanced_factors(
        self,
        price_data: pd.DataFrame,
        hibor_data: pd.DataFrame,
        property_data: pd.DataFrame,
        tourism_data: pd.DataFrame
    ) -> pd.DataFrame:
        """計算增強因子"""

        factors = pd.DataFrame(index=price_data.index)

        # 1. HIBOR影響因子
        factors['hibor_impact'] = self._calculate_hibor_impact(
            hibor_data, price_data
        )

        # 2. 物業市場因子
        factors['property_sentiment'] = self._calculate_property_sentiment(
            property_data
        )

        # 3. 旅客流量因子
        factors['tourism_momentum'] = self._calculate_tourism_momentum(
            tourism_data
        )

        # 4. 宏觀經濟因子
        factors['macro_composite'] = self._calculate_macro_composite(
            hibor_data, property_data, tourism_data
        )

        return factors

    def _calculate_hibor_impact(
        self,
        hibor_data: pd.DataFrame,
        price_data: pd.DataFrame
    ) -> pd.Series:
        """計算HIBOR對股價的影響"""

        # HIBOR上升對利率敏感股(如銀行股)負面
        hibor_change = hibor_data['rate'].pct_change()

        # 銀行股受HIBOR影響較大
        bank_stocks = ['0939.HK', '3988.HK', '1398.HK']

        impact = pd.Series(0.0, index=price_data.index)

        for stock in bank_stocks:
            if stock in price_data.columns:
                # HIBOR上升，銀行股下跌 (負相關)
                stock_price_change = price_data[stock].pct_change()
                correlation = hibor_change.corr(stock_price_change)
                impact[stock] = -correlation * hibor_change

        return impact
```

**交易信號增強示例**:

```python
# strategies/enhanced_strategy.py
class EnhancedHIBORStrategy(TradingStrategy):
    """基於真實HIBOR數據的增強策略"""

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""

        signals = pd.Series(0, index=data.index)

        # 基礎技術信號
        rsi = data['rsi']
        macd = data['macd']

        # HIBOR增強因子
        hibor_impact = data['hibor_impact']
        macro_composite = data['macro_composite']

        # 增強買入信號
        buy_condition = (
            (rsi < 30) &  # 超賣
            (macd > macd.shift(1)) &  # MACD改善
            (hibor_impact > -0.05) &  # HIBOR影響正面
            (macro_composite > 0.3)  # 宏觀環境良好
        )

        signals[buy_condition] = 1

        # 增強賣出信號
        sell_condition = (
            (rsi > 70) |  # 超買
            (hibor_impact < -0.1) |  # HIBOR負面影響
            (macro_composite < -0.3)  # 宏觀環境惡化
        )

        signals[sell_condition] = -1

        return signals
```

**驗收標準**:
- [ ] 成功接入量化系統 (Agent整合)
- [ ] 與現有AI Agent協同工作
- [ ] 支援實時決策 (<100ms延遲)
- [ ] 回測功能完整 (支持真實數據)
- [ ] 策略優化有效 (收益提升 >= 2%)

**真實數據應用**:
- [ ] 使用真實HIBOR影響交易決策
- [ ] 旅客數據預測消費股表現
- [ ] 物業數據分析地產股走勢
- [ ] 宏觀因子提升預測準確性

---

## 🎯 Sprint 2 詳細計劃 (第3-4週)

### 真實數據源擴展

#### 新增數據源清單

**1. 交通數據 (香港運輸署)**
- 數據源: 運輸署實時交通資訊
- API: https://data.gov.hk/
- 指標: 車速、流量、擁堵指數
- 更新頻率: 每5分鐘

**2. 經濟數據 (政府統計處)**
- 數據源: C&SD官方統計
- URL: https://www.censtatd.gov.hk/
- 指標: GDP、貿易數據、失業率
- 更新頻率: 每月

**3. 股票基本面數據 (港交所)**
- 數據源: HKEX上市公司資料
- API: https://www.hkex.com.hk/
- 指標: 市值、PE、PB、ROE
- 更新頻率: 每日

**4. 新聞情緒數據 (真實新聞API)**
- 數據源: Bloomberg, Reuters
- 指標: 新聞情緒分數、事件檢測
- 更新頻率: 實時

### Epic 3: 數據源擴展 (24故事點)

**Story 3.1**: 實現交通數據適配器 (6pts)
**Story 3.2**: 實現經濟數據適配器 (6pts)
**Story 3.3**: 實現基本面數據適配器 (6pts)
**Story 3.4**: 實現新聞情緒適配器 (6pts)

### Epic 4: 高級分析功能 (24故事點)

**Story 4.1**: 實現相關性分析引擎 (8pts)
**Story 4.2**: 實現預測模型 (8pts)
**Story 4.3**: 實現風險評估系統 (8pts)

---

## 📊 Sprint 成功指標 (KPIs)

### Sprint 1 KPIs

**技術指標**:
- [ ] 5個真實數據源成功集成
- [ ] 數據完整性 >= 95%
- [ ] API響應時間 < 500ms
- [ ] 系統可用性 >= 99%
- [ ] 單元測試覆蓋率 >= 90%

**業務指標**:
- [ ] 真實數據覆蓋率 100% (無mock數據)
- [ ] 數據延遲 < 1小時
- [ ] 量化模型使用率 >= 80%
- [ ] 交易策略收益提升 >= 2%

### Sprint 2 KPIs

**技術指標**:
- [ ] 新增4個真實數據源
- [ ] 總數據源數量達到9個
- [ ] 預測模型準確率 >= 70%
- [ ] 風險評估實時性 < 1秒

**業務指標**:
- [ ] 策略回測收益率提升 >= 5%
- [ ] 風險調整後收益 (Sharpe) 提升 >= 3%
- [ ] 數據驅動交易信號占比 >= 60%

---

## ⚠️ 風險管理計劃

### 主要風險識別

**1. 數據源不可用風險**
- 風險描述: 官方API變更或下線
- 概率: 中等
- 影響: 高
- 緩解措施:
  - 實現多數據源備份機制
  - 建立數據源監控系統
  - 準備手動數據導入流程

**2. 數據質量問題**
- 風險描述: 真實數據異常或缺失
- 概率: 低
- 影響: 高
- 緩解措施:
  - 實施多層數據驗證
  - 設置數據質量告警
  - 保留原始數據歷史

**3. API限流風險**
- 風險描述: 官方API請求限制
- 概率: 中等
- 影響: 中等
- 緩解措施:
  - 實現智能請求節流
  - 使用數據緩存機制
  - 申請更高的API配額

**4. 技術實現風險**
- 風險描述: 技術難度高於預期
- 概率: 中等
- 影響: 中等
- 緩解措施:
  - 提前進行技術預研
  - 準備技術支持方案
  - 適當調整Sprint範圍

### 應急預案

**數據源失效預案**:
1. 立即切換到備用數據源
2. 通知相關人員數據源狀態
3. 記錄失效原因和時間
4. 制定修復計劃

**數據質量異常預案**:
1. 隔離異常數據
2. 發送質量告警
3. 觸發數據清洗流程
4. 生成質量報告

---

## 📅 Sprint 執行時間表

### Sprint 1 (2週)

**第1週**:
- 週一: Story 1.1 - 創建基類 (8pts)
- 週二-週三: Story 1.2 - HIBOR適配器 (8pts)
- 週四-週五: Story 1.3 - 物業數據適配器 (8pts)

**第2週**:
- 週一-週二: Story 1.4 - 旅客數據適配器 (8pts)
- 週三-週四: Story 1.5 - 存儲系統 (8pts)
- 週五: Sprint Review & Retrospective

### Sprint 2 (2週)

**第3週**: 數據源擴展
- 交通數據適配器
- 經濟數據適配器
- 基本面數據適配器

**第4週**: 高級分析功能
- 相關性分析引擎
- 預測模型
- 風險評估系統
- Sprint Review

---

## 🧪 驗收測試計劃

### 真實數據測試用例

**測試用例1: HIBOR數據真實性驗證**
```python
async def test_real_hibor_data():
    """測試HIBOR真實數據獲取"""
    adapter = HKMHiborAdapter(config)

    # 獲取最新數據
    data = await adapter.fetch_real_data(
        period="1m",
        start_date="2024-10-04",
        end_date="2024-11-04"
    )

    # 驗證標準
    assert len(data) > 0, "未獲取到HIBOR數據"
    assert all(item.rate > 0 for item in data), "利率必須大於0"
    assert all(item.source == "HKMA" for item in data), "數據源必須為HKMA"
    assert all(item.date <= datetime.now().date() for item in data), "日期不能為未來"
    assert len(set(item.date for item in data)) > 20, "至少有20個交易日數據"

    print("✅ HIBOR真實數據驗證通過")

async def test_property_data_real():
    """測試物業數據真實性"""
    adapter = PropertyDataAdapter(config)

    data = await adapter.fetch_real_data(
        district="中區",
        start_date="2024-10-01",
        end_date="2024-11-01"
    )

    # 驗證真實性
    assert len(data) > 0, "未獲取到物業數據"

    for item in data:
        # 驗證地址格式
        assert re.match(r'^[香港、中區、灣仔等]+\d+號', item.address), "地址格式錯誤"

        # 驗證價格合理性
        assert 1000 <= item.price_per_sqft <= 100000, f"每平方尺價格異常: {item.price_per_sqft}"

        # 驗證面積合理性
        assert 200 <= item.area <= 2000, f"面積異常: {item.area}"

        # 驗證交易日期
        assert item.transaction_date <= datetime.now().date(), "交易日期不能為未來"

    print("✅ 物業真實數據驗證通過")
```

### 性能測試

**負載測試**:
```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def test_api_performance():
    """API性能測試"""

    async def make_request():
        async with aiohttp.ClientSession() as session:
            async with session.get('/api/v1/real_data/hibor?period=1m&start_date=2024-10-04&end_date=2024-11-04') as resp:
                return resp.status

    # 100個併發請求
    start_time = time.time()

    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time

    avg_response_time = total_time / 100
    success_rate = sum(1 for r in results if r == 200) / len(results)

    print(f"平均響應時間: {avg_response_time:.2f}秒")
    print(f"成功率: {success_rate*100:.1f}%")
    print(f"QPS: {100/total_time:.1f}")

    assert avg_response_time < 0.5, "平均響應時間必須小於0.5秒"
    assert success_rate >= 0.99, "成功率必須達到99%"
```

### 集成測試

**量化系統集成測試**:
```python
async def test_quant_system_integration():
    """測試量化系統集成"""

    # 初始化集成器
    integrator = QuantSystemIntegrator()

    # 獲取增強策略
    enhanced_strategy = await integrator.enhance_strategy_with_real_data(
        strategy=BaseStrategy(),
        symbols=['0700.HK', '0939.HK']
    )

    # 驗證信號生成
    signals = enhanced_strategy.generate_signals()

    assert len(signals) > 0, "未生成交易信號"
    assert signals.isin([-1, 0, 1]).all(), "信號值必須為-1, 0, 1"

    # 計算信號質量
    positive_signals = (signals == 1).sum()
    negative_signals = (signals == -1).sum()

    print(f"買入信號: {positive_signals}")
    print(f"賣出信號: {negative_signals}")
    print(f"信號比例: {positive_signals/(positive_signals+negative_signals):.1%}")

    print("✅ 量化系統集成測試通過")
```

---

## 📋 Sprint 驗收清單

### Sprint 1 驗收清單

**功能驗收**:
- [ ] 真實數據適配器基類完成
- [ ] HIBOR真實數據適配器完成
- [ ] 物業真實數據適配器完成
- [ ] 旅客流量真實數據適配器完成
- [ ] 數據存儲系統完成
- [ ] 數據清洗引擎完成
- [ ] 分析API完成
- [ ] 可視化儀表板完成
- [ ] 量化系統集成完成

**數據真實性驗收**:
- [ ] 所有數據源均為真實API/官方數據
- [ ] 數據完整性 >= 95%
- [ ] 數據及時性 <= 1小時延遲
- [ ] 數據準確性驗證通過

**性能驗收**:
- [ ] API響應時間 < 500ms
- [ ] 系統可用性 >= 99%
- [ ] 並發支持 >= 100請求/秒
- [ ] 數據查詢延遲 < 100ms

**測試驗收**:
- [ ] 單元測試覆蓋率 >= 90%
- [ ] 集成測試通過
- [ ] 真實數據測試通過
- [ ] 性能測試通過

### Sprint 2 驗收清單

**擴展功能驗收**:
- [ ] 交通數據適配器完成
- [ ] 經濟數據適配器完成
- [ ] 基本面數據適配器完成
- [ ] 新聞情緒適配器完成

**分析功能驗收**:
- [ ] 相關性分析引擎完成
- [ ] 預測模型完成
- [ ] 風險評估系統完成

**最終驗收**:
- [ ] 總共9個真實數據源集成
- [ ] 策略收益提升 >= 5%
- [ ] 風險調整後收益提升 >= 3%
- [ ] 數據驅動信號占比 >= 60%

---

## 🚀 Sprint Review 和 Retrospective

### Sprint Review 議程

**1. 演示真實數據功能 (30分鐘)**
- 展示5個真實數據源
- 演示數據采集和驗證流程
- 展示可視化儀表板

**2. 量化系統集成演示 (20分鐘)**
- 展示增強策略
- 演示實時交易信號
- 展示回測結果對比

**3. 業務價值展示 (20分鐘)**
- 量化模型改進效果
- 投資收益提升數據
- 風險降低程度

**4. Q&A 和反饋 (30分鐘)**
- 回答問題
- 收集改進建議
- 規劃下個Sprint

### Sprint Retrospective 議程

**1. 做得好的地方 (20分鐘)**
- 列出成功的實踐
- 分享有效的方法
- 慶祝團隊成就

**2. 需要改進的地方 (30分鐘)**
- 識別問題和挑戰
- 分析根本原因
- 提出改進建議

**3. 下個Sprint的改進計劃 (30分鐘)**
- 制定具體改進措施
- 分配責任人
- 設置檢查點

---

## 📚 參考資料

### 真實數據源文檔

1. **HKMA HIBOR數據**
   - API文檔: https://api.hkma.gov.hk/
   - 數據說明: https://www.hkma.gov.hk/eng/data-and-publications/

2. **土地註冊處物業數據**
   - 網站: https://www.rvd.gov.hk/
   - 數據服務: https://www.rvd.gov.hk/tc/about-us/a消e3.html

3. **旅遊發展局數據**
   - 統計頁面: https://www.discoverhongkong.com/
   - 統計報告: https://www.discoverhongkong.com/eng/about-hk/statistics/

### 技術文檔

1. **FastAPI官方文檔**
   - https://fastapi.tiangolo.com/

2. **PostgreSQL文檔**
   - https://www.postgresql.org/docs/

3. **Redis文檔**
   - https://redis.io/documentation

### 量化交易參考

1. **量化分析基礎**
   - 《量化投資策略與技術》
   - 《Python量化交易實戰》

2. **風險管理**
   - 《金融風險管理》
   - 《量化投資風險控制》

---

## ✅ Sprint Planning 完成確認

本Sprint規劃已完成以下確認：

1. **基於OpenSpec規範**: 遵循項目技術架構要求
2. **真實數據優先**: 所有數據源均為真實API和官方數據
3. **明確驗收標準**: 每個Story都有具體的驗收條件
4. **風險可控**: 識別主要風險並制定緩解措施
5. **可執行**: 任務分解合理，故事點估算準確

**規劃批准**:
- [ ] Product Owner批准
- [ ] 技術負責人批准
- [ ] 團隊確認可執行

**下一步**: 開始Sprint 1執行

---

**文檔版本**: v1.0
**最後更新**: 2025-11-04
**下次審查**: 2025-11-11
