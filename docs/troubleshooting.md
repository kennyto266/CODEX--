# 故障排除指南

本指南帮助您快速诊断和解决港股量化交易系统使用中遇到的问题。

## 📋 目录

- [🔍 快速诊断](#快速诊断)
- [⚙️ 系统安装问题](#系统安装问题)
- [💹 策略运行问题](#策略运行问题)
- [📊 数据获取问题](#数据获取问题)
- [🌐 网络连接问题](#网络连接问题)
- [🖥️ 系统性能问题](#系统性能问题)
- [🤖 Telegram机器人问题](#telegram机器人问题)
- [📈 Web仪表板问题](#web仪表板问题)
- [🔧 环境配置问题](#环境配置问题)
- [📝 日志分析](#日志分析)
- [🚨 紧急处理](#紧急处理)
- [📞 获取帮助](#获取帮助)

---

## 🔍 快速诊断

### 诊断工具

运行系统诊断，快速定位问题:

```bash
# 运行完整诊断
python diagnostic_tool.py

# 预期输出:
# ✅ Python版本: 3.10.8
# ✅ pandas 1.5.3
# ✅ numpy 1.24.3
# ✅ talib 0.4.25
# ✅ 数据API可访问
# ✅ 端口8001可用
#
# 系统检查通过，可以正常使用！
```

### 快速检查清单

在报告问题前，请先检查:

- [ ] Python版本是否为3.10或更高
- [ ] 虚拟环境是否已激活
- [ ] 所有依赖是否已安装 (`pip list`)
- [ ] 网络连接是否正常
- [ ] 端口8001是否被占用
- [ ] 日志文件是否有错误 (`quant_system.log`)

---

## ⚙️ 系统安装问题

### 问题1: TA-Lib安装失败

**症状:**
```
ERROR: Microsoft Visual C++ 14.0 is required
```

**解决方案:**

**方案1: 使用预编译包 (推荐)**
```bash
# 1. 访问 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 2. 下载对应版本，如: TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
# 3. 安装
pip install TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
```

**方案2: 安装Build Tools**
```bash
# 下载并安装 Microsoft C++ Build Tools
# 然后运行:
pip install TA-Lib
```

**方案3: 使用conda**
```bash
conda install -c conda-forge ta-lib
```

**验证安装:**
```python
import talib
print(f"TA-Lib版本: {talib.__version__}")
print("✅ TA-Lib安装成功")
```

---

### 问题2: 虚拟环境创建失败

**症状:**
```
python: command not found
```

**解决方案:**

**Windows:**
```cmd
# 检查Python安装
where python

# 如果找不到，使用py命令
py -m venv .venv310
.venv310\Scripts\activate

# 或从Microsoft Store安装Python
```

**Linux:**
```bash
# 安装python3和venv
sudo apt update
sudo apt install python3 python3-venv python3-pip

# 创建虚拟环境
python3 -m venv .venv310
source .venv310/bin/activate
```

---

### 问题3: 依赖安装超时

**症状:**
```
pip install -r requirements.txt
# TimeoutError
```

**解决方案:**

**方案1: 增加超时时间**
```bash
pip install -r requirements.txt --timeout 1000
```

**方案2: 使用国内镜像**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

**方案3: 逐个安装**
```bash
pip install pandas numpy matplotlib
pip install -r requirements.txt  # 剩余依赖
```

---

## 💹 策略运行问题

### 问题4: 回测结果为NaN

**症状:**
```
总收益率: nan%
夏普比率: nan
```

**原因和解决方案:**

**原因1: 数据中有NaN或无穷值**
```python
# 检查数据
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')
print(f"缺失值: {df.isnull().sum().sum()}")
print(f"无穷值: {np.isinf(df).sum().sum()}")

# 清理数据
df = df.dropna()
df = df.replace([np.inf, -np.inf], np.nan).dropna()
```

**原因2: 所有收益率都是0**
```python
# 检查收益率
returns = df['close'].pct_change().dropna()
print(f"收益率统计: {returns.describe()}")

if returns.std() == 0:
    print("错误: 所有收益率都相同，无法计算指标")
```

**原因3: 移动平均计算错误**
```python
# 错误: 使用未来数据
ma = df['close'].rolling(20).mean().shift(-20)  # 错误!

# 正确: 仅使用历史数据
ma = df['close'].rolling(20).mean()  # 正确
```

---

### 问题5: 策略信号不准确

**症状:**
- 买入/卖出信号与预期不符
- 信号过于频繁或过少

**调试方法:**

**1. 验证指标计算**
```python
import talib
import pandas as pd

# 计算KDJ
k, d = talib.STOCH(df['high'], df['low'], df['close'])
j = 3 * k - 2 * d

# 检查前10行
print("KDJ指标:")
print(pd.DataFrame({'K': k, 'D': d, 'J': j}).head(10))
```

**2. 检查信号逻辑**
```python
# 正确的穿越信号
prev_k = k.shift(1)
prev_d = d.shift(1)

buy_signal = (k > d) & (prev_k <= prev_d) & (k < 20)
sell_signal = (k < d) & (prev_k >= prev_d) & (k > 80)

print(f"买入信号数: {buy_signal.sum()}")
print(f"卖出信号数: {sell_signal.sum()}")
```

**3. 可视化检查**
```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df.index, df['close'], label='收盘价')

# 标记买入/卖出点
ax.scatter(df.index[buy_signal], df['close'][buy_signal],
           color='green', marker='^', s=100, label='买入')
ax.scatter(df.index[sell_signal], df['close'][sell_signal],
           color='red', marker='v', s=100, label='卖出')

ax.legend()
plt.show()
```

---

### 问题6: 参数优化时间过长

**症状:**
```
正在优化参数... 预计需要2小时
```

**优化方案:**

**1. 减少参数范围**
```python
# 原始: 6×3×4×4 = 288个组合
param_grid = {
    'k_period': [5, 9, 14, 20, 25, 30],
    'd_period': [3, 5, 7],
    'oversold': [15, 20, 25, 30],
    'overbought': [70, 75, 80, 85]
}

# 优化后: 4×2×3×3 = 72个组合
param_grid = {
    'k_period': [9, 14, 20, 25],
    'd_period': [3, 5],
    'oversold': [20, 25, 30],
    'overbought': [70, 75, 80]
}
```

**2. 使用遗传算法**
```python
from scipy.optimize import differential_evolution

def objective(params):
    k, d = params
    result = backtest.run_kdj_strategy(
        k_period=int(k),
        d_period=int(d)
    )
    return -result['total_return']  # 最小化负收益

result = differential_evolution(
    objective,
    bounds=[(5, 30), (3, 5)],
    maxiter=20,  # 限制迭代次数
    seed=42
)
```

**3. 并行优化**
```python
# 减少max_workers避免过载
results = backtest.optimize_parameters(
    strategy_type='kdj',
    max_workers=4  # 而不是8或16
)
```

---

## 📊 数据获取问题

### 问题7: API连接超时

**症状:**
```
requests.exceptions.ConnectTimeout: HTTPSConnectionPool
```

**诊断:**
```python
import requests
import time

start_time = time.time()
try:
    response = requests.get(
        "http://18.180.162.113:9191/inst/getInst",
        params={"symbol": "0700.hk", "duration": 10},
        timeout=30
    )
    elapsed = time.time() - start_time
    print(f"连接成功，耗时: {elapsed:.2f}秒")
except Exception as e:
    print(f"连接失败: {e}")
```

**解决方案:**

**1. 检查网络**
```bash
# Windows
ping 18.180.162.113
tracert 18.180.162.113

# Linux/macOS
ping 18.180.162.113
traceroute 18.180.162.113
```

**2. 增加超时时间**
```python
response = requests.get(
    url,
    params=params,
    timeout=60  # 60秒
)
```

**3. 使用代理**
```python
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}

response = requests.get(url, params=params, proxies=proxies)
```

---

### 问题8: 数据格式错误

**症状:**
```
KeyError: 'close'
TypeError: list indices must be integers or slices, not str
```

**解决方案:**

**1. 检查数据结构**
```python
data = requests.get(url, params=params).json()

print(f"数据类型: {type(data)}")
print(f"前5条数据: {data[:5]}")
print(f"数据键: {data[0].keys() if isinstance(data, list) else 'N/A'}")
```

**2. 标准化数据格式**
```python
import pandas as pd

# 转换为DataFrame
df = pd.DataFrame(data)

# 标准化列名
column_mapping = {
    'Date': 'date',
    'Close': 'close',
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Volume': 'volume'
}
df = df.rename(columns=column_mapping)

# 确保数据类型正确
df['date'] = pd.to_datetime(df['date'])
df['open'] = pd.to_numeric(df['open'], errors='coerce')
df['high'] = pd.to_numeric(df['high'], errors='coerce')
df['low'] = pd.to_numeric(df['low'], errors='coerce')
df['close'] = pd.to_numeric(df['close'], errors='coerce')
df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

# 清理NaN
df = df.dropna()
```

---

### 问题9: 股票代码错误

**症状:**
```
API返回数据为空或404
```

**解决方案:**

**1. 使用正确格式**
```python
# ✅ 正确
symbol = "0700.hk"  # 小写 + .hk

# ❌ 错误
symbol = "0700.HK"  # 大写
symbol = "700.hk"   # 缺少前导0
symbol = "0700"     # 缺少后缀
```

**2. 验证股票代码**
```python
def validate_symbol(symbol):
    """验证股票代码格式"""
    import re

    if not re.match(r'^\d{4}\.hk$', symbol.lower()):
        print(f"错误: {symbol} 格式不正确")
        print("正确格式: 0000.hk (4位数字 + .hk，小写)")
        return False

    return True

# 测试
test_symbols = ["0700.hk", "0388.hk", "1398.hk", "0700.HK"]
for sym in test_symbols:
    print(f"{sym}: {validate_symbol(sym)}")
```

---

## 🌐 网络连接问题

### 问题10: 防火墙阻止连接

**症状:**
```
Connection refused
Connection aborted
```

**解决方案:**

**Windows防火墙:**
1. 打开"Windows Defender防火墙"
2. 点击"允许应用或功能通过Windows Defender防火墙"
3. 找到Python或您的应用程序
4. 勾选"专用"和"公用"网络
5. 点击"确定"

**Linux防火墙 (UFW):**
```bash
# 开放端口
sudo ufw allow 8001
sudo ufw allow 9191

# 查看状态
sudo ufw status
```

**iptables:**
```bash
# 开放端口
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 9191 -j ACCEPT

# 保存规则
sudo iptables-save > /etc/iptables/rules.v4
```

---

### 问题11: 代理服务器配置

**症状:**
```
HTTPSConnectionPool: ProxyError
```

**解决方案:**

**1. 设置环境变量**
```bash
# Linux/macOS
export http_proxy=http://proxy.example.com:8080
export https_proxy=https://proxy.example.com:8080

# Windows
set http_proxy=http://proxy.example.com:8080
set https_proxy=https://proxy.example.com:8080
```

**2. 在Python中配置**
```python
import os
import requests

# 从环境变量读取
os.environ['http_proxy'] = 'http://proxy.example.com:8080'
os.environ['https_proxy'] = 'https://proxy.example.com:8080'

# 或直接设置
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}

response = requests.get(url, proxies=proxies)
```

**3. 忽略代理 (开发环境)**
```python
response = requests.get(url, proxies={'http': None, 'https': None})
```

---

## 🖥️ 系统性能问题

### 问题12: 内存不足

**症状:**
```
MemoryError: Unable to allocate array
系统变慢或卡顿
```

**解决方案:**

**1. 监控内存使用**
```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"当前内存使用: {memory_mb:.2f} MB")

# 系统内存
memory = psutil.virtual_memory()
print(f"系统内存使用率: {memory.percent}%")
```

**2. 优化数据**
```python
# 使用float32代替float64
df = pd.read_csv('data.csv', dtype={
    'open': 'float32',
    'high': 'float32',
    'low': 'float32',
    'close': 'float32',
    'volume': 'int32'
})

# 内存节省
print(f"优化前: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
```

**3. 分批处理**
```python
# 代替一次性加载所有数据
chunk_size = 1000
chunks = []

for chunk in pd.read_csv('large_data.csv', chunksize=chunk_size):
    processed = process_chunk(chunk)
    chunks.append(processed)

final_df = pd.concat(chunks)
```

**4. 及时清理**
```python
import gc

# 删除大变量
del large_dataframe
gc.collect()  # 强制垃圾回收
```

---

### 问题13: CPU使用率过高

**症状:**
- 系统风扇噪音大
- 其他程序运行缓慢
- CPU使用率持续100%

**解决方案:**

**1. 减少并行度**
```python
# 减少max_workers
results = backtest.optimize_parameters(
    strategy_type='kdj',
    max_workers=2  # 代替8
)
```

**2. 优化算法**
```python
# 代替嵌套循环
# ❌ 慢
for i in range(len(df)):
    for j in range(len(df.columns)):
        df.iloc[i, j] = complex_calculation(i, j)

# ✅ 快
df = df.apply(lambda col: col.apply(complex_calculation))
```

**3. 使用缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param):
    # 复杂计算
    return result
```

**4. 限制进程数**
```bash
# 在系统层面限制
ulimit -u 1000  # 限制用户进程数

# 或在Python中
import resource
resource.setrlimit(resource.NPROC, (100, 100))
```

---

### 问题14: 磁盘空间不足

**症状:**
```
OSError: [Errno 28] No space left on device
```

**解决方案:**

**1. 清理缓存**
```bash
# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 清理pytest缓存
rm -rf .pytest_cache

# 清理pip缓存
pip cache purge
```

**2. 清理日志**
```bash
# 查看日志大小
du -sh quant_system.log

# 备份并清理
mv quant_system.log quant_system.log.bak
touch quant_system.log

# 或使用logrotate
sudo logrotate -f /etc/logrotate.conf
```

**3. 清理数据文件**
```bash
# 删除临时文件
rm -rf /tmp/*
rm -rf ~/.cache/*

# 清理下载包
pip cache purge
```

**4. 监控磁盘使用**
```python
import shutil

total, used, free = shutil.disk_usage("/")
print(f"总空间: {total // (1024**3)} GB")
print(f"已使用: {used // (1024**3)} GB")
print(f"可用空间: {free // (1024**3)} GB")

# 如果可用空间 < 1GB，警告
if free < 1024**3:
    print("警告: 可用空间不足1GB！")
```

---

## 🤖 Telegram机器人问题

### 问题15: 机器人不回复

**症状:**
- 发送消息给机器人没有响应
- 机器人显示在线但不回复

**诊断步骤:**

**1. 验证Token**
```python
import requests

token = "YOUR_BOT_TOKEN"
url = f"https://api.telegram.org/bot{token}/getMe"

response = requests.get(url)
result = response.json()

if result['ok']:
    print("✅ Token有效")
    print(f"机器人名称: {result['result']['first_name']}")
    print(f"用户名: {result['result']['username']}")
else:
    print(f"❌ Token无效: {result}")
```

**2. 检查Chat ID**
```python
# 发送消息给自己
chat_id = "YOUR_CHAT_ID"
url = f"https://api.telegram.org/bot{token}/sendMessage"
data = {"chat_id": chat_id, "text": "测试消息"}

response = requests.post(url, data=data)
if response.json()['ok']:
    print("✅ Chat ID有效")
else:
    print(f"❌ Chat ID错误: {response.json()}")
```

**3. 获取更新**
```python
url = f"https://api.telegram.org/bot{token}/getUpdates"
response = requests.get(url)
updates = response.json()

if updates['ok']:
    print(f"获取到 {len(updates['result'])} 条更新")
    for update in updates['result'][-3:]:
        if 'message' in update:
            msg = update['message']
            print(f"来自: {msg['from']['first_name']}")
            print(f"消息: {msg.get('text', 'N/A')}")
```

**完整测试脚本:**
```python
#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("❌ 请在.env文件中设置TELEGRAM_BOT_TOKEN和TELEGRAM_CHAT_ID")
        return

    # 测试1: 验证Token
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    if not response.json()['ok']:
        print(f"❌ Token验证失败: {response.json()}")
        return

    print("✅ 机器人连接成功")

    # 测试2: 发送消息
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": "🧪 机器人测试\n连接正常！"
    }
    response = requests.post(url, data=data)

    if response.json()['ok']:
        print("✅ 测试消息发送成功")
    else:
        print(f"❌ 消息发送失败: {response.json()}")

if __name__ == "__main__":
    test_bot()
```

---

### 问题16: Webhook配置错误

**症状:**
```
Webhook was not set
```

**解决方案:**

**1. 清除Webhooks**
```python
url = f"https://api.telegram.org/bot{token}/deleteWebhook"
requests.get(url)
print("✅ Webhook已清除")
```

**2. 使用Polling模式**
```python
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 创建应用
application = Application.builder().token(token).build()

# 添加处理器
application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 使用polling (不是webhook)
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

---

## 📈 Web仪表板问题

### 问题17: 页面无法加载

**症状:**
- 浏览器显示"无法访问此网站"
- 连接被拒绝

**诊断:**

**1. 检查服务状态**
```bash
# 检查进程
# Windows
tasklist | findstr python

# Linux/macOS
ps aux | grep python

# 检查端口
netstat -an | grep 8001
```

**2. 测试本地连接**
```bash
# 使用curl
curl http://localhost:8001

# 或telnet
telnet localhost 8001
```

**3. 查看浏览器控制台**
- 按F12打开开发者工具
- 查看Console选项卡
- 查找错误信息 (红色错误)

**解决方案:**

**1. 启动服务**
```bash
python complete_project_system.py
```

**2. 使用其他端口**
```bash
python complete_project_system.py --port 8002
```

**3. 检查防火墙**
```bash
# Windows: 允许Python通过防火墙
# Linux:
sudo ufw allow 8001
```

**4. 允许外部访问**
```python
# 在complete_project_system.py中
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "complete_project_system:app",
        host="0.0.0.0",  # 允许外部访问
        port=8001
    )
```

---

### 问题18: 图表不显示

**症状:**
- 页面加载但图表区域为空白
- 显示"Failed to load chart data"

**解决方案:**

**1. 检查API数据**
```bash
curl http://localhost:8001/api/health
curl http://localhost:8001/api/strategies
```

**2. 查看JavaScript错误**
在浏览器控制台中:
```javascript
// 查看错误
console.error

// 测试数据获取
fetch('http://localhost:8001/api/strategies')
  .then(r => r.json())
  .then(d => console.log(d))
```

**3. 修复CORS问题**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发时使用*，生产时指定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**4. 检查数据格式**
```python
@app.get("/api/strategies")
async def get_strategies():
    try:
        data = get_strategies_data()
        # 确保返回的是可JSON序列化的
        return data
    except Exception as e:
        # 返回错误信息
        return {"error": str(e)}
```

---

## 🔧 环境配置问题

### 问题19: 配置文件未加载

**症状:**
```
KeyError: 'TELEGRAM_BOT_TOKEN'
```

**解决方案:**

**1. 检查.env文件**
```bash
# 确保文件存在
ls -la .env

# 查看内容
cat .env
```

**2. 验证格式**
```env
# ✅ 正确格式
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
API_PORT=8001

# ❌ 错误格式 (有空格、换行等)
TELEGRAM_BOT_TOKEN =
123456789:ABC...
```

**3. 加载环境变量**
```python
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv()

# 检查是否加载成功
print(f"TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')}")
print(f"API_PORT: {os.getenv('API_PORT')}")

# 如果为空，尝试绝对路径
load_dotenv('/path/to/your/project/.env')
```

**4. 重新加载**
```python
# 如果修改了.env文件，需要重新加载
from dotenv import load_dotenv
load_dotenv(override=True)  # override=True覆盖已加载的值
```

---

### 问题20: Python路径错误

**症状:**
```
ModuleNotFoundError: No module named 'enhanced_strategy_backtest'
```

**解决方案:**

**1. 检查当前目录**
```python
import os
print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path[0]}")
```

**2. 添加路径**
```python
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 验证路径
print(f"Python路径: {sys.path[:3]}")
```

**3. 使用绝对导入**
```python
# 代替相对导入
# from .enhanced_strategy_backtest import EnhancedStrategyBacktest  # 错误
from enhanced_strategy_backtest import EnhancedStrategyBacktest  # 正确
```

**4. 检查模块文件**
```bash
# 确认文件存在
ls -la enhanced_strategy_backtest.py

# 检查文件权限
chmod +x enhanced_strategy_backtest.py
```

---

## 📝 日志分析

### 理解日志级别

**日志文件位置:**
- `quant_system.log` - 主要日志
- `logs/` - 历史日志
- `access.log` - Web访问日志
- `error.log` - 错误日志

**日志级别:**

```python
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

logger.debug("调试信息")    # 详细调试
logger.info("信息")         # 一般信息
logger.warning("警告")      # 警告
logger.error("错误")        # 错误
logger.critical("严重错误")  # 严重错误
```

---

### 分析错误日志

**1. 搜索错误**
```bash
# 查看最新100行
tail -n 100 quant_system.log

# 搜索错误
grep -i "error" quant_system.log

# 搜索特定错误类型
grep "ConnectionError" quant_system.log
grep "ImportError" quant_system.log
grep "KeyError" quant_system.log
```

**2. 过滤时间范围**
```bash
# 查看特定时间
grep "2023-11-09 14:" quant_system.log

# 实时监控
tail -f quant_system.log | grep "ERROR"
```

**3. 统计错误**
```bash
# 统计错误数量
grep -c "ERROR" quant_system.log

# 按类型统计
grep "ERROR" quant_system.log | cut -d' ' -f5- | sort | uniq -c | sort -nr
```

---

### 日志分析工具

创建日志分析脚本:

```python
#!/usr/bin/env python3
import re
from collections import Counter, defaultdict
from datetime import datetime

def analyze_log(log_file):
    """分析日志文件"""

    errors = []
    warnings = []
    error_patterns = defaultdict(int)
    time_distribution = defaultdict(int)

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 提取时间
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
            if time_match:
                time_str = time_match.group(1)
                time_distribution[time_str[:13]] += 1  # 按小时统计

            # 分类日志
            if 'ERROR' in line:
                errors.append(line)
                # 提取错误类型
                error_type = re.search(r'(\w+Error)', line)
                if error_type:
                    error_patterns[error_type.group(1)] += 1

            elif 'WARNING' in line:
                warnings.append(line)

    # 生成报告
    print("=" * 60)
    print("日志分析报告")
    print("=" * 60)

    print(f"\n错误统计:")
    print(f"  总错误数: {len(errors)}")
    print(f"  总警告数: {len(warnings)}")

    print(f"\n错误类型Top 10:")
    for error_type, count in error_patterns.most_common(10):
        print(f"  {error_type}: {count}次")

    print(f"\n最近10个错误:")
    for error in errors[-10:]:
        print(error.strip())

    print(f"\n错误时间分布 (Top 5):")
    for time, count in sorted(time_distribution.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {time}:00 - {count}个日志")

    return errors, error_patterns

if __name__ == "__main__":
    errors, patterns = analyze_log('quant_system.log')
```

---

## 🚨 紧急处理

### 系统完全无法启动

**步骤1: 重启系统**
```bash
# Windows
shutdown /r /t 0

# Linux/macOS
sudo reboot
```

**步骤2: 清理并重装**
```bash
# 删除虚拟环境
rm -rf .venv310

# 重新创建
python -m venv .venv310
source .venv310/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**步骤3: 使用最小配置启动**
```python
# 创建一个最简启动脚本 minimal_start.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "系统运行正常"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

然后运行:
```bash
python minimal_start.py
```

---

### 数据损坏

**恢复步骤:**

**1. 备份当前数据**
```bash
cp -r data/ data_backup_$(date +%Y%m%d)/
```

**2. 清理缓存**
```bash
rm -rf .cache __pycache__ .pytest_cache
rm -f quant_system.log
```

**3. 重新下载数据**
```python
# 强制刷新数据
from enhanced_strategy_backtest import EnhancedStrategyBacktest

backtest = EnhancedStrategyBacktest("0700.hk", "2020-01-01", "2023-01-01")
backtest.load_data(force_refresh=True)
```

---

### 数据库锁定

**解决SQLite锁定:**
```python
import sqlite3
import os

db_path = 'quant_system.db'

# 检查是否有进程占用
try:
    conn = sqlite3.connect(db_path, timeout=5)
    print("数据库可用")
    conn.close()
except sqlite3.OperationalError:
    print("数据库被锁定")

# 强制删除锁文件
lock_file = db_path + '-wal'
if os.path.exists(lock_file):
    print(f"删除锁文件: {lock_file}")
    os.remove(lock_file)
```

---

## 📞 获取帮助

### 在报告问题前

请准备以下信息:

1. **系统信息**
   ```bash
   python --version
   pip list | grep -E "(pandas|numpy|talib|fastapi)"
   uname -a  # Linux/macOS
   ```

2. **错误日志**
   ```bash
   tail -n 50 quant_system.log
   ```

3. **复现步骤**
   - 具体的操作步骤
   - 使用的命令
   - 预期结果 vs 实际结果

4. **环境配置**
   - Python版本
   - 操作系统
   - 虚拟环境类型

### 联系方式

**GitHub Issues:**
- 网址: https://github.com/your-repo/issues
- 模板: 使用Bug报告模板

**社区论坛:**
- 网址: https://forum.example.com

**邮件支持:**
- 邮箱: support@example.com
- 响应时间: 24-48小时

**紧急支持:**
- 紧急热线: +86-xxx-xxxx (工作时间)
- 紧急邮箱: emergency@example.com

---

### 问题报告模板

```markdown
## 问题描述
简要描述问题

## 复现步骤
1. 运行 `python ...`
2. 点击 `...`
3. 滚动到 `...`
4. 看到错误

## 预期行为
描述预期会发生什么

## 实际行为
描述实际发生了什么

## 屏幕截图
如果适用，添加屏幕截图

## 环境信息
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.10.8]
- 系统版本: [e.g., 1.0.0]

## 日志
```
复制相关日志
```

## 其他信息
添加任何其他关于问题的信息
```

---

## 📚 常用命令速查

```bash
# 查看进程
ps aux | grep python

# 杀死进程
kill -9 <PID>

# 查看端口占用
lsof -i :8001
netstat -tulpn | grep 8001

# 清理缓存
rm -rf __pycache__ .pytest_cache .cache

# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 运行测试
python -m pytest tests/ -v

# 查看日志
tail -f quant_system.log
grep "ERROR" quant_system.log

# 诊断系统
python diagnostic_tool.py
```

---

## ✅ 检查清单

在寻求帮助前，请确认您已经:

- [ ] 运行了 `python diagnostic_tool.py`
- [ ] 查看了FAQ (`docs/faq.md`)
- [ ] 检查了日志文件 (`quant_system.log`)
- [ ] 尝试了本指南中的解决方案
- [ ] 准备了完整的错误信息和环境信息
- [ ] 搜索了已有的GitHub Issues

---

**祝您使用愉快！**

如果本指南没有解决您的问题，请不要犹豫联系我们的支持团队。我们致力于为您提供最好的帮助！
