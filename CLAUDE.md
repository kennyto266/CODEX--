# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 項目概述

這是一個基於多智能體協作的港股量化交易系統，集成了數據適配器、回測引擎、實時監控和Telegram機器人等功能模塊。系統使用Python 3.10+開發，採用FastAPI框架提供RESTful API，並實現了7個專業AI Agent協同工作的架構。

## 開發環境設置

### 必要依賴

```bash
# 創建並激活虛擬環境
python -m venv .venv310
.venv310\Scripts\activate  # Windows
source .venv310/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt

# 安裝測試依賴（可選）
pip install -r test_requirements.txt
```

### 環境配置

1. 複製環境變量模板：`cp .env.example .env`
2. 編輯 `.env` 文件，配置必要的API密鑰和數據庫連接
3. 主要配置項：
   - `API_HOST`, `API_PORT`: API服務配置
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Telegram集成
   - `DATA_SOURCE_URL`, `DATA_API_KEY`: 數據源配置

## 常用命令

### 啟動系統

```bash
# 方式1: 安全增強版（推薦用於生產環境）
python secure_complete_system.py

# 方式2: 完整系統版（推薦用於開發）
python complete_project_system.py

# 方式3: 統一系統版
python unified_quant_system.py

# 方式4: 簡單儀表板
python simple_dashboard.py

# 方式5: 使用部署腳本
python deploy.py
```

系統啟動後訪問：
- 主界面: http://localhost:8001
- API文檔: http://localhost:8001/docs
- 健康檢查: http://localhost:8001/api/health

### 測試

```bash
# 運行所有測試
python run_tests.py

# 使用pytest運行特定測試
pytest test_core_functions.py -v        # 核心功能測試
pytest test_api_endpoints.py -v        # API測試
pytest test_data_processing.py -v      # 數據處理測試

# 運行特定類型的測試
pytest -m unit                          # 單元測試
pytest -m integration                   # 集成測試
pytest -m api                          # API測試

# 生成覆蓋率報告
pytest --cov=. --cov-report=html
# 報告位於: htmlcov/index.html
```

### 策略回測與優化

```bash
# 運行策略回測
python enhanced_strategy_backtest.py

# 運行策略優化器
python enhanced_strategy_optimizer.py

# 特定股票的策略參數搜索
python scripts/param_search_0939.py
```

### Telegram機器人

```bash
# 啟動Telegram機器人
python start_telegram_bot.py

# 部署Telegram機器人
python deploy_telegram_bot.py

# 測試機器人連接
python test_bot_connection.py
```

### 數據庫初始化

```bash
# 初始化數據庫
python init_db.py
```

## 核心架構

### 多智能體系統 (src/agents/)

系統包含7個專業AI Agent，每個Agent負責特定的量化交易任務：

1. **Coordinator (coordinator.py)**: 協調所有Agent的工作流程
2. **Data Scientist (data_scientist.py)**: 數據分析和異常檢測
3. **Quantitative Analyst (quantitative_analyst.py)**: 量化分析和蒙特卡洛模擬
4. **Quantitative Engineer (quantitative_engineer.py)**: 系統監控和性能優化
5. **Portfolio Manager (portfolio_manager.py)**: 投資組合管理和風險預算
6. **Research Analyst (research_analyst.py)**: 策略研究和回測驗證
7. **Risk Analyst (risk_analyst.py)**: 風險評估和對沖策略

**Agent基類設計** (base_agent.py):
- 所有Agent繼承自 `BaseAgent` 抽象類
- 實現了消息隊列、心跳機制、錯誤處理和自動重啟
- 使用 `asyncio` 實現異步消息處理
- 通過 `MessageQueue` 進行Agent間通信

**Real Agents** (src/agents/real_agents/):
包含實際執行量化策略的增強Agent實現，集成了機器學習模型和高級分析功能。

### 數據適配器架構 (src/data_adapters/)

**設計模式**: 策略模式 + 工廠模式

所有數據適配器繼承自 `BaseAdapter`，提供統一的數據接口：

- `http_api_adapter.py`: HTTP API數據源適配器
- `raw_data_adapter.py`: 原始數據文件處理器
- `yahoo_finance_adapter.py`: Yahoo Finance API適配
- `alpha_vantage_adapter.py`: Alpha Vantage API適配
- `ccxt_crypto_adapter.py`: 加密貨幣數據適配

**關鍵方法**:
- `fetch_data(symbol, start_date, end_date)`: 獲取歷史數據
- `get_realtime_data(symbol)`: 獲取實時數據
- `validate_data(df)`: 數據驗證

### 回測引擎 (src/backtest/)

**核心組件**:
- `enhanced_backtest_engine.py`: 增強版回測引擎，支持多策略並行回測
- `base_backtest.py`: 回測基類定義
- `strategy_performance.py`: 策略性能評估模組
- `stockbacktest_adapter.py`: StockBacktest庫適配器

**回測流程**:
1. 數據準備 -> 2. 策略初始化 -> 3. 逐日回測 -> 4. 性能計算 -> 5. 結果可視化

**性能指標**:
- 總收益率、年化收益率
- Sharpe比率、Sortino比率
- 最大回撤、勝率
- VaR (Value at Risk)

### 儀表板系統 (src/dashboard/)

基於FastAPI的Web儀表板，提供實時監控和數據可視化：

- `api_routes.py`: API路由定義
- `websocket_manager.py`: WebSocket連接管理
- `agent_control.py`: Agent控制面板
- `performance_service.py`: 性能監控服務
- `strategy_data_service.py`: 策略數據服務

**WebSocket通信**:
系統使用WebSocket提供實時數據推送，客戶端可訂閱以下事件：
- Agent狀態更新
- 交易信號
- 性能指標變化

### 監控系統 (src/monitoring/)

- `performance_monitor.py`: 系統性能監控
- `health_checker.py`: 健康檢查
- `anomaly_detector.py`: 異常檢測
- `alert_manager.py`: 告警管理

### 風險管理 (src/risk_management/)

實現了完整的風險管理框架，包括：
- 倉位管理
- 止損/止盈策略
- 風險敞口計算
- 壓力測試

## 代碼風格與慣例

### Python編碼規範

- 遵循PEP 8規範
- 使用類型提示 (Type Hints)
- 每個模塊頂部包含docstring說明功能
- 複雜函數需要詳細的參數和返回值說明

### 異步編程

本項目大量使用 `asyncio` 進行異步編程：

```python
# Agent消息處理示例
async def process_message(self, message: Message) -> bool:
    """處理消息（必須是異步方法）"""
    try:
        # 處理邏輯
        return True
    except Exception as e:
        self.logger.error(f"處理失敗: {e}")
        return False
```

### 日誌記錄

使用Python標準logging模塊：

```python
import logging
logger = logging.getLogger("hk_quant_system.module_name")

logger.info("信息日誌")
logger.warning("警告日誌")
logger.error("錯誤日誌")
```

日誌文件位置: `quant_system.log`

## 重要文件說明

### 核心系統文件

- `complete_project_system.py`: 完整系統入口，集成所有功能模塊
- `secure_complete_system.py`: 安全增強版，添加了CORS、輸入驗證等安全功能
- `unified_quant_system.py`: 統一系統入口
- `simple_dashboard.py`: 簡化版儀表板

### 配置文件

- `requirements.txt`: Python依賴列表（包含TA-Lib、quantstats等量化庫）
- `pytest.ini`: 測試配置，設置了80%的覆蓋率要求
- `.env.example`: 環境變量模板
- `docker-compose.yml`: Docker部署配置

### 文檔文件

- `README.md`: 項目說明和快速開始指南
- `EXECUTION_GUIDE.md`: 詳細執行指南
- `PROJECT_COMPLETION_GUIDE.md`: 項目完成指南
- `FINAL_PROJECT_SUMMARY.md`: 項目總結
- `TEST_COVERAGE_REPORT.md`: 測試覆蓋率報告
- `TELEGRAM_BOT_README.md`: Telegram機器人使用說明
- `运行指南.md`: 中文運行指南

## 常見開發任務

### 添加新的Agent

1. 在 `src/agents/` 下創建新文件
2. 繼承 `BaseAgent` 類
3. 實現必須的抽象方法：
   - `initialize()`: 初始化邏輯
   - `process_message()`: 消息處理邏輯
   - `cleanup()`: 清理資源
4. 在 `coordinator.py` 中註冊新Agent

### 添加新的數據適配器

1. 在 `src/data_adapters/` 下創建新文件
2. 繼承 `BaseAdapter` 類
3. 實現數據獲取方法
4. 在 `data_service.py` 中註冊適配器

### 添加新的策略

1. 在 `src/strategies.py` 或 `src/enhanced_strategies.py` 中定義策略類
2. 實現 `generate_signals()` 方法
3. 在回測引擎中註冊策略
4. 使用 `enhanced_strategy_backtest.py` 進行回測驗證

### 修改API端點

1. 在 `src/dashboard/api_routes.py` 中添加新路由
2. 使用 `@app.get()` 或 `@app.post()` 裝飾器
3. 添加適當的錯誤處理
4. 更新API文檔（FastAPI自動生成）

## 特殊注意事項

### TA-Lib安裝

TA-Lib是技術分析庫，安裝可能較為複雜：

**Windows**:
1. 從 [此處](https://github.com/cgohlke/talib-build/releases) 下載對應Python版本的whl文件
2. 運行: `pip install TA_Lib‑0.4.XX‑cpXX‑cpXX‑win_amd64.whl`

**Linux**:
```bash
sudo apt-get install ta-lib
pip install TA-Lib
```

### 中文路徑問題

避免將項目放在包含中文的路徑下，可能導致某些模塊無法正常工作。

### 端口衝突

系統默認使用端口8001，如果被占用可通過命令行參數指定其他端口：
```bash
python complete_project_system.py --port 8002
```

### Agent通信機制

Agent之間通過 `MessageQueue` 進行通信，消息類型包括：
- `CONTROL`: 控制消息（啟動、停止、重啟）
- `DATA`: 數據消息
- `SIGNAL`: 交易信號
- `HEARTBEAT`: 心跳消息

發送消息示例：
```python
await self.broadcast_message(
    message_type="SIGNAL",
    content={"symbol": "0700.HK", "action": "BUY"}
)
```

### 性能優化建議

1. **數據緩存**: 系統使用LRU緩存減少重複API調用
2. **向量化計算**: 使用Pandas向量化操作代替循環
3. **異步I/O**: 對於I/O密集操作使用async/await
4. **並行回測**: 使用多進程進行策略並行回測

## 部署

### Docker部署

```bash
# 構建鏡像
docker build -t codex-quant-system .

# 運行容器
docker run -p 8001:8001 -v $(pwd)/.env:/app/.env codex-quant-system
```

### 使用docker-compose

```bash
docker-compose up -d
```

### 生產環境建議

1. 使用 `secure_complete_system.py` 版本
2. 配置反向代理（Nginx/Apache）
3. 啟用HTTPS
4. 設置日誌輪轉
5. 配置系統監控和告警
6. 定期備份數據庫

## 故障排除

### Agent無法啟動

檢查日誌文件 `quant_system.log`，常見原因：
- 端口被占用
- 依賴庫未安裝
- 環境變量未配置

### API連接失敗

1. 檢查網絡連接
2. 驗證API密鑰是否正確
3. 查看防火墻設置

### 測試失敗

1. 確保已安裝測試依賴: `pip install -r test_requirements.txt`
2. 檢查測試數據是否存在
3. 查看具體錯誤信息並針對性修復

## 參考資源

- FastAPI文檔: https://fastapi.tiangolo.com/
- Pandas文檔: https://pandas.pydata.org/docs/
- TA-Lib文檔: https://mrjbq7.github.io/ta-lib/
- Asyncio文檔: https://docs.python.org/3/library/asyncio.html
