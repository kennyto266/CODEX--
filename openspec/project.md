# Project Context

## Purpose
CODEX is a multi-agent quantitative trading system for Hong Kong stocks. It integrates data adapters, backtesting engines, real-time monitoring, and Telegram bot functionality. The system features 7 specialized AI agents that collaborate to analyze data, manage portfolios, assess risks, and execute trading strategies.

## Tech Stack
- **Language**: Python 3.10+
- **Web Framework**: FastAPI (RESTful API with automatic OpenAPI documentation)
- **Data Processing**: Pandas, NumPy (vectorized operations)
- **Technical Analysis**: TA-Lib
- **Machine Learning**: scikit-learn, TensorFlow/PyTorch (for enhanced agents)
- **Async Framework**: asyncio for agent communication
- **Database**: SQLAlchemy (configurable backends)
- **Real-time Communication**: WebSocket for dashboard updates
- **Testing**: pytest with 80% coverage requirement
- **Deployment**: Docker, docker-compose
- **Monitoring**: Prometheus metrics, custom performance monitors
- **Quantitative Libraries**: quantstats, vectorbt

## Project Conventions

### Code Style
- Follow PEP 8 coding standards strictly
- Use type hints (Type Hints) for all function signatures
- Every module must include a docstring at the top explaining its purpose
- Complex functions require detailed parameter and return value documentation
- Use English for code and comments, Chinese for user-facing documentation
- Avoid Chinese characters in file paths (can cause module loading issues)

### Architecture Patterns
- **Multi-Agent System**: All agents inherit from `BaseAgent` abstract class (src/agents/base_agent.py)
- **Message Queue Pattern**: Agents communicate via `MessageQueue` with message types: CONTROL, DATA, SIGNAL, HEARTBEAT
- **Strategy Pattern**: Data adapters inherit from `BaseAdapter` for unified data interfaces
- **Factory Pattern**: Adapter registration and instantiation in data_service.py
- **Async-First**: Extensive use of `async`/`await` for I/O operations and agent communication
- **LRU Caching**: Used throughout to reduce redundant API calls
- **Vectorization**: Prefer Pandas vectorized operations over Python loops

### Testing Strategy
- 80% minimum test coverage requirement (configured in pytest.ini)
- Three test levels:
  - Unit tests: Individual functions and classes
  - Integration tests: API endpoints and agent interactions
  - API tests: Full request/response cycles
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.api`
- Test files: test_core_functions.py, test_api_endpoints.py, test_data_processing.py
- Run with: `pytest -v` or `python run_tests.py`
- Coverage reports: `pytest --cov=. --cov-report=html` (outputs to htmlcov/)

### Git Workflow
- Main branch: `main`
- Commit messages should be concise (1-2 sentences) focusing on "why" rather than "what"
- Avoid force push to main/master
- Never use `git commit --amend` unless explicitly requested or fixing pre-commit hook changes
- Never use interactive git commands (`git rebase -i`, `git add -i`) in automated contexts

## Domain Context

### Quantitative Trading Concepts
- **港股市場**: Hong Kong stock market (stocks identified as XXXX.HK, e.g., 0700.HK for Tencent)
- **回測 (Backtesting)**: Historical strategy validation using past market data
- **夏普比率 (Sharpe Ratio)**: Risk-adjusted return metric
- **最大回撤 (Maximum Drawdown)**: Largest peak-to-trough decline
- **VaR (Value at Risk)**: Potential loss estimation
- **蒙特卡洛模擬 (Monte Carlo Simulation)**: Risk assessment through random sampling

### System Components
1. **7 AI Agents** (src/agents/):
   - Coordinator: Orchestrates workflow
   - Data Scientist: Data analysis, anomaly detection
   - Quantitative Analyst: Quant analysis, Monte Carlo simulations
   - Quantitative Engineer: System monitoring, performance optimization
   - Portfolio Manager: Portfolio management, risk budgeting
   - Research Analyst: Strategy research, backtest validation
   - Risk Analyst: Risk assessment, hedging strategies

2. **Data Adapters** (src/data_adapters/):
   - Multiple data sources: Yahoo Finance, Alpha Vantage, CCXT (crypto), HTTP API, raw files
   - Unified interface through BaseAdapter

3. **Backtest Engine** (src/backtest/):
   - Supports parallel multi-strategy backtesting
   - Comprehensive performance metrics
   - Result visualization

4. **Dashboard** (src/dashboard/):
   - FastAPI-based web interface
   - WebSocket for real-time updates
   - Agent control panel

5. **Monitoring** (src/monitoring/):
   - Performance monitoring, health checks, anomaly detection, alert management

## Important Constraints

### Technical Constraints
- **TA-Lib Installation**: Requires pre-compiled binaries on Windows (see CLAUDE.md for instructions)
- **Chinese Path Issue**: Avoid placing project in paths containing Chinese characters
- **Port Conflicts**: Default port 8001, configurable via command-line argument
- **Async Requirements**: All agent message processing must be async methods
- **Logging**: Centralized logging to `quant_system.log` using Python's logging module

### Performance Requirements
- Data caching with LRU to minimize API calls
- Vectorized calculations preferred over loops
- Parallel backtesting for strategy optimization

### Security Requirements
- Production deployment must use `secure_complete_system.py` with CORS, input validation
- API keys stored in `.env` file (never commit to git)
- HTTPS required for production

## External Dependencies

### Data Sources
- **Yahoo Finance**: Primary free data source for Hong Kong stocks
- **Alpha Vantage**: Alternative market data provider (API key required)
- **CCXT**: Cryptocurrency exchange data
- **Custom HTTP APIs**: Configurable via DATA_SOURCE_URL in .env

### Integrations
- **Telegram Bot**: Real-time alerts and notifications
  - Configure: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID in .env
  - Scripts: start_telegram_bot.py, deploy_telegram_bot.py

### Infrastructure
- **Docker/Docker Compose**: Container deployment (docker-compose.yml)
- **Prometheus**: Metrics collection (optional)
- **Redis**: Caching layer (optional, for production)

### Key Files Reference
- Main entry points: complete_project_system.py, secure_complete_system.py, unified_quant_system.py
- Configuration: .env (from .env.example), requirements.txt
- Documentation: CLAUDE.md (this file), EXECUTION_GUIDE.md, README.md
- Testing: pytest.ini, run_tests.py, test_*.py files
