# 港股量化交易系统 - 快速开始指南

## 目录
- [系统简介](#系统简介)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [基本配置](#基本配置)
- [运行第一个策略](#运行第一个策略)
- [查看结果](#查看结果)
- [常见问题](#常见问题)
- [下一步](#下一步)

---

## 系统简介

港股量化交易系统是一个基于多智能体协作的量化交易平台，支持：
- 11种技术指标策略（MA、RSI、MACD、KDJ、CCI、ADX、ATR、OBV、布林带、一目均衡图、Parabolic SAR）
- 实时数据获取和回测
- 策略参数优化
- 风险管理和投资组合管理
- Telegram机器人通知
- Web仪表板监控

---

## 环境要求

### 硬件要求
- **CPU**: 4核心以上（推荐8核心）
- **内存**: 8GB以上（推荐16GB）
- **存储**: 至少5GB可用空间
- **操作系统**: Windows 10/11、Linux、macOS

### 软件要求
- **Python**: 3.10 或更高版本
- **Git**: 最新版本
- **文本编辑器**: VS Code、PyCharm等

---

## 安装步骤

### 步骤 1: 克隆项目

```bash
git clone <项目地址>
cd codex-hk-quant-system
```

### 步骤 2: 创建虚拟环境

**Windows:**
```bash
python -m venv .venv310
.venv310\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv310
source .venv310/bin/activate
```

### 步骤 3: 安装依赖

```bash
# 安装主要依赖
pip install -r requirements.txt

# 安装测试依赖（可选）
pip install -r test_requirements.txt

# 如果TA-Lib安装失败，参考下方说明
```

### 步骤 4: TA-Lib安装（重要）

**Windows:**
1. 从 [https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) 下载对应版本
2. 例如: `TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl`
3. 安装: `pip install TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl`

**Linux:**
```bash
sudo apt-get install ta-lib
pip install TA-Lib
```

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

### 步骤 5: 验证安装

```bash
python simple_test.py
```

如果看到 "All tests passed!" 说明安装成功。

---

## 基本配置

### 步骤 1: 创建环境变量文件

```bash
cp .env.example .env
```

### 步骤 2: 编辑配置文件

编辑 `.env` 文件:

```env
# API服务配置
API_HOST=localhost
API_PORT=8001

# Telegram机器人（可选）
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 数据源配置
DATA_SOURCE_URL=http://18.180.162.113:9191
```

### 步骤 3: 配置数据源

系统使用统一数据API：
- 端点: `http://18.180.162.113:9191/inst/getInst`
- 参数: `symbol` (港股代码，如: "0700.hk"), `duration` (天数)
- 要求: 股票代码必须使用小写

---

## 运行第一个策略

### 方法 1: 使用增强回测引擎（推荐）

创建测试文件 `my_first_strategy.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enhanced_strategy_backtest import EnhancedStrategyBacktest

def main():
    # 初始化回测引擎 - 以腾讯为例
    symbol = "0700.hk"  # 腾讯控股
    start_date = "2022-01-01"
    end_date = "2023-12-31"

    print(f"正在为 {symbol} 运行策略回测...")
    print(f"时间范围: {start_date} 到 {end_date}")

    # 创建回测实例
    backtest = EnhancedStrategyBacktest(symbol, start_date, end_date)

    # 加载数据
    print("正在加载数据...")
    backtest.load_data()

    # 运行KDJ策略
    print("正在运行KDJ策略...")
    result = backtest.run_kdj_strategy(
        k_period=9,
        d_period=3,
        oversold=20,
        overbought=80
    )

    # 显示结果
    print("\n=== 回测结果 ===")
    print(f"总收益率: {result['total_return']:.2f}%")
    print(f"年化收益率: {result['annual_return']:.2f}%")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2f}%")
    print(f"胜率: {result['win_rate']:.2f}%")
    print(f"交易次数: {result['trades']}")

if __name__ == "__main__":
    main()
```

运行策略:

```bash
python my_first_strategy.py
```

### 方法 2: 优化参数

优化KDJ策略参数:

```python
#!/usr/bin/env python3
from enhanced_strategy_backtest import EnhancedStrategyBacktest

def optimize_kdj():
    backtest = EnhancedStrategyBacktest("0700.hk", "2022-01-01", "2023-12-31")
    backtest.load_data()

    print("正在优化KDJ策略参数（这可能需要几分钟）...")
    results = backtest.optimize_parameters(
        strategy_type='kdj',
        max_workers=8
    )

    # 获取最佳参数
    best_params = backtest.get_best_strategies(top_n=1)[0]
    print(f"\n最佳参数: {best_params['params']}")
    print(f"最佳收益率: {best_params['total_return']:.2f}%")

if __name__ == "__main__":
    optimize_kdj()
```

运行优化:

```bash
python my_first_strategy.py
```

### 方法 3: 运行完整系统

启动完整的Web仪表板系统:

```bash
python complete_project_system.py
```

然后在浏览器中访问:
- 主界面: http://localhost:8001
- API文档: http://localhost:8001/docs

---

## 查看结果

### 1. 命令行输出

回测完成后，您将看到类似输出:

```
=== 回测结果 ===
总收益率: 15.67%
年化收益率: 7.82%
夏普比率: 1.23
最大回撤: -8.45%
胜率: 65.50%
交易次数: 24
```

### 2. Web仪表板

启动系统后，通过Web界面查看:
- 实时图表
- 策略性能
- 交易信号
- 风险指标

### 3. 日志文件

详细日志保存在 `quant_system.log`:
```bash
tail -f quant_system.log
```

---

## 常见问题

### Q1: TA-Lib安装失败

**问题**: `Microsoft Visual C++ 14.0 is required`

**解决**:
1. 安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 或者下载预编译的whl文件: `pip install TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl`

### Q2: 数据获取失败

**问题**: `API Error: Connection timeout`

**解决**:
1. 检查网络连接
2. 确认股票代码格式正确（小写，如 "0700.hk"）
3. 检查API服务是否可访问: `ping 18.180.162.113`

### Q3: 端口8001被占用

**问题**: `OSError: [Errno 10048] Only one usage of each socket address`

**解决**:
1. 使用其他端口: `python complete_project_system.py --port 8002`
2. 或者停止占用端口的进程

### Q4: 内存不足

**问题**: `MemoryError` 或系统变慢

**解决**:
1. 减少数据量: 使用更短的时间范围
2. 关闭其他程序释放内存
3. 使用更少的并行工作进程: `max_workers=4`

### Q5: 策略结果异常

**问题**: 收益率过高或过低

**解决**:
1. 检查数据时间范围是否包含足够的历史数据
2. 验证参数设置是否合理
3. 查看日志文件了解错误信息

### Q6: 模块导入错误

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
1. 确保虚拟环境已激活: `source .venv310/bin/activate`
2. 重新安装依赖: `pip install -r requirements.txt`
3. 检查Python版本: `python --version` (需要3.10+)

### Q7: Telegram机器人无法工作

**问题**: 机器人不发送消息

**解决**:
1. 检查Token是否正确
2. 检查Chat ID是否正确
3. 使用 `/start` 命令激活机器人

---

## 高级功能

### 多策略回测

```python
# 同时测试多个策略
strategies = ['kdj', 'rsi', 'macd', 'bb']
for strategy in strategies:
    result = backtest.optimize_parameters(strategy_type=strategy, max_workers=8)
    print(f"{strategy}: {result['best_return']:.2f}%")
```

### 自定义策略

```python
# 在 enhanced_strategies.py 中创建新策略
class MyCustomStrategy(BaseStrategy):
    def generate_signals(self, data):
        # 实现您的策略逻辑
        signals = {}
        # ... 策略代码
        return signals
```

### 风险管理

```python
# 设置止损和止盈
backtest.set_stop_loss(0.05)  # 5%止损
backtest.set_take_profit(0.10)  # 10%止盈
```

### 投资组合管理

```python
# 多股票投资组合
portfolio = PortfolioManager(['0700.hk', '0388.hk', '1398.hk'])
portfolio.add_strategy('kdj', '0700.hk', weight=0.3)
portfolio.add_strategy('rsi', '0388.hk', weight=0.3)
portfolio.add_strategy('macd', '1398.hk', weight=0.4)
```

---

## 下一步

### 学习资源
1. **技术指标指南**: 阅读 `docs/technical_indicators_guide.md`
2. **API参考**: 访问 http://localhost:8001/docs
3. **用户指南**: 阅读 `docs/user_guide.md`
4. **最佳实践**: 查看 `examples/` 目录下的示例

### 实际交易前
- ✅ 在历史数据上充分回测
- ✅ 理解策略原理和风险
- ✅ 使用小资金量进行实盘测试
- ✅ 监控系统性能

### 获取帮助
- **问题反馈**: 提交GitHub Issue
- **社区讨论**: 参与项目讨论
- **邮件联系**: 发送至 [your-email@example.com]

---

## 性能基准

以下是在不同硬件上的预期性能:

| CPU核心数 | 单策略回测 | 全策略优化 | 内存使用 |
|-----------|------------|------------|----------|
| 4核心     | 5-10分钟   | 45-90分钟  | 4-6GB    |
| 8核心     | 3-5分钟    | 30-60分钟  | 6-8GB    |
| 16核心    | 2-3分钟    | 15-30分钟  | 8-12GB   |

*基于3年港股日数据，11种策略优化*

---

## 更新日志

- **v1.0.0** (2025-11-09): 初始版本，支持11种技术指标
- **v1.1.0** (计划中): 添加更多技术指标
- **v1.2.0** (计划中): 机器学习策略支持

---

**祝您使用愉快！如有问题，请查看故障排除指南或联系支持团队。**
