# 核心架構重構設計 (Core Architecture Refactoring Design)

## 概述

當前系統存在以下問題：
1. **功能重覆**: 多個模塊進行相似的數據獲取、清理和處理工作
2. **缺乏清晰的職責邊界**: 適配器、管道、儀表板和回測引擎之間的責任不明確
3. **難以維護和擴展**: 添加新的數據源或性能計算方法需要修改多個地方
4. **代碼散亂**: 相同功能分散在 `src/data_adapters/`, `src/data_pipeline/`, `src/backtest/`, 等多個位置

## 新架構設計

重構後的系統分為三個明確的層次，每層有清晰的責任和邊界：

```
┌─────────────────────────────────────────────────────────┐
│         Visualization Tools (視覺化工具層)               │
│  Dashboard | Charts | Interactive Reports | Analytics   │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│       Performance Calculation (效能計算層)               │
│  Error Detection | Normalization | Aggregation         │
│  Trading Logic | Variable Management | Result Output   │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│         Data Management (數據管理層)                     │
│  Data Fetching | Cleaning | Temporal Alignment         │
│  Asset Profiling | Database Operations                 │
└─────────────────────────────────────────────────────────┘
```

### 第一層：數據管理 (Data Management)

**責任**:
- 從多個數據源獲取原始數據 (HTTP API, Yahoo Finance, Alpha Vantage, 原始文件等)
- 進行數據清理和驗證
- 時間格式轉換和標準化 (temporal alignment)
- 資產檔案管理 (asset profiles)
- 數據庫持久化操作

**核心模塊**:
- `src/data_pipeline/sources/` - 統一數據源接口
  - `base_source.py` - 基類
  - `http_api_source.py` - HTTP API 適配器
  - `file_source.py` - 文件讀取
  - `market_data_source.py` - 市場數據專用

- `src/data_pipeline/cleaners/` - 數據清理
  - `data_cleaner.py` - 基礎清理
  - `outlier_detector.py` - 異常檢測
  - `missing_data_handler.py` - 缺失數據處理

- `src/data_pipeline/processors/` - 數據處理
  - `temporal_aligner.py` - 時間對齐
  - `asset_profiler.py` - 資產檔案
  - `normalizer.py` - 數據標準化

- `src/database/` - 數據持久化
  - `models.py` - 數據模型
  - `operations.py` - CRUD 操作
  - `queries.py` - 查詢接口

**移除的重覆代碼**:
- `src/data_adapters/` - 大部分內容遷移到 `sources/`
- `src/data_pipeline/data_cleaner.py` 和 `cleaners.py` 的重覆邏輯統一
- 回測引擎內的數據獲取邏輯統一到本層

### 第二層：效能計算 (Performance Calculation)

**責任**:
- 異常檢測 (基於統計的異常值識別)
- 結果標準化 (性能指標歸一化)
- 結果彙總 (聚合多個策略/資產的結果)
- 交易邏輯執行 (信號生成、訂單執行)
- 變數管理 (策略參數、配置)
- 參數管理 (優化參數存儲和檢索)

**核心模塊**:
- `src/core/` - 核心計算引擎
  - `signal_generator.py` - 交易信號生成
  - `variable_manager.py` - 變數管理系統
  - `parameter_manager.py` - 參數管理系統
  - `execution_engine.py` - 訂單執行邏輯

- `src/analysis/` - 分析模塊
  - `error_detector.py` - 異常檢測
  - `normalizer.py` - 結果標準化
  - `aggregator.py` - 結果彙總
  - `performance_calculator.py` - 性能指標計算

- `src/strategies/` - 策略定義
  - `base_strategy.py` - 基類
  - `technical_strategies.py` - 技術面策略
  - `ml_strategies.py` - 機器學習策略
  - `hybrid_strategies.py` - 混合策略

- `src/backtest/` - 回測引擎 (重構)
  - `core_backtest_engine.py` - 核心回測邏輯 (使用第一層的數據)
  - `strategy_evaluator.py` - 策略評估
  - `portfolio_simulator.py` - 投資組合模擬

**移除的重覆代碼**:
- `src/optimization/` 中的參數搜索邏輯統一到 `parameter_manager.py`
- 多個回測文件的重覆計算邏輯統一
- Agent 中的計算邏輯重構為可重用的模塊

### 第三層：視覺化工具 (Visualization Tools)

**責任**:
- Web 儀表板 (FastAPI)
- 圖表和數據可視化
- 互動式報告生成
- 實時性能分析

**核心模塊**:
- `src/dashboard/` - Web 儀表板 (重構)
  - `api_routes.py` - API 路由 (使用統一的數據和計算接口)
  - `chart_service.py` - 圖表服務
  - `report_generator.py` - 報告生成
  - `websocket_manager.py` - 實時更新

- `src/visualization/` - 可視化引擎
  - `chart_builder.py` - 圖表構建
  - `report_builder.py` - 報告構建
  - `analytics_dashboard.py` - 分析儀表板

**移除的重覆代碼**:
- 儀表板中的數據處理邏輯應該調用第二層的 API，而不是直接進行計算

## 數據流向

```
數據源 (HTTP API, 文件, 市場數據)
  ↓
數據管理層 (清理、驗證、標準化)
  ↓
數據庫 (持久化)
  ↓
效能計算層 (交易邏輯、參數管理、指標計算)
  ↓
結果存儲 (性能指標、信號)
  ↓
視覺化工具層 (儀表板、報告、圖表)
```

## 關鍵改進

### 1. 單一職責原則 (Single Responsibility Principle)
每個模塊只負責一件事，減少耦合。

### 2. 統一的接口
- 數據管理層: `IDataSource`, `IDataCleaner`
- 效能計算層: `IStrategy`, `IAnalyzer`
- 視覺化工具層: `IChartBuilder`, `IReportGenerator`

### 3. 依賴注入 (Dependency Injection)
模塊之間通過接口通信，方便測試和替換實現。

### 4. 配置集中管理
- 數據源配置
- 策略參數
- 顯示選項

## 遷移策略

1. **Phase 1**: 建立新的目錄結構和基類
2. **Phase 2**: 逐步遷移數據管理相關代碼
3. **Phase 3**: 重構效能計算層
4. **Phase 4**: 更新視覺化工具層
5. **Phase 5**: 刪除舊的重覆代碼

## 預期效果

1. **代碼重用率提高**: 相同功能不再分散
2. **可維護性提升**: 清晰的職責邊界，易於理解和修改
3. **易於擴展**: 添加新功能只需在對應的層添加新模塊
4. **測試覆蓋率提高**: 更小的模塊更容易測試
5. **性能優化機會**: 統一的接口方便引入快取和優化
