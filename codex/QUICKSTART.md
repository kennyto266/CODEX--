# 快速開始指南

## 3步驟快速使用

### 1. 準備你的數據

CSV格式，必需欄位：
```
date,symbol,open,high,low,close,volume
```

### 2. 運行優化器

**Windows:**
```bash
run_optimizer.bat 你的數據.csv
```

**Linux/Mac:**
```bash
chmod +x run_optimizer.sh
./run_optimizer.sh 你的數據.csv
```

**或直接使用Python:**
```bash
python simple_strategy_optimizer.py --data 你的數據.csv
```

### 3. 查看結果

結果保存在 `results/` 目錄：
- `optimization_results.csv` - 所有300個週期的完整結果
- `top_10_strategies.csv` - 前10名最佳策略
- `best_strategy_backtest.csv` - 最佳策略詳細回測

## 測試運行

使用示例數據測試：

```bash
# Windows
run_optimizer.bat ..\examples\raw_data_sample.csv

# Linux/Mac
./run_optimizer.sh ../examples/raw_data_sample.csv

# Python直接運行
python simple_strategy_optimizer.py --data ../examples/raw_data_sample.csv
```

## 自定義參數

```bash
# 只測試週期5-100，步距2
python simple_strategy_optimizer.py --data 數據.csv --start 5 --end 100 --step 2

# 指定輸出目錄
python simple_strategy_optimizer.py --data 數據.csv --output my_results
```

## 輸出示例

```
============================================================
開始優化: 週期範圍 1-300, 步距 1
============================================================
進度: 週期 10/300, 當前最佳Sharpe: 19.6280 (週期 2)
進度: 週期 20/300, 當前最佳Sharpe: 19.6280 (週期 2)
...
[OK] 優化完成！
最佳週期: 2
最佳Sharpe比率: 19.6280

============================================================
前10名策略參數:
============================================================
週期:   2 | Sharpe: 19.6280 | 年化收益: 309.00% | 年化波動:  15.74%
週期:   3 | Sharpe: 19.6280 | 年化收益: 309.00% | 年化波動:  15.74%
...

所有結果已保存至: results\optimization_results.csv
前10名策略已保存至: results\top_10_strategies.csv
最佳策略回測詳情已保存至: results\best_strategy_backtest.csv
```

## 理解結果

- **Sharpe Ratio**: 風險調整後收益，>2為優秀，>1為良好
- **Annual Return**: 年化收益率（已考慮複利）
- **Annual Volatility**: 年化波動率（風險指標）
- **Total Return**: 整個測試期間的總收益率

## 離線使用

此工具100%離線運行：
- ✅ 無需網絡連接
- ✅ 無需API密鑰
- ✅ 所有計算本地完成
- ✅ 數據完全由你控制

## 常見問題

**Q: 為什麼計算這麼快？**
A: 使用Pandas向量化計算，300個週期只需幾秒。

**Q: 可以改變策略嗎？**
A: 可以！編輯 `simple_strategy_optimizer.py` 中的 `moving_average_strategy()` 方法。

**Q: 支援多個股票嗎？**
A: 支援！CSV中包含多個symbol即可，系統會自動處理。

**Q: 數據需要什麼格式？**
A: 標準OHLCV格式（開高低收量），日期必須是YYYY-MM-DD。

## 更多信息

查看完整文檔: `STRATEGY_OPTIMIZER_README.md`
