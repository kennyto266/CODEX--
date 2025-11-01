# 🔧 CODEX Trading Dashboard - 故障排除指南

## 📋 目录

1. [快速诊断](#快速诊断)
2. [安装和部署问题](#安装和部署问题)
3. [运行时错误](#运行时错误)
4. [性能问题](#性能问题)
5. [网络和连接问题](#网络和连接问题)
6. [数据问题](#数据问题)
7. [智能体相关问题](#智能体相关问题)
8. [前端界面问题](#前端界面问题)
9. [后端API问题](#后端api问题)
10. [数据库问题](#数据库问题)
11. [WebSocket问题](#websocket问题)
12. [日志分析](#日志分析)
13. [系统监控](#系统监控)
14. [常用调试工具](#常用调试工具)
15. [FAQ - 常见问题](#faq---常见问题)

---

## 快速诊断

### 系统健康检查

在排查问题之前，首先运行系统健康检查：

```bash
# 检查服务状态
curl -f http://localhost:8001/api/health

# 检查API文档
curl http://localhost:8001/docs

# 检查WebSocket连接
wscat -c ws://localhost:8001/ws

# 检查系统资源
htop
df -h
free -h
```

### 获取日志

```bash
# 查看应用日志
tail -f logs/quant_system.log

# 查看错误日志
tail -f logs/error.log

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 查看Systemd服务日志
sudo journalctl -u codex-dashboard -f
```

### 快速重启

如果遇到临时问题，尝试快速重启：

```bash
# 重启后端服务
sudo systemctl restart codex-dashboard

# 重启前端服务
sudo systemctl restart nginx

# 或直接重启应用
python run_dashboard.py
```

---

## 安装和部署问题

### 问题 1: Python环境设置失败

**错误信息**:
```bash
ERROR: Failed building wheel for ta-lib
```

**原因**: TA-Lib库缺少系统依赖

**解决方案**:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libta-lib-dev
pip install TA-Lib

# CentOS/RHEL
sudo yum install -y ta-lib-devel
pip install TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib

# Windows
# 1. 下载预编译wheel文件
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 2. 安装
pip install TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
```

### 问题 2: Node.js依赖安装失败

**错误信息**:
```bash
npm ERR! peer dep missing
```

**解决方案**:

```bash
# 清除npm缓存
npm cache clean --force

# 删除node_modules和package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install

# 或使用yarn
yarn install
```

### 问题 3: 端口被占用

**错误信息**:
```
OSError: [Errno 10048] Only one usage of each socket address
```

**解决方案**:

```bash
# 查找占用端口的进程
sudo lsof -i :8001

# 终止进程
sudo kill -9 <PID>

# 或使用不同端口
python run_dashboard.py --port 8002
```

### 问题 4: 权限错误

**错误信息**:
```bash
PermissionError: [Errno 13] Permission denied
```

**解决方案**:

```bash
# 检查文件权限
ls -la /path/to/codex-trading-system

# 修复权限
sudo chown -R $USER:$USER /path/to/codex-trading-system
chmod -R 755 /path/to/codex-trading-system
chmod -R 644 /path/to/codex-trading-system/src/dashboard/static/js/components/*.js

# 检查SELinux (CentOS/RHEL)
getenforce
# 如果是Enforcing
sudo setenforce 0
```

### 问题 5: 数据库连接失败

**错误信息**:
```bash
psycopg2.OperationalError: could not connect to server
```

**解决方案**:

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 启动PostgreSQL
sudo systemctl start postgresql

# 检查配置
sudo -u postgres psql -c "SELECT version();"

# 检查连接配置
grep DATABASE_URL .env
```

---

## 运行时错误

### 问题 1: FastAPI启动失败

**错误信息**:
```python
AttributeError: module 'fastapi' has no attribute 'FastAPI'
```

**解决方案**:

```bash
# 检查FastAPI版本
pip show fastapi

# 升级到最新版本
pip install --upgrade fastapi

# 如果使用conda
conda install -c conda-forge fastapi
```

### 问题 2: Vue组件加载失败

**错误信息**:
```
Failed to load component: AgentPanel.js
```

**解决方案**:

```bash
# 检查文件是否存在
ls -la src/dashboard/static/js/components/AgentPanel.js

# 检查文件权限
chmod 644 src/dashboard/static/js/components/*.js

# 检查文件内容
head -20 src/dashboard/static/js/components/AgentPanel.js

# 清理浏览器缓存
# Ctrl+Shift+R (强制刷新)
```

### 问题 3: Pinia Store错误

**错误信息**:
```javascript
Uncaught ReferenceError: useAgentStore is not defined
```

**解决方案**:

```javascript
// 确保正确导入
import { useAgentStore } from './stores/agents.js';

// 检查stores目录
ls -la src/dashboard/static/js/stores/

// 验证store定义
// stores/agents.js
const useAgentStore = defineStore('agents', {
    // ...
});
```

### 问题 4: WebSocket连接失败

**错误信息**:
```
WebSocket connection to 'ws://localhost:8001/ws' failed
```

**解决方案**:

```bash
# 检查WebSocket端点
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8001/ws

# 检查Nginx配置
sudo nginx -t
sudo systemctl reload nginx
```

### 问题 5: TA-Lib导入错误

**错误信息**:
```python
ImportError: No module named 'talib'
```

**解决方案**:

```python
# 验证安装
python -c "import talib; print(talib.__version__)"

# 重新安装
pip uninstall talib
pip install TA-Lib

# 如果仍失败，使用conda
conda install -c conda-forge ta-lib
```

---

## 性能问题

### 问题 1: 系统响应缓慢

**症状**: 页面加载慢，API调用超时

**诊断**:

```bash
# 检查CPU使用率
htop

# 检查内存使用
free -h

# 检查磁盘I/O
iostat -x 1

# 检查网络
netstat -i
```

**解决方案**:

```bash
# 增加系统资源
# 或优化代码

# 检查慢查询
python -m cProfile -s cumulative your_script.py

# 使用性能分析
pip install py-spy
py-spy top --pid <PID>
```

### 问题 2: 内存泄漏

**症状**: 系统运行一段时间后变慢或崩溃

**诊断**:

```python
# 检查内存使用
import tracemalloc
tracemalloc.start()

# 运行代码
your_function()

# 显示内存使用
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
```

**解决方案**:

```python
# 确保释放资源
# 使用context managers
with open('file.txt') as f:
    data = f.read()

# 清理缓存
APICache.clear()

# 重启服务
sudo systemctl restart codex-dashboard
```

### 问题 3: 数据库性能慢

**症状**: 查询响应时间长

**诊断**:

```sql
-- 启用慢查询日志
SHOW VARIABLES LIKE 'slow_query_log';

-- 查看当前查询
SHOW PROCESSLIST;

-- 分析查询计划
EXPLAIN SELECT * FROM agents WHERE status = 'running';
```

**解决方案**:

```sql
-- 添加索引
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);

-- 优化查询
-- 使用LIMIT分页
SELECT * FROM agents ORDER BY id LIMIT 50 OFFSET 0;

-- 使用索引覆盖
SELECT id, name, status FROM agents WHERE status = 'running';
```

### 问题 4: 前端打包过大

**症状**: 首页加载时间长

**诊断**:

```bash
# 检查bundle大小
npm run build
ls -lh dist/

# 分析bundle
npx vite-bundle-analyzer dist/
```

**解决方案**:

```javascript
// vite.config.js
export default defineConfig({
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    'vue-vendor': ['vue', 'vue-router', 'pinia'],
                    'components': [
                        './js/components/AgentPanel.js',
                        './js/components/RiskPanel.js'
                    ]
                }
            }
        },
        minify: 'terser',
        terserOptions: {
            compress: {
                drop_console: true,
                drop_debugger: true
            }
        }
    }
});
```

---

## 网络和连接问题

### 问题 1: API调用失败

**错误信息**:
```bash
curl: (7) Failed to connect to localhost port 8001
```

**诊断**:

```bash
# 检查服务是否运行
netstat -tulpn | grep :8001

# 检查防火墙
sudo ufw status
sudo iptables -L

# 测试本地连接
telnet localhost 8001
```

**解决方案**:

```bash
# 启动服务
python run_dashboard.py

# 开放端口
sudo ufw allow 8001

# 或绑定到0.0.0.0
uvicorn src.dashboard.main:app --host 0.0.0.0 --port 8001
```

### 问题 2: 跨域问题

**错误信息**:
```javascript
Access to fetch at 'http://localhost:8001/api/agents' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**解决方案**:

```python
# 在main.py中启用CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题 3: HTTPS证书错误

**错误信息**:
```bash
SSL certificate error
```

**解决方案**:

```bash
# 使用Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 或禁用SSL检查 (仅开发环境)
curl -k https://localhost:8001/api/health

# 在生产环境，使用有效证书
```

### 问题 4: WebSocket连接不稳定

**症状**: 连接频繁断开

**解决方案**:

```nginx
# Nginx配置
location /ws {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}
```

---

## 数据问题

### 问题 1: 数据源连接失败

**错误信息**:
```
requests.exceptions.ConnectionError
```

**解决方案**:

```python
# 检查数据源URL
print(os.getenv('DATA_SOURCE_URL'))

# 测试连接
import requests
response = requests.get('http://18.180.162.113:9191/inst/getInst', params={
    'symbol': '0700.hk',
    'duration': 365
})
print(response.status_code)
```

### 问题 2: 数据格式错误

**错误信息**:
```python
KeyError: 'data' in response
```

**解决方案**:

```python
# 添加数据验证
import pandas as pd

def validate_data(data):
    required_fields = ['open', 'high', 'low', 'close', 'volume']
    if not all(field in data for field in required_fields):
        raise ValueError(f"Missing required fields: {required_fields}")
    return True

# 使用验证
try:
    validate_data(response.json())
except ValueError as e:
    print(f"Data validation error: {e}")
```

### 问题 3: 历史数据缺失

**症状**: 部分日期数据为空

**解决方案**:

```python
# 检查数据完整性
def check_data_gaps(df):
    dates = pd.date_range(start=df.index.min(), end=df.index.max())
    missing_dates = dates.difference(df.index)
    if len(missing_dates) > 0:
        print(f"Missing dates: {missing_dates}")
    return len(missing_dates) == 0

# 处理缺失数据
df = df.fillna(method='ffill')  # 前向填充
```

### 问题 4: 回测数据不一致

**症状**: 回测结果与实际交易不符

**解决方案**:

```python
# 检查数据来源
print(f"Data source: {data_source}")
print(f"Data period: {start_date} to {end_date}")

# 检查数据质量
assert not df.isnull().any().any(), "Data contains null values"
assert df.index.is_monotonic_increasing, "Data not sorted"

# 使用相同的交易规则
def calculate_returns(price_series):
    return price_series.pct_change().dropna()
```

---

## 智能体相关问题

### 问题 1: 智能体无法启动

**错误信息**:
```
Agent startup failed: Connection refused
```

**诊断**:

```bash
# 检查智能体进程
ps aux | grep agent

# 查看智能体日志
tail -f logs/agents/coordinator.log

# 检查消息队列
redis-cli ping
```

**解决方案**:

```bash
# 重启智能体服务
sudo systemctl restart codex-agents

# 清理进程
pkill -f "agent.*python"

# 重新启动
python -m src.agents.coordinator
```

### 问题 2: 智能体通信失败

**症状**: 智能体之间无法传递消息

**解决方案**:

```python
# 检查消息队列
from src.agents.message_queue import MessageQueue

mq = MessageQueue()
await mq.initialize()

# 测试消息发送
await mq.send_message(
    sender_id=1,
    receiver_id=2,
    message_type="TASK",
    content={"task": "analyze_data"}
)
```

### 问题 3: 智能体CPU使用率过高

**诊断**:

```bash
# 查看CPU使用率
top -p $(pgrep -f "agent.*python")

# 检查循环
# 查看代码是否有无限循环
```

**解决方案**:

```python
# 添加限制
import time

def process_tasks():
    for task in task_queue:
        start_time = time.time()
        process_task(task)
        # 防止占用过多CPU
        elapsed = time.time() - start_time
        if elapsed > 1.0:
            time.sleep(0.1)
```

### 问题 4: 智能体内存泄漏

**诊断**:

```python
# 使用memory_profiler
from memory_profiler import profile

@profile
def agent_main_loop():
    while True:
        process_messages()
        time.sleep(0.1)

# 运行
python -m memory_profiler agent.py
```

**解决方案**:

```python
# 定期清理
import gc

def cleanup():
    gc.collect()
    # 清理旧消息
    message_queue.cleanup(max_age=3600)

# 每小时清理一次
schedule.every().hour.do(cleanup)
```

---

## 前端界面问题

### 问题 1: 页面空白或白屏

**症状**: 打开页面后显示空白

**诊断**:

```javascript
// 检查控制台错误
console.error('JavaScript Error:', error);

// 检查网络请求
// 开发者工具 -> Network -> 查看失败请求
```

**解决方案**:

```javascript
// 1. 检查HTML容器
<div id="app"></div>

// 2. 检查Vue挂载
const app = createApp(AppComponent);
app.mount('#app');

// 3. 检查CSS加载
<link rel="stylesheet" href="/static/css/main.css">
```

### 问题 2: 组件样式错乱

**症状**: 元素位置混乱，样式不正确

**解决方案**:

```html
<!-- 确保Tailwind CSS正确加载 -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- 或检查自定义CSS -->
<style>
.container {
    max-width: 1200px;
    margin: 0 auto;
}
</style>
```

### 问题 3: 数据不更新

**症状**: 页面数据不刷新

**解决方案**:

```javascript
// 使用Vue响应式
import { ref, onMounted } from 'vue';

setup() {
    const agents = ref([]);

    const fetchAgents = async () => {
        agents.value = await api.get('/api/agents/list');
    };

    onMounted(() => {
        fetchAgents();
        // 定期刷新
        setInterval(fetchAgents, 30000);
    });

    return { agents, fetchAgents };
}
```

### 问题 4: 图表不显示

**症状**: Chart组件渲染空白

**解决方案**:

```javascript
// 确保容器有高度
<div style="height: 400px;">
    <canvas id="myChart"></canvas>
</div>

// 使用Chart.js
import Chart from 'chart.js/auto';

const ctx = document.getElementById('myChart');
new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: chartOptions
});
```

### 问题 5: 搜索功能不工作

**症状**: 输入搜索后无响应

**解决方案**:

```javascript
// 使用防抖
import { debounce } from 'lodash';

const search = debounce((query) => {
    fetchResults(query);
}, 300);

<input @input="search($event.target.value)" />

// 或直接实现
const search = (() => {
    let timeoutId;
    return (query) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            fetchResults(query);
        }, 300);
    };
})();
```

---

## 后端API问题

### 问题 1: API返回500错误

**诊断**:

```python
# 查看详细错误
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__}
    )
```

**解决方案**:

```python
# 添加错误处理
@router.get("/agents")
async def get_agents():
    try:
        agents = await agent_service.get_agents()
        return agents
    except Exception as e:
        logger.error(f"Error getting agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### 问题 2: API返回404错误

**解决方案**:

```bash
# 检查路由
curl -X GET http://localhost:8001/docs

# 查看注册的路由
# 在main.py中
for route in app.routes:
    print(route.path)
```

### 问题 3: 参数验证失败

**错误信息**:
```python
ValidationError: 1 validation error for Item
name
  field required (type=value_error.missing)
```

**解决方案**:

```python
# 使用Pydantic模型
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)

@router.post("/items")
async def create_item(item: Item):
    return item
```

### 问题 4: 并发请求处理

**症状**: 高并发时响应慢或错误

**解决方案**:

```python
# 使用异步
@router.get("/data")
async def get_data():
    # 异步操作
    data = await fetch_from_database()
    return data

# 使用连接池
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30
)
```

### 问题 5: 内存使用过高

**诊断**:

```python
# 检查内存使用
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**解决方案**:

```python
# 使用流式处理
@router.get("/large-data")
async def get_large_data():
    async def generate():
        for i in range(100000):
            yield {"id": i, "data": "..."}

    return StreamingResponse(generate())
```

---

## 数据库问题

### 问题 1: 连接超时

**错误信息**:
```sql
OperationalError: could not receive server response
```

**解决方案**:

```python
# 调整超时时间
engine = create_async_engine(
    DATABASE_URL,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### 问题 2: 死锁

**症状**: 操作长时间无响应

**解决方案**:

```sql
-- 查看锁
SELECT * FROM pg_locks;

-- 终止进程
SELECT pg_terminate_backend(pid);
```

### 问题 3: 数据不一致

**症状**: 查询结果不正确

**解决方案**:

```python
# 使用事务
async with database.transaction():
    await database.execute("INSERT INTO ...")
    await database.execute("UPDATE ...")

# 检查约束
# 添加外键约束
ALTER TABLE orders ADD CONSTRAINT fk_orders_agent
FOREIGN KEY (agent_id) REFERENCES agents(id);
```

### 问题 4: 备份失败

**解决方案**:

```bash
# 备份数据库
pg_dump -U username -h localhost -d codex_db > backup.sql

# 恢复数据库
psql -U username -h localhost -d codex_db < backup.sql
```

---

## WebSocket问题

### 问题 1: WebSocket握手失败

**错误信息**:
```
WebSocket handshake error: Unexpected response code: 404
```

**解决方案**:

```python
# 确保WebSocket路由存在
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
```

### 问题 2: 消息丢失

**症状**: 客户端未收到部分消息

**解决方案**:

```python
# 使用消息队列
import asyncio
import json

message_queue = asyncio.Queue()

async def broadcast_message(message):
    # 存储消息
    await message_queue.put(message)

    # 发送给所有连接
    for connection in connections:
        try:
            await connection.send_json(message)
        except:
            # 处理断开连接
            connections.remove(connection)
```

### 问题 3: 连接数限制

**症状**: 超过最大连接数后无法连接

**解决方案**:

```python
# 限制连接数
MAX_CONNECTIONS = 100

connections = set()

async def websocket_endpoint(websocket: WebSocket):
    if len(connections) >= MAX_CONNECTIONS:
        await websocket.close(code=1008, reason="Max connections reached")
        return

    connections.add(websocket)
    try:
        # 处理消息
    finally:
        connections.remove(websocket)
```

---

## 日志分析

### 查看错误日志

```bash
# 实时查看错误
tail -f logs/error.log | grep ERROR

# 统计错误类型
grep "ERROR" logs/quant_system.log | \
    awk '{print $5}' | sort | uniq -c | sort -rn

# 查看最近1小时的错误
grep "$(date '+%Y-%m-%d %H'):" logs/quant_system.log | grep ERROR
```

### 分析慢操作

```bash
# 查找慢查询
grep "slow" logs/quant_system.log

# 统计耗时操作
awk '/completed in/ {print $NF}' logs/quant_system.log | sort -n
```

### 生成日志报告

```python
# log_analyzer.py
import re
from collections import Counter

def analyze_logs(log_file):
    with open(log_file) as f:
        logs = f.read()

    # 统计错误
    errors = re.findall(r'ERROR: (.+)', logs)
    error_counts = Counter(errors)

    print("Top errors:")
    for error, count in error_counts.most_common(10):
        print(f"{count}x: {error}")

    # 统计耗时
    times = re.findall(r'completed in ([\d.]+)ms', logs)
    times = [float(t) for t in times]
    print(f"\nAverage time: {sum(times)/len(times):.2f}ms")
    print(f"Max time: {max(times):.2f}ms")

analyze_logs('logs/quant_system.log')
```

---

## 系统监控

### 监控脚本

```bash
# monitor.sh
#!/bin/bash

# 检查服务状态
if ! curl -f http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "Service is down, restarting..."
    sudo systemctl restart codex-dashboard
fi

# 检查磁盘空间
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "Disk usage is ${DISK_USAGE}%, cleaning up..."
    # 清理日志
    find logs/ -name "*.log" -mtime +7 -delete
fi

# 检查内存使用
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "Memory usage is ${MEMORY_USAGE}%"
fi

# 检查进程数
PROCESS_COUNT=$(ps aux | grep -c "[p]ython.*dashboard")
echo "Dashboard processes: $PROCESS_COUNT"
```

### Prometheus监控

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
AGENT_COUNT = Gauge('agents_total', 'Total number of agents')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percent')

# 使用指标
@router.get("/agents")
async def get_agents():
    REQUEST_COUNT.inc()
    start_time = time.time()

    agents = await agent_service.get_agents()

    REQUEST_LATENCY.observe(time.time() - start_time)
    AGENT_COUNT.set(len(agents))
    CPU_USAGE.set(psutil.cpu_percent())

    return agents
```

---

## 常用调试工具

### Python调试

```python
# 使用pdb
import pdb; pdb.set_trace()

# 使用ipdb (推荐)
pip install ipdb
import ipdb; ipdb.set_trace()

# 使用rich
from rich.console import Console
console = Console()
console.print("[bold red]Error![/bold red]", log_locals=True)

# 使用loguru
from loguru import logger
logger.add("logs/debug.log", level="DEBUG")
logger.error("Error occurred")
```

### JavaScript调试

```javascript
// 使用console
console.log('Debug info:', data);
console.error('Error:', error);
console.table(array);

// 使用断点
debugger;

// 性能测试
console.time('Operation');
// 操作
console.timeEnd('Operation');

// 内存检查
console.memory; // Chrome DevTools

// Vue调试
this.$nextTick(() => {
    console.log('Updated:', this.data);
});
```

### 数据库调试

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看当前查询
SHOW PROCESSLIST;

-- 分析查询
EXPLAIN SELECT * FROM agents WHERE status = 'running';

-- 查看表大小
SELECT
    table_name,
    round(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'codex_db';
```

### 网络调试

```bash
# 使用curl
curl -v http://localhost:8001/api/health
curl -X POST http://localhost:8001/api/agents/1/start

# 使用wireshark
sudo wireshark -i lo

# 使用netstat
netstat -tulpn | grep :8001
ss -tulpn | grep :8001

# 使用tcpdump
sudo tcpdump -i lo port 8001
```

---

## FAQ - 常见问题

### Q1: 如何查看系统版本？

```bash
# Python版本
python --version

# Node.js版本
node --version

# 系统版本
cat /etc/os-release
uname -a
```

### Q2: 如何重置数据库？

```bash
# 删除数据库文件
rm -f data/codex.db

# 重新初始化
python init_db.py

# 或使用迁移
alembic downgrade base
alembic upgrade head
```

### Q3: 如何更新系统？

```bash
# 拉取最新代码
git pull upstream main

# 更新依赖
pip install -r requirements.txt --upgrade
cd src/dashboard/static
npm install --upgrade

# 运行迁移
alembic upgrade head

# 重启服务
sudo systemctl restart codex-dashboard
```

### Q4: 如何备份配置？

```bash
# 备份.env文件
cp .env .env.backup.$(date +%Y%m%d)

# 备份数据库
pg_dump -U username codex_db > backup_$(date +%Y%m%d).sql

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### Q5: 如何查看API文档？

```bash
# 访问Swagger UI
# 浏览器打开: http://localhost:8001/docs

# 访问ReDoc
# 浏览器打开: http://localhost:8001/redoc

# 导出OpenAPI规范
curl http://localhost:8001/openapi.json > openapi.json
```

### Q6: 如何清理缓存？

```bash
# 清理Python缓存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清理npm缓存
npm cache clean --force

# 清理浏览器缓存
# Ctrl+Shift+Delete

# 清理APICache (应用内)
APICache.clear()
```

### Q7: 如何查看WebSocket消息？

```bash
# 使用wscat
npm install -g wscat
wscat -c ws://localhost:8001/ws

# 或编写测试脚本
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8001/ws');

ws.on('open', () => {
    ws.send(JSON.stringify({
        action: 'subscribe',
        channel: 'agents'
    }));
});

ws.on('message', (data) => {
    console.log('Received:', data);
});
```

### Q8: 如何优化数据库查询？

```sql
-- 1. 添加索引
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);

-- 2. 使用EXPLAIN分析
EXPLAIN ANALYZE SELECT * FROM agents WHERE status = 'running';

-- 3. 优化查询
-- 避免SELECT *
SELECT id, name FROM agents WHERE status = 'running';

-- 使用LIMIT
SELECT * FROM agents LIMIT 50;

-- 4. 分区表 (大数据量)
CREATE TABLE trades_2025 PARTITION OF trades
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### Q9: 如何监控系统性能？

```bash
# 安装htop
sudo apt-get install htop

# 使用htop
htop

# 监控特定进程
top -p $(pgrep -f "dashboard")

# 监控I/O
iotop

# 监控网络
iftop
```

### Q10: 如何报告问题？

创建GitHub Issue时，请包含：

```markdown
**问题描述**
简要描述问题

**复现步骤**
1. 执行 ...
2. 点击 ...
3. 滚动到 ...
4. 看到错误

**预期行为**
描述预期会发生什么

**实际行为**
描述实际发生了什么

**截图**
如果适用，请添加截图

**环境信息**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.10.12]
- Node.js: [e.g. 18.17.0]
- 浏览器: [e.g. Chrome 118]

**日志**
请粘贴相关日志
```

---

## 联系我们

如果以上方法都无法解决问题，请联系技术支持：

- 📧 **邮箱**: support@codex-trading.com
- 📱 **电话**: 400-888-0000
- 💬 **在线客服**: 工作日 9:00-18:00
- 🐛 **Bug报告**: [GitHub Issues](https://github.com/your-org/codex-trading-system/issues)
- 📖 **文档**: [官方文档](https://docs.codex-trading.com)

---

**感谢您使用CODEX Trading Dashboard！**

---

*最后更新: 2025-10-27*
*版本: v1.0.0*
