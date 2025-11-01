# Spec: NBA Scraper 更新

## ADDED Requirements

### 1. ESPN NBA API 整合
**Requirement**: NBA scraper 必須能夠從 ESPN 公開 API 獲取真實比分數據

#### Scenario: 成功獲取 NBA 比分
- **Given**: ESPN API 端點可訪問且返回有效數據
- **When**: 調用 `fetch_scores()` 方法
- **Then**: 返回包含真實 NBA 比分數據的列表

#### Scenario: API 不可用時的備用機制
- **Given**: ESPN API 端點無法訪問或返回錯誤
- **When**: 調用 `fetch_scores()` 方法
- **Then**: 自動切換到備用模擬數據模式，返回模擬比賽數據

#### Scenario: 網絡超時處理
- **Given**: API 請求超時（>10秒）
- **When**: 調用 `fetch_scores()` 方法
- **Then**: 捕獲超時異常，記錄日誌，並返回備用數據

### 2. 數據解析和格式化
**Requirement**: 必須正確解析 ESPN API 響應並格式化為統一數據結構

#### Scenario: 解析完整的比賽信息
- **Given**: ESPN API 返回完整比賽數據
- **When**: 解析數據
- **Then**: 提取並格式化以下字段：
  - `date`: 比賽日期（YYYY-MM-DD）
  - `home_team`: 主隊名稱（中文或英文簡稱）
  - `away_team`: 客隊名稱
  - `home_score`: 主隊得分（整數）
  - `away_score`: 客隊得分（整數）
  - `status`: 比賽狀態（scheduled/live/finished）
  - `quarter`: 當前節次（Q1/Q2/Q3/Q4/Final）
  - `time_remaining`: 剩餘時間（MM:SS 格式）
  - `league`: 聯賽名稱（NBA）

#### Scenario: 處理進行中的比賽
- **Given**: 比賽狀態為 "In Progress"
- **When**: 解析數據
- **Then**:
  - `status` 設置為 "live"
  - 提取當前節次（Q1-Q4）
  - 提取剩餘時間（MM:SS）

#### Scenario: 處理已結束的比賽
- **Given**: 比賽狀態為 "Final"
- **When**: 解析數據
- **Then**:
  - `status` 設置為 "finished"
  - `quarter` 設置為 "Final"
  - `time_remaining` 設置為 "0:00" 或 None

#### Scenario: 處理未開始的比賽
- **Given**: 比賽狀態為 "Scheduled"
- **When**: 解析數據
- **Then**:
  - `status` 設置為 "scheduled"
  - `quarter` 設置為 None
  - `time_remaining` 設置為 None
  - 比分設置為 0

### 3. 球隊名稱格式化
**Requirement**: 必須將 ESPN 球隊名稱格式化為用戶友好的格式

#### Scenario: 格式化標準 NBA 球隊名稱
- **Given**: ESPN 返回的球隊名稱如 "Los Angeles Lakers"
- **When**: 調用 `format_team_name()` 方法
- **Then**: 返回簡化名稱 "Lakers"

#### Scenario: 支持中文球隊名稱
- **Given**: 系統配置為中文模式
- **When**: 格式化球隊名稱
- **Then**: 返回中文名稱（如 "湖人"）

### 4. 錯誤處理機制
**Requirement**: 必須具備完善的錯誤處理，避免程序崩潰

#### Scenario: JSON 解析失敗
- **Given**: ESPN API 返回無效 JSON
- **When**: 嘗試解析響應
- **Then**: 捕獲 JSONDecodeError，記錄日誌，返回備用數據

#### Scenario: 數據字段缺失
- **Given**: ESPN API 響應缺少某些字段
- **When**: 解析數據
- **Then**: 使用默認值或跳過該比賽，繼續處理其他比賽

#### Scenario: 網絡連接錯誤
- **Given**: 網絡連接中斷
- **When**: 發送 API 請求
- **Then**: 捕獲連接錯誤，記錄日誌，啟用備用數據

### 5. 性能要求
**Requirement**: API 調用必須高效且有適當的限制

#### Scenario: API 請求超時
- **Given**: 配置超時時間為 10 秒
- **When**: API 響應時間超過 10 秒
- **Then**: 自動終止請求，記錄超時日誌，使用備用數據

#### Scenario: 請求間隔控制
- **Given**: 連續多次調用
- **When**: 發送請求
- **Then**: 在請求之間添加 0.5 秒延遲，避免過於頻繁的請求

### 6. 日誌記錄
**Requirement**: 必須記錄關鍵操作和錯誤信息

#### Scenario: 記錄成功操作
- **Given**: 成功獲取並解析 NBA 數據
- **When**: 完成操作
- **Then**: 記錄 INFO 級別日誌，包含獲取到的比賽數量

#### Scenario: 記錄錯誤和警告
- **Given**: 發生錯誤或使用備用數據
- **When**: 完成操作
- **Then**: 記錄 ERROR 或 WARNING 級別日誌，包含錯誤原因

## MODIFIED Requirements

### 1. fetch_scores() 方法簽名
**Requirement**: 保持現有 API 介面不變，向後兼容

#### Before:
```python
async def fetch_scores(self) -> List[Dict[str, Any]]:
    """獲取 NBA 當日比分（僅模擬數據）"""
```

#### After:
```python
async def fetch_scores(self) -> List[Dict[str, Any]]:
    """
    獲取 NBA 當日比分

    首先嘗試從 ESPN 獲取真實數據，
    如果失敗則使用備用模擬數據

    Returns:
        List[Dict[str, Any]]: 比賽數據列表
    """
```

**Validation**: 現有調用此方法的代碼無需修改

### 2. 數據返回格式
**Requirement**: 保持現有返回數據格式

#### Before:
```python
{
    "date": "2025-10-31",
    "home_team": "Lakers",
    "away_team": "Celtics",
    "home_score": 118,
    "away_score": 102,
    "status": "finished",
    "quarter": "Final",
    "time_remaining": "0:00",
    "start_time": "10:30",
    "venue": "Crypto.com Arena",
    "league": "NBA"
}
```

#### After:
- 保持完全相同的數據結構
- 可能額外添加字段（如 `minute`, `added_time`）但非必須
- 現有字段必須保持一致

**Validation**: 使用現有數據的代碼不會受到影響

## REMOVED Requirements

### 1. 模擬數據的優先使用
**Requirement**: 不再優先使用模擬數據

#### Before:
- 默認返回模擬數據
- 真實 API 調用是次要選項

#### After:
- 默認嘗試獲取真實數據
- 模擬數據僅作為備用方案

**Reason**: 提供真實比分是核心需求，模擬數據僅用於故障轉移

## Backward Compatibility

### API 介面兼容性
- ✅ `fetch_scores()` 方法保持不變
- ✅ 返回數據格式保持一致
- ✅ 現有調用代碼無需修改

### 行為變更
- ⚠️ 當 ESPN API 可用時，現在返回真實數據而非模擬數據
- ⚠️ 可能返回不同的球隊名稱格式（取決於 ESPN API）

### 向後兼容策略
如果新實現導致現有功能異常：
1. 檢查 `use_mock_data` 配置選項
2. 如果設置為 True，則跳過真實 API 調用
3. 直接使用備用模擬數據

## Testing Requirements

### 單元測試覆蓋率
- [ ] ESPN API 調用測試（Mock aiohttp）
- [ ] JSON 數據解析測試
- [ ] 錯誤處理測試
- [ ] 球隊名稱格式化測試
- [ ] 備用數據機制測試

### 集成測試
- [ ] 完整比分獲取流程測試
- [ ] API 失敗時的降級測試
- [ ] 多比賽數據解析測試

### 測試數據
- Mock ESPN API 響應數據
- 各種比賽狀態的測試案例
- 錯誤場景測試數據

---

**Spec 版本**: 1.0
**創建日期**: 2025-10-31
**狀態**: 待審核
