# 常见问题解答 (FAQ)

欢迎查看港股量化交易系统FAQ！这里收集了用户最常遇到的问题和解决方案。

## 📋 目录

- [🔧 安装与配置](#安装与配置)
- [📊 数据相关](#数据相关)
- [💹 策略与回测](#策略与回测)
- [🎯 性能优化](#性能优化)
- [🌐 系统运行](#系统运行)
- [🤖 Telegram机器人](#telegram机器人)
- [📈 Web仪表板](#web仪表板)
- [🔍 故障排除](#故障排除)
- [💡 最佳实践](#最佳实践)
- [❓ 其他问题](#其他问题)

---

## 🔧 安装与配置

### Q1: Python版本要求是什么？

**A:** 系统需要Python 3.10或更高版本。

检查版本:
```bash
python --version
```

**推荐版本:**
- Python 3.10.x (最稳定)
- Python 3.11.x (性能更好)
- Python 3.12.x (最新功能)

**不推荐:**
- Python 3.9及以下 (缺少必要特性)
- Python 3.13+ (未充分测试)

---

### Q2: TA-Lib安装失败怎么办？

**A:** TA-Lib是技术分析库，安装可能遇到问题。

**Windows解决方案:**

1. **使用预编译包 (推荐):**
   ```bash
   # 访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   # 下载对应版本，如: TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
   pip install TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
   ```

2. **安装Visual C++ Build Tools:**
   ```bash
   pip install ta-lib
   # 如果失败，下载并安装 Microsoft C++ Build Tools
   ```

3. **使用conda (替代方案):**
   ```bash
   conda install -c conda-forge ta-lib
   ```

**Linux解决方案:**
```bash
# Ubuntu/Debian
sudo apt-get install ta-lib
pip install TA-Lib

# CentOS/RHEL
sudo yum install ta-lib-devel
pip install TA-Lib
```

**macOS解决方案:**
```bash
brew install ta-lib
pip install TA-Lib
```

**验证安装:**
```python
import talib
print(talib.__version__)
```

---

### Q3: 虚拟环境激活失败

**A:** 虚拟环境创建和激活问题。

**问题症状:**
```
'.venv310\Scripts\activate' is not recognized as an internal or external command
```

**解决方案:**

**Windows:**
```bash
# 方法1: 使用完整路径
C:\Users\YourName\project\.venv310\Scripts\activate

# 方法2: 重新创建虚拟环境
python -m venv .venv310
.venv310\Scripts\activate

# 方法3: 使用PowerShell (如果需要)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv310\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
# 方法1: 使用bash
source .venv310/bin/activate

# 方法2: 使用zsh (macOS Catalina+)
zsh
source .venv310/bin/activate

# 方法3: 检查文件权限
chmod +x .venv310/bin/activate
```

**验证激活:**
```bash
which python
# 应该显示: .../.venv310/bin/python
```

---

### Q4: 依赖安装失败

**A:** pip安装依赖时可能出现网络或版本冲突问题。

**常见错误及解决:**

1. **网络超时**
   ```bash
   # 使用国内镜像
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

2. **版本冲突**
   ```bash
   # 升级pip
   python -m pip install --upgrade pip

   # 使用--no-deps跳过依赖检查
   pip install -r requirements.txt --no-deps
   ```

3. **权限问题 (Linux/macOS)**
   ```bash
   # 不使用sudo，使用用户安装
   pip install --user -r requirements.txt
   ```

4. **缓存问题**
   ```bash
   # 清理pip缓存
   pip cache purge
   pip install -r requirements.txt
   ```

**完整重装:**
```bash
# 删除虚拟环境
rm -rf .venv310  # Linux/macOS
rmdir /s .venv310  # Windows

# 重新创建
python -m venv .venv310
source .venv310/bin/activate  # Linux/macOS
.venv310\Scripts\activate  # Windows

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Q5: .env配置文件问题

**A:** 环境变量配置错误或缺失。

**创建配置文件:**
```bash
cp .env.example .env
```

**编辑 .env 文件:**
```env
# API服务配置
API_HOST=localhost
API_PORT=8001

# Telegram机器人
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 数据源
DATA_SOURCE_URL=http://18.180.162.113:9191
```

**检查配置是否加载:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
print(f"API_HOST: {os.getenv('API_HOST')}")
print(f"API_PORT: {os.getenv('API_PORT')}")
```

**常见错误:**
- `Token 格式错误`: 确保Token以数字开头
- `Chat ID 错误`: 使用 BotFather 获取正确的Chat ID
- `端口占用`: 修改API_PORT为其他端口

---

## 📊 数据相关

### Q6: 数据获取失败

**A:** 常见数据获取错误及解决。

**错误1: 连接超时**
```
API Error: requests.exceptions.ConnectTimeout
```

**解决方案:**
```python
# 增加超时时间
import requests

response = requests.get(
    url,
    params={'symbol': '0700.hk', 'duration': 365},
    timeout=60  # 60秒超时
)
```

**错误2: 404 Not Found**
```
API Error: 404 Client Error
```

**解决方案:**
```python
# 检查股票代码格式
symbol = "0700.hk"  # 正确: 小写 + .hk
# 错误: "0700.HK", "700.hk", "0700"
```

**错误3: 数据为空**
```python
# 检查返回数据
data = response.json()
if not data or len(data) == 0:
    print("数据为空，可能原因:")
    print("1. 股票代码错误")
    print("2. 时间范围超出数据范围")
    print("3. API服务暂时不可用")
```

**调试数据获取:**
```python
import requests
import json

def debug_data_fetch():
    url = "http://18.180.162.113:9191/inst/getInst"
    params = {
        "symbol": "0700.hk",
        "duration": 365
    }

    try:
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")

        response = requests.get(url, params=params, timeout=30)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        data = response.json()
        print(f"数据条数: {len(data) if isinstance(data, list) else 'N/A'}")
        print(f"前5条数据: {data[:5] if isinstance(data, list) else data}")

        return data
    except Exception as e:
        print(f"错误: {e}")
        return None

debug_data_fetch()
```

---

### Q7: 数据格式不正确

**A:** 收到的数据格式与预期不符。

**标准数据格式:**
```json
[
  {
    "date": "2023-01-01",
    "open": 350.0,
    "high": 360.0,
    "low": 345.0,
    "close": 355.0,
    "volume": 1000000
  }
]
```

**常见问题:**

1. **缺少字段**
   ```python
   # 检查必要字段
   required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
   data = response.json()

   for field in required_fields:
       if field not in data[0]:
           print(f"缺少字段: {field}")
   ```

2. **数据类型错误**
   ```python
   # 转换数据类型
   for item in data:
       item['open'] = float(item['open'])
       item['high'] = float(item['high'])
       item['low'] = float(item['low'])
       item['close'] = float(item['close'])
       item['volume'] = int(item['volume'])
   ```

3. **日期格式错误**
   ```python
   from datetime import datetime

   # 标准化日期格式
   for item in data:
       date_str = item['date']
       item['date'] = datetime.strptime(date_str, '%Y-%m-%d')
   ```

---

### Q8: 替代数据问题

**A:** 替代数据（35个指标）相关问题。

**当前状态:**
⚠️ 重要: `gov_crawler/data/all_alternative_data_*.json` 中的数据是**模拟数据**，不是真实数据！

**问题1: 模拟数据与真实数据差异**
```python
# 检查数据文件
import json
from datetime import datetime

with open('gov_crawler/data/all_alternative_data_20251023_210419.json', 'r') as f:
    data = json.load(f)

print(f"数据源标识: {data.get('data_source', 'unknown')}")
print(f"数据模式: {data.get('mode', 'unknown')}")  # 应该是 'mock' 或 'real'
print(f"生成时间: {data.get('generated_at', 'unknown')}")
```

**问题2: 何时有真实数据？**
根据路线图，预计在Phase 1-5完成后（6-7周）将提供真实数据。

**问题3: 使用模拟数据的影响**
- 所有回测结果**仅供参考**
- 实际交易中可能表现不同
- 建议仅用于系统测试

**获取真实数据:**
1. 等待官方通知真实数据可用
2. 或按照 `docs/alternative-data-guide.md` 自行实现数据源

---

### Q9: 数据缓存问题

**A:** 缓存可能导致数据不是最新的。

**清理缓存:**
```python
import os
import shutil

# 清理所有缓存
cache_dirs = ['.cache', '__pycache__', '.pytest_cache']
for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print(f"已删除缓存: {cache_dir}")
```

**禁用缓存 (调试时):**
```python
import requests
from requests_cache import DisabledCache

# 使用 DisabledCache 禁用缓存
session = requests.Session()
session.mount('http://', DisabledCache())
```

**检查缓存设置:**
```python
# 查看requests_cache配置
import requests_cache
print(f"缓存后端: {requests_cache.get_cache()}")
print(f"缓存过期时间: {requests_cache.get_cache().expire_after}")
```

---

## 💹 策略与回测

### Q10: 回测结果不合理

**A:** 回测结果异常（过高、过低、NaN）。

**问题1: 收益率过高 (>50%)**
```python
# 检查原因
print(f"初始资金: {initial_capital}")
print(f"最终资金: {final_value}")
print(f"交易次数: {num_trades}")
print(f"胜率: {win_rate}%")

# 可能原因
# 1. 数据重复计算
# 2. 交易成本未扣除
# 3. 参数过拟合
# 4. 数据质量差
```

**问题2: 收益率为NaN**
```python
# 检查数据
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')
print(f"缺失值数量: {df.isnull().sum().sum()}")
print(f"无穷值数量: {np.isinf(df).sum().sum()}")

# 清理数据
df = df.dropna()  # 删除缺失值
df = df.replace([np.inf, -np.inf], np.nan).dropna()  # 删除无穷值
```

**问题3: 最大回撤过大 (>50%)**
```python
# 分析回撤
returns = df['returns']
cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max

print(f"最大回撤: {drawdown.min():.2%}")
print(f"回撤时间: {drawdown.idxmin()}")

# 解决方案
# 1. 添加止损: set_stop_loss(0.05)  # 5%
# 2. 调整参数: 使用更保守的参数
# 3. 优化策略: 减少持仓时间
```

**标准回测结果参考:**
- 年化收益率: 5-15% (合理)
- 最大回撤: <20% (优秀), 20-30% (可接受), >30% (风险高)
- 夏普比率: >1.0 (优秀), 0.5-1.0 (良好), <0.5 (一般)
- 胜率: 50-70% (合理)

---

### Q11: 策略过拟合

**A:** 策略在历史数据上表现完美，但未来表现差。

**识别过拟合:**
```python
# 1. 训练集 vs 测试集
train_start = "2020-01-01"
train_end = "2021-12-31"
test_start = "2022-01-01"
test_end = "2023-12-31"

# 训练集表现
train_result = backtest.run_strategy(start=train_start, end=train_end)
print(f"训练集收益率: {train_result['total_return']:.2f}%")

# 测试集表现
test_result = backtest.run_strategy(start=test_start, end=test_end)
print(f"测试集收益率: {test_result['total_return']:.2f}%")

# 表现差异
diff = train_result['total_return'] - test_result['total_return']
print(f"差异: {diff:.2f}%")  # 差异过大说明过拟合
```

**避免过拟合:**
1. **使用样本外测试**: 至少30%的数据用于测试
2. **交叉验证**: 多时间段测试
3. **简化参数**: 避免过多参数组合
4. **验证指标**: 多个评估指标综合判断

**交叉验证示例:**
```python
# 滚动窗口验证
windows = [
    ("2020-2021", "2022-2023"),
    ("2021-2022", "2023-2024"),
    # ...
]

results = []
for train, test in windows:
    train_result = backtest.run_strategy(start=train[0], end=train[1])
    test_result = backtest.run_strategy(start=test[0], end=test[1])
    results.append({
        'train': train_result,
        'test': test_result
    })

# 计算平均表现
avg_test_return = sum(r['test']['total_return'] for r in results) / len(results)
print(f"平均测试集收益率: {avg_test_return:.2f}%")
```

---

### Q12: 参数优化缓慢

**A:** 参数优化耗时过长（>1小时）。

**优化方法:**

1. **减少参数范围**
```python
# 原始范围
k_periods = range(5, 31, 5)  # 6个值

# 优化后范围
k_periods = [9, 14, 20, 25]  # 4个值
```

2. **减少并行数 (避免过载)**
```python
# 谨慎使用: max_workers=CPU核心数
backtest.optimize_parameters(
    strategy_type='kdj',
    max_workers=4  # 4核心CPU
)
```

3. **使用分阶段优化**
```python
# 第一阶段: 粗略搜索
k_range = [5, 15, 25, 30]

# 第二阶段: 精细搜索
best_k = 15
k_range = range(best_k-2, best_k+3)
```

4. **使用遗传算法 (高级)**
```python
# 避免暴力搜索，使用遗传算法
from scipy.optimize import differential_evolution

def objective(params):
    k, d = params
    result = backtest.run_kdj_strategy(k_period=int(k), d_period=int(d))
    return -result['total_return']  # 最大化收益率

result = differential_evolution(
    objective,
    bounds=[(5, 30), (3, 5)],
    seed=42
)
```

**性能参考:**
- 单策略优化: 3-10分钟 (8核心)
- 全策略优化: 30-60分钟 (8核心)
- 超过此时间说明参数范围过大

---

### Q13: 策略信号不准确

**A:** 交易信号与预期不符。

**调试策略:**
```python
# 1. 检查指标计算
import talib
import pandas as pd

df = pd.read_csv('data.csv')
df['k'], df['d'] = talib.STOCH(df['high'], df['low'], df['close'])
df['signal'] = 0

# 生成信号
df.loc[df['k'] < 20, 'signal'] = 1  # 买入
df.loc[df['k'] > 80, 'signal'] = -1  # 卖出

# 查看信号
print(df[['date', 'k', 'd', 'signal']].tail(10))
```

**常见问题:**

1. **参数顺序错误**
   ```python
   # 错误
   k, d = talib.STOCH(df['close'], df['high'], df['low'])

   # 正确
   k, d = talib.STOCH(df['high'], df['low'], df['close'])
   ```

2. **信号逻辑错误**
   ```python
   # 错误: K线在D线上方就买入
   df.loc[df['k'] > df['d'], 'signal'] = 1

   # 正确: K线从下方穿越D线
   df['prev_k'] = df['k'].shift(1)
   df['prev_d'] = df['d'].shift(1)
   cross_up = (df['k'] > df['d']) & (df['prev_k'] < df['prev_d'])
   df.loc[cross_up, 'signal'] = 1
   ```

3. **未处理边界条件**
   ```python
   # 添加边界检查
   df['signal'] = 0
   df.loc[(df['k'] < 20) & (df['prev_k'] >= 20), 'signal'] = 1
   ```

**信号验证:**
```python
# 验证信号准确性
signals = df[df['signal'] != 0]
print(f"买入信号数: {(signals['signal'] == 1).sum()}")
print(f"卖出信号数: {(signals['signal'] == -1).sum()}")

# 检查信号分布
print("\n信号日期:")
for idx, row in signals.iterrows():
    action = "买入" if row['signal'] == 1 else "卖出"
    print(f"{row['date']}: {action} (K={row['k']:.2f}, D={row['d']:.2f})")
```

---

## 🎯 性能优化

### Q14: 系统运行缓慢

**A:** 系统响应慢或卡顿。

**分析性能瓶颈:**
```python
import cProfile
import pstats

# 分析性能
cProfile.run('backtest.run_kdj_strategy()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)  # 显示前20个最耗时函数
```

**常见原因及解决:**

1. **内存不足**
   ```bash
   # 检查内存使用
   # Windows
   tasklist | findstr python

   # Linux/macOS
   ps aux | grep python
   htop  # 实时监控

   # 解决方案
   # 1. 增加虚拟内存
   # 2. 关闭其他程序
   # 3. 减少数据量
   ```

2. **I/O密集型操作**
   ```python
   # 使用缓存减少文件读写
   import joblib
   cache = joblib.Memory('cache_dir', verbose=1)

   @cache.cache
   def expensive_function(data):
       return data.process()
   ```

3. **计算密集型操作**
   ```python
   # 使用向量化代替循环
   # 错误
   for i in range(len(df)):
       df.loc[i, 'ma'] = df['close'].iloc[:i+1].mean()

   # 正确
   df['ma'] = df['close'].rolling(window=20).mean()
   ```

4. **串行执行**
   ```python
   # 使用并行处理
   from concurrent.futures import ProcessPoolExecutor

   def optimize_single_strategy(args):
       return backtest.optimize_strategy(*args)

   with ProcessPoolExecutor(max_workers=4) as executor:
       results = list(executor.map(optimize_single_strategy, param_combinations))
   ```

**性能监控:**
```python
import time
import psutil

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_cpu = psutil.cpu_percent()

        result = func(*args, **kwargs)

        end_time = time.time()
        end_cpu = psutil.cpu_percent()

        print(f"执行时间: {end_time - start_time:.2f}秒")
        print(f"CPU使用率: {end_cpu:.2f}%")
        print(f"内存使用: {psutil.virtual_memory().percent}%")

        return result
    return wrapper

# 使用装饰器
@monitor_performance
def run_backtest():
    # 回测代码
    pass
```

---

### Q15: 内存占用过高

**A:** 内存使用超过8GB或系统变慢。

**检查内存使用:**
```python
import psutil
import os

# 进程内存使用
process = psutil.Process(os.getpid())
print(f"当前进程内存: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# 系统内存
memory = psutil.virtual_memory()
print(f"系统内存使用率: {memory.percent}%")
print(f"可用内存: {memory.available / 1024 / 1024:.2f} MB")
```

**内存优化方法:**

1. **数据类型优化**
   ```python
   import pandas as pd
   import numpy as np

   # 使用适当的数据类型
   df = pd.read_csv('data.csv', dtype={
       'open': 'float32',  # 而不是float64
       'high': 'float32',
       'low': 'float32',
       'close': 'float32',
       'volume': 'int32'  # 而不是int64
   })

   # 内存节省
   print(f"优化前: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
   ```

2. **分批处理**
   ```python
   # 分批读取大数据
   chunk_size = 1000
   chunks = []

   for chunk in pd.read_csv('large_data.csv', chunksize=chunk_size):
       processed_chunk = process_chunk(chunk)
       chunks.append(processed_chunk)

   df = pd.concat(chunks, ignore_index=True)
   ```

3. **及时释放内存**
   ```python
   # 删除不需要的变量
   del large_dataframe
   gc.collect()  # 强制垃圾回收

   # 使用with语句
   with pd.read_csv('data.csv') as df:
       # 处理数据
       pass
   # 文件自动关闭，内存自动释放
   ```

4. **使用生成器**
   ```python
   # 代替一次性加载所有数据
   def data_generator():
       for chunk in pd.read_csv('data.csv', chunksize=1000):
           yield process_chunk(chunk)

   # 迭代处理
   for processed_data in data_generator():
       # 处理数据
       pass
   ```

---

### Q16: 并行处理错误

**A:** 多进程/多线程处理时出现错误。

**常见错误:**

1. **PicklingError**
   ```python
   # 错误: 使用lambda或嵌套函数
   from concurrent.futures import ProcessPoolExecutor

   # 这会失败
   with ProcessPoolExecutor() as executor:
       results = executor.map(lambda x: x*2, data)

   # 解决: 使用普通函数
   def multiply_by_two(x):
       return x * 2

   with ProcessPoolExecutor() as executor:
       results = executor.map(multiply_by_two, data)
   ```

2. **共享状态错误**
   ```python
   # 错误: 多进程共享全局变量
   global_var = []

   def worker():
       global_var.append(result)  # 错误!

   # 解决: 使用参数传递
   def worker(data, result_list):
       result_list.append(process(data))
   ```

3. **死锁**
   ```python
   # 避免嵌套锁
   import threading

   lock1 = threading.Lock()
   lock2 = threading.Lock()

   # 错误: 可能的死锁
   def process1():
       with lock1:
           with lock2:
               # 处理
               pass

   def process2():
       with lock2:
           with lock1:  # 死锁!
               # 处理
               pass

   # 解决: 总是按相同顺序获取锁
   ```

**正确的并行处理:**
```python
from concurrent.futures import ProcessPoolExecutor, as_completed

def parallel_optimization(param_list):
    """安全的并行参数优化"""
    results = []

    with ProcessPoolExecutor(max_workers=4) as executor:
        # 提交任务
        future_to_params = {
            executor.submit(run_single_optimization, params): params
            for params in param_list
        }

        # 收集结果
        for future in as_completed(future_to_params):
            params = future_to_params[future]
            try:
                result = future.result()
                results.append({
                    'params': params,
                    'result': result
                })
            except Exception as e:
                print(f"参数 {params} 处理失败: {e}")

    return results
```

---

## 🌐 系统运行

### Q17: 端口8001被占用

**A:** 启动时提示端口已被占用。

**查找占用进程:**
```bash
# Windows
netstat -ano | findstr :8001
tasklist | findstr <PID>

# Linux
lsof -i :8001
netstat -tulpn | grep :8001

# macOS
lsof -i :8001
netstat -an | grep :8001
```

**解决方案:**

1. **使用其他端口**
   ```bash
   python complete_project_system.py --port 8002
   ```

2. **停止占用进程**
   ```bash
   # Windows
   taskkill /PID <PID> /F

   # Linux/macOS
   kill -9 <PID>
   ```

3. **配置动态端口**
   ```python
   # 随机选择可用端口
   import socket

   def find_free_port():
       with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
           s.bind(('', 0))
           s.listen(1)
           port = s.getsockname()[1]
       return port

   port = find_free_port()
   print(f"使用端口: {port}")
   ```

---

### Q18: Web仪表板无法访问

**A:** 浏览器无法打开 http://localhost:8001。

**检查列表:**

1. **服务是否启动**
   ```bash
   # 检查进程
   # Windows
   tasklist | findstr python

   # Linux/macOS
   ps aux | grep complete_project_system

   # 检查端口
   netstat -an | grep 8001
   ```

2. **防火墙设置**
   ```bash
   # Windows防火墙
   # 添加例外: 允许Python通过防火墙

   # Linux防火墙 (ufw)
   sudo ufw allow 8001

   # iptables
   sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
   ```

3. **网络配置**
   ```bash
   # 测试本地连接
   curl http://localhost:8001
   curl http://127.0.0.1:8001

   # 检查IP地址
   # Windows
   ipconfig

   # Linux/macOS
   ifconfig
   # 或
   ip addr show
   ```

4. **浏览器问题**
   - 尝试其他浏览器
   - 清除浏览器缓存
   - 禁用浏览器扩展
   - 使用无痕/隐私模式

**远程访问配置:**
```python
# 在complete_project_system.py中修改
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "complete_project_system:app",
        host="0.0.0.0",  # 允许外部访问
        port=8001,
        reload=False
    )
```

**访问地址:**
- 本地访问: http://localhost:8001
- 局域网访问: http://[你的IP]:8001
  - 查找IP: `ipconfig` (Windows) 或 `ifconfig` (Linux/macOS)
- API文档: http://localhost:8001/docs

---

### Q19: 系统无响应

**A:** 系统启动后无响应或卡死。

**诊断步骤:**

1. **检查日志**
   ```bash
   # 查看最新日志
   tail -n 100 quant_system.log

   # 实时监控日志
   tail -f quant_system.log
   ```

2. **检查系统资源**
   ```bash
   # CPU使用率
   # Windows
   wmic cpu get loadpercentage /value

   # Linux/macOS
   top
   htop  # 如果安装了

   # 内存使用
   # Windows
   wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value

   # Linux
   free -h
   ```

3. **检查进程状态**
   ```python
   import psutil
   import signal
   import os

   # 查找Python进程
   for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
       if 'python' in proc.info['name'].lower():
           print(f"PID: {proc.info['pid']}, 内存: {proc.info['memory_percent']:.2f}%, CPU: {proc.info['cpu_percent']:.2f}%")
   ```

4. **强制重启**
   ```bash
   # Windows
   taskkill /F /IM python.exe

   # Linux/macOS
   pkill python
   # 或
   killall python
   ```

**预防措施:**
- 定期重启系统（每周一次）
- 监控系统资源使用
- 设置内存限制
- 使用进程守护工具 (supervisor, pm2等)

---

### Q20: 数据库连接错误

**A:** SQLite或其他数据库连接失败。

**常见错误:**

1. **权限错误**
   ```python
   import os
   import sqlite3

   db_path = 'quant_system.db'

   # 检查文件权限
   if os.path.exists(db_path):
       print(f"文件存在: {os.access(db_path, os.R_OK and os.W_OK)}")

   # 修改权限
   os.chmod(db_path, 0o666)  # 读写权限
   ```

2. **数据库锁定**
   ```python
   # 错误: 多个进程同时访问
   conn1 = sqlite3.connect('db.sqlite')
   conn2 = sqlite3.connect('db.sqlite')  # 可能被锁定

   # 解决: 使用连接池或序列化访问
   import sqlite3
   from contextlib import contextmanager

   @contextmanager
   def get_db_connection():
       conn = sqlite3.connect('db.sqlite', timeout=30)
       try:
           yield conn
       finally:
           conn.close()

   # 使用
   with get_db_connection() as conn:
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM trades")
       results = cursor.fetchall()
   ```

3. **数据库损坏**
   ```bash
   # 检查数据库
   sqlite3 db.sqlite ".schema"

   # 恢复数据库
   sqlite3 db.sqlite ".recover" > recovered.sql
   sqlite3 new_db.sqlite < recovered.sql
   ```

---

## 🤖 Telegram机器人

### Q21: 机器人不响应

**A:** 发送消息给机器人但没有回复。

**检查步骤:**

1. **Token验证**
   ```python
   import requests

   token = "YOUR_BOT_TOKEN"
   url = f"https://api.telegram.org/bot{token}/getMe"

   response = requests.get(url)
   print(response.json())

   # 正常响应示例:
   # {"ok": true, "result": {"id": 123456789, "first_name": "Bot Name", ...}}
   ```

2. **Chat ID获取**
   ```python
   # 发送消息给自己
   url = f"https://api.telegram.org/bot{token}/sendMessage"
   data = {
       "chat_id": "YOUR_CHAT_ID",
       "text": "Test message"
   }

   response = requests.post(url, data=data)
   print(response.json())

   # 获取Chat ID: 将机器人拉入群组，查看Webhook日志或使用getUpdates
   ```

3. **检查运行状态**
   ```python
   # 运行机器人测试
   python test_bot_connection.py

   # 预期输出:
   # Bot connected successfully
   # 发送测试消息
   # 消息发送成功
   ```

4. **Webhook设置**
   ```python
   # 清除Webhook (如果之前设置过)
   url = f"https://api.telegram.org/bot{token}/deleteWebhook"
   requests.get(url)

   # 设置Webhook (可选)
   webhook_url = f"https://yourdomain.com/webhook/{token}"
   url = f"https://api.telegram.org/bot{token}/setWebhook"
   data = {"url": webhook_url}
   requests.post(url, data=data)
   ```

**完整测试脚本:**
```python
#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_telegram_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("错误: 请检查.env文件中的TELEGRAM_BOT_TOKEN和TELEGRAM_CHAT_ID")
        return

    # 1. 验证Token
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    result = response.json()

    if not result['ok']:
        print(f"Token验证失败: {result}")
        return

    bot_info = result['result']
    print(f"机器人名称: {bot_info['first_name']}")
    print(f"机器人用户名: {bot_info['username']}")

    # 2. 发送测试消息
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": "🧪 系统测试消息\n机器人连接正常！"
    }

    response = requests.post(url, data=data)
    result = response.json()

    if result['ok']:
        print("✅ 消息发送成功")
    else:
        print(f"❌ 消息发送失败: {result}")

    # 3. 获取更新
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url)
    updates = response.json()

    if updates['ok']:
        print(f"获取到 {len(updates['result'])} 条更新")
        for update in updates['result'][-3:]:  # 显示最近3条
            print(f"更新ID: {update['update_id']}")
            if 'message' in update:
                msg = update['message']
                print(f"来自: {msg['from']['first_name']}")
                print(f"消息: {msg['text']}")

if __name__ == "__main__":
    test_telegram_bot()
```

---

### Q22: 机器人消息格式错误

**A:** 发送的消息格式混乱或无法阅读。

**Markdown格式:**
```python
# 正确使用Markdown
message = (
    "📊 *回测结果报告*\n\n"
    "📈 *股票代码:* 0700.hk\n"
    "📅 *时间范围:* 2023-01-01 到 2023-12-31\n\n"
    "💰 *收益情况:*\n"
    "├─ 总收益率: *15.67%*\n"
    "├─ 年化收益率: *7.82%*\n"
    "└─ 夏普比率: *1.23*\n\n"
    "⚠️ 风险指标:\n"
    "├─ 最大回撤: -8.45%\n"
    "└─ 波动率: 12.34%\n\n"
    "🔗 [查看详情](http://localhost:8001)"
)

url = f"https://api.telegram.org/bot{token}/sendMessage"
data = {
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "Markdown"  # 或 "HTML"
}
```

**HTML格式:**
```python
# 使用HTML (更灵活)
message = (
    "<b>📊 回测结果报告</b>\n\n"
    "<b>📈 股票代码:</b> 0700.hk\n"
    "<b>📅 时间范围:</b> 2023-01-01 到 2023-12-31\n\n"
    "<b>💰 收益情况:</b>\n"
    "• 总收益率: <code>15.67%</code>\n"
    "• 年化收益率: <code>7.82%</code>\n"
    "• 夏普比率: <code>1.23</code>\n\n"
    "<b>⚠️ 风险指标:</b>\n"
    "• 最大回撤: -8.45%\n"
    "• 波动率: 12.34%"
)

data = {
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "HTML"
}
```

**表情符号使用:**
```python
# 常用表情符号
EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'chart': '📊',
    'money': '💰',
    'calendar': '📅',
    'stock': '📈',
    'risk': '⚠️',
    'time': '⏰',
    'rocket': '🚀'
}
```

**表格格式:**
```python
def format_table(data):
    """格式化为等宽表格"""
    # 使用等宽字体
    lines = []
    for row in data:
        line = " | ".join(f"{str(cell):>10}" for cell in row)
        lines.append(line)

    # 添加分隔线
    separator = "-" * len(lines[0])
    table = "\n".join([lines[0], separator] + lines[1:])
    return f"<pre>{table}</pre>"

# 使用
table_data = [
    ["指标", "数值"],
    ["总收益率", "15.67%"],
    ["最大回撤", "-8.45%"],
    ["夏普比率", "1.23"]
]

message = format_table(table_data)
```

---

## 📈 Web仪表板

### Q23: 图表不显示

**A:** 仪表板上的图表为空白或加载失败。

**检查步骤:**

1. **查看浏览器控制台**
   - 按F12打开开发者工具
   - 查看Console选项卡
   - 寻找错误信息（如404、500等）

2. **检查API数据**
   ```bash
   # 测试API端点
   curl http://localhost:8001/api/health
   curl http://localhost:8001/api/strategies
   ```

3. **检查数据格式**
   ```javascript
   // 在浏览器控制台中执行
   fetch('http://localhost:8001/api/strategies')
     .then(response => response.json())
     .then(data => console.log(data));
   ```

**常见问题:**

1. **数据为空**
   ```python
   # 后端: 检查数据获取
   @app.get("/api/strategies")
   async def get_strategies():
       try:
           data = fetch_strategies()  # 检查此函数
           if not data:
               return {"error": "No data available"}
           return data
       except Exception as e:
           return {"error": str(e)}
   ```

2. **CORS错误**
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 或指定域名
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **JavaScript错误**
   ```html
   <!-- 在index.html中添加错误处理 -->
   <script>
   window.addEventListener('error', function(e) {
       console.error('JavaScript错误:', e.error);
   });

   window.addEventListener('unhandledrejection', function(e) {
       console.error('未处理的Promise拒绝:', e.reason);
   });
   </script>
   ```

**调试图表:**
```html
<!-- 在dashboard.html中添加调试代码 -->
<div id="chart-container">
    <canvas id="performance-chart"></canvas>
</div>

<script>
const ctx = document.getElementById('performance-chart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: '收益',
            data: [],
            borderColor: 'rgb(75, 192, 192)',
        }]
    },
    options: {
        onClick: (e, elements) => {
            console.log('点击事件:', e, elements);
        }
    }
});

// 测试数据加载
fetch('/api/performance')
  .then(response => response.json())
  .then(data => {
      console.log('数据加载成功:', data);
      chart.data.labels = data.labels;
      chart.data.datasets[0].data = data.values;
      chart.update();
  })
  .catch(error => {
      console.error('数据加载失败:', error);
  });
</script>
```

---

### Q24: 实时数据不更新

**A:** WebSocket连接失败或数据不刷新。

**检查WebSocket连接:**
```javascript
// 在浏览器控制台中执行
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = function() {
    console.log('WebSocket连接已建立');
    ws.send(JSON.stringify({action: 'subscribe', channel: 'performance'}));
};

ws.onmessage = function(event) {
    console.log('收到消息:', JSON.parse(event.data));
};

ws.onerror = function(error) {
    console.error('WebSocket错误:', error);
};

ws.onclose = function() {
    console.log('WebSocket连接已关闭');
};
```

**后端WebSocket检查:**
```python
# 检查WebSocket路由
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket连接已建立")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"收到消息: {data}")

            # 发送响应
            await websocket.send_text(f"响应: {data}")

    except WebSocketDisconnect:
        print("WebSocket连接断开")
```

**常见问题:**

1. **防火墙阻止WebSocket**
   - 检查防火墙设置
   - 确保WebSocket端口开放

2. **代理服务器问题**
   ```nginx
   # Nginx配置示例
   location /ws {
       proxy_pass http://localhost:8001;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_read_timeout 86400;
   }
   ```

3. **浏览器支持**
   - 使用现代浏览器 (Chrome 80+, Firefox 72+, Safari 13+)
   - 检查浏览器是否支持WebSocket

---

## 🔍 故障排除

### Q25: 错误日志分析

**A:** 如何从日志文件中快速定位问题。

**日志位置:**
```
quant_system.log  # 主要日志
logs/  # 历史日志目录
```

**查看日志:**
```bash
# 查看最新100行
tail -n 100 quant_system.log

# 实时监控
tail -f quant_system.log

# 搜索错误
grep -i "error" quant_system.log

# 搜索特定时间段
grep "2023-11-09" quant_system.log
```

**日志级别说明:**

```python
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quant_system.log'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
```

**常见错误模式:**

1. **ImportError**
   ```
   ImportError: No module named 'talib'
   ```
   **解决:** `pip install TA-Lib`

2. **ConnectionError**
   ```
   requests.exceptions.ConnectionError: HTTPSConnectionPool
   ```
   **解决:** 检查网络连接和API端点

3. **KeyError**
   ```
   KeyError: '0700.HK'
   ```
   **解决:** 检查数据字典键名

4. **ValueError**
   ```
   ValueError: could not convert string to float: 'N/A'
   ```
   **解决:** 数据清理，转换N/A为NaN

5. **MemoryError**
   ```
   MemoryError: Unable to allocate array
   ```
   **解决:** 减少数据量或增加内存

**分析脚本:**
```python
#!/usr/bin/env python3
import re
from collections import Counter

def analyze_log(log_file):
    """分析日志文件中的错误"""
    errors = []
    warnings = []

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'ERROR' in line:
                errors.append(line)
            elif 'WARNING' in line:
                warnings.append(line)

    # 错误统计
    error_types = Counter(
        re.search(r'(\w+Error)', line).group(1)
        for line in errors
        if re.search(r'(\w+Error)', line)
    )

    print(f"=== 日志分析报告 ===")
    print(f"总错误数: {len(errors)}")
    print(f"总警告数: {len(warnings)}")
    print(f"\n错误类型统计:")
    for error_type, count in error_types.most_common(10):
        print(f"  {error_type}: {count}次")

    print(f"\n最近5个错误:")
    for error in errors[-5:]:
        print(error.strip())

if __name__ == "__main__":
    analyze_log('quant_system.log')
```

---

### Q26: 快速诊断工具

**A:** 使用内置工具快速诊断系统问题。

**系统诊断脚本:**
```python
#!/usr/bin/env python3
"""
系统诊断工具
检查系统配置、依赖、环境等
"""

import sys
import os
import importlib
import platform
from pathlib import Path

def check_python():
    """检查Python版本"""
    version = sys.version_info
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    if version < (3, 10):
        print("⚠️  警告: 建议使用Python 3.10或更高版本")
        return False
    return True

def check_dependencies():
    """检查依赖库"""
    required = [
        'pandas', 'numpy', 'talib', 'fastapi',
        'uvicorn', 'requests', 'talib'
    ]

    missing = []
    for module in required:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - 未安装")
            missing.append(module)

    return len(missing) == 0, missing

def check_files():
    """检查必要文件"""
    required_files = [
        'requirements.txt',
        '.env',
        'enhanced_strategy_backtest.py',
        'complete_project_system.py'
    ]

    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - 不存在")
            missing.append(file)

    return len(missing) == 0, missing

def check_data_access():
    """检查数据访问"""
    try:
        import requests
        response = requests.get(
            "http://18.180.162.113:9191/inst/getInst",
            params={"symbol": "0700.hk", "duration": 10},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ 数据API可访问")
            return True
        else:
            print(f"⚠️  数据API返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 数据API访问失败: {e}")
        return False

def check_ports():
    """检查端口占用"""
    import socket

    ports_to_check = [8001, 8002, 8003]
    occupied = []
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            print(f"⚠️  端口 {port} 已被占用")
            occupied.append(port)
        else:
            print(f"✅ 端口 {port} 可用")
        sock.close()

    return len(occupied) == 0, occupied

def main():
    print("=" * 60)
    print("港股量化交易系统 - 系统诊断")
    print("=" * 60)

    print("\n📋 Python环境检查:")
    python_ok = check_python()

    print("\n📦 依赖库检查:")
    deps_ok, missing_deps = check_dependencies()

    print("\n📁 文件检查:")
    files_ok, missing_files = check_files()

    print("\n🌐 数据访问检查:")
    data_ok = check_data_access()

    print("\n🔌 端口检查:")
    ports_ok, occupied_ports = check_ports()

    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    if python_ok and deps_ok and files_ok and data_ok and ports_ok:
        print("✅ 系统检查通过，可以正常使用！")
        return True
    else:
        print("⚠️  发现问题，需要修复:")
        if not python_ok:
            print("  - 请升级Python到3.10或更高版本")
        if not deps_ok:
            print(f"  - 请安装缺失的依赖: pip install {' '.join(missing_deps)}")
        if not files_ok:
            print(f"  - 请检查缺失的文件: {', '.join(missing_files)}")
        if not data_ok:
            print("  - 请检查网络连接或API端点")
        if not ports_ok:
            print(f"  - 请使用其他端口: python complete_project_system.py --port {occupied_ports[0]+1}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

**运行诊断:**
```bash
python diagnostic_tool.py
```

---

## 💡 最佳实践

### Q27: 策略开发最佳实践

**A:** 避免常见错误，提高策略质量。

**1. 数据质量优先**
```python
# ✅ 正确: 验证数据
def load_data(symbol, start_date, end_date):
    data = fetch_data(symbol, start_date, end_date)

    # 验证必要字段
    required = ['date', 'open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in data.columns:
            raise ValueError(f"缺少必要字段: {col}")

    # 检查缺失值
    if data.isnull().any().any():
        print("警告: 发现缺失值，正在填充...")
        data = data.fillna(method='ffill')

    # 检查重复
    duplicates = data.duplicated().sum()
    if duplicates > 0:
        print(f"警告: 发现 {duplicates} 条重复数据")
        data = data.drop_duplicates()

    return data
```

**2. 使用参数验证**
```python
# ✅ 正确: 验证参数
def run_strategy(data, **params):
    # 验证参数范围
    if params.get('k_period', 0) < 5 or params['k_period'] > 30:
        raise ValueError("k_period 必须在 5-30 之间")

    if params.get('oversold', 0) >= params.get('overbought', 100):
        raise ValueError("oversold 必须小于 overbought")

    # 执行策略
    return calculate_signals(data, params)
```

**3. 避免前视偏差**
```python
# ❌ 错误: 使用未来数据
def calculate_signals(data):
    # 这里使用了shift(-1)，相当于看到了未来
    data['ma_short'] = data['close'].rolling(10).mean()
    data['signal'] = (data['close'] > data['ma_short'].shift(-1)).astype(int)

# ✅ 正确: 仅使用历史数据
def calculate_signals(data):
    data['ma_short'] = data['close'].rolling(10).mean()
    # 使用当前时刻的移动平均
    data['signal'] = (data['close'] > data['ma_short']).astype(int)
```

**4. 包含交易成本**
```python
# ✅ 正确: 扣除交易成本
def backtest_with_costs(data, signals, commission=0.001):
    capital = 100000  # 初始资金
    position = 0  # 持仓
    cash = capital

    for i in range(1, len(data)):
        # 检查信号
        if signals.iloc[i] == 1 and position == 0:  # 买入
            price = data['close'].iloc[i]
            position = cash * (1 - commission) / price
            cash = 0

        elif signals.iloc[i] == -1 and position > 0:  # 卖出
            price = data['close'].iloc[i]
            cash = position * price * (1 - commission)
            position = 0

    return cash
```

**5. 多时间框架验证**
```python
# ✅ 正确: 多时间框架测试
def validate_strategy(data, strategy_params):
    # 将数据分为多个时间段
    total_days = len(data)
    train_size = int(total_days * 0.6)  # 60%训练
    val_size = int(total_days * 0.2)  # 20%验证

    train_data = data[:train_size]
    val_data = data[train_size:train_size+val_size]
    test_data = data[train_size+val_size:]

    # 在每个时间段上测试
    train_result = run_strategy(train_data, strategy_params)
    val_result = run_strategy(val_data, strategy_params)
    test_result = run_strategy(test_data, strategy_params)

    return {
        'train': train_result,
        'val': val_result,
        'test': test_result
    }
```

---

### Q28: 代码规范

**A:** 编写清晰、可维护的代码。

**命名规范:**
```python
# ✅ 好的命名
def calculate_moving_average(prices: pd.Series, window: int) -> pd.Series:
    """计算移动平均线"""
    return prices.rolling(window=window).mean()

class StrategyBacktest:
    """策略回测类"""
    def __init__(self, symbol: str, start_date: str, end_date: str):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

    def run_backtest(self) -> Dict[str, float]:
        """运行回测"""
        pass

# ❌ 差的命名
def calcMA(p, w):
    return p.rolling(w).mean()

class sb:
    def __init__(self, s, sd, ed):
        self.s = s
```

**文档字符串:**
```python
def calculate_kdj(data: pd.DataFrame, k_period: int = 9,
                 d_period: int = 3) -> pd.DataFrame:
    """
    计算KDJ指标

    Parameters
    ----------
    data : pd.DataFrame
        包含OHLC价格数据的DataFrame
    k_period : int, default 9
        K值计算周期
    d_period : int, default 3
        D值计算周期

    Returns
    -------
    pd.DataFrame
        包含KDJ指标的DataFrame，列名为'k'、'd'、'j'

    Examples
    --------
    >>> df = pd.DataFrame(...)
    >>> result = calculate_kdj(df, k_period=9, d_period=3)
    >>> print(result[['k', 'd']].tail())
    """
    pass
```

**错误处理:**
```python
def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取股票数据

    Raises
    ------
    ValueError
        当股票代码格式不正确时
    ConnectionError
        当网络连接失败时
    DataError
        当数据格式不正确时
    """
    # 参数验证
    if not symbol or not isinstance(symbol, str):
        raise ValueError("股票代码不能为空")

    if not re.match(r'^\d{4}\.hk$', symbol.lower()):
        raise ValueError("股票代码格式错误，应为: 0000.hk")

    try:
        # 尝试获取数据
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # 验证数据
        if not data or len(data) == 0:
            raise DataError(f"未获取到 {symbol} 的数据")

        # 转换为DataFrame
        df = pd.DataFrame(data)
        return df

    except requests.ConnectionError as e:
        raise ConnectionError(f"网络连接失败: {e}")
    except requests.Timeout as e:
        raise ConnectionError(f"请求超时: {e}")
    except Exception as e:
        raise DataError(f"数据处理错误: {e}")
```

**类型注解:**
```python
from typing import List, Dict, Optional, Union
import pandas as pd

def optimize_parameters(
    data: pd.DataFrame,
    strategy_type: str,
    max_workers: int = 4,
    metric: str = "total_return"
) -> Dict[str, Union[float, List[Dict[str, float]]]]:
    """
    优化策略参数

    Parameters
    ----------
    data : pd.DataFrame
        输入数据
    strategy_type : str
        策略类型
    max_workers : int, optional
        最大并行数
    metric : str, optional
        优化指标

    Returns
    -------
    Dict
        包含最佳参数和结果的字典
    """
    pass
```

---

### Q29: 测试策略

**A:** 全面测试确保策略可靠性。

**单元测试:**
```python
import unittest
import pandas as pd
import numpy as np

class TestKDJStrategy(unittest.TestCase):
    """KDJ策略单元测试"""

    def setUp(self):
        """测试前准备"""
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        self.test_data = pd.DataFrame({
            'date': dates,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 105,
            'low': np.random.randn(100).cumsum() + 95,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        })

    def test_kdj_calculation(self):
        """测试KDJ计算"""
        result = calculate_kdj(self.test_data, k_period=9, d_period=3)

        # 验证返回值
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('k', result.columns)
        self.assertIn('d', result.columns)
        self.assertIn('j', result.columns)

        # 验证数据范围
        self.assertTrue(result['k'].between(0, 100).all())
        self.assertTrue(result['d'].between(0, 100).all())

    def test_signal_generation(self):
        """测试信号生成"""
        signals = generate_kdj_signals(self.test_data)

        # 验证信号值
        valid_signals = [-1, 0, 1]
        self.assertTrue(all(s in valid_signals for s in signals))

    def test_backtest_execution(self):
        """测试回测执行"""
        backtest = KDJBacktest("0700.hk", "2020-01-01", "2021-01-01")
        result = backtest.run()

        # 验证结果
        self.assertIn('total_return', result)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('max_drawdown', result)

        # 验证结果合理性
        self.assertIsInstance(result['total_return'], float)
        self.assertGreater(result['total_return'], -1)  # 不应亏损超过100%
        self.assertLess(result['max_drawdown'], 0)  # 回撤应为负数

if __name__ == '__main__':
    unittest.main()
```

**性能测试:**
```python
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

class TestPerformance(unittest.TestCase):
    """性能测试"""

    def test_backtest_speed(self):
        """测试回测速度"""
        backtest = EnhancedStrategyBacktest("0700.hk", "2020-01-01", "2023-01-01")
        backtest.load_data()

        start_time = time.time()
        result = backtest.run_kdj_strategy()
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"回测执行时间: {execution_time:.2f}秒")

        # 要求在10秒内完成
        self.assertLess(execution_time, 10)

    def test_optimization_speed(self):
        """测试优化速度"""
        backtest = EnhancedStrategyBacktest("0700.hk", "2020-01-01", "2023-01-01")
        backtest.load_data()

        start_time = time.time()
        result = backtest.optimize_parameters('kdj', max_workers=4)
        end_time = time.time()

        optimization_time = end_time - start_time
        print(f"参数优化时间: {optimization_time:.2f}秒")

        # 要求在300秒（5分钟）内完成
        self.assertLess(optimization_time, 300)

    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        backtest = EnhancedStrategyBacktest("0700.hk", "2020-01-01", "2023-01-01")
        backtest.load_data()
        backtest.run_kdj_strategy()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"内存增长: {memory_increase:.2f}MB")

        # 内存增长不应超过2GB
        self.assertLess(memory_increase, 2048)
```

**集成测试:**
```python
import pytest
from enhanced_strategy_backtest import EnhancedStrategyBacktest

@pytest.mark.integration
def test_full_workflow():
    """完整流程集成测试"""
    # 1. 获取数据
    backtest = EnhancedStrategyBacktest("0700.hk", "2022-01-01", "2023-01-01")
    backtest.load_data()

    assert len(backtest.data) > 0

    # 2. 运行策略
    result = backtest.run_kdj_strategy()
    assert result['total_return'] is not None

    # 3. 优化参数
    best_params = backtest.optimize_parameters('kdj', max_workers=2)
    assert len(best_params) > 0

    # 4. 验证结果
    assert result['total_return'] > -1
    assert result['max_drawdown'] < 0
```

---

### Q30: 生产环境部署

**A:** 安全、高效地部署到生产环境。

**环境准备:**
```bash
# 创建生产环境
python -m venv .venv_prod
source .venv_prod/bin/activate  # Linux/macOS
# .venv_prod\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp .env .env.prod
# 编辑 .env.prod 添加生产环境配置
```

**.env.prod 配置:**
```env
# 生产环境配置
ENVIRONMENT=production
DEBUG=False
API_HOST=0.0.0.0  # 允许外部访问
API_PORT=8001

# 日志级别
LOG_LEVEL=INFO

# 数据库
DATABASE_URL=sqlite:///prod.db

# 安全设置
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,localhost

# 第三方服务
TELEGRAM_BOT_TOKEN=prod_bot_token
```

**使用Gunicorn部署:**
```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -k uvicorn.workers.UvicornWorker complete_project_system:app \
  --bind 0.0.0.0:8001 \
  --access-logfile access.log \
  --error-logfile error.log \
  --log-level info
```

**使用systemd服务 (Linux):**
```ini
# /etc/systemd/system/codex-quant.service
[Unit]
Description=CODEX HK Quant System
After=network.target

[Service]
User=codex
Group=codex
WorkingDirectory=/opt/codex-hk-quant
Environment=PATH=/opt/codex-hk-quant/.venv_prod/bin
ExecStart=/opt/codex-hk-quant/.venv_prod/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker complete_project_system:app --bind 0.0.0.0:8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable codex-quant
sudo systemctl start codex-quant

# 检查状态
sudo systemctl status codex-quant
# 查看日志
sudo journalctl -u codex-quant -f
```

**Nginx反向代理:**
```nginx
# /etc/nginx/sites-available/codex-quant
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**监控和告警:**
```python
# monitoring/health_check.py
import requests
import logging
from datetime import datetime

def check_system_health():
    """系统健康检查"""
    try:
        # 检查API
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        if response.status_code == 200:
            logging.info("✅ 系统健康")
            return True
        else:
            logging.error(f"❌ API返回错误: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ 系统不可用: {e}")
        return False

if __name__ == "__main__":
    if not check_system_health():
        # 发送告警
        # 可以集成Telegram、邮件等
        print("需要人工干预")
```

**备份策略:**
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/codex-quant"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
cp prod.db $BACKUP_DIR/quant_system_$DATE.db
cp -r logs $BACKUP_DIR/logs_$DATE
cp .env.prod $BACKUP_DIR/env_$DATE

# 压缩备份
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/quant_system_$DATE.db $BACKUP_DIR/logs_$DATE

# 保留最近30天的备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR/backup_$DATE.tar.gz"
```

**自动重启脚本:**
```bash
#!/bin/bash
# restart.sh

SERVICE="codex-quant"
MAX_RESTARTS=3
RESTART_COUNT=0

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    echo "尝试启动 $SERVICE (第 $((RESTART_COUNT + 1)) 次)"
    sudo systemctl start $SERVICE

    sleep 10

    if systemctl is-active --quiet $SERVICE; then
        echo "✅ $SERVICE 启动成功"
        exit 0
    else
        echo "❌ $SERVICE 启动失败"
        RESTART_COUNT=$((RESTART_COUNT + 1))
        sleep 5
    fi
done

echo "❌ 超过最大重启次数，服务无法启动"
exit 1
```

---

## ❓ 其他问题

### Q31: 如何贡献代码？

**A:** 欢迎贡献代码！

**步骤:**

1. **Fork项目**
   ```
   访问GitHub，点击Fork按钮
   ```

2. **克隆到本地**
   ```bash
   git clone https://github.com/your-username/codex-hk-quant.git
   cd codex-hk-quant
   git remote add upstream https://github.com/original/codex-hk-quant.git
   ```

3. **创建开发分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **设置开发环境**
   ```bash
   python -m venv .venv_dev
   source .venv_dev/bin/activate
   pip install -r requirements.txt
   pip install -r test_requirements.txt
   ```

5. **编写代码**
   - 遵循代码规范
   - 添加单元测试
   - 更新文档

6. **运行测试**
   ```bash
   python -m pytest tests/ -v
   ```

7. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   git push origin feature/your-feature-name
   ```

8. **创建Pull Request**
   ```
   在GitHub上创建Pull Request
   描述变更内容和测试结果
   ```

**代码规范检查:**
```bash
# 安装pre-commit
pip install pre-commit
pre-commit install

# 运行检查
pre-commit run --all-files
```

---

### Q32: 如何报告Bug？

**A:** 详细报告Bug有助于快速修复。

**GitHub Issue模板:**
```markdown
## Bug描述
简要描述Bug

## 复现步骤
1. 运行 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 预期结果
描述预期会发生什么

## 实际结果
描述实际发生了什么

## 屏幕截图
如果适用，添加屏幕截图

## 环境信息
- OS: [e.g. Ubuntu 20.04]
- Python版本: [e.g. 3.10.5]
- 系统版本: [e.g. 1.0.0]

## 日志
```
复制相关日志
```

## 其他信息
添加任何其他关于问题的信息
```

**提供调试信息:**
```python
# 运行系统诊断
python diagnostic_tool.py > diagnostic_output.txt 2>&1

# 收集系统信息
import platform
import sys
import pkg_resources

print(f"操作系统: {platform.system()} {platform.release()}")
print(f"Python版本: {sys.version}")
print(f"已安装包:")
for pkg in pkg_resources.working_set:
    print(f"  {pkg.project_name}=={pkg.version}")
```

---

### Q33: 如何获取最新更新？

**A:** 保持系统最新。

**获取更新:**
```bash
# 拉取最新代码
git pull upstream main

# 更新依赖
pip install -r requirements.txt --upgrade

# 运行测试
python -m pytest tests/

# 重启服务
sudo systemctl restart codex-quant
```

**版本历史:**
- 查看 `CHANGELOG.md` 了解更新内容
- 查看 `RELEASES.md` 了解版本信息

**订阅更新:**
- 关注GitHub Release
- 订阅邮件通知
- 加入社区讨论

---

### Q34: 性能基准参考

**A:** 不同配置下的性能数据。

**测试环境:**
- **数据**: 0700.hk, 2020-2023 (3年日数据)
- **策略**: 11种技术指标
- **参数优化**: 所有参数组合

**结果:**

| 配置 | 启动时间 | 策略运行 | 参数优化 | 内存使用 |
|------|----------|----------|----------|----------|
| 4核 / 8GB | 15-20秒 | 8-12分钟 | 60-90分钟 | 4-6GB |
| 8核 / 16GB | 8-12秒 | 4-6分钟 | 30-45分钟 | 6-8GB |
| 16核 / 32GB | 5-8秒 | 2-4分钟 | 15-25分钟 | 8-12GB |

**优化建议:**
- 使用SSD存储提高I/O性能
- 增加内存减少磁盘交换
- 使用多核CPU加速并行计算

---

### Q35: 技术支持渠道

**A:** 获取帮助的方式。

**官方渠道:**

1. **GitHub Issues**
   - 报告Bug
   - 功能请求
   - 网址: https://github.com/your-repo/issues

2. **文档**
   - 快速开始: `docs/quickstart.md`
   - 用户指南: `docs/user_guide.md`
   - API参考: http://localhost:8001/docs

3. **社区论坛**
   - 讨论区: https://forum.example.com
   - 教程区: https://tutorials.example.com

**商业支持:**
- 邮箱: support@example.com
- 企业版: enterprise@example.com

---

## 📞 联系与反馈

如果您的问题没有在FAQ中找到答案，请:

1. **搜索现有Issues** - 也许其他人已经遇到
2. **查看文档** - 详细阅读相关文档
3. **运行诊断工具** - `python diagnostic_tool.py`
4. **提交Issue** - 使用Bug报告模板
5. **参与讨论** - 加入社区讨论

我们致力于提供最好的用户体验！

---

**最后更新: 2025-11-09**
