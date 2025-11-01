# 香港市場量化分析 - 文件索引

生成日期: 2025-10-24

---

## 📊 主要報告文件

### 1. 執行摘要
**文件**: `EXECUTIVE_SUMMARY_HK_QUANT_ANALYSIS.md`
**用途**: 高層決策者閱讀，包含核心發現和策略建議
**長度**: 中等（約50頁）
**閱讀時間**: 15-20分鐘

### 2. 完整分析報告
**文件**: `FINAL_QUANT_ANALYSIS_REPORT.md`
**用途**: 詳細技術分析報告，包含所有統計結果和策略評估
**長度**: 長（約100頁）
**閱讀時間**: 1-2小時

### 3. 快速開始指南
**文件**: `QUICK_START_GUIDE.md`
**用途**: 快速了解關鍵發現和如何使用分析工具
**長度**: 短（約10頁）
**閱讀時間**: 5分鐘

### 4. 本索引文件
**文件**: `ANALYSIS_INDEX.md`
**用途**: 所有文件的導航指南
**長度**: 短
**閱讀時間**: 5分鐘

---

## 🔬 分析代碼

### 1. 綜合量化分析器
**文件**: `comprehensive_hk_quant_analysis.py`
**功能**:
- 加載HIBOR、HKEX、訪客數據
- 數據質量評估
- 相關性分析（Pearson, Spearman）
- 滯後相關性分析
- Granger因果性檢驗
- 風險指標計算（VaR, CVaR, Sharpe, Sortino）
- 交易策略建議
- 可視化生成
- 結果導出

**運行**:
```bash
python comprehensive_hk_quant_analysis.py
```

**輸出**: analysis_output/ 目錄下的所有文件

### 2. 6個月HIBOR預測策略
**文件**: `hibor_6m_prediction_strategy.py`
**功能**:
- 基於6M HIBOR的交易策略
- 信號生成
- 回測引擎
- 參數敏感性分析
- 性能可視化

**運行**:
```bash
python hibor_6m_prediction_strategy.py
```

**輸出**: 策略回測報告和圖表

---

## 📁 數據文件

### 原始數據源

#### HIBOR利率數據
**文件**: `gov_crawler/data/hibor_data_20251023_205904.csv`
**內容**: 262天的HIBOR日度數據
**字段**:
- date
- hibor_overnight
- hibor_1m
- hibor_3m
- hibor_6m
- hibor_12m

#### 訪客統計數據
**文件**: `gov_crawler/data/visitor_data_20251023_205904.csv`
**內容**: 12個月訪客統計
**字段**:
- date
- visitor_arrivals_total
- visitor_arrivals_mainland
- visitor_arrivals_growth

#### HKEX市場數據
**文件**: `hkex爬蟲/data/hkex_all_market_data.csv`
**內容**: 33個交易日市場數據
**字段**:
- Date
- Trading_Volume
- Advanced_Stocks, Declined_Stocks, Unchanged_Stocks
- Turnover_HKD
- Deals
- Morning_Close, Afternoon_Close
- Change, Change_Percent

#### 房地產數據
**文件**: `gov_crawler/data/processed/property_property_market_price_20251023_220832.csv`
**內容**: 1982-1998年季度房價數據
**注**: 本次分析未使用（歷史數據過舊）

---

### 分析輸出數據

#### 合併數據集
**文件**: `analysis_output/merged_dataset_20251024_035022.csv`
**內容**: HKEX + HIBOR合併後的完整數據集
**行數**: 33
**用途**: 所有分析的基礎數據

#### 相關性矩陣
**文件**: `analysis_output/correlation_matrix_20251024_035022.csv`
**內容**: Pearson相關性矩陣
**維度**: 9x9
**用途**: 識別變量間線性關係

#### 滯後相關性
**文件**: `analysis_output/lagged_correlations_20251024_035022.csv`
**內容**: 0-5天滯後的相關性分析
**行數**: 30（5個HIBOR × 6個滯後期）
**用途**: 識別預測關係

#### Granger因果性結果
**文件**: `analysis_output/granger_causality_20251024_035022.csv`
**內容**: Granger因果性檢驗結果
**行數**: 25（5個HIBOR × 5個滯後期）
**關鍵發現**: 6M HIBOR在所有滯後期均顯著

#### 風險指標
**文件**: `analysis_output/risk_metrics_20251024_035022.json`
**內容**:
```json
{
  "sharpe_ratio": 0.563,
  "sortino_ratio": 0.977,
  "max_drawdown": -0.075,
  "var_95": -0.021,
  "var_99": -0.030,
  "cvar_95": -0.029,
  "cvar_99": -0.032,
  "beta": 0.095,
  "alpha": 0.128,
  "win_rate": 0.531,
  "win_loss_ratio": 0.978
}
```

#### 交易策略參數
**文件**: `analysis_output/trading_strategies_20251024_035022.csv`
**內容**: 4個交易策略的參數配置
**策略**:
1. HIBOR Mean Reversion
2. Volume Momentum
3. HIBOR Term Structure
4. Turnover Efficiency

#### 6M HIBOR策略交易記錄
**文件**: `analysis_output/hibor_6m_trades_20251024_035308.csv`
**內容**: 回測期間的所有交易記錄
**字段**:
- exit_date
- direction (LONG/SHORT)
- pnl
- pnl_pct

#### 6M HIBOR策略信號
**文件**: `analysis_output/hibor_6m_signals_20251024_035308.csv`
**內容**: 每日的信號生成記錄
**字段**:
- Date
- Afternoon_Close
- hibor_6m
- hibor_6m_change
- signal (-1/0/1)
- position
- Returns

---

## 📈 可視化圖表

### 1. 相關性熱力圖
**文件**: `analysis_output/correlation_heatmap.png`
**描述**: 9x9相關性矩陣熱力圖
**要點**:
- 12M HIBOR與市場正相關（+0.257）
- 交易筆數與市場負相關（-0.397）

### 2. 時間序列總覽
**文件**: `analysis_output/time_series_overview.png`
**描述**: 三個子圖
- 市場收盤價走勢
- HIBOR利率走勢（5條曲線）
- 交易量柱狀圖

### 3. 收益分佈
**文件**: `analysis_output/returns_distribution.png`
**描述**: 兩個子圖
- 收益直方圖（含均值和中位數）
- Q-Q圖（正態性檢驗）
**發現**: 略微左偏，尾部較薄

### 4. HIBOR-收益散點圖
**文件**: `analysis_output/hibor_returns_scatter.png`
**描述**: 5個子圖（5個HIBOR期限）
- 散點圖 + 回歸線
- 顯示相關係數
**發現**: 大部分相關性較弱

### 5. 累計收益與回撤
**文件**: `analysis_output/cumulative_returns_drawdown.png`
**描述**: 兩個子圖
- 累計收益曲線
- 回撤曲線（最大-7.48%）

### 6. 6M HIBOR策略結果
**文件**: `analysis_output/hibor_6m_strategy_results.png`
**描述**: 6個子圖
- 權益曲線（策略 vs 買入持有）
- 回撤曲線
- 6M HIBOR走勢
- 交易信號標註
- 交易盈虧分佈
- 累計收益對比

---

## 📝 文本報告

### 1. 綜合分析報告
**文件**: `analysis_output/comprehensive_analysis_report_20251024_035022.txt`
**內容**:
- 數據來源摘要
- 風險指標總結
- 關鍵相關性
- 推薦策略參數

### 2. 6M HIBOR策略報告
**文件**: `analysis_output/hibor_6m_strategy_report_20251024_035308.txt`
**內容**:
- 策略參數
- 回測結果
- 性能指標

---

## 🗂 文件結構樹

```
CODEX--/
├── 📄 主要報告
│   ├── EXECUTIVE_SUMMARY_HK_QUANT_ANALYSIS.md
│   ├── FINAL_QUANT_ANALYSIS_REPORT.md
│   ├── QUICK_START_GUIDE.md
│   └── ANALYSIS_INDEX.md (本文件)
│
├── 🐍 Python代碼
│   ├── comprehensive_hk_quant_analysis.py
│   └── hibor_6m_prediction_strategy.py
│
├── 📊 原始數據
│   ├── gov_crawler/data/
│   │   ├── hibor_data_20251023_205904.csv
│   │   ├── visitor_data_20251023_205904.csv
│   │   └── processed/property_property_market_price_*.csv
│   └── hkex爬蟲/data/
│       └── hkex_all_market_data.csv
│
└── 📈 分析輸出
    └── analysis_output/
        ├── 數據文件
        │   ├── merged_dataset_20251024_035022.csv
        │   ├── correlation_matrix_20251024_035022.csv
        │   ├── lagged_correlations_20251024_035022.csv
        │   ├── granger_causality_20251024_035022.csv
        │   ├── risk_metrics_20251024_035022.json
        │   ├── trading_strategies_20251024_035022.csv
        │   ├── hibor_6m_trades_20251024_035308.csv
        │   └── hibor_6m_signals_20251024_035308.csv
        │
        ├── 可視化
        │   ├── correlation_heatmap.png
        │   ├── time_series_overview.png
        │   ├── returns_distribution.png
        │   ├── hibor_returns_scatter.png
        │   ├── cumulative_returns_drawdown.png
        │   └── hibor_6m_strategy_results.png
        │
        └── 文本報告
            ├── comprehensive_analysis_report_20251024_035022.txt
            └── hibor_6m_strategy_report_20251024_035308.txt
```

---

## 📖 閱讀順序建議

### 對於高管/決策者
1. `QUICK_START_GUIDE.md` (5分鐘)
2. `EXECUTIVE_SUMMARY_HK_QUANT_ANALYSIS.md` (15分鐘)
3. 查看關鍵圖表:
   - `correlation_heatmap.png`
   - `hibor_6m_strategy_results.png`

### 對於量化分析師
1. `EXECUTIVE_SUMMARY_HK_QUANT_ANALYSIS.md` (15分鐘)
2. `FINAL_QUANT_ANALYSIS_REPORT.md` (1小時)
3. 審閱所有可視化圖表
4. 檢查數據文件:
   - `granger_causality_*.csv`
   - `lagged_correlations_*.csv`
5. 運行代碼驗證結果

### 對於交易員
1. `QUICK_START_GUIDE.md` (5分鐘)
2. 風險管理章節（報告中）
3. 交易策略參數:
   - `trading_strategies_*.csv`
4. 查看策略表現:
   - `hibor_6m_strategy_results.png`

### 對於開發人員
1. `comprehensive_hk_quant_analysis.py` 代碼
2. `hibor_6m_prediction_strategy.py` 代碼
3. 數據結構:
   - `merged_dataset_*.csv`
4. 實施風險管理框架（報告中）

---

## 🔍 關鍵數據點快速查找

### Granger因果性（6M HIBOR）
**位置**: `analysis_output/granger_causality_20251024_035022.csv`
**關鍵行**:
- hibor_6m, lag=1, p=0.017
- hibor_6m, lag=2, p=0.015
- hibor_6m, lag=3, p=0.018

### 滯後相關性（12M HIBOR）
**位置**: `analysis_output/lagged_correlations_20251024_035022.csv`
**關鍵行**:
- hibor_12m, lag=2, correlation=-0.374, p=0.038

### 風險指標
**位置**: `analysis_output/risk_metrics_20251024_035022.json`
**關鍵指標**:
```json
{
  "sharpe_ratio": 0.563,
  "alpha": 0.128,
  "max_drawdown": -0.075
}
```

### 策略參數
**位置**: `analysis_output/trading_strategies_20251024_035022.csv`
**推薦策略**:
- Volume Momentum
- HIBOR Term Structure

---

## 💡 使用提示

### 如何重新運行分析
1. 確保虛擬環境激活：`.venv310\Scripts\activate`
2. 運行主分析：`python comprehensive_hk_quant_analysis.py`
3. 運行策略測試：`python hibor_6m_prediction_strategy.py`
4. 查看結果：`cd analysis_output`

### 如何修改參數
1. 編輯Python文件中的配置部分
2. 例如在 `hibor_6m_prediction_strategy.py` 中:
   ```python
   strategy = HIBOR6MStrategy(
       hibor_threshold=0.001,  # 修改這裡
       holding_period=5,       # 修改這裡
       position_size=0.20      # 修改這裡
   )
   ```

### 如何擴展數據
1. 將新的HKEX數據放入 `hkex爬蟲/data/`
2. 更新 `hkex_all_market_data.csv`
3. 重新運行分析

---

## ⚠️ 注意事項

1. **數據時效性**: 數據截至2025-10-17，需要定期更新
2. **樣本期限**: HKEX數據僅33天，建議擴展至6個月以上
3. **策略表現**: 當前回測表現不理想，需要優化
4. **風險警告**: 歷史表現不代表未來收益

---

## 📞 技術支持

**問題排查**:
1. 數據加載錯誤 → 檢查文件路徑
2. 依賴包缺失 → `pip install -r requirements.txt`
3. 結果異常 → 查看日誌輸出

**代碼問題**:
- 查看代碼註釋
- 參考 `FINAL_QUANT_ANALYSIS_REPORT.md` 技術實施章節

---

## 🔄 更新日誌

**Version 1.0 (2025-10-24)**:
- 初始版本
- 完整量化分析
- 5個交易策略
- 完整文檔

**計劃更新**:
- 擴展數據至6-12個月
- 優化6M HIBOR策略
- 增加機器學習模型
- 實時數據管道

---

**最後更新**: 2025-10-24 03:53:00
**版本**: 1.0
**狀態**: 完成

---

**索引結束** 📊
