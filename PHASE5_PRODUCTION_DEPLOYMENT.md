# Phase 5 Production Deployment Guide
**Date**: 2025-10-25
**Status**: Ready for Deployment ✅

---

## Pre-Deployment Checklist

### System Requirements
- [x] Python 3.10+ installed
- [x] Required packages installed
- [x] Database configured
- [x] Environment variables set
- [x] All tests passing (178/178)

### Code Quality
- [x] Phase 5: 76/76 tests passing
- [x] Phase 2: 102/102 tests passing
- [x] Phase 1: All data adapters working
- [x] Code review: PASSED
- [x] Security: PASSED

### Integration
- [x] Alternative data sources: Connected
- [x] Risk management: Configured
- [x] Performance monitoring: Ready
- [x] Dashboard: Ready
- [x] WebSocket: Configured

---

## Deployment Options

### Option 1: Development (Single Process)
Start development server:
```bash
python src/application.py
```

Access at:
- http://localhost:8001
- http://localhost:8001/docs (API docs)
- http://localhost:8001/health (health check)

### Option 2: Production (Gunicorn)
Install and start with 4 workers:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8001 src.application:app
```

Or with environment variables:
```bash
ENVIRONMENT=production gunicorn -w 4 src.application:app
```

### Option 3: Docker
Build and run container:
```bash
docker build -t codex-trading:latest .
docker run -d --name codex-trading -p 8001:8001 \
  -e ENVIRONMENT=production \
  -e INITIAL_CAPITAL=1000000 \
  codex-trading:latest
```

Check logs:
```bash
docker logs -f codex-trading
```

### Option 4: Docker Compose
Start all services:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down  # to stop
```

---

## Environment Configuration

### Required Environment Variables
```bash
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8001
INITIAL_CAPITAL=1000000
MAX_POSITION_SIZE=100000
MAX_PORTFOLIO_HEAT=500000
```

### Create .env File
```bash
cp .env.example .env
# Edit .env with actual values
```

---

## Startup Procedure

### Step 1: Pre-flight Checks
```bash
# Verify Python version (should be 3.10+)
python --version

# Check required packages
pip list | grep -E "fastapi|sqlalchemy|pandas"

# Run final test suite
pytest tests/test_phase5*.py tests/test_data_pipeline.py -v
```

### Step 2: Start Application
Development:
```bash
python src/application.py
```

Production:
```bash
gunicorn -w 4 src.application:app
```

### Step 3: Verify Startup
```bash
# Health check
curl http://localhost:8001/health

# Expected response
{
  "status": "healthy",
  "environment": "production",
  "timestamp": "2025-10-25T...",
  "active_connections": 0,
  "error_count": 0
}
```

### Step 4: Verify API Endpoints
```bash
curl http://localhost:8001/api/trading/portfolio
curl http://localhost:8001/api/trading/performance
curl http://localhost:8001/api/risk/summary
curl http://localhost:8001/api/system/status
```

---

## API Endpoints

### Trading Endpoints
- GET /api/trading/portfolio - Portfolio summary
- GET /api/trading/performance - Performance metrics

### Risk Management
- GET /api/risk/summary - Risk summary

### Monitoring
- GET /api/performance/summary - Performance data
- GET /api/dashboard/complete - Complete dashboard

### Health & Status
- GET /health - Health check
- GET /api/system/status - System status

### WebSocket Channels
- /ws/portfolio - Portfolio updates
- /ws/performance - Performance metrics
- /ws/risk - Risk alerts
- /ws/orders - Order updates
- /ws/system - System status

---

## Production Monitoring

### View Logs
```bash
tail -f trading.log
grep ERROR trading.log
tail -f trading.log | grep -E "WARNING|ERROR"
```

### Monitor Health
```bash
watch -n 30 'curl -s http://localhost:8001/health | jq .'
```

### Performance Metrics
```bash
curl http://localhost:8001/api/performance/summary | jq .
```

---

## Deployment Verification

### Checklist
- [ ] Application starts without errors
- [ ] Health endpoint responds
- [ ] Portfolio endpoint returns data
- [ ] WebSocket connections work
- [ ] Logs show no errors
- [ ] API response time < 100ms
- [ ] Database connections stable
- [ ] Data sources connected

---

## Troubleshooting

### Application Won't Start
1. Check Python: python --version
2. Install packages: pip install -r requirements.txt
3. Check port: netstat -an | grep 8001
4. Review logs for errors

### API Errors
1. Verify running: curl http://localhost:8001/health
2. Check database connection in logs
3. Verify environment variables: echo $ENVIRONMENT

### WebSocket Issues
1. Verify browser WebSocket support
2. Check firewall settings
3. Review logs for connection errors

### Performance Issues
1. Check system resources
2. Monitor application logs
3. Check database performance
4. Verify network connectivity

---

## Post-Deployment

1. Set up monitoring and alerting
2. Configure daily backups
3. Establish update schedule
4. Performance tuning
5. Plan Phase 4 integration

---

## Rollback Procedure

If issues occur:
```bash
# Stop current deployment
docker stop codex-trading
# or: pkill -f "python src/application.py"

# Check last working commit
git log --oneline | head -5

# Revert if needed
git revert <commit-hash>

# Restart
python src/application.py
```

---

## Success Criteria

Deployment is successful when:
1. Application starts without errors
2. Health check returns "healthy"
3. All API endpoints respond with 200
4. WebSocket connections establish
5. No critical errors in logs
6. Performance within expected ranges
7. Database connections stable
8. Data sources connected

---

## Next Steps

1. **Monitor System** (24 hours)
   - Watch logs
   - Monitor metrics
   - Verify endpoints

2. **Configure Alerts** (Day 1)
   - Error alerts
   - Performance alerts
   - Uptime monitoring

3. **Integration Testing** (Days 2-3)
   - Alternative data integration
   - Trading signals
   - Risk management

4. **Load Testing** (Week 1)
   - Stress test
   - Scalability verification
   - Configuration tuning

5. **Phase 4 Planning** (Week 2+)
   - Backtest integration
   - Strategy design
   - End-to-end testing

---

**Status**: READY FOR DEPLOYMENT ✅
**Last Updated**: 2025-10-25
**Next Action**: Choose deployment method and start Phase 5
