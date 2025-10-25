# 運行指南 - 高級技術指標回測系統

## 快速開始

### 方式 1: 直接運行主程序（推薦）

```bash
# 運行增強回測系統（11種技術指標）
python enhanced_strategy_backtest.py
```

這將：
- 加載 0700.HK（騰訊）約5年數據
- 運行 KDJ 策略參數優化
- 生成回測報告 `strategy_backtest_report.txt`

---

## 方式 2: 自定義股票和策略

### 2.1 運行單一策略

```python
from enhanced_strategy_backtest import EnhancedStrategyBacktest
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)

# 創建回測實例
backtest = EnhancedStrategyBacktest('0939.HK', duration=1000)  # 建設銀行，1000天數據

# 加載數據
if backtest.load_data():
    # 測試 KDJ 策略
    result = backtest.run_kdj_strategy(k_period=9, d_period=3, overbought=80, oversold=20)
    print(result)
```

### 2.2 運行參數優化

```python
from enhanced_strategy_backtest import EnhancedStrategyBacktest
import logging

logging.basicConfig(level=logging.INFO)

# 創建回測實例
backtest = EnhancedStrategyBacktest('0700.HK', duration=1825)

# 加載數據
if backtest.load_data():
    # 優化特定策略（選擇一種）
    backtest.optimize_parameters(strategy_type='kdj')      # KDJ策略
    # backtest.optimize_parameters(strategy_type='cci')    # CCI策略
    # backtest.optimize_parameters(strategy_type='adx')    # ADX策略
    # backtest.optimize_parameters(strategy_type='all')    # 全部11種策略

    # 獲取最佳策略
    best = backtest.get_best_strategies(10)
    for i, strategy in enumerate(best, 1):
        print(f"{i}. {strategy['strategy_name']}")
        print(f"   Sharpe比率: {strategy['sharpe_ratio']:.3f}")
        print(f"   年化收益: {strategy['annual_return']:.2f}%")
        print(f"   最大回撤: {strategy['max_drawdown']:.2f}%\n")

    # 生成報告
    backtest.generate_report('my_backtest_report.txt')
```

---

## 支持的策略類型

運行 `optimize_parameters(strategy_type=...)` 時可選：

| 策略類型 | 說明 | 參數組合數 |
|---------|------|-----------|
| `'ma'` | 移動平均交叉 | ~200 |
| `'rsi'` | RSI超買超賣 | ~25 |
| `'macd'` | MACD指標 | ~100 |
| `'bb'` | 布林帶 | ~18 |
| `'kdj'` ⭐ | KDJ/Stochastic | ~240 |
| `'cci'` ⭐ | CCI商品通道 | ~120 |
| `'adx'` ⭐ | ADX趨向指標 | ~35 |
| `'atr'` ⭐ | ATR波動率 | ~50 |
| `'obv'` ⭐ | OBV能量潮 | ~10 |
| `'ichimoku'` ⭐ | 一目均衡表 | ~108 |
| `'parabolic_sar'` ⭐ | 拋物線轉向 | ~180 |
| `'all'` | 全部策略 | ~1243 |

⭐ 表示本次新增的高級指標

---

## 方式 3: 使用交互式腳本

創建 `run_backtest.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交互式回測腳本"""

from enhanced_strategy_backtest import EnhancedStrategyBacktest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # 配置參數
    SYMBOL = '0700.HK'        # 股票代碼
    DURATION = 1825           # 數據天數（約5年）
    STRATEGY = 'kdj'          # 策略類型
    TOP_N = 10                # 顯示前N個最佳策略

    print(f"=" * 60)
    print(f"回測配置:")
    print(f"  股票: {SYMBOL}")
    print(f"  數據天數: {DURATION}")
    print(f"  策略類型: {STRATEGY}")
    print(f"=" * 60 + "\n")

    # 創建回測引擎
    backtest = EnhancedStrategyBacktest(SYMBOL, duration=DURATION)

    # 加載數據
    if not backtest.load_data():
        print("❌ 數據加載失敗！")
        return

    print(f"✅ 數據加載成功: {len(backtest.data)} 個交易日")
    print(f"   範圍: {backtest.data.index.min().date()} -> {backtest.data.index.max().date()}\n")

    # 運行優化
    print(f"🔄 開始優化 {STRATEGY} 策略...")
    results = backtest.optimize_parameters(strategy_type=STRATEGY)

    if not results:
        print("❌ 未找到有效策略結果")
        return

    print(f"\n✅ 優化完成！測試了 {len(results)} 種參數組合\n")

    # 顯示最佳策略
    print(f"{'='*60}")
    print(f"前 {TOP_N} 名最佳策略 (按Sharpe比率排序)")
    print(f"{'='*60}\n")

    best = backtest.get_best_strategies(TOP_N)
    for i, strategy in enumerate(best, 1):
        print(f"{i:2d}. {strategy['strategy_name']}")
        print(f"    📊 Sharpe比率: {strategy['sharpe_ratio']:>7.3f}")
        print(f"    💰 年化收益率: {strategy['annual_return']:>7.2f}%")
        print(f"    📉 最大回撤:   {strategy['max_drawdown']:>7.2f}%")
        print(f"    🎯 勝率:       {strategy['win_rate']:>7.2f}%")
        print(f"    🔢 交易次數:   {strategy['trade_count']:>7d}")
        print()

    # 生成報告
    report_file = f'{SYMBOL}_{STRATEGY}_report.txt'
    backtest.generate_report(report_file)
    print(f"📄 詳細報告已保存至: {report_file}")

if __name__ == "__main__":
    main()
```

運行：
```bash
python run_backtest.py
```

---

## 方式 4: 批量測試多個股票

創建 `batch_backtest.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量回測多個股票"""

from enhanced_strategy_backtest import EnhancedStrategyBacktest
import logging
import pandas as pd

logging.basicConfig(level=logging.WARNING)  # 減少日誌輸出

def backtest_stock(symbol, duration=1000, strategy='kdj'):
    """回測單個股票"""
    try:
        backtest = EnhancedStrategyBacktest(symbol, duration=duration)
        if not backtest.load_data():
            return None

        backtest.optimize_parameters(strategy_type=strategy)
        best = backtest.get_best_strategies(1)

        if best:
            return {
                'symbol': symbol,
                'strategy': best[0]['strategy_name'],
                'sharpe': best[0]['sharpe_ratio'],
                'annual_return': best[0]['annual_return'],
                'max_drawdown': best[0]['max_drawdown'],
                'win_rate': best[0]['win_rate']
            }
    except Exception as e:
        print(f"❌ {symbol} 失敗: {e}")
        return None

def main():
    # 港股列表（可自定義）
    stocks = [
        '0700.HK',  # 騰訊
        '0939.HK',  # 建設銀行
        '0941.HK',  # 中國移動
        '1398.HK',  # 工商銀行
        '2318.HK',  # 中國平安
    ]

    results = []
    for i, symbol in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] 正在回測 {symbol}...")
        result = backtest_stock(symbol, duration=1000, strategy='kdj')
        if result:
            results.append(result)
            print(f"  ✅ 完成 - Sharpe: {result['sharpe']:.3f}, 年化收益: {result['annual_return']:.2f}%")

    # 生成匯總報告
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('sharpe', ascending=False)

        print("\n" + "="*80)
        print("匯總報告 - 最佳策略排名")
        print("="*80)
        print(df.to_string(index=False))

        df.to_csv('batch_backtest_results.csv', index=False, encoding='utf-8-sig')
        print(f"\n📄 結果已保存至: batch_backtest_results.csv")

if __name__ == "__main__":
    main()
```

運行：
```bash
python batch_backtest.py
```

---

## 常見問題

### Q1: API 連接失敗？
```python
# 檢查 API 是否可訪問
import requests
response = requests.get('http://18.180.162.113:9191/inst/getInst?symbol=0700.HK&duration=100')
print(response.status_code)
print(response.json())
```

### Q2: 如何調整參數範圍？
編輯 `enhanced_strategy_backtest.py` 中對應的 `_optimize_xxx_parameters()` 方法。

例如調整 KDJ 參數範圍：
```python
def _optimize_kdj_parameters(self, max_workers: int) -> List[Dict]:
    results = []
    k_periods = range(5, 21, 5)           # 改為 5, 10, 15, 20
    d_periods = range(3, 8, 2)            # 改為 3, 5, 7
    oversold_values = range(20, 31, 5)    # 改為 20, 25, 30
    overbought_values = range(70, 81, 5)  # 改為 70, 75, 80
    # ...
```

### Q3: 如何只測試單個參數組合？
```python
backtest = EnhancedStrategyBacktest('0700.HK', duration=1000)
backtest.load_data()

# 直接調用策略方法
result = backtest.run_kdj_strategy(
    k_period=9,
    d_period=3,
    overbought=80,
    oversold=20
)
print(result)
```

### Q4: 優化速度太慢？
```python
# 1. 減少數據天數
backtest = EnhancedStrategyBacktest('0700.HK', duration=500)  # 從1825減到500

# 2. 只測試單一策略
backtest.optimize_parameters(strategy_type='kdj')  # 不要用 'all'

# 3. 增加線程數（根據CPU核心數）
backtest.optimize_parameters(strategy_type='kdj', max_workers=16)
```

---

## 輸出文件

運行後會生成：

1. **strategy_backtest_report.txt** - 詳細回測報告
2. **quant_system.log** - 系統日誌
3. **batch_backtest_results.csv** (如果運行批量腳本)

---

## 性能參考

| 股票 | 數據天數 | 策略類型 | 參數組合 | 預計時間 (8核) |
|------|----------|---------|---------|---------------|
| 0700.HK | 1000 | kdj | ~240 | 2-3分鐘 |
| 0700.HK | 1825 | kdj | ~240 | 4-5分鐘 |
| 0700.HK | 1825 | all | ~1243 | 15-25分鐘 |

---

## 進階使用

### 保存優化結果到數據庫
```python
import sqlite3
import json

# 運行優化
backtest = EnhancedStrategyBacktest('0700.HK', duration=1825)
backtest.load_data()
backtest.optimize_parameters(strategy_type='all')

# 保存到SQLite
conn = sqlite3.connect('backtest_results.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    strategy TEXT,
    sharpe REAL,
    annual_return REAL,
    max_drawdown REAL,
    params TEXT
)
''')

for result in backtest.results:
    cursor.execute('''
        INSERT INTO results (symbol, strategy, sharpe, annual_return, max_drawdown, params)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        backtest.symbol,
        result['strategy_name'],
        result['sharpe_ratio'],
        result['annual_return'],
        result['max_drawdown'],
        json.dumps(result)
    ))

conn.commit()
conn.close()
```

---

需要其他運行方式的幫助嗎？
