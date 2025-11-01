# Add Advanced Technical Indicators Backtest

## Why
當前回測系統僅支持 4 種基礎技術指標策略（RSI、MACD、布林帶、MA交叉），限制了策略研究的廣度。添加 7 種高級技術指標（KDJ、CCI、ADX、ATR、OBV、Ichimoku、Parabolic SAR）可以提供更全面的市場分析視角，並通過 0-300 參數範圍的網格搜索找到最優策略組合。

## What Changes
- 添加 KDJ/Stochastic 隨機指標策略（K/D 閾值參數範圍 0-100，步距 5）
- 添加 CCI 商品通道指標策略（超買/超賣閾值 -300 至 +300，步距 5）
- 添加 ADX 平均趨向指標策略（ADX 閾值 0-100，步距 5，配合 +DI/-DI）
- 添加 ATR 平均真實範圍策略（波動率倍數 0-10，步距 0.5）
- 添加 OBV 能量潮指標策略（配合價格趨勢確認）
- 添加 Ichimoku 一目均衡表策略（轉換線/基準線/延遲線參數範圍 0-60，步距 5）
- 添加 Parabolic SAR 拋物線轉向指標策略（加速因子 0-1，步距 0.05）
- 為每個指標實現參數優化函數（類似現有 `_optimize_rsi_parameters`）
- 更新 `optimize_parameters()` 支持新指標類型選擇
- 擴展 `calculate_technical_indicators()` 計算新指標（部分已存在但未用於策略）

## Impact
- Affected specs: `strategy-backtest`
- Affected code:
  - `enhanced_strategy_backtest.py:49-99` (calculate_technical_indicators 擴展)
  - `enhanced_strategy_backtest.py:257-290` (optimize_parameters 添加新指標類型)
  - 新增 7 個策略執行方法：`run_kdj_strategy`, `run_cci_strategy`, `run_adx_strategy`, `run_atr_strategy`, `run_obv_strategy`, `run_ichimoku_strategy`, `run_parabolic_sar_strategy`
  - 新增 7 個參數優化方法：`_optimize_kdj_parameters`, `_optimize_cci_parameters`, 等
- Performance impact: 參數組合數量大幅增加，建議使用多進程並行優化（已有 ThreadPoolExecutor 支持）
- Estimated testing combinations per indicator: ~100-300 組合（取決於參數範圍）
