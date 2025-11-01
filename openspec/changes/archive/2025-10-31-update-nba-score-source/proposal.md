# 更新 NBA 比分來源

## Why

當前 Telegram bot 的 NBA 比分功能僅返回模擬數據，無法獲取真實的 NBA 比賽信息。現有的 `src/telegram_bot/sports_scoring/nba_scraper.py` 中 `_fetch_from_espn()` 方法未實現實際 API 調用，導致用戶無法獲得真實的 NBA 比賽比分和狀態。

參考 `real_data_fetcher.py` 中足球比分實現的成功經驗，我們需要為 NBA scraper 整合 ESPN 公開 API，提供真實的 NBA 比分數據，提升用戶體驗。

## What Changes

### Modified Files
- `src/telegram_bot/sports_scoring/nba_scraper.py`: 完全重寫數據獲取邏輯

### New Features
- 整合 ESPN NBA API 端點: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard`
- 實現真實數據解析邏輯（參考 `real_data_fetcher.py` 模式）
- 保留模擬數據作為備用方案
- 添加錯誤處理和重試機制
- 添加請求超時控制（10秒）
- 實現球隊名稱格式化函數（30 支 NBA 球隊）
- 添加詳細的日誌記錄

### Implementation Details
1. **ESPN NBA API 整合**
   - 使用 aiohttp 異步獲取 NBA比分數據
   - 實現 `_fetch_from_espn()` 真實 API 調用邏輯
   - 解析 ESPN API 響應的 JSON 數據

2. **數據解析和格式化**
   - 提取比賽基本信息（球隊名稱、比分）
   - 提取比賽狀態（scheduled/live/finished）
   - 提取時間信息（剩餘時間、節次）
   - 格式化球隊名稱（簡化英文名稱）

3. **錯誤處理機制**
   - API 失敗時自動切換到備用模擬數據
   - 網絡超時處理（10秒超時）
   - JSON 解析錯誤處理
   - 詳細的日誌記錄

4. **向後兼容性**
   - 保持 `fetch_scores()` 方法簽名不變
   - 保持返回數據格式一致
   - 現有調用代碼無需修改

## Impact

### Affected Specs
- `nba-scraper`: 更新 NBA 數據獲取規格

### Affected Code
- `src/telegram_bot/sports_scoring/nba_scraper.py`: 核心修改
  - `fetch_scores()` 方法實現真實 API 調用
  - `_fetch_from_espn()` 方法實現 ESPN API 整合
  - `_parse_espn_response()` 方法新增數據解析邏輯
  - `format_team_name()` 方法擴展球隊名稱映射

### Performance Impact
- API 調用時間: < 5 秒（正常情況）
- 超時處理: 10 秒後自動切換到備用數據
- 內存使用: 最小影響（僅存儲必要數據）

### Testing Impact
需要添加測試用例：
- Mock ESPN API 響應測試
- 錯誤處理測試（API 失敗、超時等）
- 備用數據機制測試
- 向後兼容性測試

---

**提案創建日期**: 2025-10-31
**負責人**: Claude Code
**狀態**: 待審核

## 實施完成記錄

### 完成的變更
- ✅ 實現 ESPN NBA API 整合（`site/v2` 端點）
- ✅ 實現數據解析和格式化邏輯
- ✅ 添加錯誤處理和備用方案
- ✅ 測試 ESPN API 調用功能（獲取 4 場真實比賽）
- ✅ 驗證向後兼容性（所有測試通過）

### 測試結果
- **真實數據獲取**: 成功獲取 4 場 NBA 比賽
- **數據格式**: 所有 11 個字段完整
- **向後兼容性**: 100% 通過（方法簽名、返回格式一致）
- **錯誤處理**: 6 種異常類型完整處理

### 修改的文件
1. `src/telegram_bot/sports_scoring/nba_scraper.py` - 核心功能更新
2. `test_nba_espn_simple.py` - API 測試
3. `test_nba_backward_compat.py` - 兼容性測試

### 成果
- Telegram bot 現在可以獲取真實 NBA 比分
- 保持現有代碼無需修改
- 提供可靠的備用機制

**完成時間**: 2025-10-31 15:20
**狀態更新**: ✅ 已完成
