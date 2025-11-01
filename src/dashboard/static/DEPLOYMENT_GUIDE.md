# 🚀 CODEX Trading Dashboard - 部署指南

## 📋 目录

1. [概述](#概述)
2. [系统要求](#系统要求)
3. [快速开始](#快速开始)
4. [本地开发部署](#本地开发部署)
5. [生产环境部署](#生产环境部署)
6. [Docker部署](#docker部署)
7. [云平台部署](#云平台部署)
8. [性能优化](#性能优化)
9. [监控和日志](#监控和日志)
10. [故障排除](#故障排除)

---

## 概述

CODEX Trading Dashboard 是一个基于 Vue 3 + FastAPI 的现代化量化交易系统。本指南将帮助您在不同环境中部署和配置系统。

### 核心特性

- ✅ Vue 3 + Composition API
- ✅ Pinia 状态管理
- ✅ Vue Router 懒加载
- ✅ FastAPI 后端
- ✅ 多智能体系统
- ✅ 实时监控
- ✅ 性能优化 (Phase 7)
- ✅ 错误边界处理
- ✅ API缓存系统

### 技术栈

**前端**:
- Vue 3.4+
- Vue Router 4
- Pinia 2
- Tailwind CSS 3
- Vite 5
- Vitest (测试)

**后端**:
- Python 3.10+
- FastAPI
- WebSocket
- AsyncIO

---

## 系统要求

### 最低要求

| 组件 | 要求 |
|------|------|
| **操作系统** | Linux (Ubuntu 20.04+), Windows 10+, macOS 11+ |
| **内存** | 4GB RAM |
| **存储** | 10GB 可用空间 |
| **CPU** | 2核心 |
| **网络** | 宽带互联网连接 |

### 推荐配置

| 组件 | 要求 |
|------|------|
| **内存** | 8GB+ RAM |
| **存储** | 50GB+ SSD |
| **CPU** | 4核心+ |
| **网络** | 100Mbps+ |

### 软件依赖

```bash
# 必需软件
- Python 3.10+
- Node.js 18+ / npm 9+
- Git 2.30+

# 可选软件
- Docker 20.10+
- Docker Compose 2.0+
- Nginx 1.20+
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-org/codex-trading-system.git
cd codex-trading-system
```

### 2. 一键启动 (开发环境)

```bash
# 方式1: 使用默认配置
python run_dashboard.py

# 方式2: 指定端口
python run_dashboard.py --port 8001

# 方式3: 启用调试模式
python run_dashboard.py --debug
```

### 3. 访问系统

打开浏览器访问:
- **主界面**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/api/health

---

## 本地开发部署

### 环境准备

#### 1. Python 环境

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖 (可选)
pip install -r requirements-dev.txt
```

#### 2. Node.js 环境

```bash
# 安装前端依赖
cd src/dashboard/static
npm install

# 启动开发服务器
npm run dev

# 或运行测试
npm test

# 生成覆盖率报告
npm run test:coverage
```

### 开发模式启动

#### 后端开发

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动FastAPI开发服务器
uvicorn src.dashboard.main:app --reload --host 0.0.0.0 --port 8001

# 查看实时日志
tail -f quant_system.log
```

#### 前端开发

```bash
cd src/dashboard/static

# 启动Vite开发服务器
npm run dev

# 或监听模式运行测试
npm run test:watch

# 或启动UI测试界面
npm run test:ui
```

### 热重载

开发模式下支持热重载：

1. **后端**: 修改Python文件自动重启
2. **前端**: 修改Vue组件自动刷新
3. **静态文件**: 修改CSS/JS自动注入

---

## 生产环境部署

### 准备工作

#### 1. 环境变量配置

创建 `.env` 文件:

```bash
# .env.example 模板
# API配置
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4

# 安全配置
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 数据库配置 (可选)
DATABASE_URL=postgresql://user:pass@localhost:5432/codex

# Telegram配置 (可选)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# 数据源配置
DATA_SOURCE_URL=http://18.180.162.113:9191
DATA_API_KEY=your-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/quant_system.log

# 性能配置
CACHE_TTL=300
MAX_CONNECTIONS=100
```

#### 2. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    build-essential \
    libta-lib-dev \
    nginx

# CentOS/RHEL
sudo yum install -y \
    python3.10 \
    python3.10-devel \
    gcc \
    gcc-c++ \
    ta-lib-devel \
    nginx
```

### 使用 Gunicorn + Nginx

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

#### 2. 创建启动脚本

```bash
#!/bin/bash
# start_production.sh

# 设置环境变量
export PYTHONPATH=$(pwd)
export ENVIRONMENT=production

# 启动Gunicorn
gunicorn src.dashboard.main:app \
    --bind 0.0.0.0:8001 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --daemon

echo "✅ Production server started on port 8001"
```

#### 3. 配置 Nginx

```nginx
# /etc/nginx/sites-available/codex-dashboard

server {
    listen 80;
    server_name your-domain.com;

    # 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 静态文件
    location /static/ {
        alias /path/to/codex-trading-system/src/dashboard/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### 4. 启动服务

```bash
# 创建日志目录
mkdir -p logs

# 启动后端
chmod +x start_production.sh
./start_production.sh

# 启用Nginx配置
sudo ln -s /etc/nginx/sites-available/codex-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 设置开机自启
sudo systemctl enable nginx
sudo systemctl enable gunicorn
```

### 使用 Systemd

#### 1. 创建 Systemd 服务

```ini
# /etc/systemd/system/codex-dashboard.service

[Unit]
Description=CODEX Trading Dashboard
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/codex-trading-system
Environment=PATH=/path/to/codex-trading-system/.venv/bin
ExecStart=/path/to/codex-trading-system/.venv/bin/gunicorn src.dashboard.main:app --bind 0.0.0.0:8001 --workers 4
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. 管理服务

```bash
# 启动服务
sudo systemctl start codex-dashboard

# 停止服务
sudo systemctl stop codex-dashboard

# 重启服务
sudo systemctl restart codex-dashboard

# 查看状态
sudo systemctl status codex-dashboard

# 查看日志
sudo journalctl -u codex-dashboard -f
```

---

## Docker部署

### 1. 创建 Dockerfile

```dockerfile
# Dockerfile

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# 启动命令
CMD ["gunicorn", "src.dashboard.main:app", "--bind", "0.0.0.0:8001", "--workers", "4"]
```

### 2. 创建 docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
      - API_HOST=0.0.0.0
      - API_PORT=8001
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  logs:
  data:
```

### 3. 构建和运行

```bash
# 构建镜像
docker-compose build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build
```

### 4. 前端单独构建

```dockerfile
# Dockerfile.frontend

FROM node:18-alpine AS builder

WORKDIR /app
COPY src/dashboard/static/package*.json ./
RUN npm ci --only=production

COPY src/dashboard/static/ .
RUN npm run build

# 生产镜像
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 云平台部署

### AWS部署

#### 1. 使用 AWS Elastic Beanstalk

```bash
# 安装EB CLI
pip install awsebcli

# 初始化
eb init

# 创建环境
eb create production

# 部署
eb deploy
```

#### 2. 使用 AWS ECS (Fargate)

```json
{
  "family": "codex-dashboard",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "codex-dashboard",
      "image": "your-account.dkr.ecr.region.amazonaws.com/codex-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/codex-dashboard",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### 1. 使用 App Engine

```yaml
# app.yaml
runtime: python310

env_variables:
  ENVIRONMENT: production
  API_HOST: "0.0.0.0"
  API_PORT: "8080"

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 60

handlers:
  - url: /static
    static_dir: src/dashboard/static/dist

  - url: /api/.*
    script: auto

  - url: /.*
    static_files: src/dashboard/static/dist/index.html
```

#### 2. 部署命令

```bash
# 部署到App Engine
gcloud app deploy

# 查看应用
gcloud app browse
```

### Heroku部署

#### 1. 创建 Procfile

```
web: gunicorn src.dashboard.main:app --bind 0.0.0.0:$PORT --workers 4
```

#### 2. 部署命令

```bash
# 登录Heroku
heroku login

# 创建应用
heroku create codex-dashboard

# 设置环境变量
heroku config:set ENVIRONMENT=production

# 部署
git push heroku main

# 查看日志
heroku logs --tail
```

### DigitalOcean App Platform

#### 1. 创建 .do/app.yaml

```yaml
name: codex-dashboard
services:
- name: web
  source_dir: /
  github:
    repo: your-username/codex-trading-system
    branch: main
  run_command: gunicorn src.dashboard.main:app --bind 0.0.0.0:$PORT --workers 4
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: ENVIRONMENT
    value: production
  - key: API_PORT
    value: 8080
```

#### 2. 部署

```bash
# 安装 doctl
brew install doctl

# 创建应用
doctl apps create --spec .do/app.yaml
```

---

## 性能优化

### 生产环境优化清单

#### 1. Python 优化

```bash
# 使用PyPy替代CPython (可选)
pypy3 -m pip install -r requirements.txt

# 编译Python字节码
python -m compileall src/

# 安装Cython扩展 (可选)
pip install cython
```

#### 2. Gunicorn 优化

```bash
# 根据CPU核心数调整workers
export WORKERS=$(($(nproc) * 2 + 1))

gunicorn src.dashboard.main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload-app \
    --keep-alive 5
```

#### 3. Nginx 优化

```nginx
# /etc/nginx/nginx.conf

# 工作进程数 (等于CPU核心数)
worker_processes auto;

# 工作连接数
worker_connections 1024;

# 缓冲大小
client_body_buffer_size 128k;
client_max_body_size 10m;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;

# 超时设置
client_body_timeout 12;
client_header_timeout 12;
keepalive_timeout 15;
send_timeout 10;

# Gzip压缩
gzip on;
gzip_comp_level 6;
gzip_min_length 1000;
gzip_proxied any;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss
    application/atom+xml;
```

#### 4. 系统级优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 启用TCP快速打开
echo 3 > /proc/sys/net/ipv4/tcp_fastopen

# 调整TCP窗口
echo 1 > /proc/sys/net/ipv4/tcp_window_scaling
```

#### 5. 监控资源使用

```bash
# 安装htop
sudo apt-get install htop

# 监控系统资源
htop

# 查看网络连接
ss -tulpn | grep :8001

# 查看进程详情
ps aux | grep gunicorn

# 查看磁盘使用
df -h
du -sh /path/to/codex-trading-system
```

### 缓存优化

#### 1. Redis 缓存 (可选)

```python
# 安装Redis客户端
pip install redis

# 配置Redis
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

# 使用Redis缓存API响应
async def get_cached_data(key):
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    # ... fetch from API
    r.setex(key, 300, json.dumps(data))  # 5分钟TTL
```

#### 2. CDN 配置

```nginx
# CloudFlare或CDN配置
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
}
```

---

## 监控和日志

### 1. 应用日志

#### 配置日志

```python
# src/dashboard/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # 创建logs目录
    import os
    os.makedirs('logs', exist_ok=True)

    # 根日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                'logs/quant_system.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )

    # 错误日志单独记录
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger('error').addHandler(error_handler)
```

#### 查看日志

```bash
# 查看实时日志
tail -f logs/quant_system.log

# 查看错误日志
tail -f logs/error.log

# 搜索错误
grep "ERROR" logs/quant_system.log

# 统计日志行数
wc -l logs/quant_system.log
```

### 2. 系统监控

#### 使用 Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

#### 启动监控

```bash
# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 访问Grafana
# http://localhost:3000
# 用户名: admin
# 密码: admin
```

### 3. 健康检查

#### 创建健康检查端点

```python
# src/dashboard/health.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import psutil
import time

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    try:
        # 系统信息
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - psutil.boot_time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            },
            "version": "1.0.0"
        }

        # 如果资源使用过高，返回warning
        if cpu_percent > 80 or memory.percent > 85:
            health_data["status"] = "warning"

        return JSONResponse(content=health_data)

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )
```

#### 配置监控检查

```bash
# 使用curl检查健康状态
curl -f http://localhost:8001/api/health

# 配置监控脚本
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health)
if [ $RESPONSE -eq 200 ]; then
    echo "✅ Service is healthy"
else
    echo "❌ Service is unhealthy (HTTP $RESPONSE)"
    # 发送告警
    # mail -s "Service Down" admin@example.com < /dev/null
fi
EOF

chmod +x /usr/local/bin/health-check.sh

# 添加到crontab (每分钟检查)
echo "* * * * * /usr/local/bin/health-check.sh" | crontab -
```

### 4. 告警配置

#### 邮件告警

```python
# src/dashboard/alerts.py
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

def send_alert(subject, message):
    """发送邮件告警"""
    try:
        msg = MimeMultipart()
        msg['From'] = "alerts@your-domain.com"
        msg['To'] = "admin@your-domain.com"
        msg['Subject'] = subject

        msg.attach(MimeText(message, 'html'))

        server = smtplib.SMTP('localhost')
        server.send_message(msg)
        server.quit()

        print(f"✅ Alert sent: {subject}")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")
```

#### Telegram告警

```python
# src/dashboard/telegram_alerts.py
import requests

def send_telegram_alert(message, bot_token, chat_id):
    """发送Telegram告警"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": f"🚨 {message}",
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
```

---

## 故障排除

### 常见问题及解决方案

#### 1. 端口被占用

**错误**: `Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
sudo lsof -i :8001

# 杀死进程
sudo kill -9 <PID>

# 或使用不同端口
python run_dashboard.py --port 8002
```

#### 2. 依赖安装失败

**错误**: `ERROR: Failed building wheel for ta-lib`

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt-get install libta-lib-dev
pip install TA-Lib

# CentOS/RHEL
sudo yum install ta-lib-devel
pip install TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib

# Windows
# 下载预编译wheel: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib-0.4.XX-cpXX-cpXXm-win_amd64.whl
```

#### 3. Vue组件加载失败

**错误**: `Failed to load component`

**检查步骤**:
```bash
# 检查文件是否存在
ls -la src/dashboard/static/js/components/AgentPanel.js

# 检查文件权限
chmod 644 src/dashboard/static/js/components/*.js

# 检查浏览器控制台错误
# 打开开发者工具 -> Console

# 检查网络请求
# 开发者工具 -> Network -> 查看是否有404错误
```

#### 4. API调用失败

**错误**: `Failed to fetch agents`

**解决方案**:
```bash
# 检查API服务状态
curl -f http://localhost:8001/api/health

# 检查日志
tail -f logs/quant_system.log | grep ERROR

# 测试API端点
curl -X GET http://localhost:8001/api/agents/list

# 检查网络连接
ping localhost
telnet localhost 8001
```

#### 5. 内存使用过高

**错误**: 系统变慢或OOM

**解决方案**:
```bash
# 查看内存使用
free -h
htop

# 重启服务
sudo systemctl restart codex-dashboard

# 调整Gunicorn workers数量
export WORKERS=2  # 减少workers数量

# 启用swap (临时解决方案)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 6. 数据库连接失败

**错误**: `psycopg2.OperationalError: could not connect`

**解决方案**:
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接配置
grep DATABASE_URL .env

# 测试连接
psql -h localhost -U postgres -d codex

# 检查防火墙
sudo ufw status
sudo ufw allow 5432
```

#### 7. WebSocket连接失败

**错误**: `WebSocket connection failed`

**解决方案**:
```nginx
# 检查Nginx配置
# 确保WebSocket代理配置正确
location /ws {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

#### 8. SSL证书问题

**错误**: `SSL certificate error`

**解决方案**:
```bash
# 使用Let's Encrypt获取免费证书
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 续期证书
sudo certbot renew

# 检查证书状态
sudo certbot certificates
```

#### 9. 权限错误

**错误**: `Permission denied`

**解决方案**:
```bash
# 修复文件权限
sudo chown -R www-data:www-data /path/to/codex-trading-system
sudo chmod -R 755 /path/to/codex-trading-system
sudo chmod -R 644 /path/to/codex-trading-system/src/dashboard/static/js/components/*.js

# 检查SELinux (CentOS/RHEL)
getenforce
# 如果是Enforcing，设置为Permissive
sudo setenforce 0
```

#### 10. 性能问题

**错误**: 响应缓慢

**解决方案**:
```bash
# 启用性能监控
python -m cProfile -o profile.stats your_script.py

# 安装性能分析工具
pip install py-spy
py-spy top --pid <PID>

# 检查数据库查询
# 启用SQL日志
```

### 日志分析

#### 分析常见模式

```bash
# 统计错误类型
grep "ERROR" logs/quant_system.log | awk '{print $5}' | sort | uniq -c | sort -rn

# 分析访问日志
awk '{print $1}' logs/access.log | sort | uniq -c | sort -rn | head -10

# 查找慢请求
grep "slow" logs/quant_system.log

# 监控错误率
grep "timestamp:" logs/quant_system.log | awk '{print $2}' | sort | uniq -c
```

### 调试工具

#### Python调试

```bash
# 启用调试模式
export DEBUG=1
python run_dashboard.py

# 使用pdb调试
python -m pdb your_script.py

# 使用ipdb (更好的调试体验)
pip install ipdb
# 在代码中添加: import ipdb; ipdb.set_trace()
```

#### 前端调试

```javascript
// 在main.js中启用详细日志
if (import.meta.env.DEV) {
    console.log('🔍 Debug mode enabled');
    // 详细日志输出
}

// 检查Vue组件
window.App?.useAgentStore?.agents
```

### 获取帮助

如果遇到其他问题:

1. **查看文档**: 阅读本部署指南和API文档
2. **检查日志**: 查看 `logs/quant_system.log`
3. **搜索Issues**: 在GitHub仓库搜索已知问题
4. **创建Issue**: 提供详细的错误信息和复现步骤
5. **社区支持**: 参与Discord/论坛讨论

---

## 结语

恭喜！您已成功部署 CODEX Trading Dashboard。

### 快速参考

```bash
# 常用命令
python run_dashboard.py                    # 启动服务
python run_dashboard.py --help             # 查看帮助
tail -f logs/quant_system.log              # 查看日志
sudo systemctl restart codex-dashboard     # 重启服务

# 重要路径
/var/log/codex/                            # 日志目录
/etc/nginx/sites-available/codex-dashboard # Nginx配置
/etc/systemd/system/codex-dashboard.service # Systemd服务
```

### 下一步

- 📚 阅读 [API文档](./API_DOCUMENTATION.md)
- 👤 阅读 [用户手册](./USER_MANUAL.md)
- 👨‍💻 阅读 [开发者指南](./DEVELOPER_GUIDE.md)
- 🔧 查看 [故障排除指南](./TROUBLESHOOTING.md)

### 反馈

如果您在使用过程中遇到任何问题或有改进建议，欢迎:
- 创建GitHub Issue
- 提交Pull Request
- 参与社区讨论

---

**部署愉快！** 🚀

---

*最后更新: 2025-10-27*
*版本: v1.0.0*
