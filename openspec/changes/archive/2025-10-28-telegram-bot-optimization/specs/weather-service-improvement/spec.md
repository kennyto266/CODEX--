# 天氣服務改進規格說明

**規格ID**: weather-service-improvement-v1
**版本**: 1.0.0
**最後更新**: 2025-10-28

## 📋 規格概述

本規格說明定義了將天氣服務升級為使用香港天文台官方API的具體要求，提供更準確的實時天氣數據和警告信號信息。

## 🎯 改進目標

### 主要目標
1. 接入香港天文台官方API (http://weather.gov.hk/)
2. 提升天氣數據準確率至95%以上
3. 獲取實時警告信號
4. 保持向下兼容現有接口

### 成功標準
- 數據準確率 > 95% (原75%)
- 回應時間 < 2秒
- 支持18區天氣查詢
- 實時警告信號顯示

## ✅ 修改需求

### MODIFIED Requirements

#### WSI-001: 升級天氣數據服務
**描述**: The system MUST The system SHALL 修改 `weather_service.py`，接入香港天文台API

**文件位置**: `src/telegram_bot/weather_service.py`

**新增功能**:
```python
class HKOWeatherService:
    """香港天文台天氣服務"""

    async def get_current_weather(self, region: str = "") -> Optional[Dict]:
        """獲取實時天氣數據"""
        # 從天文台API獲取
        pass

    async def get_weather_warnings(self) -> List[Dict]:
        """獲取當前天氣警告"""
        # 從天文台API獲取警告信號
        pass

    async def get_9day_forecast(self) -> List[Dict]:
        """獲取九天預報"""
        # 從天文台API獲取
        pass

    async def get_uv_index(self) -> Optional[Dict]:
        """獲取紫外線指數"""
        pass
```

**數據源**:
- **主要API**: http://weather.gov.hk/wxinfo/currwx/fnday.htm
- **警告API**: http://weather.gov.hk/wx/warning/wnsum.htm
- **UV指數**: http://weather.gov.hk/wxinfo/currwx/uvindex.htm

**數據格式**:
```python
CurrentWeather = {
    "region": str,                # 地區名稱
    "temperature": float,         # 溫度 (°C)
    "humidity": int,              # 濕度 (%)
    "wind_direction": str,        # 風向
    "wind_speed": str,            # 風速
    "weather": str,               # 天氣狀況
    "uv_index": Optional[int],    # 紫外線指數
    "update_time": str,           # 數據更新時間
    "data_source": "天文台",      # 數據來源
}

WeatherWarning = {
    "warning_type": str,          # 警告類型
    "warning_code": str,          # 警告代碼
    "issue_time": str,            # 發出時間
    "description": str,           # 警告描述
    "valid_until": Optional[str], # 有效期至
}
```

**支持的18區**:
```
中西區、灣仔區、南區、深水埗、油尖旺、九龍城、
黃大仙、觀塘、葵青、荃灣、屯門、元朗、北區、
大埔、沙田、西貢、葵青、島嶼
```

**驗收條件**:
- [ ] 成功獲取天文台數據
- [ ] 數據準確率 > 95%
- [ ] 支持18區查詢
- [ ] 警告信號正確顯示

**Scenario: 查詢香港整體天氣**
```
用戶輸入: /weather
系統回應:
🌤️ 香港天氣 (2025-10-28 14:00)

🌡️ 溫度: 26°C (濕度 65%)
🌬️ 風向: 東風 15 km/h
☁️ 天氣: 部分多雲

⚠️ 警告: 酷熱天氣警告

🔆 UV指數: 7 (高)

📊 數據源: 香港天文台
```

**Scenario: 查詢特定地區天氣**
```
用戶輸入: /weather 九龍城
系統回應:
🌤️ 九龍城區天氣 (14:00)

🌡️ 溫度: 27°C (濕度 62%)
🌬️ 風向: 東南風 12 km/h
☁️ 天氣: 天晴

📊 數據源: 香港天文台
```

#### WSI-002: 實施智能快取
**描述**: The system MUST The system SHALL 為天氣數據實施分級快取機制

**快取策略**:
```python
WEATHER_CACHE_CONFIG = {
    "current_weather": {
        "ttl": 900,    # 15分鐘
        "description": "實時天氣數據"
    },
    "weather_warnings": {
        "ttl": 1800,   # 30分鐘
        "description": "天氣警告信號"
    },
    "9day_forecast": {
        "ttl": 3600,   # 1小時
        "description": "九天預報"
    },
    "uv_index": {
        "ttl": 1800,   # 30分鐘
        "description": "UV指數"
    }
}
```

**實現方式**:
```python
class WeatherCacheManager:
    _cache = {}
    _cache_metadata = {}

    async def get(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            ttl = self._cache_metadata[key]["ttl"]
            if time.time() - timestamp < ttl:
                return data
        return None

    async def set(self, key: str, data, ttl: int):
        self._cache[key] = (data, time.time())
        self._cache_metadata[key] = {"ttl": ttl}
```

**驗收條件**:
- [ ] 快取機制正常工作
- [ ] TTL設置合理
- [ ] 命中率 > 80%
- [ ] 內存使用 < 50MB

#### WSI-003: 優化回應格式
**描述**: The system MUST The system SHALL 簡化天氣回應格式，突出核心信息

**舊格式**:
```
🌤️ 香港天氣 (2025-10-28 14:00)

📍 地區: 香港
🌡️ 氣溫: 26.5°C
💧 濕度: 65%
🌬️ 風向: 東風
🌬️ 風速: 15 公里/小時
☁️ 天氣: 部分多雲
🌅 日出: 06:32
🌇 日落: 17:45
🌡️ 最高溫: 29°C
🌡️ 最低溫: 24°C
💧 降雨量: 0.0 mm
📊 氣壓: 1015.6 hPa
🌡️ 露點: 19.2°C
... (過多技術參數)
```

**新格式**:
```
🌤️ 香港天氣 (14:00)

🌡️ 26°C (濕度 65%)
🌬️ 東風 15 km/h
☁️ 部分多雲

⚠️ 酷熱天氣警告
🔆 UV指數: 7 (高)

📊 數據源: 香港天文台
⏰ 更新: 5分鐘前
```

**驗收條件**:
- [ ] 回應長度 < 400字符 (原 > 1000字符)
- [ ] 突出核心信息（溫度、濕度、天氣、警告）
- [ ] 移除冗餘技術參數
- [ ] 保持信息準確性

#### WSI-004: 添加警告信號支持
**描述**: The system MUST The system SHALL 實時顯示香港天文台發布的天氣警告

**支持的警告類型**:
```
✅ 酷熱天氣警告
✅ 雷暴警告
✅ 颱風警告
✅ 火警危險警告
✅ 黃雨警告
✅ 紅雨警告
✅ 黑雨警告
✅ 強烈季候風信號
✅ 新界北區水浸警告
```

**顯示格式**:
```
⚠️ 天氣警告 (2025-10-28 14:00)

🔥 酷熱天氣警告
   生效時間: 12:30
   持續時間: 2小時30分鐘

💧 雷暴警告
   生效時間: 11:00
   預計持續: 至 17:00

⚠️ 請注意防暑
💡 戶外活動請多補水
```

**實現方式**:
```python
def format_weather_warnings(warnings: List[Dict]):
    if not warnings:
        return "✅ 目前沒有天氣警告"

    text = "⚠️ 天氣警告\n\n"
    for warning in warnings:
        icon = WARNING_ICONS.get(warning["warning_code"], "⚠️")
        text += f"{icon} {warning['warning_type']}\n"
        text += f"   生效: {warning['issue_time']}\n\n"

    text += "💡 請留意天氣變化"
    return text
```

**驗收條件**:
- [ ] 正確獲取警告信號
- [ ] 警告類型識別準確
- [ ] 顯示格式清晰
- [ ] 警告更新及時

#### WSI-005: 實施錯誤處理與回退
**描述**: The system MUST The system SHALL 天文台API失效時的錯誤處理和回退機制

**錯誤場景與處理**:

1. **API超時** (5秒):
```python
try:
    data = await fetch_hko_data(timeout=5)
except asyncio.TimeoutError:
    # 嘗試緩存數據
    cached_data = await self.cache.get("weather")
    if cached_data:
        return cached_data
    return self._get_error_message("timeout")
```

2. **網站不可訪問**:
```python
except aiohttp.ClientError:
    # 嘗試備用API
    return await self._fetch_from_backup_api()
```

3. **數據解析失敗**:
```python
except (KeyError, ValueError) as e:
    logger.error(f"天氣數據解析失敗: {e}")
    return self._get_error_message("parse_error")
```

**回退策略**:
```python
class WeatherServiceWithFallback:
    def __init__(self):
        self.primary = HKOWeatherService()  # 香港天文台
        self.backup = ThirdPartyWeatherAPI()  # 備用第三方API
        self.cache = WeatherCache()  # 本地快取

    async def get_weather(self, region):
        try:
            # 1. 嘗試天文台
            return await self.primary.get(region)
        except:
            try:
                # 2. 嘗試備用API
                return await self.backup.get(region)
            except:
                # 3. 嘗試快取
                cached = await self.cache.get(region)
                if cached:
                    return self._add_fallback_notice(cached)
                # 4. 返回友好錯誤
                return self._get_error_message()
```

**驗收條件**:
- [ ] API失效時自動回退
- [ ] 快取數據正常返回
- [ ] 錯誤消息友好準確
- [ ] 日誌記錄完整

#### WSI-006: 保留向下兼容
**描述**: The system MUST The system SHALL 保持與現有代碼的向下兼容性

**保持不變**:
```python
# 原有的 weather_service 函數
async def weather_service(update: Update, context):
    data = await get_weather_data()  # 內部調用新服務
    # 保持原接口
```

**接口說明**:
```python
class WeatherService:
    """向下兼容的天氣服務接口"""

    async def get_current_weather(self, region: str = ""):
        """獲取當前天氣"""
        return await self.hko_service.get_current_weather(region)

    def format_weather_message(self, data: Dict, region: str = ""):
        """格式化天氣消息"""
        # 保持與現有代碼兼容
        return self._format_message(data, region)
```

**驗收條件**:
- [ ] 現有代碼無需修改
- [ ] 新舊接口一致
- [ ] 功能完全兼容
- [ ] 測試通過

## 🔍 測試需求

### 單元測試

#### T-WSI-001: 測試天文台數據獲取
```python
@pytest.mark.asyncio
async def test_hko_data_fetching():
    """測試天文台數據獲取"""
    service = HKOWeatherService()

    data = await service.get_current_weather()

    assert data["temperature"] > 0
    assert data["humidity"] > 0
    assert data["data_source"] == "天文台"
```

#### T-WSI-002: 測試警告信號獲取
```python
@pytest.mark.asyncio
async def test_weather_warnings():
    """測試天氣警告獲取"""
    service = HKOWeatherService()

    warnings = await service.get_weather_warnings()

    for warning in warnings:
        assert "warning_type" in warning
        assert "issue_time" in warning
```

#### T-WSI-003: 測試快取機制
```python
@pytest.mark.asyncio
async def test_weather_cache():
    """測試天氣數據快取"""
    cache = WeatherCacheManager()

    # 設置數據
    await cache.set("weather", {"temp": 26}, 900)

    # 獲取未過期數據
    data = await cache.get("weather")
    assert data["temp"] == 26

    # 等待過期
    await asyncio.sleep(1)
    data = await cache.get("weather")
    assert data is None
```

#### T-WSI-004: 測試錯誤回退
```python
@pytest.mark.asyncio
async def test_fallback_mechanism():
    """測試錯誤回退機制"""
    service = WeatherServiceWithFallback()
    service.primary.get = Mock(side_effect=Exception("Error"))

    data = await service.get_weather("香港")

    # 應該從備用源或快取獲取數據
    assert data is not None
    assert "數據源" in data
```

### 集成測試

#### T-WSI-005: 端到端測試
```python
@pytest.mark.asyncio
async def test_weather_e2e():
    """測試完整天氣服務"""
    bot = TestBot("test_token")

    response = await bot.send_command("/weather")

    assert response.status_code == 200
    assert "香港天氣" in response.text
    assert "數據源" in response.text
    assert response.text_length < 400
```

#### T-WSI-006: 性能測試
```python
@pytest.mark.asyncio
async def test_weather_performance():
    """測試天氣服務性能"""
    start_time = time.time()

    service = HKOWeatherService()
    await service.get_current_weather()

    elapsed = time.time() - start_time
    assert elapsed < 2.0
```

### 準確性測試

#### T-WSI-007: 數據準確率驗證
```python
@pytest.mark.asyncio
async def test_data_accuracy():
    """測試天氣數據準確率"""
    service = HKOWeatherService()
    bot_data = await service.get_current_weather()

    # 與官方網站對比
    official_data = await fetch_hko_official()

    temp_diff = abs(bot_data["temperature"] - official_data["temperature"])
    assert temp_diff <= 1.0  # 溫差 < 1°C

    humidity_diff = abs(bot_data["humidity"] - official_data["humidity"])
    assert humidity_diff <= 5  # 濕度差 < 5%
```

**準確率目標**: 95% 以上

## 📊 性能需求

### 性能指標
- **響應時間**: < 2秒 (90%分位)
- **數據準確率**: > 95%
- **服務可用性**: 99%
- **快取命中率**: > 80%
- **錯誤率**: < 2%

### 監控指標
```python
WEATHER_METRICS = {
    "avg_response_time": "平均響應時間",
    "cache_hit_rate": "快取命中率",
    "data_accuracy": "數據準確率",
    "api_success_rate": "API成功率",
    "warning_update_rate": "警告更新頻率",
    "user_satisfaction": "用戶滿意度",
}
```

## 🔄 向下兼容

### 兼容策略
1. **保持接口**: 現有 `weather_service()` 函數不變
2. **保持格式**: 回應格式基本一致
3. **增強功能**: 添加警告信號、UV指數等
4. **性能提升**: 僅優化，不破壞現有功能

### 遷移策略
1. **第一週**: 新服務作為備用
2. **第二週**: 設為主要服務
3. **第三週**: 移除舊服務代碼

## 📝 實施檢查清單

- [ ] WSI-001: 升級天氣數據服務
- [ ] WSI-002: 實施智能快取
- [ ] WSI-003: 優化回應格式
- [ ] WSI-004: 添加警告信號支持
- [ ] WSI-005: 實施錯誤處理與回退
- [ ] WSI-006: 保留向下兼容
- [ ] T-WSI-001: 單元測試 - 數據獲取
- [ ] T-WSI-002: 單元測試 - 警告信號
- [ ] T-WSI-003: 單元測試 - 快取機制
- [ ] T-WSI-004: 單元測試 - 錯誤回退
- [ ] T-WSI-005: 集成測試
- [ ] T-WSI-006: 性能測試
- [ ] T-WSI-007: 準確性測試
- [ ] 文檔更新
- [ ] 部署檢查

---

**規格作者**: Claude Code
**審核狀態**: 待審核
**優先級**: 中高
**估計工期**: 5天
**依賴**: command-simplification
