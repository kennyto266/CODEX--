# Mini Hedge Fund Sprint 0 Story 上下文定義

**版本**: v1.0
**創建日期**: 2025年11月5日
**Sprint**: Sprint 0 (2025/11/05 - 2025/11/19)
**負責人**: Scrum Master + 架構師

---

## Story Context 總覽

本文檔為 Sprint 0 中的每個 User Story 提供詳細的上下文定義，包括業務背景、技術實現、依賴關係和任務分解。

---

## [US-001] 搭建開發環境和工具鏈

### 業務上下文

**業務背景**:
作為Mini Hedge Fund系統的基礎，需要建立穩定、可重現的開發環境，確保所有開發者能夠快速上手，降低環境配置成本。

**現狀分析**:
- 現有系統使用Python 3.10+和FastAPI
- 已部署在localhost:8001
- 包含7個AI Agent和多個數據適配器
- 需要升級支持Mini Hedge Fund的5層架構

**業務價值**:
- 開發環境一鍵啟動，節省80%環境配置時間
- 統一的開發工具鏈，保證代碼質量
- 為多團隊協作奠定基礎

### 技術上下文

**架構影響**:
需要擴展現有架構支持：
- 5層架構：表現層 → API層 → 應用層 → 數據層 → 基礎設施
- 多數據庫：PostgreSQL + InfluxDB + Redis集群
- API版本管理：v1.0兼容 + v2.0新增

**技術約束**:
- 保持與現有v1.0系統的100%兼容性
- 新增組件必須支持Docker容器化
- 數據庫遷移需要零停機時間

**依賴關係**:
- 前置條件：無
- 後置影響：為US-002、US-003提供基礎

### 實現細節

**關鍵任務分解**:
```yaml
Task 1.1: Docker環境容器化
  - 創建docker-compose.yml (PostgreSQL + InfluxDB + Redis)
  - 配置網絡和卷掛載
  - 設置環境變量管理
  - 預估: 2小時

Task 1.2: 數據庫初始化
  - PostgreSQL初始化腳本 (schema.sql)
  - InfluxDB保留策略配置
  - Redis集群配置
  - 預估: 1.5小時

Task 1.3: 開發工具鏈
  - Python虛擬環境配置
  - 代碼格式化工具 (black, isort, flake8)
  - 預提交鉤子 (pre-commit)
  - 預估: 1小時

Task 1.4: 環境驗證
  - 創建verify-env.sh腳本
  - 檢查所有服務連接
  - 驗證API端點
  - 預估: 1小時

Task 1.5: 文檔編寫
  - 開發環境啟動指南
  - 故障排除文檔
  - 新開發者入門指南
  - 預估: 1.5小時
```

**驗收標準細化**:
- [ ] `docker-compose up` 在10分鐘內完成所有服務啟動
- [ ] PostgreSQL、InfluxDB、Redis連接測試通過
- [ ] 現有系統(complete_project_system.py)正常啟動
- [ ] 新增的Mini Hedge Fund組件可選啟動
- [ ] `./verify-env.sh` 輸出所有檢查通過
- [ ] 新開發者可在30分鐘內完成環境設置

**技術棧**:
- Container: Docker + Docker Compose
- 數據庫: PostgreSQL 14+, InfluxDB 2.x, Redis 7.x
- 代碼質量: black, isort, flake8, pre-commit
- 監控: 自定義健康檢查腳本

**風險與緩解**:
- 風險: Docker版本兼容性問題 → 緩解: 指定明確版本號
- 風險: 端口衝突 → 緩解: 動態端口分配
- 風險: 權限問題 → 緩解: Docker用戶組配置

---

## [US-002] 建立代碼結構和規範

### 業務上下文

**業務背景**:
需要為Mini Hedge Fund系統建立清晰的代碼結構，確保5層架構落地，並建立統一的編碼規範，提升代碼可維護性。

**現狀分析**:
現有系統結構：
```
src/
├── agents/          # 7個AI Agent
├── data_adapters/   # 數據適配器
├── dashboard/       # 儀表板API
├── backtest/        # 回測引擎
├── monitoring/      # 監控系統
└── risk_management/ # 風險管理
```

**業務價值**:
- 統一代碼結構，降低學習成本
- 強制執行編碼規範，提升代碼質量
- 建立可持續的代碼審查流程

### 技術上下文

**架構設計**:
5層架構映射：
```
表現層 (Presentation):     src/dashboard/, web/
API層 (API Gateway):       src/api/, src/dashboard/api_routes.py
應用層 (Application):      src/agents/, src/services/, src/strategies/
數據層 (Data Access):      src/data_adapters/, src/db/
基礎設施 (Infrastructure): src/config/, src/utils/, docker/, k8s/
```

**與現有系統整合**:
- 保持現有Agent架構不變
- 新增MacroIndicator模塊
- 擴展API支持v2.0版本
- 添加風險管理和績效分析模塊

**依賴關係**:
- 前置條件：US-001 (開發環境)
- 後置影響：為US-003 (數據適配器框架) 提供結構

### 實現細節

**關鍵任務分解**:
```yaml
Task 2.1: 5層架構重構
  - 重新組織代碼目錄結構
  - 創建層間接口定義
  - 移動現有代碼到新結構
  - 預估: 4小時

Task 2.2: 編碼規範配置
  - 配置.black (代碼格式化)
  - 配置.isort (import排序)
  - 配置.flake8 (代碼檢查)
  - 配置.mypy (類型檢查)
  - 預估: 2小時

Task 2.3: Git工作流
  - 創建git-flow工作流文檔
  - 配置分支保護規則
  - 設置提交信息規範 (Conventional Commits)
  - 配置PR審查流程
  - 預估: 2小時

Task 2.4: 測試框架
  - 配置pytest框架
  - 設置測試覆蓋率 (coverage.py)
  - 創建測試模板和示例
  - 配置CI/CD測試流程
  - 預估: 3小時

Task 2.5: 代碼審查
  - 創建代碼審查清單
  - 配置GitHub/GitLab審查規則
  - 設置自動檢查 (lint, test)
  - 預估: 1小時
```

**驗收標準細化**:
- [ ] 5層架構目錄結構完整創建
- [ ] 現有代碼成功遷移到新結構
- [ ] 代碼格式檢查通過率100%
- [ ] 單元測試覆蓋率達到80%
- [ ] Git工作流文檔完整
- [ ] 預提交鉤子攔截格式錯誤
- [ ] PR審查流程正常運行

**技術規範**:
- 代碼格式: Black (line-length=88)
- Import排序: isort (profile=black)
- 類型檢查: mypy (strict模式)
- 文檔字符串: Google Style
- 提交規範: Conventional Commits

**質量保證**:
- 靜態代碼分析: flake8 + bandit
- 測試覆蓋: pytest-cov > 80%
- 安全檢查: safety + bandit
- 性能檢查: pytest-benchmark

---

## [US-003] 實現基礎數據適配器框架

### 業務上下文

**業務背景**:
Mini Hedge Fund需要整合9個數據源（HKMA、C&SD、旅發局等），現有系統已有3個數據適配器，需要建立統一的擴展框架。

**數據源需求**:
```
現有數據源 (3個):
- Yahoo Finance (股價數據)
- Alpha Vantage (技術指標)
- HKEX API (港股數據)

新增數據源 (9個):
- HKMA (HIBOR利率, 5指標)
- C&SD (GDP/零售數據, 11指標)
- 旅發局 (訪客數據, 3指標)
- 移民局 (邊境數據, 3指標)
- 房地產 (房價/租金, 5指標)
- 交通署 (交通數據, 3指標)
- MTR (地鐵數據, 2指標)
- 貿易署 (貿易數據, 3指標)
```

**業務價值**:
- 統一的數據適配器接口，簡化新數據源集成
- 標準化的數據驗證和清洗流程
- 支持異步數據獲取和緩存

### 技術上下文

**現有架構分析**:
```python
# src/data_adapters/base_adapter.py (現有)
class BaseAdapter(ABC):
    @abstractmethod
    async def fetch_data(self, symbol, start_date, end_date):
        pass

    def validate_data(self, df):
        """數據驗證"""
        pass
```

**需要擴展的功能**:
- 異步數據獲取 (asyncio)
- 重試和錯誤處理機制
- 數據緩存和去重
- 速率限制和並發控制
- 數據標準化 (統一格式)

**依賴關係**:
- 前置條件：US-002 (代碼結構)
- 後置影響：為US-004 (HKMA適配器) 提供基礎

### 實現細節

**關鍵任務分解**:
```yaml
Task 3.1: BaseAdapter擴展
  - 創建BaseRealAdapter抽象類
  - 添加異步方法定義
  - 定義標準化數據格式
  - 預估: 2小時

Task 3.2: 工廠模式實現
  - 創建DataAdapterFactory
  - 支持動態適配器加載
  - 實現適配器註冊機制
  - 預估: 2小時

Task 3.3: 數據驗證引擎
  - 實現數據質量檢查
  - 添加異常值檢測
  - 創建數據清洗管道
  - 預估: 3小時

Task 3.4: 錯誤處理
  - 實現重試機制 (exponential backoff)
  - 添加熔斷器模式
  - 創建錯誤日誌和監控
  - 預估: 2小時

Task 3.5: 緩存機制
  - 實現Redis緩存層
  - 添加數據去重邏輯
  - 配置TTL和清理策略
  - 預估: 2小時

Task 3.6: 單元測試
  - 創建BaseAdapter測試
  - 測試工廠模式
  - 驗證錯誤處理
  - 預估: 3小時
```

**驗收標準細化**:
- [ ] BaseRealAdapter抽象類完整定義
- [ ] 成功創建新適配器 (繼承BaseRealAdapter)
- [ ] 工廠模式正確加載適配器
- [ ] 數據驗證攔截無效數據 (100%攔截率)
- [ ] 重試機制工作正常 (最多3次重試)
- [ ] 緩存命中率 > 70%
- [ ] 測試覆蓋率 > 90%

**設計模式**:
- 抽象工廠模式: 創建相關適配器
- 策略模式: 不同數據源適配策略
- 裝飾器模式: 添加緩存、日誌功能
- 觀察者模式: 數據更新通知

**標準化數據格式**:
```python
class StandardDataFormat(BaseModel):
    """統一數據格式"""
    timestamp: datetime
    symbol: Optional[str]  # 非價格數據為None
    value: float
    category: str  # hibor, gdp, retail等
    indicator: str  # 具體指標名
    source: str  # 數據源
    quality_score: float  # 數據質量評分 (0-1)
    metadata: dict  # 其他元數據
```

**性能要求**:
- 數據獲取延遲 < 2秒 (P95)
- 支持並發適配器數量 >= 10
- 緩存響應時間 < 100ms
- 數據驗證時間 < 500ms

---

## [US-004] 實現HKMA數據適配器

### 業務上下文

**業務背景**:
HKMA (香港金融管理局) 提供HIBOR利率數據，是Mini Hedge Fund的核心指標之一，需要獲取5個期限的HIBOR數據。

**業務需求**:
HIBOR是香港銀行同業拆息，反映銀行間資金成本，是宏觀經濟的重要指標：
- overnight: 隔夜拆息 (資金成本動量)
- 1m: 1個月期限結構
- 3m: 3個月期限結構
- 6m: 6個月期限結構
- 12m: 12個月期限結構

**業務價值**:
- 為資金成本分析提供基礎數據
- 期限結構變化預測利率趨勢
- 作為宏觀振盪器的5個輸入指標

### 技術上下文

**數據源分析**:
- HKMA官方網站: https://www.hkma.gov.hk/
- 數據格式: HTML表格 + CSV下載
- 更新頻率: 每日 (工作日)
- 歷史數據: 支持最多2年

**技術挑戰**:
- 需要網頁抓取或API調用
- 數據格式轉換 (HTML → 標準格式)
- 異常處理 (週末、假期無數據)
- 數據完整性驗證

**依賴關係**:
- 前置條件：US-003 (適配器框架)
- 後置影響：為US-005 (指標轉換) 提供HIBOR數據

### 實現細節

**關鍵任務分解**:
```yaml
Task 4.1: HKMA API/網頁分析
  - 研究HKMA數據接口
  - 分析網頁結構和數據格式
  - 確定最佳數據獲取方式
  - 測試API穩定性和速率限制
  - 預估: 3小時

Task 4.2: HKBORAdapter實現
  - 繼承BaseRealAdapter
  - 實現5個HIBOR指標獲取
  - 添加數據解析邏輯
  - 實現異步數據獲取
  - 預估: 4小時

Task 4.3: 數據清洗
  - 處理日期格式轉換
  - 清理無效數值 (NaN, 空值)
  - 標準化數值精度 (4位小數)
  - 添加數據質量標記
  - 預估: 2小時

Task 4.4: 錯誤處理
  - 網絡異常重試 (3次)
  - 數據缺失處理 (填充/跳過)
  - 速率限制控制 (每秒1次)
  - 詳細錯誤日誌
  - 預估: 2小時

Task 4.5: 緩存實現
  - Redis緩存最新數據 (1小時TTL)
  - 緩存歷史數據 (24小時TTL)
  - 實現緩存更新策略
  - 預估: 1小時

Task 4.6: 集成測試
  - 測試實時數據獲取
  - 驗證5個指標完整性
  - 測試錯誤處理流程
  - 性能測試 (<2秒響應)
  - 預估: 2小時
```

**驗收標準細化**:
- [ ] 成功獲取5個HIBOR指標 (overnight, 1m, 3m, 6m, 12m)
- [ ] 數據格式符合StandardDataFormat
- [ ] 數據清洗正確處理異常值
- [ ] 錯誤處理機制有效 (網絡、數據缺失)
- [ ] 緩存機制工作正常 (命中率>70%)
- [ ] 支持歷史數據獲取 (最多2年)
- [ ] 響應時間 < 2秒 (P95)
- [ ] 測試覆蓋率 > 90%

**數據示例**:
```python
# 期望輸出格式
{
  "timestamp": "2025-11-05T00:00:00",
  "indicators": {
    "hibor_overnight": 0.0425,
    "hibor_1m": 0.0435,
    "hibor_3m": 0.0450,
    "hibor_6m": 0.0475,
    "hibor_12m": 0.0500
  },
  "source": "HKMA",
  "data_quality": 0.95
}
```

**性能指標**:
- 數據獲取時間 < 2秒
- 數據準確性 > 99% (與官網一致)
- 系統可用性 > 99% (工作日)
- 緩存命中率 > 70%

**風險與緩解**:
- 風險: HKMA網站結構變更 → 緩解: 監控網頁變化，版本控制
- 風險: 速率限制 → 緩解: 實施緩存和請求節流
- 風險: 數據格式異常 → 緩解: 強化的數據驗證

---

## Story間整合與驗收

### Sprint 0 完成標準

**技術標準**:
- [ ] 所有Story的驗收標準達成
- [ ] 測試覆蓋率 > 80%
- [ ] 代碼審查通過
- [ ] API響應時間 < 200ms (P95)

**功能標準**:
- [ ] 開發環境可一鍵啟動
- [ ] 5層架構完整實現
- [ ] 數據適配器框架可擴展
- [ ] HKMA適配器正常工作

**文檔標準**:
- [ ] 技術設計文檔完整
- [ ] API文檔更新
- [ ] 開發指南完成
- [ ] 部署說明清楚

### Sprint 1 前置條件

完成Sprint 0後，系統將具備：
1. 穩定的開發環境
2. 清晰的代碼結構
3. 可擴展的數據適配器框架
4. 第一個真實數據源 (HKMA HIBOR)

為Sprint 1做準備：
- US-005: 實現宏觀指標技術化框架
- US-006: 實現HIBOR指標轉換器

---

**文檔版本**: v1.0
**創建者**: Scrum Master + 架構師
**審核者**: 開發團隊
**批准者**: 產品負責人
**狀態**: ✅ 準備就緒，可進入開發階段
