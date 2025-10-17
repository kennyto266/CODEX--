# 簡潔股票回測策略優化器

極致簡潔的離線優先股票回測工具，用於計算最佳Sharpe ratio。

## 特點

- ✅ **極致簡潔**: 單一Python文件，無複雜依賴
- ✅ **離線優先**: 所有計算在本地完成，無需網絡連接
- ✅ **自動優化**: 自動掃描參數範圍(1-300)找出最佳Sharpe ratio
- ✅ **快速執行**: 純NumPy/Pandas向量化計算
- ✅ **完整輸出**: 提供優化結果、前10名策略、詳細回測數據

## 安裝依賴

```bash
pip install pandas numpy
```

## 數據格式

CSV文件需包含以下欄位：
- `date`: 日期（YYYY-MM-DD格式）
- `symbol`: 股票代碼
- `open`: 開盤價
- `high`: 最高價
- `low`: 最低價
- `close`: 收盤價
- `volume`: 成交量（可選）

示例：
```csv
date,symbol,open,high,low,close,volume
2024-01-01,0001.HK,100.00,105.00,99.00,104.00,1000000
2024-01-02,0001.HK,104.00,106.00,100.00,105.00,1100000
```

## 使用方法

### 基本使用（默認參數：1-300，步距1）

```bash
python simple_strategy_optimizer.py --data your_data.csv
```

### 自定義參數範圍

```bash
python simple_strategy_optimizer.py --data your_data.csv --start 5 --end 100 --step 2
```

### 指定輸出目錄

```bash
python simple_strategy_optimizer.py --data your_data.csv --output my_results
```

## 輸出結果

優化完成後，結果保存在 `results/` 目錄（可自定義）：

1. **optimization_results.csv**: 所有測試週期的完整結果
   - `period`: 移動平均線週期
   - `sharpe_ratio`: Sharpe比率
   - `total_return`: 總收益率
   - `annual_return`: 年化收益率
   - `annual_volatility`: 年化波動率

2. **top_10_strategies.csv**: 前10名最佳策略參數

3. **best_strategy_backtest.csv**: 最佳策略的詳細回測數據
   - 包含每日信號、收益率、累計收益等

## 策略說明

當前實現的是**移動平均線交叉策略**：
- 當收盤價 > 移動平均線時，持有股票（信號=1）
- 當收盤價 ≤ 移動平均線時，空倉（信號=0）

優化器會測試不同的移動平均線週期（1-300天），找出Sharpe ratio最高的參數。

## 快速測試

使用示例數據進行測試：

```bash
python simple_strategy_optimizer.py --data ../examples/raw_data_sample.csv --end 50
```

## 命令行參數

| 參數 | 說明 | 默認值 |
|------|------|--------|
| `--data` | CSV數據文件路徑（必需） | - |
| `--start` | 起始週期 | 1 |
| `--end` | 結束週期 | 300 |
| `--step` | 步距 | 1 |
| `--output` | 輸出目錄 | results |

## 性能指標說明

- **Sharpe Ratio**: 風險調整後收益指標，數值越高越好（>1為良好，>2為優秀）
- **Annual Return**: 年化收益率
- **Annual Volatility**: 年化波動率
- **Total Return**: 整個回測期間的總收益率

## 擴展建議

如需添加其他策略，可修改 `moving_average_strategy()` 方法：

```python
def your_custom_strategy(self, df: pd.DataFrame, param: int) -> pd.DataFrame:
    df = df.copy()
    # 你的策略邏輯
    df['signal'] = ...  # 生成交易信號
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    return df
```

## 離線使用

此工具完全離線運行，不需要：
- ❌ 網絡連接
- ❌ 外部API
- ❌ 數據庫連接

所有計算基於你提供的CSV文件本地完成。

## 注意事項

1. 數據必須按 `symbol` 和 `date` 排序（代碼會自動處理）
2. 確保數據無缺失日期，否則可能影響移動平均線計算
3. 週期範圍越大，計算時間越長（300個週期約需數秒）
4. Sharpe ratio計算假設252個交易日/年

## 故障排除

**問題**: `FileNotFoundError`
**解決**: 檢查 `--data` 參數路徑是否正確

**問題**: Sharpe ratio為負無窮
**解決**: 檢查數據是否包含有效的價格變動，或策略收益率標準差是否為0

**問題**: 結果不理想
**解決**:
- 嘗試不同的參數範圍
- 檢查數據質量
- 考慮更換策略邏輯
