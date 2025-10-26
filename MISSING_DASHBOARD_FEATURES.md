# Dashboard 未實現功能清單

**日期**: 2025-10-26
**狀態**: 功能對比分析

---

## 已實現的前端功能 ✅

### 1. Stock Selector (股票選擇器)
- ✅ 股票代碼輸入
- ✅ 實時股票數據顯示 (連接真實 HKEX API)
- ✅ 價格變化顯示
- ✅ 市值顯示

### 2. System Metrics (系統指標)
- ✅ Initial Capital (初始資本)
- ✅ Portfolio Value (投資組合價值)
- ✅ Active Positions (活躍持倉)
- ✅ Total Return (總回報)

### 3. Quick Actions (快速操作)
- ✅ API Documentation 連結
- ✅ Health Check 連結
- ✅ Refresh Metrics 按鈕
- ✅ Complete Dashboard 連結

### 4. System Status (系統狀態)
- ✅ 系統運行狀態指示器
- ✅ 系統狀態 API 調用

### 5. API Endpoint 列表
- ✅ REST API 端點列表
- ✅ WebSocket 端點列表 (僅顯示，未實現連接)

---

## 系統中存在但未在前端實現的功能 ❌

### A. 回測系統 (Backtest System)

**相關文件**:
- `src/backtest/enhanced_backtest_engine.py` (27KB)
- `src/backtest/real_data_backtest.py` (18KB)
- `src/backtest/parameter_optimizer.py` (15KB)
- `src/backtest/signal_validation.py` (21KB)
- `src/backtest/vectorbt_engine.py` (15KB)

**功能**:
- 策略回測引擎
- 參數優化器
- 多策略並行回測
- 性能指標計算 (Sharpe Ratio, Sortino Ratio, Max Drawdown 等)
- 信號驗證
- VectorBT 集成

**缺失的前端功能**:
- [ ] 回測配置界面 (選擇策略、時間範圍、初始資本)
- [ ] 回測結果展示 (折線圖、表格)
- [ ] 參數優化界面
- [ ] 策略對比工具
- [ ] 回測報告生成

**潛在 API 端點需要實現**:
```
POST /api/backtest/run
GET /api/backtest/results/{backtest_id}
POST /api/backtest/optimize
GET /api/backtest/strategies
GET /api/backtest/compare
```

---

### B. AI Agent 系統

**相關文件**:
- `src/agents/coordinator.py` - 協調所有 Agent
- `src/agents/data_scientist.py` - 數據分析 Agent
- `src/agents/quantitative_analyst.py` - 量化分析 Agent
- `src/agents/quantitative_engineer.py` - 系統監控 Agent
- `src/agents/portfolio_manager.py` - 投資組合管理 Agent
- `src/agents/research_analyst.py` - 策略研究 Agent
- `src/agents/risk_analyst.py` - 風險分析 Agent

**功能**:
- 7 個專業 AI Agent 協同工作
- 消息隊列通信機制
- 心跳監控
- 自動重啟機制
- 異步消息處理

**缺失的前端功能**:
- [ ] Agent 管理界面 (啟動/停止/重啟)
- [ ] Agent 狀態監控 (在線/離線/故障)
- [ ] Agent 工作日誌顯示
- [ ] Agent 性能指標 (CPU、內存、消息處理速度)
- [ ] Agent 通信可視化

**潛在 API 端點需要實現**:
```
GET /api/agents/list
GET /api/agents/{agent_id}/status
POST /api/agents/{agent_id}/start
POST /api/agents/{agent_id}/stop
GET /api/agents/{agent_id}/logs
GET /api/agents/{agent_id}/metrics
GET /api/agents/communication
```

---

### C. 風險管理系統

**相關文件**:
- `src/agents/portfolio_manager/risk_budget.py` - 風險預算
- `src/risk_management/` 目錄 (完整的風險管理框架)
- `src/backtest/signal_attribution_metrics.py` - 信號歸因指標

**功能**:
- 倉位管理
- 止損/止盈策略
- 風險敞口計算
- VaR (Value at Risk) 計算
- 壓力測試
- 風險預算分配

**缺失的前端功能**:
- [ ] 風險儀表板 (詳細的風險指標)
- [ ] 倉位管理界面 (查看、添加、關閉倉位)
- [ ] 風險警告顯示 (超過風險閾值時)
- [ ] VaR 可視化
- [ ] 壓力測試結果展示
- [ ] 風險熱力圖

**潛在 API 端點需要實現**:
```
GET /api/risk/portfolio
GET /api/risk/var
GET /api/risk/alerts
GET /api/risk/positions
POST /api/risk/stress-test
GET /api/risk/heatmap
```

---

### D. 另類數據系統

**相關文件**:
- `gov_crawler/` 目錄 - 數據爬蟲
- `src/backtest/alt_data_backtest_extension.py` - 另類數據回測
- `src/data_adapters/alternative_data_adapter.py` - 另類數據適配器

**功能**:
- HIBOR 利率數據
- 房產市場數據
- 零售銷售數據
- GDP 指標
- 訪客數據
- 貿易數據
- 流量數據
- MTR 乘客數據
- 邊境通行數據

**缺失的前端功能**:
- [ ] 另類數據儀表板
- [ ] 數據源選擇器
- [ ] 數據時間序列圖表
- [ ] 相關性分析顯示
- [ ] 交易信號結合另類數據

**潛在 API 端點需要實現**:
```
GET /api/alternative-data/list
GET /api/alternative-data/{source}
GET /api/alternative-data/correlation
GET /api/alternative-data/signals
```

---

### E. 策略管理系統

**相關文件**:
- `src/strategies.py` - 基本策略
- `src/enhanced_strategies.py` - 增強策略
- `enhanced_strategy_backtest.py` - 策略回測 (11 種指標)

**功能**:
- 11 種技術指標支持
  - MA (移動平均)
  - RSI (相對強度)
  - MACD (指數平滑)
  - BB (布林帶)
  - KDJ (隨機指標)
  - CCI (商品通道)
  - ADX (趨勢強度)
  - ATR (波動率)
  - OBV (能量潮)
  - Ichimoku (雲圖)
  - Parabolic SAR (轉向點)
- 參數優化 (1000+ 種組合)
- 多策略並行執行

**缺失的前端功能**:
- [ ] 策略列表頁面 (查看所有可用策略)
- [ ] 策略詳情頁面 (參數配置、回測結果)
- [ ] 策略性能對比
- [ ] 技術指標可視化 (在價格圖表上疊加)
- [ ] 參數優化界面
- [ ] 策略信號顯示

**潛在 API 端點需要實現**:
```
GET /api/strategies/list
GET /api/strategies/{strategy_id}
POST /api/strategies/create
GET /api/strategies/{strategy_id}/performance
GET /api/strategies/{strategy_id}/signals
POST /api/strategies/{strategy_id}/optimize
```

---

### F. 交易執行系統

**相關文件**:
- `src/core/execution_engine.py` - 執行引擎
- `src/agents/portfolio_manager.py` - 投資組合管理

**功能**:
- 訂單執行
- 倉位跟蹤
- 交易歷史記錄
- 成交確認

**缺失的前端功能**:
- [ ] 交易界面 (買/賣表單)
- [ ] 訂單列表 (待處理、已成交、已取消)
- [ ] 實時成交價格顯示
- [ ] 交易歷史表格
- [ ] 倉位明細列表
- [ ] 訂單修改/取消功能

**潛在 API 端點需要實現**:
```
POST /api/trading/order
GET /api/trading/orders
GET /api/trading/positions
PUT /api/trading/orders/{order_id}
DELETE /api/trading/orders/{order_id}
GET /api/trading/history
```

---

### G. 性能分析系統

**相關文件**:
- `src/backtest/strategy_performance.py`
- `src/backtest/vectorbt_metrics.py`

**功能**:
- 詳細的性能指標計算
- 風險調整收益率 (Sharpe, Sortino)
- 回撤分析
- 勝率統計
- 盈虧比分析

**缺失的前端功能**:
- [ ] 性能指標儀表板 (更詳細的指標)
- [ ] 月度/年度收益率表
- [ ] 回撤曲線圖
- [ ] 收益分佈直方圖
- [ ] 月份熱力圖 (月度收益)
- [ ] 對標指數對比

**潛在 API 端點需要實現**:
```
GET /api/performance/detailed
GET /api/performance/monthly
GET /api/performance/drawdown
GET /api/performance/distribution
GET /api/performance/benchmark
```

---

### H. 實時監控系統

**相關文件**:
- `src/monitoring/` 目錄
- `src/agents/quantitative_engineer.py` - 性能監控

**功能**:
- 系統性能監控 (CPU、內存、磁盤)
- 健康檢查
- 異常檢測
- 告警管理

**缺失的前端功能**:
- [ ] 系統性能圖表 (CPU、內存、磁盤使用率趨勢)
- [ ] 實時日誌流 (系統、錯誤日誌)
- [ ] 告警列表和歷史
- [ ] 系統健康指標詳情
- [ ] 異常事件日誌

**潛在 API 端點需要實現**:
```
GET /api/monitoring/metrics
GET /api/monitoring/logs
GET /api/monitoring/alerts
GET /api/monitoring/health
```

---

## 優先級建議 🎯

### 高優先級 (1-2 週)
1. **回測系統** - 最重要，用戶迫切需要
2. **風險管理儀表板** - 生產環境必需
3. **Agent 控制界面** - 系統管理必需

### 中優先級 (2-3 週)
4. **策略管理系統** - 提高易用性
5. **交易執行界面** - 實現完整交易流程
6. **性能分析增強** - 詳細的性能指標

### 低優先級 (3-4 週)
7. **另類數據儀表板** - 增強分析能力
8. **實時監控系統** - 提高可操作性

---

## 技術實現路線圖

### 第 1 階段: 回測系統集成 (1 週)

**後端**:
```python
# 新增 API 端點 (src/dashboard/api_routes.py)
@app.post("/api/backtest/run")
async def run_backtest(config: BacktestConfig):
    # 調用 enhanced_backtest_engine
    return backtest_results

@app.get("/api/backtest/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    # 返回回測結果
    return results
```

**前端**:
```html
<!-- 新增回測界面 -->
<div class="backtest-section">
    <form>
        <select name="strategy">...</select>
        <input type="date" name="start_date">
        <input type="date" name="end_date">
        <input type="number" name="initial_capital">
        <button onclick="runBacktest()">運行回測</button>
    </form>
    <div id="backtest-results">
        <!-- 結果展示 -->
    </div>
</div>
```

### 第 2 階段: Agent 控制系統 (1 週)

**後端**:
```python
@app.get("/api/agents/list")
async def list_agents():
    return agent_manager.get_all_agents()

@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    return agent_manager.start_agent(agent_id)
```

**前端**:
```html
<!-- Agent 管理界面 -->
<div class="agents-grid">
    <div class="agent-card" v-for="agent in agents">
        <h3>{{ agent.name }}</h3>
        <p>Status: {{ agent.status }}</p>
        <button @click="startAgent(agent.id)">Start</button>
        <button @click="stopAgent(agent.id)">Stop</button>
    </div>
</div>
```

### 第 3 階段: 風險管理儀表板 (1 週)

**後端**:
```python
@app.get("/api/risk/portfolio")
async def get_risk_portfolio():
    return risk_manager.calculate_portfolio_risk()

@app.get("/api/risk/var")
async def calculate_var(confidence: float = 0.95):
    return risk_manager.calculate_var(confidence)
```

---

## 文件大小統計

| 功能模塊 | 代碼文件 | 代碼量 | 前端實現 |
|---------|---------|-------|---------|
| 回測系統 | 8+ 文件 | ~120KB | ❌ 0% |
| Agent 系統 | 7+ 文件 | ~50KB | ❌ 0% |
| 風險管理 | 5+ 文件 | ~40KB | ❌ 5% |
| 另類數據 | 4+ 文件 | ~35KB | ❌ 0% |
| 策略系統 | 6+ 文件 | ~80KB | ❌ 0% |
| 交易執行 | 3+ 文件 | ~25KB | ❌ 0% |
| 性能分析 | 4+ 文件 | ~35KB | ⚠️ 20% |
| 監控系統 | 3+ 文件 | ~20KB | ❌ 0% |
| **總計** | **40+ 文件** | **~385KB** | **~5%** |

---

## 結論

儀表板前端目前實現了 **約 5-10% 的系統功能**，主要集中在：
- 基本信息展示 (股票、指標)
- API 文檔和狀態檢查
- 實時數據連接

但系統中有豐富的後端功能尚未在前端展現：
- 回測和策略優化
- AI Agent 管理
- 詳細的風險分析
- 完整的交易執行
- 實時監控和告警

建議按優先級逐步實現這些功能，以提升用戶體驗和系統可用性。

---

**生成日期**: 2025-10-26
**狀態**: 功能缺口分析完成
