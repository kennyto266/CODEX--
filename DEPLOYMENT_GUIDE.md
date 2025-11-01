# CODEX 量化交易系统 - 部署指南

## 目录

1. [部署概述](#1-部署概述)
2. [系统要求](#2-系统要求)
3. [开发环境部署](#3-开发环境部署)
4. [生产环境部署](#4-生产环境部署)
5. [Docker部署](#5-docker部署)
6. [云服务部署](#6-云服务部署)
7. [配置说明](#7-配置说明)
8. [监控与日志](#8-监控与日志)
9. [备份与恢复](#9-备份与恢复)
10. [故障排除](#10-故障排除)
11. [性能优化](#11-性能优化)
12. [安全配置](#12-安全配置)

---

## 1. 部署概述

### 1.1 部署模式

CODEX量化交易系统支持多种部署模式：

| 部署模式 | 适用场景 | 特点 |
|---------|---------|------|
| 🖥️ **开发环境** | 开发调试 | 快速启动，完整日志 |
| 🏭 **生产环境** | 生产使用 | 高可用，高性能 |
| 🐳 **Docker** | 容器化部署 | 快速部署，环境隔离 |
| ☁️ **云服务** | 云端部署 | 自动扩缩，弹性计算 |

### 1.2 部署架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        负载均衡层                                │
├─────────────────────────────────────────────────────────────────┤
│  Nginx / HAProxy  │  SSL证书  │  域名解析  │  防火墙         │
└─────────────────────────────────────────────────────────────────┘
                                ↕
┌─────────────────────────────────────────────────────────────────┐
│                        应用层                                    │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI应用  │  Vue Dashboard  │  WebSocket  │  静态文件服务  │
└─────────────────────────────────────────────────────────────────┘
                                ↕
┌─────────────────────────────────────────────────────────────────┐
│                        数据层                                    │
├─────────────────────────────────────────────────────────────────┤
│  SQLite/PostgreSQL  │  Redis缓存  │  日志文件  │  备份存储      │
└─────────────────────────────────────────────────────────────────┘
                                ↕
┌─────────────────────────────────────────────────────────────────┐
│                        外部服务                                  │
├─────────────────────────────────────────────────────────────────┤
│  富途API  │  HKEX API  │  GOV数据  │  第三方服务  │  监控服务    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 系统要求

### 2.1 硬件要求

#### 最低配置
- **CPU**: 2核心 2.0GHz
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **网络**: 1Mbps 带宽

#### 推荐配置
- **CPU**: 4核心 3.0GHz
- **内存**: 8GB RAM
- **存储**: 100GB SSD
- **网络**: 10Mbps 带宽

#### 生产环境配置
- **CPU**: 8核心 3.5GHz
- **内存**: 16GB RAM
- **存储**: 500GB NVMe SSD
- **网络**: 100Mbps 带宽

### 2.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| **操作系统** | Linux/Ubuntu 20.04+ / CentOS 7+ / Windows 10+ | 推荐Linux |
| **Python** | 3.10 - 3.13 | 必须支持3.10+ |
| **Node.js** | 16.0+ | 用于前端构建 |
| **NPM** | 8.0+ | 包管理器 |
| **Git** | 2.20+ | 版本控制 |

### 2.3 依赖包

#### Python依赖
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
aiofiles>=23.0.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
redis>=5.0.0
```

#### Node.js依赖
```
vue@3.3.4
pinia@2.1.6
vue-router@4.2.5
vite@5.0.0
```

---

## 3. 开发环境部署

### 3.1 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/codex-quant-system.git
cd codex-quant-system

# 2. 创建虚拟环境
python -m venv .venv310

# 3. 激活虚拟环境
# Linux/Mac:
source .venv310/bin/activate
# Windows:
.venv310\Scripts\activate

# 4. 安装Python依赖
pip install -r requirements.txt

# 5. 安装前端依赖
cd src/dashboard/static
npm install --legacy-peer-deps

# 6. 启动系统
cd /path/to/project
python complete_project_system.py

# 7. 访问系统
# 主界面: http://localhost:8001
# API文档: http://localhost:8001/docs
```

### 3.2 分步启动

```bash
# 方式1: 完整系统版 (推荐)
python complete_project_system.py

# 方式2: 仪表板服务
python run_dashboard.py

# 方式3: 安全增强版
python secure_complete_system.py

# 方式4: 统一系统版
python unified_quant_system.py

# 方式5: 使用UVicorn直接启动
uvicorn complete_project_system:app --host 0.0.0.0 --port 8000 --reload
```

### 3.3 验证部署

```bash
# 1. 检查服务状态
curl http://localhost:8001/health

# 2. 检查API文档
curl http://localhost:8000/docs

# 3. 检查前端页面
curl http://localhost:8001

# 4. 运行测试
python -m pytest tests/ -v
```

---

## 4. 生产环境部署

### 4.1 使用Gunicorn部署

```bash
# 1. 安装Gunicorn
pip install gunicorn

# 2. 配置Gunicorn
# 创建gunicorn.conf.py
cat > gunicorn.conf.py << 'EOF'
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# 3. 启动应用
gunicorn complete_project_system:app -c gunicorn.conf.py

# 4. 使用systemd管理服务
sudo tee /etc/systemd/system/codex.service > /dev/null <<EOF
[Unit]
Description=CODEX Trading System
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/codex-quant-system
Environment="PATH=/home/ubuntu/codex-quant-system/.venv310/bin"
ExecStart=/home/ubuntu/codex-quant-system/.venv310/bin/gunicorn complete_project_system:app -c gunicorn.conf.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 5. 启动并启用服务
sudo systemctl daemon-reload
sudo systemctl enable codex
sudo systemctl start codex
sudo systemctl status codex
```

### 4.2 使用Nginx反向代理

```bash
# 1. 安装Nginx
sudo apt update
sudo apt install nginx -y

# 2. 配置Nginx
sudo tee /etc/nginx/sites-available/codex > /dev/null <<'EOF'
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 前端静态文件
    location / {
        root /home/ubuntu/codex-quant-system/src/dashboard/static;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # API文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
}
EOF

# 3. 启用站点
sudo ln -s /etc/nginx/sites-available/codex /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4.3 SSL证书配置

```bash
# 使用Let's Encrypt免费SSL证书
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 5. Docker部署

### 5.1 创建Dockerfile

```dockerfile
# Dockerfile
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 codex && chown -R codex:codex /app
USER codex

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "complete_project_system:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 创建docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./codex.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 5.3 启动Docker服务

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

---

## 6. 云服务部署

### 6.1 AWS部署

```bash
# 1. 创建EC2实例
# - AMI: Ubuntu 20.04 LTS
# - Instance Type: t3.medium (推荐)
# - Storage: 20GB GP2

# 2. 连接到实例
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. 安装依赖
sudo apt update
sudo apt install python3-pip python3-venv git nginx -y

# 4. 克隆代码
git clone https://github.com/your-org/codex-quant-system.git
cd codex-quant-system

# 5. 部署应用 (参考生产环境部署)

# 6. 配置安全组
# - 开放HTTP (80)
# - 开放HTTPS (443)
# - 开放SSH (22)
```

### 6.2 阿里云部署

```bash
# 1. 创建ECS实例
# - 镜像: Ubuntu 20.04 64位
# - 实例规格: ecs.t5-lc1m2.small (推荐)
# - 系统盘: 20GB 高效云盘

# 2. 连接到实例
ssh root@your-ecs-ip

# 3. 安装依赖并部署 (同AWS步骤3-6)

# 4. 配置安全组
# - 授权规则: HTTP(80)
# - 授权规则: HTTPS(443)
# - 授权规则: SSH(22)
```

### 6.3 使用云数据库

```yaml
# config/production.py
DATABASE_CONFIG = {
    "url": "postgresql://user:password@your-db-host:5432/codex",
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}
```

---

## 7. 配置说明

### 7.1 环境变量

创建`.env`文件：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./codex.db
# DATABASE_URL=postgresql://user:password@localhost:5432/codex

# Redis配置
REDIS_URL=redis://localhost:6379/0

# API密钥
FUTU_API_KEY=your_futu_api_key
FUTU_SECRET=your_futu_secret
FUTU_TRADE_PASSWORD=your_trade_password

# 安全配置
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/codex/codex.log

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 7.2 配置文件

#### config/settings.py

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库
    database_url: str = "sqlite:///./codex.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # FastAPI
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # 富途API
    futu_host: str = "127.0.0.1"
    futu_port: int = 11111
    futu_trade_password: str = ""

    # 安全
    secret_key: str = "your-secret-key"
    access_token_expire_minutes: int = 60 * 24

    # 日志
    log_level: str = "INFO"
    log_file: str = "/var/log/codex/codex.log"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 7.3 日志配置

```python
# config/logging.py
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(log_level: str, log_file: str):
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))

    # 文件处理器
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level))

    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger
```

---

## 8. 监控与日志

### 8.1 日志管理

```bash
# 查看实时日志
tail -f /var/log/codex/codex.log

# 查看错误日志
grep ERROR /var/log/codex/codex.log

# 轮转日志
logrotate -f /etc/logrotate.d/codex
```

### 8.2 性能监控

```python
# 监控中间件
from fastapi import Request
import time
import psutil

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求
    response = await call_next(request)

    process_time = time.time() - start_time

    # 记录到日志
    logger.info(
        f"path={request.url.path} "
        f"method={request.method} "
        f"status={response.status_code} "
        f"duration={process_time:.3f}s "
        f"memory={psutil.virtual_memory().percent}%"
    )

    return response
```

### 8.3 健康检查

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "redis": "ok",
            "futu_api": "ok"
        }
    }
```

### 8.4 Prometheus监控

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
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana_data:
```

---

## 9. 备份与恢复

### 9.1 数据库备份

```bash
# SQLite备份
cp codex.db codex.db.backup.$(date +%Y%m%d_%H%M%S)

# PostgreSQL备份
pg_dump -h localhost -U user -d codex > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 9.2 自动备份脚本

```bash
#!/bin/bash
# backup.sh

# 设置参数
BACKUP_DIR="/backup/codex"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="codex.db"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $DB_FILE $BACKUP_DIR/codex_$DATE.db

# 备份日志
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /var/log/codex/

# 删除7天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 9.3 恢复数据

```bash
# 恢复SQLite数据库
cp codex.db.backup.20251031 codex.db

# 恢复PostgreSQL数据库
psql -h localhost -U user -d codex < backup_20251031.sql
```

### 9.4 配置cron自动备份

```bash
# 编辑crontab
crontab -e

# 添加以下行 (每天凌晨2点备份)
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

---

## 10. 故障排除

### 10.1 常见问题

#### 问题1: 端口被占用
```bash
# 查看端口占用
sudo netstat -tulpn | grep 8000

# 杀死占用进程
sudo kill -9 <PID>
```

#### 问题2: 数据库锁定
```bash
# 检查数据库锁
lsof codex.db

# 重启应用
sudo systemctl restart codex
```

#### 问题3: 内存不足
```bash
# 检查内存使用
free -h

# 查看进程内存使用
ps aux --sort=-%mem | head
```

#### 问题4: 磁盘空间不足
```bash
# 检查磁盘使用
df -h

# 清理日志文件
sudo find /var/log/codex/ -name "*.log" -type f -mtime +7 -delete
```

### 10.2 日志分析

```bash
# 查看错误日志
grep -i error /var/log/codex/codex.log | tail -20

# 查看异常堆栈
grep -A 10 "Exception" /var/log/codex/codex.log

# 统计错误数量
grep -c "ERROR" /var/log/codex/codex.log
```

### 10.3 调试模式

```python
# 启用调试模式
export DEBUG=1
export LOG_LEVEL=DEBUG

# 重新启动应用
python complete_project_system.py
```

---

## 11. 性能优化

### 11.1 应用层优化

```python
# 使用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_data(key: str):
    # 获取数据
    return data

# 数据库连接池
from sqlalchemy import create_engine
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30
)
```

### 11.2 Nginx优化

```nginx
# nginx.conf
worker_processes auto;
worker_connections 1024;

# 启用gzip压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# 静态文件缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 11.3 数据库优化

```sql
-- 为常用查询添加索引
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);

-- 分析查询性能
EXPLAIN QUERY PLAN SELECT * FROM positions WHERE symbol = '0700.HK';
```

---

## 12. 安全配置

### 12.1 防火墙配置

```bash
# 使用ufw配置防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw deny 8000  # 禁用直接访问应用端口

# 检查防火墙状态
sudo ufw status
```

### 12.2 SSL/TLS配置

```nginx
# 强化的SSL配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# CSP
add_header Content-Security-Policy "default-src 'self'" always;
```

### 12.3 访问控制

```python
# IP白名单
ALLOWED_IPS = ["192.168.1.0/24", "10.0.0.0/8"]

@app.middleware("http")
async def check_ip(request: Request, call_next):
    client_ip = request.client.host
    if not any(ipaddress.ip_address(client_ip) in ipaddress.ip_network(net) for net in ALLOWED_IPS):
        raise HTTPException(status_code=403, detail="IP not allowed")
    return await call_next(request)
```

### 12.4 API限流

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/data")
@limiter.limit("10/minute")
async def get_data(request: Request):
    return {"data": "some data"}
```

---

## 总结

本部署指南涵盖了CODEX量化交易系统的各种部署场景。请根据实际需求选择合适的部署方式。

### 快速部署命令

```bash
# 开发环境 (最快)
git clone <repo> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python complete_project_system.py

# 生产环境 (推荐)
docker-compose up -d

# 或使用systemd + Nginx
gunicorn complete_project_system:app -c gunicorn.conf.py
```

### 验证部署

```bash
# 检查服务状态
curl http://localhost:8001/health

# 检查API文档
curl http://localhost:8000/docs

# 运行测试
python -m pytest tests/ -v
```

### 获取帮助

- 📧 邮件支持: support@codex-trading.com
- 📖 在线文档: https://docs.codex-trading.com
- 💬 技术社区: https://community.codex-trading.com

---

**部署指南版本**: v1.0.0
**最后更新**: 2025-10-31
**文档维护**: CODEX开发团队

---

*祝您部署顺利！*
