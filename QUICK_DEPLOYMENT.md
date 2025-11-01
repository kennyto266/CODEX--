# Quick Deployment Reference - Phase 5

**Deployment Time**: 30-45 minutes
**Complexity**: Medium
**Status**: Production-Ready

---

## 5-Minute Quick Start

### 1. Environment Setup

```bash
# Activate virtual environment
.venv310\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy and configure .env
cp .env.example .env

# Edit .env with your values
# - ENVIRONMENT=production
# - DB_HOST, DB_USER, DB_PASSWORD
# - LOG_LEVEL=INFO or WARNING
```

### 3. Test

```bash
# Run all Phase 5 tests
python -m pytest tests/test_phase5*.py -v

# Should show: 76 passed ✅
```

### 4. Deploy

```bash
# Option A: Development
python src/application.py

# Option B: Production
gunicorn -w 4 -b 0.0.0.0:8001 src.application:app

# Option C: Docker
docker build -t trading:latest .
docker run -d -p 8001:8001 --env-file .env trading:latest
```

### 5. Verify

```bash
# Test API
curl http://localhost:8001/health

# Should return: {"status": "healthy", ...}
```

---

## Essential Commands

### Testing
```bash
pytest tests/test_phase5_realtime.py -v       # Trading engine
pytest tests/test_phase5_dashboard.py -v      # Dashboard
pytest tests/test_phase5_production.py -v     # Production setup
pytest tests/test_phase5*.py -v               # All Phase 5 tests
```

### Running
```bash
python src/application.py                     # Development
uvicorn src.application:app --port 8001       # Uvicorn
gunicorn -w 4 src.application:app             # Production (4 workers)
```

### Monitoring
```bash
curl http://localhost:8001/health             # Health check
curl http://localhost:8001/api/system/status  # System status
curl http://localhost:8001/api/trading/portfolio  # Portfolio
tail -f logs/trading_system.log               # Live logs
tail -f logs/errors.log                       # Error logs
```

### Database
```bash
python init_db.py                             # Initialize
psql -U postgres -d trading_system            # Connect
```

---

## Environment Variables

### Minimal Required
```env
ENVIRONMENT=production
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=trading_system
LOG_DIR=logs
API_PORT=8001
```

### Full Configuration
See `.env.example` for all available options

---

## Deployment Paths

### Path 1: Development
```
Virtual Env → .env (dev) → python app.py
```

### Path 2: Linux Server
```
Virtual Env → .env (prod) → Systemd Service
```

### Path 3: Docker
```
Dockerfile → Docker Image → Docker Container
```

### Path 4: Kubernetes
```
Docker Image → K8s Deployment → K8s Service
```

---

## Verification Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (pip list | grep fastapi)
- [ ] .env file configured
- [ ] Database connected (python init_db.py)
- [ ] All tests pass (76/76)
- [ ] API responds (curl /health)
- [ ] Logs created (ls -la logs/)

---

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/system/status` | GET | System status |
| `/api/trading/portfolio` | GET | Portfolio summary |
| `/api/trading/performance` | GET | Performance metrics |
| `/api/risk/summary` | GET | Risk summary |
| `/api/live/signals` | GET | Recent signals |
| `/api/live/summary` | GET | Dashboard summary |
| `/api/live/ws/portfolio` | WS | Live positions |

---

## Troubleshooting Quick Fix

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Database connection failed` | Check .env DB variables |
| `Port 8001 in use` | Change `API_PORT` in .env |
| `Permission denied (logs)` | `mkdir logs && chmod 777 logs` |
| `Tests failing` | Run from project root directory |
| `WebSocket errors` | Check firewall port 8001 |

---

## Performance Tips

- Use `API_WORKERS=4+` for production
- Enable `CACHE_ENABLED=true`
- Set `DB_POOL_SIZE=20` for concurrency
- Use `LOG_LEVEL=WARNING` in production
- Monitor with `/api/system/status`

---

## Security Checklist

- [ ] .env not committed to git
- [ ] Database password strong (20+ chars)
- [ ] API_HOST=0.0.0.0 → restricted via firewall
- [ ] HTTPS enabled (for production)
- [ ] SSL certificates valid
- [ ] Regular backups configured
- [ ] Access logs reviewed weekly

---

## Support

**Detailed Guide**: `PHASE5_DEPLOYMENT_GUIDE.md`
**Completion Report**: `PHASE5_COMPLETION_REPORT.md`
**Implementation Plan**: `PHASE5_IMPLEMENTATION_PLAN.md`

---

**Status**: ✅ Production-Ready
**Last Updated**: 2025-10-25
**Version**: 1.0.0
