# Mark6 集成規格說明

**規格ID**: mark6-integration-v1
**版本**: 1.0.0
**最後更新**: 2025-10-28

## 📋 規格概述

本規格說明定義了將香港六合彩（Mark6）功能集成到Telegram Bot的具體要求，提供下期開獎期數、日期和估計頭獎基金等關鍵信息。

## 🎯 改進目標

### 主要目標
1. 新增 `/mark6` 命令
2. 抓取官方HKJC網站數據
3. 提供簡潔準確的回應
4. 實施錯誤處理和備用機制

### 成功標準
- `/mark6` 命令響應時間 < 2秒
- 數據準確率 > 95%
- 回應格式簡潔 < 500字符
- 99% 正常運行時間

## ✅ 新增需求

### ADDED Requirements

#### M6-001: 創建 Mark6 數據服務
**描述**: The system MUST The system SHALL 創建 `mark6_service.py` 模組，負責抓取和解析HKJC網站數據

**文件位置**: `src/telegram_bot/mark6_service.py`

**核心類**:
```python
class Mark6Service:
    """香港六合彩數據服務"""

    async def get_next_draw_info(self) -> Optional[Dict]:
        """獲取下期攪珠信息"""
        # 從 https://bet.hkjc.com/ch/marksix 抓取
        pass

    async def get_last_draw_result(self) -> Optional[Dict]:
        """獲取上期開獎結果"""
        pass

    async def fetch_data(self) -> Optional[str]:
        """抓取原始HTML數據"""
        pass
```

**數據結構**:
```python
NextDrawInfo = {
    "draw_no": str,      # 期數，如 "2024125"
    "draw_date": str,    # 開獎日期，如 "2025-10-30"
    "draw_time": str,    # 開獎時間，如 "21:30"
    "estimated_prize": str,  # 估計頭獎基金，如 "28,000,000"
    "currency": str,     # 貨幣，"HKD"
    "sales_close": str,  # 截止售票時間，如 "21:15"
}

LastDrawResult = {
    "draw_no": str,           # 期數
    "draw_date": str,         # 開獎日期
    "winning_numbers": List[str],  # 6個中獎號碼
    "special_number": str,    # 特別號碼
}
```

**驗收條件**:
- [ ] 成功抓取HKJC網站數據
- [ ] 正確解析下期開獎信息
- [ ] 正確解析上期開獎結果
- [ ] 錯誤處理機制完善

**Scenario: 獲取下期攪珠信息**
```
用戶輸入: /mark6
系統回應:
🎰 六合彩下期攪珠

期數: 2024125
日期: 10月30日 (三)
時間: 21:30
估計頭獎基金: $2,800萬

💡 截止售票: 21:15
📅 開獎: 逢週二、四、六
```

#### M6-002: 實現 `/mark6` 命令
**描述**: The system MUST The system SHALL 在 `telegram_quant_bot.py` 中實現 `mark6_cmd()` 函數

**文件位置**: `src/telegram_bot/telegram_quant_bot.py`

**函數簽名**:
```python
async def mark6_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查詢香港六合彩下期開獎資訊"""
    # 實現邏輯
```

**實現要求**:
1. **響應速度**: 調用mark6_service.get_next_draw_info()
2. **格式簡潔**: 回應 < 500字符
3. **錯誤處理**: 網站不可用時提供友好提示
4. **用戶體驗**: 發送"🔍 正在查詢..."提示

**驗收條件**:
- [ ] 命令註冊成功
- [ ] 正確調用Mark6Service
- [ ] 格式化回應符合要求
- [ ] 錯誤情況處理得當

**Scenario: 正常情況**
```
用戶輸入: /mark6
系統回應: "🔍 正在查詢..."
系統回應: [格式化的攪珠信息]
```

**Scenario: 網站不可用**
```
用戶輸入: /mark6
系統回應: "🔍 正在查詢..."
系統回應: "❌ 無法獲取攪珠信息，請稍後重試"
```

#### M6-003: 註冊 `/mark6` 命令處理器
**描述**: The system MUST The system SHALL 在 `build_app()` 函數中註冊新命令

**修改位置**: `src/telegram_bot/telegram_quant_bot.py:1652`

**代碼示例**:
```python
# 添加新命令
app.add_handler(CommandHandler("mark6", mark6_cmd))

# 更新命令列表
commands = [
    BotCommand("mark6", "六合彩資訊"),
    # ... 其他命令
]
```

**驗收條件**:
- [ ] 命令成功註冊
- [ ] Bot命令列表包含 "mark6"
- [ ] 命令描述顯示為"六合彩資訊"

#### M6-004: 更新幫助文檔
**描述**: The system MUST The system SHALL 在幫助文檔中添加 `/mark6` 命令說明

**修改位置**: `src/telegram_bot/telegram_quant_bot.py:321`

**添加內容**:
```python
"💰 六合彩：\n"
"/mark6  - 查看下期攪珠資訊（期數、日期、頭獎基金）\n"
```

**驗收條件**:
- [ ] 幫助文檔包含Mark6說明
- [ ] 說明清晰簡潔
- [ ] 放在"生活服務"分類下

#### M6-005: 實施數據快取
**描述**: The system MUST The system SHALL 為Mark6數據實施快取機制，避免重複抓取

**快取配置**:
```python
MARK6_CACHE_TTL = 3600  # 1小時

# 為什麼是1小時？
# - 攪珠信息每天更新1-2次
# - 避免頻繁抓取給服務器壓力
# - 1小時足夠響應用戶需求
```

**實現方式**:
```python
class Mark6Service:
    _cache = {}
    _cache_time = {}

    async def get_next_draw_info(self):
        # 檢查快取
        if self._is_cache_valid():
            return self._cache["next_draw"]

        # 抓取新數據
        data = await self._fetch_and_parse()
        self._cache["next_draw"] = data
        self._cache_time["next_draw"] = time.time()
        return data
```

**驗收條件**:
- [ ] 快取機制正常工作
- [ ] TTL設置為3600秒
- [ ] 快取失效時自動更新

## 🔍 測試需求

### 單元測試

#### T-M6-001: 測試數據抓取
```python
@pytest.mark.asyncio
async def test_mark6_data_parsing():
    """測試HTML數據解析"""
    service = Mark6Service()

    # 模擬HTML數據
    html = """
    <div class="next-draw">
        <span>2024125</span>
        <span>2025-10-30</span>
        <span>$28,000,000</span>
    </div>
    """

    result = await service.parse_html(html)
    assert result["draw_no"] == "2024125"
    assert result["draw_date"] == "2025-10-30"
    assert result["estimated_prize"] == "28,000,000"
```

#### T-M6-002: 測試命令響應
```python
@pytest.mark.asyncio
async def test_mark6_command():
    """測試/mark6命令響應"""
    update = MockUpdate()
    context = MockContext()

    await mark6_cmd(update, context)

    # 驗證回應包含必要信息
    assert "期數" in context.last_message
    assert "日期" in context.last_message
    assert "頭獎基金" in context.last_message
```

#### T-M6-003: 測試錯誤處理
```python
@pytest.mark.asyncio
async def test_mark6_error_handling():
    """測試網站不可用時的錯誤處理"""
    service = Mark6Service()
    service.fetch_data = Mock(side_effect=Exception("Network error"))

    result = await service.get_next_draw_info()
    assert result is None
```

### 集成測試

#### T-M6-004: 端到端測試
```python
@pytest.mark.asyncio
async def test_mark6_e2e():
    """測試完整流程"""
    bot = TestBot("test_token")

    response = await bot.send_command("/mark6")

    assert response.status_code == 200
    assert "期數" in response.text
    assert response.text_length < 500
```

#### T-M6-005: 性能測試
```python
@pytest.mark.asyncio
async def test_mark6_performance():
    """測試響應時間"""
    start_time = time.time()

    service = Mark6Service()
    await service.get_next_draw_info()

    elapsed = time.time() - start_time
    assert elapsed < 2.0  # 目標 < 2秒
```

## 📊 性能需求

### 性能指標
- **響應時間**: < 2秒 (90%分位)
- **數據準確率**: > 95%
- **服務可用性**: 99%
- **快取命中率**: > 80%

### 監控指標
```python
MARK6_METRICS = {
    "fetch_success_rate": "數據抓取成功率",
    "avg_response_time": "平均響應時間",
    "cache_hit_rate": "快取命中率",
    "error_count": "錯誤次數",
    "user_request_count": "用戶請求次數",
}
```

## 🔄 錯誤處理

### 錯誤場景

#### 場景1: HKJC網站不可訪問
**處理方式**:
```python
try:
    data = await service.get_next_draw_info()
except (aiohttp.ClientError, asyncio.TimeoutError):
    await reply_long(update, "❌ 網站暫時無法訪問，請稍後重試")
```

#### 場景2: 數據解析失敗
**處理方式**:
```python
if not data or "draw_no" not in data:
    await reply_long(update, "❌ 數據格式異常，已通知管理員")
    # 記錄日誌
    logger.error(f"Mark6數據解析失敗: {data}")
```

#### 場景3: 網絡超時
**處理方式**:
```python
async with aiohttp.ClientTimeout(total=5):
    data = await service.fetch_data()
```

### 備用機制
1. **多重數據源**:
   - 主源: https://bet.hkjc.com/ch/marksix
   - 備用: https://bet.hkjc.com/marksix (英文版)

2. **本地備份**:
   - 存儲最近3天的數據
   - 網站不可用時使用備份數據

3. **降級策略**:
   - 網站失效：返回友好錯誤提示
   - 解析失敗：記錄日誌並通知管理員

## 📝 實施檢查清單

- [ ] M6-001: 創建mark6_service.py
- [ ] M6-002: 實現mark6_cmd()函數
- [ ] M6-003: 註冊命令處理器
- [ ] M6-004: 更新幫助文檔
- [ ] M6-005: 實施快取機制
- [ ] T-M6-001: 單元測試 - 數據抓取
- [ ] T-M6-002: 單元測試 - 命令響應
- [ ] T-M6-003: 單元測試 - 錯誤處理
- [ ] T-M6-004: 集成測試
- [ ] T-M6-005: 性能測試
- [ ] 文檔更新
- [ ] 部署檢查

---

**規格作者**: Claude Code
**審核狀態**: 待審核
**優先級**: 高
**估計工期**: 5天
**依賴**: command-simplification (必須先完成)
