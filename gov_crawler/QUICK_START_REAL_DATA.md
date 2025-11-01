# 真實數據收集系統 - 快速啟動指南

## 🚨 重要提醒

**此系統僅處理真實數據，絕對禁止使用 mock 數據！**

所有 mock 數據生成功能已被完全移除，系統會自動檢測並拒絕任何 mock 數據。

---

## ⚡ 快速啟動

### 1. 檢查系統狀態

```bash
cd gov_crawler
python quick_real_data_test.py
```

### 2. 啟動真實數據收集

```bash
python start_real_data_collection.py
```

### 3. 運行完整測試

```bash
python test_real_data_collection.py
```

---

## 📊 支持的數據源

| 數據源 | 優先級 | 狀態 | 描述 |
|--------|--------|------|------|
| HKMA HIBOR | 🔴 高 | ✅ 完成 | 銀行同業拆息 |
| C&SD 經濟統計 | 🔴 高 | ✅ 完成 | GDP、零售等 |
| 土地註冊處 | 🟡 中 | 📋 計劃中 | 物業交易數據 |
| 旅遊發展局 | 🟡 中 | 📋 計劃中 | 訪客統計 |

---

## 🛠️ 使用示例

### 獲取 HIBOR 數據

```python
from adapters.real_data.hibor.hkma_hibor_adapter import HKMAHiborAdapter

async with HKMAHiborAdapter() as adapter:
    df = await adapter.fetch_real_data('2025-10-01', '2025-10-27')
    print(f"獲取 {len(df)} 條真實 HIBOR 記錄")
```

### 獲取經濟數據

```python
from adapters.real_data.economic.csd_economic_adapter import CSDEconomicAdapter

async with CSDEconomicAdapter() as adapter:
    df = await adapter.fetch_real_data('2025-01-01', '2025-12-31')
    print(f"獲取 {len(df)} 條真實經濟數據記錄")
```

### 統一收集

```python
from collect_real_data_only import RealDataOnlyCollector

collector = RealDataOnlyCollector()
results = await collector.collect_all_real_data(
    start_date='2025-10-01',
    end_date='2025-10-27'
)
print(f"成功: {results['successful_collections']}/{len(collector.adapters)}")
```

---

## ✅ 驗證真實數據

系統自動檢查以下指標：

1. **Mock 標記檢查**
   ```python
   if 'is_mock' in df.columns and df['is_mock'].any():
       raise MockDataError("檢測到 mock 數據！")
   ```

2. **時間戳驗證**
   ```python
   dates = pd.to_datetime(df['date'], errors='coerce')
   if dates.isna().any():
       raise ValueError("無效的日期格式")
   ```

3. **數值範圍檢查**
   ```python
   if rates.min() < -1.0 or rates.max() > 15.0:
       raise ValueError("數值超出合理範圍")
   ```

---

## 📁 重要文件

| 文件 | 描述 |
|------|------|
| `REAL_DATA_SYSTEM_FINAL.md` | 完整系統文檔 |
| `base_real_adapter.py` | 適配器基類 |
| `hkma_hibor_adapter.py` | HKMA HIBOR 適配器 |
| `csd_economic_adapter.py` | C&SD 經濟適配器 |
| `collect_real_data_only.py` | 統一收集器 |
| `start_real_data_collection.py` | 啟動腳本 |
| `WEB_EXPLORATION_RESULTS.md` | 網頁探索報告 |

---

## 🔍 檢查數據質量

```python
# 獲取質量報告
quality_report = await adapter.validate_data_quality(df, start_date, end_date)

print(f"總體分數: {quality_report.overall_score:.2f}")
print(f"真實數據: {'是' if quality_report.is_real_data else '否'}")
print(f"可接受: {'是' if quality_report.is_acceptable() else '否'}")
```

**質量閾值**:
- 總體分數 >= 0.85
- `is_real_data = true`
- 無驗證錯誤

---

## ⚠️ 常見問題

### Q: 如何檢查數據是否為真實數據？
A: 系統自動檢查 `is_real` 標記和 `is_mock` 標記。所有真實數據都應設置 `is_real=True` 和 `is_mock=False`。

### Q: 如果遇到 mock 數據會怎樣？
A: 系統會立即拋出 `MockDataError` 異常，拒絕處理該數據，並記錄詳細錯誤。

### Q: 數據質量分數低於 0.85 怎麼辦？
A: 檢查 `quality_report.validation_errors` 和 `warnings` 字段，定位問題並修復。

### Q: 如何添加新的數據源？
A: 創建新的適配器，繼承 `RealDataAdapter`，實現 `fetch_real_data` 方法。

---

## 🚀 下一步

1. **立即執行**:
   ```bash
   python start_real_data_collection.py
   ```

2. **查看數據**:
   ```bash
   ls -la data/real_data/
   ```

3. **檢查質量報告**:
   ```bash
   ls -la data/quality_reports/
   ```

4. **查看日誌**:
   ```bash
   tail -f logs/real_data_collection.log
   ```

---

## 📞 支持

如需幫助，請查看：
- 完整文檔: `REAL_DATA_SYSTEM_FINAL.md`
- 網頁探索結果: `WEB_EXPLORATION_RESULTS.md`
- OpenSpec 提案: `../openspec/changes/expand-gov-crawler-data-collection/`

---

**最後更新**: 2025-10-27
**狀態**: ✅ 生產就緒
**版本**: v1.0.0
