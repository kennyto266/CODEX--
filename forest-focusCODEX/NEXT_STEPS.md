# 后续步骤 - RSI回测优化器

**项目状态**：✅ 核心实现完成
**最后更新**：2025-10-17
**当前阶段**：准备测试和部署

---

## 🎯 立即行动项（优先级：高）

### 1. 安装TA-Lib依赖

**为什么重要**：RSI计算需要TA-Lib库，这是核心功能依赖

**Windows安装步骤**：
```bash
# 1. 下载预编译wheel文件
# 访问：https://github.com/cgohlke/talib-build/releases
# 下载对应Python版本的文件，例如：
# TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl (Python 3.10)

# 2. 安装wheel
pip install TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl

# 3. 验证安装
python -c "import talib; print('TA-Lib版本:', talib.__version__)"
```

**备选方案**（如果TA-Lib安装失败）：
- 系统会自动使用纯Python实现（性能较慢但功能完整）
- 仍可正常运行，但建议安装TA-Lib以获得最佳性能

---

### 2. 安装项目依赖

```bash
# 激活虚拟环境
cd C:\Users\Penguin8n\CODEX--\forest-focusCODEX
.venv310\Scripts\activate  # 如果已有虚拟环境
# 或创建新的：python -m venv venv && venv\Scripts\activate

# 安装所有依赖
pip install -r requirements.txt

# 验证关键库
python -c "import pandas, numpy, matplotlib; print('核心库安装成功')"
```

---

### 3. 运行测试套件

**目的**：验证所有功能正常工作

```bash
# 运行所有测试（需要先安装pytest）
pytest

# 如果出现错误，逐步运行：
pytest tests/unit/ -v           # 单元测试
pytest tests/integration/ -v    # 集成测试（较慢）
pytest tests/contract/ -v       # CLI测试（最慢）

# 查看测试覆盖率
pytest --cov=src --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```

**预期结果**：
- 所有测试通过（可能有部分慢速测试被跳过）
- 测试覆盖率 >80%

---

### 4. 首次试运行

**使用示例数据测试**：

```bash
# 快速测试（10-20窗口，不生成图表）
python rsi_backtest_optimizer.py \
  --data data/0700_HK_sample.csv \
  --start-window 10 \
  --end-window 20 \
  --step 5 \
  --no-charts \
  --output-dir results/test_run

# 检查输出
dir results\test_run
# 应该看到：
# - optimization_results.csv
# - top_10_windows.csv
# - summary_report.txt
# - logs/backtest_*.log

# 查看结果
type results\test_run\summary_report.txt
```

**预期耗时**：约10-30秒

---

## 📊 准备真实数据

### 5. 获取0700.HK历史数据

**选项A：从Yahoo Finance下载**

```python
# 创建脚本：download_data.py
import yfinance as yf
import pandas as pd

# 下载腾讯控股(0700.HK)数据
ticker = yf.Ticker("0700.HK")
data = ticker.history(period="2y")  # 最近2年

# 重命名列以匹配格式
data = data.reset_index()
data.columns = data.columns.str.lower()
data = data.rename(columns={'date': 'date'})

# 保存
data[['date', 'open', 'high', 'low', 'close', 'volume']].to_csv(
    'data/0700_HK.csv',
    index=False
)
print(f"下载完成：{len(data)}天数据")
```

运行：
```bash
pip install yfinance
python download_data.py
```

**选项B：手动准备CSV**

确保CSV包含以下列：
- `date`（格式：YYYY-MM-DD）
- `open`、`high`、`low`、`close`（价格）
- `volume`（成交量）

**数据质量检查**：
```bash
python rsi_backtest_optimizer.py \
  --data data/0700_HK.csv \
  --start-window 14 \
  --end-window 14 \
  --no-charts
# 如果有数据问题，会立即报错并提示
```

---

## 🚀 完整回测运行

### 6. 运行完整优化

**生产级配置**（推荐）：

```bash
python rsi_backtest_optimizer.py \
  --data data/0700_HK.csv \
  --start-window 5 \
  --end-window 100 \
  --step 1 \
  --buy-threshold 30 \
  --sell-threshold 70 \
  --commission 0.001 \
  --stamp-duty 0.001 \
  --initial-capital 100000 \
  --output-dir results/production_run \
  --verbose
```

**预期耗时**：
- 96个窗口（5-100）
- 约2-3分钟（取决于CPU核心数）

**输出文件**：
- `optimization_results.csv`：所有结果
- `top_10_windows.csv`：最佳10个配置
- `summary_report.txt`：可读报告
- `charts/equity_curve.png`：权益曲线图
- `charts/rsi_sharpe_relationship.png`：参数敏感度图
- `logs/backtest_*.log`：详细日志

---

## ✅ 验证和调试

### 7. 检查结果合理性

**打开summary_report.txt，验证**：

```
Optimal Result:
- Best RSI Window: XX        # 应在10-50之间较合理
- Sharpe Ratio: X.XX         # >1.0为良好，>2.0为优秀
- Total Return: XX.XX%       # 应为正数（如果市场上涨）
- Max Drawdown: -XX.XX%      # 应<-20%（风险控制）
- Win Rate: XX.X%            # 应>50%
- Number of Trades: XX       # 应>10（样本充足）
```

**红旗警告**（可能的问题）：
- ❌ 夏普比率 <0：策略亏损
- ❌ 交易次数 <5：样本不足
- ❌ 最大回撤 <-50%：风险过高
- ❌ 胜率 <40%：策略失效

**如果结果异常**：
1. 检查日志文件：`results/production_run/logs/*.log`
2. 验证数据：确保价格、日期正确
3. 调整参数：尝试不同的阈值

---

## 📈 分析和迭代

### 8. 参数调优实验

**实验1：不同阈值组合**

```bash
# 测试保守策略（20/80）
python rsi_backtest_optimizer.py \
  --data data/0700_HK.csv \
  --buy-threshold 20 \
  --sell-threshold 80 \
  --output-dir results/conservative

# 测试激进策略（40/60）
python rsi_backtest_optimizer.py \
  --data data/0700_HK.csv \
  --buy-threshold 40 \
  --sell-threshold 60 \
  --output-dir results/aggressive

# 比较结果
grep "Optimal RSI window" results/*/summary_report.txt
```

**实验2：成本敏感度分析**

```bash
# 零成本（理论最优）
python rsi_backtest_optimizer.py \
  --commission 0 \
  --stamp-duty 0 \
  --output-dir results/zero_cost

# 高成本（0.2%）
python rsi_backtest_optimizer.py \
  --commission 0.002 \
  --stamp-duty 0.002 \
  --output-dir results/high_cost
```

---

## 🔧 可选改进

### 9. 未来增强功能（低优先级）

**短期改进**（1-2周）：
- [ ] 添加止损/止盈功能
- [ ] 支持多股票批量回测
- [ ] 生成Excel报告（pandas.to_excel）
- [ ] 添加滚动窗口验证（walk-forward）

**中期改进**（1-2月）：
- [ ] Web界面（Flask/Streamlit）
- [ ] 实时监控模式（连接实时数据）
- [ ] 策略组合优化
- [ ] 机器学习参数推荐

**实现建议**：
- 从最简单的功能开始
- 每个功能独立分支开发
- 保持测试覆盖率 >80%

---

## 📋 问题排查清单

### 常见问题解决

**问题：导入错误 "No module named 'src'"**
```bash
# 解决：确保在项目根目录运行
cd C:\Users\Penguin8n\CODEX--\forest-focusCODEX
python rsi_backtest_optimizer.py
```

**问题：TA-Lib安装失败**
```bash
# 解决：使用fallback模式
# 代码会自动切换到纯Python实现，无需操作
# 日志会显示：WARNING: TA-Lib not available. Using fallback...
```

**问题：数据验证失败**
```bash
# 检查CSV格式
python -c "import pandas as pd; df = pd.read_csv('data/0700_HK.csv'); print(df.info())"

# 常见问题：
# - 列名大小写不匹配 → 改为小写
# - 日期格式错误 → 使用 YYYY-MM-DD
# - OHLC关系错误 → high应 >= open/close/low
```

**问题：运行超时（>10分钟）**
```bash
# 减少测试窗口数
python rsi_backtest_optimizer.py \
  --start-window 10 \
  --end-window 50 \
  --step 5  # 只测试9个窗口

# 或增加并行进程（如果CPU核心多）
--parallel-workers 8
```

---

## 📞 获取帮助

**资源**：
- 📖 完整文档：`README.md`
- 🔧 技术设计：`specs/001-rsi-backtest-optimizer/`
- 📊 快速开始：`specs/001-rsi-backtest-optimizer/quickstart.md`
- 🧪 测试：运行 `pytest -v`

**下次继续开发时**：
1. 查看此文件（NEXT_STEPS.md）
2. 运行快速测试验证环境
3. 查看results/目录了解上次运行结果
4. 继续未完成的改进项

---

## ✨ 成功标志

完成以下所有项，项目即可投入使用：

- [x] 代码实现完成（所有阶段）
- [ ] TA-Lib安装成功
- [ ] 测试套件全部通过
- [ ] 使用示例数据成功运行
- [ ] 真实数据回测完成
- [ ] 结果分析合理
- [ ] 文档阅读完毕

**当前进度**：1/7 ✅

祝回测顺利！📈
