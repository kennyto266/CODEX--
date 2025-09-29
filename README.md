# AI Agent 量化交易系统 - 多智能体协作平台

一个基于多智能体协作的量化交易系统，集成了数据适配器、回测引擎、实时监控和Telegram机器人等功能模块。

## 系统架构

### 核心组件

1. **多智能体系统** - 7个专业AI Agent协作处理量化交易
2. **数据适配器** - 支持多种数据源（HTTP API、原始数据等）
3. **回测引擎** - 集成Sharpe比率和最大回撤计算
4. **实时监控** - WebSocket实时数据推送和性能监控
5. **Telegram集成** - 通过机器人接收交易信号和系统状态
6. **Web仪表板** - 可视化界面展示系统状态和交易决策

### 核心特性

- **模块化设计**: 可插拔的组件架构
- **实时通信**: WebSocket + HTTP API双重通信机制
- **风险管理**: 集成Sharpe比率和最大回撤计算
- **多数据源**: 支持HTTP API和原始数据适配器
- **用户友好**: 提供Web界面和Telegram机器人交互

## 📋 系统要求

### 最低要求
- **Python**: 3.8+ (推荐 3.10 或 3.11)
- **内存**: 至少 2GB RAM
- **磁盘空间**: 至少 1GB 可用空间
- **网络**: 稳定的互联网连接 (用于获取股票数据)

### 支持的操作系统
- ✅ **Windows** 10/11 (主要优化平台)
- ✅ **Linux** (Ubuntu 18.04+, CentOS 7+)
- ✅ **macOS** 10.15+

### 推荐配置
- **Python**: 3.10 或 3.11
- **内存**: 4GB+ RAM
- **CPU**: 多核处理器 (用于并行计算)

## 🚀 快速开始 (5分钟部署)

### 方法一：一键启动 (推荐新手)

```bash
# 1. 克隆项目
git clone <repository-url>
cd CODEX-寫量化團隊

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动系统
python complete_project_system.py

# 4. 访问系统
# 浏览器打开: http://localhost:8001
```

### 方法二：使用部署脚本

```bash
# 运行自动部署脚本
python deploy.py

# 系统会自动安装依赖并启动
# 访问: http://localhost:8001
```

### 方法三：安全增强版 (推荐生产环境)

```bash
# 启动安全增强版本
python secure_complete_system.py

# 访问: http://localhost:8001
```

## 📦 详细安装指南

### 第一步：环境准备

#### 1.1 检查Python版本
```bash
python --version
# 或
python3 --version

# 需要 Python 3.8 或更高版本
```

#### 1.2 创建虚拟环境 (强烈推荐)

**Windows:**
```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 验证激活
where python
```

**Linux/macOS:**
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证激活
which python
```

### 第二步：安装依赖

#### 2.1 更新pip (推荐)
```bash
python -m pip install --upgrade pip
```

#### 2.2 安装基础依赖
```bash
pip install -r requirements.txt
```

#### 2.3 安装Telegram机器人依赖 (可选)
```bash
pip install -r telegram_requirements.txt
```

#### 2.4 安装测试依赖 (开发者)
```bash
pip install -r test_requirements.txt
```

#### 2.5 国内用户加速安装
```bash
# 使用清华大学镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 第三步：配置系统

#### 3.1 Telegram机器人配置 (可选)
```bash
# 复制配置模板
cp telegram_bot.env.example .env

# 编辑配置文件
# Windows: notepad .env
# Linux/macOS: nano .env
```

**配置内容示例:**
```env
# Telegram Bot配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# 量化交易系统配置
STOCK_API_URL=http://18.180.162.113:9191/inst/getInst
STOCK_API_TIMEOUT=10

# 权限控制 (可选)
TG_ALLOWED_USER_IDS=123456789,987654321
TG_ALLOWED_CHAT_IDS=-1001234567890
```

#### 3.2 获取Telegram Bot Token
1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示创建机器人
4. 复制获得的Token到配置文件

### 第四步：启动系统

#### 4.1 选择启动方式

**完整系统 (推荐):**
```bash
python complete_project_system.py
```

**安全增强版:**
```bash
python secure_complete_system.py
```

**简单版本:**
```bash
python simple_dashboard.py
```

**系统运行脚本:**
```bash
python run_system.py
```

#### 4.2 验证启动成功
```bash
# 检查系统健康状态
curl http://localhost:8001/api/health

# 或在浏览器访问
# http://localhost:8001
```

### 第五步：使用系统

#### 5.1 主要功能入口
- **主界面**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/api/health
- **系统监控**: http://localhost:8001/api/monitoring

#### 5.2 功能使用
1. **股票分析**: 输入股票代码 (如: 0700.HK)
2. **技术指标**: 查看SMA, EMA, RSI, MACD等
3. **策略回测**: 查看回测结果和交易记录
4. **风险评估**: 查看风险等级和投资建议

## 🤖 Telegram机器人设置

### 启动Telegram机器人
```bash
# 确保已配置 .env 文件
python telegram_quant_bot.py

# 或使用启动脚本
python start_telegram_bot.py
```

### 机器人命令
- `/start` - 开始使用机器人
- `/help` - 查看帮助信息
- `/status` - 查看系统状态
- `/analyze <股票代码>` - 分析股票

## 🧪 运行测试

### 基础测试
```bash
# 运行所有测试
python run_tests.py

# 运行特定测试
pytest test_core_functions.py -v
pytest test_api_endpoints.py -v
```

### 测试覆盖率
```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html
# 查看报告: htmlcov/index.html
```

## 🔧 开发环境设置

### 代码格式化
```bash
# 安装开发工具
pip install black flake8 isort pre-commit

# 设置pre-commit钩子
pre-commit install

# 格式化代码
black .
isort .
```

### IDE配置推荐
- **VS Code**: 安装Python、Pylance插件
- **PyCharm**: 配置虚拟环境解释器
- **Cursor**: AI辅助开发

## 项目结构

```
CODEX-寫量化團隊/
├── src/
│   ├── agents/         # AI Agent实现
│   ├── backtest/       # 回测引擎
│   ├── core/           # 核心模块
│   ├── dashboard/      # Web仪表板
│   ├── data_adapters/  # 数据适配器
│   ├── integration/    # 系统集成
│   ├── monitoring/     # 监控模块
│   ├── strategy_management/ # 策略管理
│   ├── telegram/       # Telegram机器人
│   └── utils/          # 工具函数
├── scripts/            # 启动脚本
├── tests/              # 测试文件
├── docs/               # 文档
├── config/             # 配置文件
├── examples/           # 示例代码
└── requirements.txt    # 依赖包
```

## ⚠️ 常见问题与故障排除

### 安装问题

#### 问题1：Python版本不兼容
```bash
# 错误信息: "Python version not supported"
# 解决方案: 安装Python 3.8+
python --version
# 如果版本过低，请安装新版本Python
```

#### 问题2：pip安装失败
```bash
# 错误信息: "pip install failed"
# 解决方案:
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# 国内用户使用镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 问题3：虚拟环境激活失败
```bash
# Windows PowerShell执行策略问题
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Linux权限问题
chmod +x venv/bin/activate
source venv/bin/activate
```

### 启动问题

#### 问题1：端口被占用
```bash
# 错误信息: "Port 8001 is already in use"
# 查看端口占用
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux/macOS

# 终止占用进程
taskkill /PID <进程ID> /F      # Windows
kill -9 <进程ID>               # Linux/macOS

# 或使用其他端口启动
python complete_project_system.py --port 8002
```

#### 问题2：模块导入错误
```bash
# 错误信息: "ModuleNotFoundError"
# 解决方案:
pip install -r requirements.txt
# 确保虚拟环境已激活
# 检查Python路径是否正确
```

#### 问题3：API连接失败
```bash
# 错误信息: "Connection refused" 或 "Timeout"
# 检查网络连接
ping 18.180.162.113

# 检查防火墙设置
# 确保允许Python程序访问网络
```

### 运行时问题

#### 问题1：数据获取失败
```bash
# 检查API状态
curl http://18.180.162.113:9191/inst/getInst

# 查看系统日志
tail -f quant_system.log
```

#### 问题2：内存不足
```bash
# 监控内存使用
# Windows: 任务管理器
# Linux: htop 或 top
# 解决: 增加系统内存或优化代码
```

#### 问题3：Telegram机器人无响应
```bash
# 检查Token配置
echo $TELEGRAM_BOT_TOKEN

# 测试机器人连接
python -c "
import requests
token = 'YOUR_TOKEN'
print(requests.get(f'https://api.telegram.org/bot{token}/getMe').json())
"
```

### 性能问题

#### 问题1：响应速度慢
- 检查网络连接质量
- 优化数据库查询
- 启用缓存机制
- 使用更快的服务器

#### 问题2：CPU使用率高
- 检查是否有无限循环
- 优化算法复杂度
- 使用多进程或多线程

### 开发问题

#### 问题1：代码格式化失败
```bash
# 安装格式化工具
pip install black flake8 isort

# 手动格式化
black .
isort .
flake8 .
```

#### 问题2：测试失败
```bash
# 运行详细测试
pytest -v --tb=long

# 生成测试报告
pytest --html=report.html
```

### 获取帮助

如果以上解决方案都无法解决问题，请：

1. **查看日志文件**:
   - `quant_system.log`
   - `secure_quant_system.log`

2. **检查系统状态**:
   ```bash
   curl http://localhost:8001/api/health
   ```

3. **提交问题报告**:
   - 包含错误信息
   - 包含系统环境
   - 包含复现步骤

## 📊 系统监控与日志

### 日志文件位置
- **主系统日志**: `quant_system.log`
- **安全日志**: `secure_quant_system.log`
- **Telegram机器人日志**: `telegram_bot.log`
- **错误日志**: `error.log`

### 监控端点
- **健康检查**: `GET /api/health`
- **系统状态**: `GET /api/monitoring`
- **性能指标**: `GET /api/metrics`

### 日志级别配置
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🔧 配置说明

系统支持通过环境变量进行配置，主要配置项包括：

### 基础配置
- **API_HOST**: API服务器地址 (默认: localhost)
- **API_PORT**: API服务器端口 (默认: 8001)
- **DEBUG**: 调试模式 (默认: False)

### Telegram配置
- **TELEGRAM_BOT_TOKEN**: 机器人Token
- **TG_ALLOWED_USER_IDS**: 允许的用户ID列表
- **TG_ALLOWED_CHAT_IDS**: 允许的聊天ID列表

### 数据源配置
- **STOCK_API_URL**: 股票数据API地址
- **STOCK_API_TIMEOUT**: API超时时间 (秒)
- **DATA_CACHE_TTL**: 数据缓存时间 (秒)

### 回测配置
- **RISK_FREE_RATE**: 无风险利率 (默认: 0.03)
- **MAX_POSITION_SIZE**: 最大仓位大小
- **INITIAL_CAPITAL**: 初始资金

详细配置请参考 `telegram_bot.env.example` 文件。

## 主要功能

### 1. 多智能体协作
- 7个专业AI Agent协同工作
- 实时消息传递和状态同步
- 智能决策和风险控制

### 2. 数据适配器
- HTTP API数据源适配
- 原始数据文件处理
- 实时数据流处理

### 3. 回测引擎
- Sharpe比率计算
- 最大回撤分析
- 策略性能评估

### 4. Web仪表板
- 实时系统状态监控
- 交易信号可视化
- 性能指标展示

### 5. Telegram集成
- 交易信号推送
- 系统状态通知
- 远程控制命令

## 🚀 生产环境部署

### Docker部署 (推荐)

#### 创建Dockerfile
```dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
COPY telegram_requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r telegram_requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1

# 启动命令
CMD ["python", "secure_complete_system.py"]
```

#### 构建和运行
```bash
# 构建镜像
docker build -t quant-system .

# 运行容器
docker run -d \
  --name quant-system \
  -p 8001:8001 \
  --env-file .env \
  --restart unless-stopped \
  quant-system

# 查看日志
docker logs -f quant-system
```

#### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  quant-system:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DEBUG=false
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - quant-system
    restart: unless-stopped
```

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down
```

### 系统服务部署 (Linux)

#### 创建systemd服务
```bash
# 创建服务文件
sudo nano /etc/systemd/system/quant-system.service
```

```ini
[Unit]
Description=Quantitative Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/quant-system
Environment=PATH=/home/ubuntu/quant-system/venv/bin
ExecStart=/home/ubuntu/quant-system/venv/bin/python secure_complete_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用和启动服务
sudo systemctl daemon-reload
sudo systemctl enable quant-system
sudo systemctl start quant-system

# 查看状态
sudo systemctl status quant-system

# 查看日志
sudo journalctl -u quant-system -f
```

### 反向代理配置 (Nginx)

```nginx
# /etc/nginx/sites-available/quant-system
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📈 性能优化

### 系统性能指标
- **响应时间**: < 2秒 (95%分位)
- **内存使用**: < 500MB (正常负载)
- **并发支持**: > 50用户
- **可用性**: > 99.5%

### 优化建议

#### 1. 缓存优化
```python
# 启用Redis缓存
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379/0"
CACHE_DEFAULT_TIMEOUT = 300
```

#### 2. 数据库优化
```python
# 连接池配置
DATABASE_POOL_SIZE = 10
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
```

#### 3. 异步处理
```python
# 使用异步任务队列
CELERY_BROKER_URL = "redis://localhost:6379/1"
CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
```

#### 4. 监控配置
```python
# Prometheus监控
PROMETHEUS_METRICS = True
METRICS_PORT = 9090
```

### 负载均衡

#### HAProxy配置
```haproxy
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend quant_frontend
    bind *:80
    default_backend quant_backend

backend quant_backend
    balance roundrobin
    server app1 127.0.0.1:8001 check
    server app2 127.0.0.1:8002 check
    server app3 127.0.0.1:8003 check
```

## 🔒 安全配置

### HTTPS配置
```bash
# 使用Let's Encrypt获取SSL证书
sudo certbot --nginx -d your-domain.com
```

### 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 环境变量安全
```bash
# 设置适当的文件权限
chmod 600 .env
chown app:app .env
```

## 📊 监控和日志

### 日志系统
- **日志格式**: JSON结构化日志
- **日志轮转**: 按日期和大小自动轮转
- **日志级别**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 监控工具
- **系统监控**: Prometheus + Grafana
- **应用监控**: 自定义指标收集
- **错误追踪**: Sentry集成
- **日志分析**: ELK Stack (可选)

### 告警配置
```yaml
# Prometheus告警规则
groups:
  - name: quant-system
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
      
      - alert: SystemDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Quant system is down"
```

## 🧪 测试

### 测试类型
- **单元测试**: 测试个别函数和类
- **集成测试**: 测试组件间交互
- **API测试**: 测试REST API端点
- **性能测试**: 测试系统性能
- **端到端测试**: 测试完整用户流程

### 运行测试
```bash
# 运行所有测试
python run_tests.py

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行API测试
pytest test_api_endpoints.py -v

# 运行性能测试
pytest tests/performance/ -v

# 运行特定测试文件
pytest test_core_functions.py::test_specific_function -v
```

### 测试覆盖率
```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html --cov-report=term tests/

# 查看覆盖率报告
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

### 测试配置
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    api: marks tests as API tests
```

## 📚 文档和资源

### 项目文档
- **[执行指南](EXECUTION_GUIDE.md)**: 详细的系统启动和使用指南
- **[项目完成指南](PROJECT_COMPLETION_GUIDE.md)**: 项目开发完成情况
- **[测试覆盖率报告](TEST_COVERAGE_REPORT.md)**: 测试覆盖率详细报告
- **[最终项目总结](FINAL_PROJECT_SUMMARY.md)**: 项目功能和特性总结

### API文档
- **交互式API文档**: http://localhost:8001/docs
- **OpenAPI规范**: http://localhost:8001/openapi.json
- **ReDoc文档**: http://localhost:8001/redoc

### 示例代码
```bash
# 查看示例代码
ls examples/
- basic_usage.py          # 基础使用示例
- advanced_strategies.py  # 高级策略示例
- telegram_bot_usage.py   # Telegram机器人使用
- api_integration.py      # API集成示例
```

## 🤝 贡献指南

### 开发流程
1. **Fork项目**: 在GitHub上Fork本项目
2. **创建分支**: `git checkout -b feature/amazing-feature`
3. **开发功能**: 编写代码和测试
4. **运行测试**: 确保所有测试通过
5. **提交代码**: `git commit -m 'Add amazing feature'`
6. **推送分支**: `git push origin feature/amazing-feature`
7. **创建PR**: 在GitHub上创建Pull Request

### 代码规范
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码格式化
black .
isort .

# 代码检查
flake8 .
mypy src/

# 安全检查
bandit -r src/
```

### 提交规范
```bash
# 提交消息格式
type(scope): description

# 类型:
# feat: 新功能
# fix: 修复bug
# docs: 文档更新
# style: 代码格式
# refactor: 重构
# test: 测试相关
# chore: 构建过程或辅助工具的变动

# 示例:
git commit -m "feat(api): add stock analysis endpoint"
git commit -m "fix(telegram): resolve bot connection issue"
git commit -m "docs(readme): update installation instructions"
```

### 问题报告
提交Issue时请包含：
- **问题描述**: 清晰描述遇到的问题
- **复现步骤**: 详细的复现步骤
- **期望行为**: 期望的正确行为
- **实际行为**: 实际发生的行为
- **环境信息**: 操作系统、Python版本等
- **错误日志**: 相关的错误信息和日志

## 🔄 版本历史

### v7.1.0 (当前版本)
- ✅ 安全增强版本
- ✅ 完整的技术分析功能
- ✅ 策略回测引擎
- ✅ Telegram机器人集成
- ✅ Web界面优化
- ✅ 85%测试覆盖率

### v7.0.0
- ✅ 多智能体系统架构
- ✅ 数据适配器模块
- ✅ 实时监控系统
- ✅ 风险管理模块

### v6.x
- ✅ 基础量化交易功能
- ✅ HTTP API接口
- ✅ 数据处理引擎

## 🔗 相关链接

### 外部资源
- **Python官网**: https://www.python.org/
- **FastAPI文档**: https://fastapi.tiangolo.com/
- **Pandas文档**: https://pandas.pydata.org/docs/
- **Telegram Bot API**: https://core.telegram.org/bots/api

### 金融数据源
- **Yahoo Finance**: https://finance.yahoo.com/
- **Alpha Vantage**: https://www.alphavantage.co/
- **Quandl**: https://www.quandl.com/

### 技术栈
- **后端框架**: FastAPI 0.104.1
- **数据处理**: Pandas 2.1.3, NumPy 1.24.3
- **HTTP客户端**: Requests 2.31.0
- **异步服务器**: Uvicorn 0.24.0
- **机器人框架**: python-telegram-bot 21.6

## 📞 支持与联系

### 技术支持
- **文档首选**: 优先查看项目文档解决问题
- **GitHub Issues**: 提交bug报告和功能请求
- **社区讨论**: 参与GitHub Discussions

### 联系信息
- **项目维护者**: 港股量化交易团队
- **邮箱**: contact@hk-quant-team.com
- **项目地址**: https://github.com/hk-quant-team/hk-quant-ai-agents

### 商业支持
如需商业级支持、定制开发或企业部署服务，请联系我们获取详细信息。

---

## 🎯 快速开始总结

**新用户5分钟上手指南:**

1. **环境检查**:
   ```bash
   python --version  # 需要3.8+
   ```

2. **安装系统**:
   ```bash
   pip install -r requirements.txt
   ```

3. **启动系统**:
   ```bash
   python complete_project_system.py
   ```

4. **访问界面**:
   ```
   http://localhost:8001
   ```

5. **开始使用**:
   - 输入股票代码 (如: 0700.HK)
   - 点击"安全分析"查看结果
   - 探索其他功能标签页

**🎉 现在您可以开始使用AI量化交易系统了！**

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⭐ 如果这个项目对您有帮助，请给我们一个星标！

感谢您使用AI Agent量化交易系统！
