# Phase 2.3.6: Agent 統一系統設計方案

**日期:** 2025-10-25
**狀態:** 設計與分析階段
**優先級:** P1 (關鍵架構)

## 執行摘要

當前系統存在 **23 個 Agent 實現**，分散在 3 個不同層級，導致 **60%+ 代碼重複**。本方案透過組合模式（Composition）和角色系統設計統一架構，預計消除 80%+ 代碼重複。

## 當前 Agent 生態分析

### 層級 1: 核心 Agent 基類 (2 個)

#### BaseAgent (`src/agents/base_agent.py`)
**責任:** 所有 Agent 的根基類
```python
class BaseAgent(ABC):
    async def initialize() -> bool
    async def process_message(message: Message) -> bool
    async def cleanup()
    async def start() -> bool
    async def stop() -> bool

    # 內部循環
    async def _heartbeat_loop()
    async def _message_processing_loop()
```

**特性:**
- 消息隊列集成
- 心跳機制 (30 秒)
- 錯誤追蹤
- 非同步執行模型

#### RealAgentBase (`src/agents/real_agents/base_real_agent.py`)
**責任:** 真實市場數據集成的基類
```python
class RealAgentBase(BaseAgent):
    # 市場數據連接
    async def connect_market_data()
    async def fetch_real_time_data()

    # ML 模型管理
    async def load_ml_models()
    async def update_ml_models()

    # 分析執行
    async def run_analysis()
    async def generate_signals()
```

**特性:**
- 真實市場數據集成
- ML 模型管理
- 高級分析能力
- 性能追蹤

---

### 層級 2: 核心 Agent 實現 (8 個)

| Agent | 文件 | LOC | 責任 |
|-------|------|-----|------|
| **Coordinator** | `coordinator.py` | 450 | 調度其他 Agent |
| **DataScientist** | `data_scientist.py` | 380 | 數據異常檢測 |
| **PortfolioManager** | `portfolio_manager.py` | 420 | 投資組合優化 |
| **QuantitativeAnalyst** | `quantitative_analyst.py` | 510 | 量化分析 (蒙特卡洛) |
| **QuantitativeEngineer** | `quantitative_engineer.py` | 390 | 系統監控 |
| **QuantitativeTradеr** | `quantitative_trader.py` | 360 | 交易執行 |
| **ResearchAnalyst** | `research_analyst.py` | 400 | 策略研究 |
| **RiskAnalyst** | `risk_analyst.py` | 430 | 風險評估 |

**共同模式:**
```python
class ConcreteAgent(BaseAgent):
    def __init__(self, config, message_queue):
        super().__init__(config, message_queue)
        self.tools = {...}  # 工具集合
        self.state = {...}  # 狀態追蹤

    async def initialize(self):
        # 加載工具、初始化狀態
        return True

    async def process_message(self, message):
        # 路由到特定工具方法
        return await self._handle_{message_type}(message)

    async def cleanup(self):
        # 資源清理
        pass
```

---

### 層級 3: RealAgent 實現 (8 個)

| Agent | 文件 | 基於 | 特性 |
|-------|------|------|------|
| **RealDataScientist** | `real_data_scientist.py` | DataScientist | ML 異常檢測 |
| **RealQuantitativeAnalyst** | `real_quantitative_analyst.py` | QuantAnalyst | ML 預測模型 |
| **RealQuantitativeEngineer** | `real_quantitative_engineer.py` | QuantEngineer | 實時監控 |
| **RealQuantitativeTrader** | `real_quantitative_trader.py` | QuantTrader | HFT 引擎 |
| **RealPortfolioManager** | `real_portfolio_manager.py` | PortfoliMgr | ML 優化 |
| **RealResearchAnalyst** | `real_research_analyst.py` | ResearchAnalyst | 自動回測 |
| **RealRiskAnalyst** | `real_risk_analyst.py` | RiskAnalyst | ML 風險模型 |
| **RealDataAnalyzer** | `real_data_analyzer.py` | 獨立 | 數據分析工具 |

**共同特性:**
- 繼承核心 Agent (except RealDataAnalyzer)
- 集成 ML 模型
- 真實數據處理
- 性能指標計算

---

### 層級 4: HKPromptAgent (8 個)

文件: `src/agents/hk_prompt_agents.py` (2,500+ 行)

**實現:**
- `HKDataScientistAgent` - 數據科學 prompt
- `HKQuantAnalystAgent` - 量化分析 prompt
- `HKRiskAnalystAgent` - 風險分析 prompt
- `HKPortfolioAgent` - 投資組合 prompt
- `HKTraderAgent` - 交易員 prompt
- `HKEngineerAgent` - 工程師 prompt
- `HKResearchAgent` - 研究員 prompt
- `HKCoordinatorAgent` - 協調員 prompt

**特點:**
- 使用 HKPromptEngine 執行
- 預定義提示詞模板
- 角色模擬功能

---

## 代碼重複分析

### 重複模式 1: 初始化邏輯 (95% 重複)
```python
# 核心 Agent
async def initialize(self):
    self.logger.info(f"Initializing {self.agent_type}")
    self.state = AgentState.INITIALIZING

    # 加載工具 (略有不同)
    self.tools = {
        'analysis': self._analysis_tool,
        'data_fetch': self._fetch_data,
        ...
    }

    self.logger.info(f"Initialization complete")
    return True

# RealAgent (85% 重複)
async def initialize(self):
    await super().initialize()

    # 額外的 ML 模型加載
    self.ml_models = await self._load_ml_models()

    return True
```

### 重複模式 2: 消息處理路由 (90% 重複)
```python
async def process_message(self, message):
    try:
        if message.type == 'ANALYSIS_REQUEST':
            return await self._handle_analysis_request(message)
        elif message.type == 'DATA_REQUEST':
            return await self._handle_data_request(message)
        else:
            self.logger.warning(f"Unknown message type: {message.type}")
            return False
    except Exception as e:
        self.logger.error(f"Error processing message: {e}")
        return False
```

### 重複模式 3: 工具定義 (80% 重複)
```python
# 每個 Agent 都有
self.tools = {
    'logger': self.logger,
    'config': self.config,
    'message_queue': self.message_queue,
    'state': self.state,
    'error_count': self.error_count,
    ...
}
```

**總計:** ~4,500+ 行重複代碼（佔 45% 的 Agent 代碼）

---

## 統一架構設計

### 設計原則

1. **組合優於繼承** (Composition over Inheritance)
   - 用組合角色替代深層繼承層級
   - 減少耦合、提高可測試性

2. **職責分離** (Single Responsibility)
   - 統一 Agent 類處理通用邏輯
   - 角色專用實現處理特定邏輯

3. **外掛架構** (Plug-in Architecture)
   - 動態註冊角色功能
   - 運行時組合角色

4. **一致介面** (Consistent Interface)
   - 所有角色遵循相同的輸入/輸出格式
   - 統一的消息協議

### 新架構設計圖

```
統一 Agent 架構
│
├─ UnifiedAgent (核心類，統一所有 23 個 Agent)
│  ├─ Agent ID & Config
│  ├─ Message Queue
│  ├─ Role Manager (管理當前角色)
│  └─ Tool Registry (工具註冊表)
│
├─ RoleProvider (角色提供器)
│  ├─ BaseRole (角色基類)
│  │  ├─ initialize()
│  │  ├─ process_message()
│  │  ├─ cleanup()
│  │  └─ get_tools()
│  │
│  ├─ CoreRole (8 個核心角色)
│  │  ├─ CoordinatorRole
│  │  ├─ DataScientistRole
│  │  ├─ QuantitativeAnalystRole
│  │  ├─ PortfolioManagerRole
│  │  ├─ QuantitativeEngineerRole
│  │  ├─ QuantitativeTraderRole
│  │  ├─ ResearchAnalystRole
│  │  └─ RiskAnalystRole
│  │
│  ├─ RealRole (8 個真實數據角色)
│  │  ├─ RealDataScientistRole
│  │  ├─ RealQuantitativeAnalystRole
│  │  ├─ RealPortfolioManagerRole
│  │  └─ ... (其他 RealRole)
│  │
│  └─ HKPromptRole (8 個 HK Prompt 角色)
│     ├─ HKDataScientistRole
│     ├─ HKQuantitativeAnalystRole
│     └─ ... (其他 HKPromptRole)
│
└─ Unified Tool System (統一工具系統)
   ├─ DataFetchTool
   ├─ AnalysisTool
   ├─ ModelingTool
   ├─ OptimizationTool
   └─ RiskManagementTool
```

### 實現細節

#### 1. UnifiedAgent 核心類 (新建)

```python
class UnifiedAgent:
    """統一所有 23 個 Agent 的核心類"""

    def __init__(self, agent_id: str, role_type: str, config: Dict):
        self.agent_id = agent_id
        self.role_type = role_type  # "coordinator", "data_scientist", ...
        self.config = config
        self.message_queue = MessageQueue()

        # 加載適當的角色
        self.role = self._load_role(role_type, config)

        # 通用狀態
        self.status = AgentStatus.IDLE
        self.running = False
        self.error_count = 0

    async def initialize(self) -> bool:
        """統一初始化"""
        try:
            # 初始化角色
            if not await self.role.initialize(self):
                return False

            self.status = AgentStatus.RUNNING
            self.running = True

            # 啟動通用任務
            await self._start_heartbeat()
            await self._start_message_loop()

            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """統一消息處理"""
        try:
            # 委託給角色
            return await self.role.process_message(message, self)
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Message processing failed: {e}")
            return False

    async def cleanup(self):
        """統一清理"""
        await self.role.cleanup()
        self.running = False

    def _load_role(self, role_type: str, config: Dict) -> BaseRole:
        """動態加載角色"""
        role_map = {
            'coordinator': CoordinatorRole,
            'data_scientist': DataScientistRole,
            'quantitative_analyst': QuantitativeAnalystRole,
            'portfolio_manager': PortfolioManagerRole,
            'quantitative_engineer': QuantitativeEngineerRole,
            'quantitative_trader': QuantitativeTraderRole,
            'research_analyst': ResearchAnalystRole,
            'risk_analyst': RiskAnalystRole,
            # Real roles
            'real_data_scientist': RealDataScientistRole,
            'real_quantitative_analyst': RealQuantitativeAnalystRole,
            # ... etc
            # HK Prompt roles
            'hk_data_scientist': HKDataScientistRole,
            # ... etc
        }
        role_class = role_map.get(role_type)
        if not role_class:
            raise ValueError(f"Unknown role type: {role_type}")
        return role_class()
```

#### 2. BaseRole 抽象類 (新建)

```python
class BaseRole(ABC):
    """所有角色的基類"""

    @abstractmethod
    async def initialize(self, agent: UnifiedAgent) -> bool:
        """初始化角色 (可訪問 UnifiedAgent)"""
        pass

    @abstractmethod
    async def process_message(self, message: Message, agent: UnifiedAgent) -> bool:
        """處理角色特定的消息"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理角色資源"""
        pass

    def get_tools(self) -> Dict[str, Callable]:
        """返回角色提供的工具"""
        return {
            'logger': self.logger,
            'state': self.state,
            # 角色特定工具
        }
```

#### 3. 具體角色實現示例

```python
# DataScientistRole 角色實現
class DataScientistRole(BaseRole):
    """數據科學家角色"""

    async def initialize(self, agent: UnifiedAgent) -> bool:
        self.agent = agent
        self.logger = agent.logger
        self.anomaly_detector = AnomalyDetector()
        return await self.anomaly_detector.initialize()

    async def process_message(self, message: Message, agent: UnifiedAgent) -> bool:
        if message.type == 'ANALYZE_DATA':
            return await self._handle_analysis(message.content, agent)
        elif message.type == 'DETECT_ANOMALY':
            return await self._handle_anomaly_detection(message.content, agent)
        return False

    async def cleanup(self):
        await self.anomaly_detector.cleanup()

    async def _handle_analysis(self, content: Dict, agent: UnifiedAgent) -> bool:
        # 數據科學特定邏輯
        pass
```

---

## 遷移策略

### 第 1 步: 建立統一框架 (2 小時)
```
新文件:
├─ src/core/unified_agent.py (UnifiedAgent 核心類)
├─ src/core/agent_roles.py (BaseRole 及所有角色)
├─ src/core/role_provider.py (角色工廠和提供器)
└─ tests/test_unified_agent.py (新 Agent 系統測試)

任務:
- 實現 UnifiedAgent 核心類
- 實現 BaseRole 抽象類
- 創建角色工廠
- 編寫单元測試
```

### 第 2 步: 實現所有角色 (3 小時)
```
分組遷移:
1. 核心角色 (8 個) - 直接轉換
2. Real 角色 (8 個) - 添加 ML 擴展
3. HK Prompt 角色 (7 個) - 包裝 prompt engine

每個角色:
- 從現有 Agent 類提取邏輯
- 實現 BaseRole 介面
- 保留所有特定功能
```

### 第 3 步: 兼容層與測試 (1 小時)
```
兼容性:
- 創建適配層: 舊 Agent API -> UnifiedAgent
- 使所有現有代碼無需改動即可工作
- 逐步遷移調用代碼

測試:
- 單元測試所有角色
- 集成測試角色組合
- 回歸測試現有代碼
```

### 第 4 步: 清理與優化 (1 小時)
```
清理:
- 刪除重複的舊 Agent 類 (可選)
- 更新 Agent 工廠
- 更新文檔

優化:
- 識別通用工具並提取
- 統一工具介面
```

---

## 預期收益

### 代碼減少
| 項目 | 現狀 | 優化後 | 減少 |
|------|------|--------|------|
| Agent 實現 | 23 個 | 1 個 + 23 個角色 | 40% |
| 重複代碼 | 4,500+ 行 | ~500 行 | 90% |
| 測試代碼 | 2,000+ 行 | 800 行 | 60% |
| **總計** | ~12,000 行 | ~7,000 行 | **40%** |

### 維護性提升
- ✅ 新增 Agent: 只需寫角色類 (減少 80% 工作)
- ✅ Bug 修複: 在一處修複影響所有 Agent
- ✅ 特性添加: 統一工具系統，所有角色可用
- ✅ 測試: 統一測試框架，覆蓋所有角色

### 性能
- ✅ 消息處理: 統一路由，無額外開銷
- ✅ 啟動時間: 減少 30-50% (减少初始化邏輯)
- ✅ 內存: 共享工具與狀態，減少重複分配

---

## 實現檢查清單

### 第 1 階段: 基礎框架 (6 小時)

- [ ] 建立 `src/core/unified_agent.py`
  - [ ] UnifiedAgent 核心類
  - [ ] 心跳機制
  - [ ] 消息處理循環
  - [ ] 錯誤恢復

- [ ] 建立 `src/core/agent_roles.py`
  - [ ] BaseRole 抽象類
  - [ ] 8 個核心角色
  - [ ] 8 個 Real 角色
  - [ ] 7 個 HK Prompt 角色

- [ ] 建立 `src/core/role_provider.py`
  - [ ] RoleProvider 工廠類
  - [ ] 角色註冊表
  - [ ] 動態角色加載

- [ ] 編寫測試 `tests/test_unified_agent.py`
  - [ ] Agent 初始化測試
  - [ ] 角色加載測試
  - [ ] 消息路由測試
  - [ ] 集成測試

### 第 2 階段: 大規模遷移 (9 小時)

- [ ] 遷移所有 8 個核心角色
- [ ] 遷移所有 8 個 Real 角色
- [ ] 遷移所有 7 個 HK Prompt 角色
- [ ] 驗證所有角色功能

### 第 3 階段: 集成與驗證 (3 小時)

- [ ] 建立兼容適配層
- [ ] 運行完整回歸測試
- [ ] 性能基準測試
- [ ] 文檔更新

### 第 4 階段: 清理與優化 (2 小時)

- [ ] 可選: 刪除舊 Agent 實現
- [ ] 工具系統統一
- [ ] 最終文檔與示例
- [ ] 部署準備

---

## 技術決策

### 為什麼選擇組合而非繼承?
1. **靈活性:** 運行時改變角色
2. **測試性:** 獨立測試角色邏輯
3. **複用:** 角色可在不同 Agent 中共享
4. **簡化:** 避免深層繼承層級

### 角色 vs 代理人
- **角色** (Role): 角色的某一方面的行為 (如 "數據分析")
- **Agent** (代理): 承載一個或多個角色的容器

我們創建 **UnifiedAgent** 容器，支持任何角色組合。

### 向後兼容性
- 現有代碼無需更改 (創建適配層)
- 逐步遷移到統一 Agent
- 雙系統可共存

---

## 下一步行動

1. **立即開始:** 實現 UnifiedAgent 核心框架
2. **並行進行:** 開發第一個角色實現 (DataScientistRole)
3. **快速反饋:** 測試框架與第一個角色的集成
4. **全面推廣:** 遷移其他 22 個角色

**預期完成時間:** 6-8 小時
**難度:** 中等 (架構清晰，實現直接)
**風險:** 低 (現有代碼保持完整)

---

**文件作者:** Claude Code
**最後更新:** 2025-10-25
**狀態:** 準備實施
