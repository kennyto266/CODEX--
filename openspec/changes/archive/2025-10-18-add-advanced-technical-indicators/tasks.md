# Implementation Tasks

## 1. 擴展技術指標計算
- [ ] 1.1 在 `calculate_technical_indicators()` 中添加完整的 KDJ/Stochastic 計算
- [ ] 1.2 添加 CCI (Commodity Channel Index) 計算
- [ ] 1.3 完善 ADX 計算（包括 +DI 和 -DI）
- [ ] 1.4 確保 ATR 計算正確（已存在，需驗證）
- [ ] 1.5 添加 OBV (On-Balance Volume) 計算
- [ ] 1.6 添加 Ichimoku Cloud 所有組件（轉換線、基準線、先行帶 A/B、延遲線）
- [ ] 1.7 添加 Parabolic SAR 計算

## 2. 實現策略執行方法
- [ ] 2.1 實現 `run_kdj_strategy(k_period, d_period, overbought, oversold)`
- [ ] 2.2 實現 `run_cci_strategy(period, overbought, oversold)`
- [ ] 2.3 實現 `run_adx_strategy(period, adx_threshold)`
- [ ] 2.4 實現 `run_atr_strategy(period, atr_multiplier)`
- [ ] 2.5 實現 `run_obv_strategy(trend_period)`
- [ ] 2.6 實現 `run_ichimoku_strategy(conversion, base, span_b)`
- [ ] 2.7 實現 `run_parabolic_sar_strategy(acceleration, max_acceleration)`

## 3. 實現參數優化方法
- [ ] 3.1 實現 `_optimize_kdj_parameters(max_workers)` - K/D 週期 5-30（步距5），閾值 20-80（步距5）
- [ ] 3.2 實現 `_optimize_cci_parameters(max_workers)` - 週期 10-30（步距5），閾值 -300 至 +300（步距25）
- [ ] 3.3 實現 `_optimize_adx_parameters(max_workers)` - 週期 10-30（步距5），ADX閾值 15-50（步距5）
- [ ] 3.4 實現 `_optimize_atr_parameters(max_workers)` - 週期 10-30（步距5），倍數 0.5-5.0（步距0.5）
- [ ] 3.5 實現 `_optimize_obv_parameters(max_workers)` - 趨勢週期 10-100（步距10）
- [ ] 3.6 實現 `_optimize_ichimoku_parameters(max_workers)` - 轉換線 5-15（步距5），基準線 20-40（步距5），延遲線 40-60（步距5）
- [ ] 3.7 實現 `_optimize_parabolic_sar_parameters(max_workers)` - 加速因子 0.01-0.2（步距0.01），最大加速 0.1-0.5（步距0.05）

## 4. 更新優化器主方法
- [ ] 4.1 在 `optimize_parameters()` 中添加新策略類型：'kdj', 'cci', 'adx', 'atr', 'obv', 'ichimoku', 'parabolic_sar'
- [ ] 4.2 確保 'all' 選項包含所有 11 種策略（原有4種 + 新增7種）
- [ ] 4.3 更新日誌輸出以反映測試的策略範圍

## 5. 測試與驗證
- [ ] 5.1 為每個新策略編寫單元測試（test_core_functions.py）
- [ ] 5.2 測試參數優化性能（確保多線程正常工作）
- [ ] 5.3 對比新舊指標的回測結果合理性
- [ ] 5.4 驗證參數範圍涵蓋常用技術分析閾值
- [ ] 5.5 運行完整回測測試 0939.HK 股票（所有指標）

## 6. 文檔更新
- [ ] 6.1 更新 CLAUDE.md 中的策略列表
- [ ] 6.2 在 enhanced_strategy_backtest.py 頂部 docstring 列出新增的 7 種指標
- [ ] 6.3 為每個新方法添加完整的 docstring 說明
- [ ] 6.4 更新 README.md 的策略回測部分
