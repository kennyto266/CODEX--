# Phase 5: Real-time Trading System - Deployment Guide

**Status**: Production-Ready for Deployment
**Date**: 2025-10-25
**Deployment Complexity**: Medium
**Estimated Setup Time**: 30-45 minutes

---

## Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] Database configured (PostgreSQL recommended)
- [ ] Network connectivity validated

### Configuration Requirements
- [ ] `.env` file created with all variables
- [ ] API keys and credentials configured
- [ ] Database connection string verified
- [ ] Log directory created with write permissions
- [ ] Market data feed connection tested

### Testing Requirements
- [ ] All 76 Phase 5 tests passing
- [ ] Integration tests successful
- [ ] Production environment tested
- [ ] Error recovery validated
- [ ] Signal handling verified

### Security Requirements
- [ ] API keys stored securely (not in git)
- [ ] Database credentials encrypted
- [ ] HTTPS enabled for dashboard
- [ ] Network access restricted to trusted IPs
- [ ] Audit logging enabled

---

## Step 1: Environment Setup

### 1.1 Create Virtual Environment

```bash
# Windows
python -m venv .venv310
.venv310\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 1.2 Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Optional: Test dependencies
pip install -r test_requirements.txt
```

### 1.3 Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Check key packages
python -c "import fastapi, asyncio, pandas; print('All dependencies OK')"
```

---

## Step 2: Configuration Setup

### 2.1 Create Environment File

Copy the template and configure:

```bash
cp .env.example .env
```

### 2.2 Configure .env Variables

**Critical Variables**:

```env
# Environment
ENVIRONMENT=production  # development, staging, or production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_DIR=logs
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=trading_system

# Connection Pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30

# Caching
CACHE_ENABLED=true
CACHE_SIZE=1000
CACHE_TTL=3600

# Performance
MAX_QUEUE_SIZE=1000
BATCH_SIZE=100
TIMEOUT_SECONDS=30.0
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=1.0

# Monitoring
MONITORING_ENABLED=true
METRICS_INTERVAL=60

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4

# Market Data
MARKET_DATA_SOURCE=http://18.180.162.113:9191
MARKET_DATA_TIMEOUT=30

# Trading Configuration
INITIAL_CAPITAL=1000000
MAX_POSITION_SIZE=100000
MAX_PORTFOLIO_HEAT=500000
MAX_DAILY_LOSS=50000
MAX_DRAWDOWN=-0.20

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 2.3 Validate Configuration

```bash
# Test config loading
python -c "
from src.infrastructure.production_setup import ProductionManager
pm = ProductionManager('production')
print('Configuration loaded successfully')
print(f'Environment: {pm.config.environment.value}')
print(f'Log Level: {pm.config.logging.level}')
print(f'Database: {pm.config.database.host}:{pm.config.database.port}')
"
```

---

## Step 3: Database Setup

### 3.1 Initialize Database

```bash
# Create database tables
python init_db.py

# Verify database connection
python -c "
from src.database import get_db_connection
conn = get_db_connection()
print(f'Database connected: {conn}')
"
```

### 3.2 Create Required Tables

```sql
-- Run these in your PostgreSQL database
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity FLOAT,
    entry_price FLOAT,
    exit_price FLOAT,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    pnl FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    quantity FLOAT,
    entry_price FLOAT,
    current_price FLOAT,
    unrealized_pnl FLOAT,
    entry_time TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    direction VARCHAR(10),
    confidence FLOAT,
    entry_price FLOAT,
    target_price FLOAT,
    stop_loss FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20),
    message TEXT,
    symbol VARCHAR(20),
    action VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 Verify Database Setup

```bash
# Check tables exist
python -c "
from src.database import execute_query
result = execute_query(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\")
print('Tables:', result)
"
```

---

## Step 4: Test Before Deployment

### 4.1 Run All Tests

```bash
# Run Phase 5 tests
python -m pytest tests/test_phase5_realtime.py tests/test_phase5_dashboard.py tests/test_phase5_production.py -v

# Expected output: 76 passed
```

### 4.2 Test Production Configuration

```bash
# Test production manager
python -c "
from src.infrastructure.production_setup import ProductionManager
import os
os.environ['ENVIRONMENT'] = 'production'

pm = ProductionManager()
status = pm.get_system_status()
print('System Status:', status)
print('Error Count:', pm.error_handler.error_count)
print('Active Tasks:', pm.resource_manager.get_active_task_count())
"
```

### 4.3 Test Trading Engine

```bash
# Test real-time trading engine
python -c "
import asyncio
from src.trading.realtime_trading_engine import RealtimeTradingEngine

async def test():
    engine = RealtimeTradingEngine(initial_capital=1000000)
    await engine.start_trading()

    summary = engine.get_portfolio_summary()
    print('Engine initialized:', summary)

    await engine.stop_trading()

asyncio.run(test())
"
```

### 4.4 Test Dashboard

```bash
# Test dashboard system
python -c "
import asyncio
from src.dashboard.realtime_dashboard import RealtimeDashboard

dashboard = RealtimeDashboard()
print('Dashboard initialized')
print(f'Active connections: {dashboard.ws_manager.get_active_count()}')
print(f'Dashboard summary: {dashboard.get_dashboard_summary()}')
"
```

---

## Step 5: Deploy FastAPI Application

### 5.1 Create Deployment Application

Create `src/application.py`:

```python
\"\"\"
Production FastAPI Application with Real-time Trading Integration
\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os

from src.infrastructure.production_setup import ProductionManager
from src.dashboard.realtime_dashboard import RealtimeDashboard, create_realtime_dashboard_routes
from src.trading.realtime_trading_engine import RealtimeTradingEngine
from src.trading.realtime_risk_manager import RealtimeRiskManager
from src.monitoring.realtime_performance_monitor import RealtimePerformanceMonitor

# Initialize production manager
production_manager = ProductionManager(os.getenv('ENVIRONMENT', 'development'))

# Initialize trading components
trading_engine = RealtimeTradingEngine(initial_capital=float(os.getenv('INITIAL_CAPITAL', '1000000')))
risk_manager = RealtimeRiskManager(
    max_position_size=float(os.getenv('MAX_POSITION_SIZE', '100000')),
    max_portfolio_heat=float(os.getenv('MAX_PORTFOLIO_HEAT', '500000'))
)
performance_monitor = RealtimePerformanceMonitor()
dashboard = RealtimeDashboard()

# Create FastAPI application
app = FastAPI(
    title="Real-time Trading System",
    description="Phase 5: Real-time Trading Integration",
    version="1.0.0"
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv('ALLOWED_HOSTS', '*').split(',')
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include dashboard routes
dashboard_routes = create_realtime_dashboard_routes(dashboard)
app.include_router(dashboard_routes)

# Health check endpoint
@app.get("/health")
async def health_check():
    \"\"\"System health check\"\"\"
    return {
        "status": "healthy",
        "environment": production_manager.config.environment.value,
        "active_connections": dashboard.ws_manager.get_active_count(),
        "error_count": production_manager.error_handler.error_count
    }

# System status endpoint
@app.get("/api/system/status")
async def system_status():
    \"\"\"Get detailed system status\"\"\"
    return production_manager.get_system_status()

# Trading engine endpoints
@app.get("/api/trading/portfolio")
async def get_portfolio():
    \"\"\"Get current portfolio summary\"\"\"
    return trading_engine.get_portfolio_summary()

@app.get("/api/trading/performance")
async def get_performance():
    \"\"\"Get trading performance metrics\"\"\"
    return trading_engine.get_performance_metrics()

# Risk manager endpoints
@app.get("/api/risk/summary")
async def get_risk_summary():
    \"\"\"Get risk management summary\"\"\"
    return risk_manager.get_risk_summary()

# Performance monitor endpoints
@app.get("/api/performance/summary")
async def get_performance_summary():
    \"\"\"Get performance monitoring summary\"\"\"
    return performance_monitor.get_performance_summary()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8001'))
    workers = int(os.getenv('API_WORKERS', '1'))

    uvicorn.run(
        "src.application:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        access_log=True
    )
```

### 5.2 Run Deployment Application

```bash
# Single worker (development)
python src/application.py

# Multiple workers (production)
gunicorn -w 4 -b 0.0.0.0:8001 src.application:app

# Using Uvicorn directly
uvicorn src.application:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Step 6: Production Deployment Options

### 6.1 Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "src.application:app", "--host", "0.0.0.0", "--port", "8001"]
```

Build and run:

```bash
# Build image
docker build -t trading-system:latest .

# Run container
docker run -d \
  --name trading-system \
  -p 8001:8001 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  trading-system:latest
```

### 6.2 Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trading-system
  template:
    metadata:
      labels:
        app: trading-system
    spec:
      containers:
      - name: trading-system
        image: trading-system:latest
        ports:
        - containerPort: 8001
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_DIR
          value: "/var/log/trading"
        envFrom:
        - configMapRef:
            name: trading-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

Deploy:

```bash
kubectl apply -f k8s-deployment.yaml
```

### 6.3 Systemd Service (Linux)

Create `/etc/systemd/system/trading-system.service`:

```ini
[Unit]
Description=Real-time Trading System
After=network.target postgresql.service

[Service]
Type=notify
User=trading
WorkingDirectory=/home/trading/trading-system
Environment="PATH=/home/trading/trading-system/.venv/bin"
EnvironmentFile=/home/trading/trading-system/.env
ExecStart=/home/trading/trading-system/.venv/bin/python src/application.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Enable service
sudo systemctl enable trading-system

# Start service
sudo systemctl start trading-system

# Check status
sudo systemctl status trading-system
```

---

## Step 7: Verification & Testing

### 7.1 Test API Endpoints

```bash
# Health check
curl http://localhost:8001/health

# System status
curl http://localhost:8001/api/system/status

# Portfolio summary
curl http://localhost:8001/api/trading/portfolio

# Performance metrics
curl http://localhost:8001/api/trading/performance

# Risk summary
curl http://localhost:8001/api/risk/summary

# Dashboard summary
curl http://localhost:8001/api/live/summary
```

### 7.2 Test WebSocket Connection

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8001/api/live/ws/portfolio"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # Send ping
        await websocket.send("PING")

        # Receive response
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(test_websocket())
```

### 7.3 Run Integration Tests

```bash
# Run all integration tests
python -m pytest tests/ -v -m integration

# Run under load
python -m pytest tests/test_phase5_production.py::TestProductionIntegration::test_production_under_load -v
```

---

## Step 8: Monitoring & Operations

### 8.1 Set Up Log Monitoring

```bash
# Monitor live logs
tail -f logs/trading_system.log

# Monitor error logs
tail -f logs/errors.log

# Search for specific errors
grep "ERROR" logs/*.log
```

### 8.2 System Monitoring Dashboard

Access dashboard at: `http://localhost:8001/api/live/summary`

Monitor:
- Active connections
- Position count
- Daily P&L
- Win rate
- Sharpe ratio
- Error count

### 8.3 Performance Monitoring

```bash
# Check system resources
python -c "
from src.infrastructure.production_setup import ProductionManager
pm = ProductionManager('production')
import asyncio

async def check():
    status = await pm.resource_manager.get_resource_status()
    print(f'Active tasks: {status[\"active_tasks\"]}')
    print(f'Queue size: {status[\"max_queue_size\"]}')

asyncio.run(check())
"
```

### 8.4 Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/trading-system"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump trading_system > "$BACKUP_DIR/db_$DATE.sql"

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

# Backup configuration (encrypted)
gpg -c -o "$BACKUP_DIR/config_$DATE.gpg" .env

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

---

## Step 9: Operational Procedures

### 9.1 Graceful Shutdown

```bash
# Send SIGTERM (graceful shutdown)
kill -TERM $(pidof python)

# Monitor shutdown
tail -f logs/trading_system.log
```

### 9.2 Error Recovery

System automatically handles:
- ✅ Network timeouts (retry with exponential backoff)
- ✅ Database connection failures (reconnect with pooling)
- ✅ API errors (automatic retry up to 3 attempts)
- ✅ Resource exhaustion (graceful cleanup)

### 9.3 Restart Procedure

```bash
# Stop service
sudo systemctl stop trading-system

# Check logs for errors
tail -20 logs/errors.log

# Verify configuration
python -c "from src.infrastructure.production_setup import ProductionManager; ProductionManager()"

# Start service
sudo systemctl start trading-system

# Verify startup
sudo systemctl status trading-system
```

---

## Step 10: Security Hardening

### 10.1 API Security

```python
# Add authentication to sensitive endpoints
from fastapi.security import HTTPBearer, HTTPAuthCredential

security = HTTPBearer()

@app.get("/api/trading/portfolio")
async def get_portfolio(credentials: HTTPAuthCredential = Depends(security)):
    # Verify credentials
    return trading_engine.get_portfolio_summary()
```

### 10.2 HTTPS Setup

```bash
# Generate SSL certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with HTTPS
uvicorn src.application:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

### 10.3 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/trading/portfolio")
@limiter.limit("100/minute")
async def get_portfolio(request: Request):
    return trading_engine.get_portfolio_summary()
```

---

## Troubleshooting

### Issue: Database Connection Failed

```bash
# Check database status
psql -U postgres -c "SELECT version();"

# Verify connection string
python -c "from src.database import get_db_connection; print(get_db_connection())"

# Check .env variables
grep "DB_" .env
```

### Issue: WebSocket Disconnections

```bash
# Check active connections
curl http://localhost:8001/api/live/ws-connections

# Check logs for connection errors
grep "WebSocket" logs/trading_system.log

# Verify firewall rules
netstat -an | grep 8001
```

### Issue: High Memory Usage

```bash
# Check active tasks
python -c "
from src.infrastructure.production_setup import ProductionManager
pm = ProductionManager()
print(f'Active tasks: {pm.resource_manager.get_active_task_count()}')
"

# Restart service
sudo systemctl restart trading-system
```

### Issue: Performance Degradation

```bash
# Check error rate
grep "ERROR" logs/errors.log | wc -l

# Check system health
curl http://localhost:8001/api/system/status

# Review recent errors
tail -50 logs/errors.log
```

---

## Maintenance Schedule

### Daily
- [ ] Check system health via `/api/system/status`
- [ ] Monitor active positions
- [ ] Review error logs
- [ ] Verify data freshness

### Weekly
- [ ] Review performance metrics
- [ ] Check database size
- [ ] Backup configuration and logs
- [ ] Test graceful shutdown/restart

### Monthly
- [ ] Security audit
- [ ] Database maintenance (vacuum, analyze)
- [ ] Certificate renewal (if HTTPS)
- [ ] Capacity planning review
- [ ] Archive old logs

---

## Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] API endpoints responding correctly
- [ ] WebSocket connections working
- [ ] Database connectivity verified
- [ ] Logging infrastructure operational
- [ ] Monitoring dashboard accessible
- [ ] Backup system configured
- [ ] SSL certificates valid (if HTTPS)
- [ ] Firewall rules configured
- [ ] Team trained on operations
- [ ] Documentation up to date
- [ ] Rollback procedure documented

---

## Rollback Procedure

If issues occur in production:

```bash
# 1. Stop current deployment
sudo systemctl stop trading-system

# 2. Revert to previous git commit
git checkout [previous_commit_hash]

# 3. Reinstall dependencies
pip install -r requirements.txt

# 4. Restart service
sudo systemctl start trading-system

# 5. Verify health
curl http://localhost:8001/health
```

---

## Support & Monitoring

### Real-time Monitoring Dashboard
- Access: `http://your-server:8001/api/live/summary`
- Updates: Real-time via WebSocket
- Metrics: Positions, P&L, Signals, Alerts

### Alert Configuration
Configure alerts for:
- System errors (ERROR and above)
- Portfolio heat exceeding limits
- Win rate below threshold
- WebSocket disconnections
- Database connection failures

### Escalation Procedure
1. Monitor alerts on dashboard
2. Check system logs
3. Verify API endpoints
4. Contact database administrator if needed
5. Execute rollback if necessary

---

## Success Metrics

After deployment, verify:

| Metric | Target | Status |
|--------|--------|--------|
| API Response Time | < 100ms | ✅ Monitor |
| WebSocket Latency | < 50ms | ✅ Monitor |
| System Uptime | 99.9% | ✅ Monitor |
| Error Rate | < 0.1% | ✅ Monitor |
| Database Queries | < 1000/min | ✅ Monitor |
| Active Connections | < 500 | ✅ Monitor |

---

## Additional Resources

- **Documentation**: `PHASE5_COMPLETION_REPORT.md`
- **Architecture**: `PHASE5_IMPLEMENTATION_PLAN.md`
- **API Documentation**: `http://localhost:8001/docs`
- **Project Configuration**: `.env.example`

---

**Deployment Status**: Ready for Production
**Version**: 1.0.0
**Last Updated**: 2025-10-25
