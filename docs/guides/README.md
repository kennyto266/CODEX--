# 測試框架 README
## Sprint 0 - US-002 Task 2.4

### 快速開始

```bash
# 運行所有測試
python scripts/run-tests.py all

# 運行單元測試
python scripts/run-tests.py unit

# 生成覆蓋率報告
python scripts/run-tests.py coverage

# 運行快速測試
python scripts/run-tests.py fast
```

### 測試標記

使用 `@pytest.mark.xxx` 標記測試：

```python
@pytest.mark.unit
def test_simple():
    pass

@pytest.mark.integration
@pytest.mark.database
async def test_database():
    pass

@pytest.mark.slow
def test_expensive():
    pass
```

### 常用命令

```bash
# 基本命令
pytest                          # 運行所有測試
pytest -m unit                  # 運行標記為 unit 的測試
pytest -m "not slow"            # 排除慢速測試
pytest tests/unit/              # 運行特定目錄
pytest tests/test_file.py       # 運行特定文件

# 覆蓋率
pytest --cov=src                # 生成覆蓋率報告
pytest --cov=src --cov-report=html  # 生成 HTML 報告
open htmlcov/index.html         # 查看報告

# 並行執行
pytest -n auto                  # 自動並行

# 詳細信息
pytest -v                       # 詳細輸出
pytest -vv                      # 更詳細
pytest -s                       # 顯示 print 輸出

# 失敗測試
pytest --lf                     # 重新運行失敗測試
pytest --ff                     # 失敗優先

# 性能
pytest --durations=10           # 顯示最慢的10個測試
```

### 測試配置文件

- `pytest.ini` - pytest 主配置
- `conftest.py` - 全局 fixtures
- `tests/unit/conftest.py` - 單元測試配置
- `tests/integration/conftest.py` - 集成測試配置

### 覆蓋率要求

- **最低覆蓋率**: 80%
- **分支覆蓋**: 啟用
- **報告格式**: HTML, XML, JSON, Terminal

查看覆蓋率報告：
```bash
open htmlcov/index.html
```

### 最佳實踐

1. **命名測試**: `test_功能_場景()`
2. **使用 AAA 模式**: Arrange → Act → Assert
3. **適當標記**: @pytest.mark.unit, @pytest.mark.integration 等
4. **Mock 外部依賴**: 使用 unittest.mock
5. **測試邊界情況**: 空值、異常、大數據量
6. **保持測試獨立**: 每個測試可以獨立運行

### 故障排除

**測試失敗**
```bash
pytest --lf                    # 重新運行失敗測試
pytest -x                      # 第一個失敗後停止
pytest --pdb                   # 進入調試器
```

**覆蓋率不足**
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html         # 查看未覆蓋的代碼
```

**測試太慢**
```bash
pytest -m "not slow"           # 跳過慢速測試
pytest -n auto                 # 並行執行
```

### 更多信息

- 完整文檔: `docs/test-framework-sprint0.md`
- 測試模板: `tests/unit/test_repository_template.py`

---

# Sprint 5 整合測試系統

## 概述

本測試系統實現了 Sprint 5 的5個 User Story，提供完整的端到端、性能、集成、負載和故障轉移測試能力。

### User Story 映射

| User Story | 故事點 | 優先級 | 測試文件 | 描述 |
|-----------|--------|--------|----------|------|
| US-021 | 8 | P0 | `integration/test_end_to_end.py` | 端到端測試實現 |
| US-022 | 13 | P0 | `performance/benchmark.py` | 性能基準測試實現 |
| US-023 | 8 | P1 | `integration/test_suite.py` | 集成測試實現 |
| US-024 | 8 | P1 | `performance/load_test.py` | 負載測試實現 |
| US-025 | 8 | P1 | `reliability/failover_test.py` | 故障轉移測試實現 |

## 性能目標

系統需要達到以下性能指標：

- **HTTP延遲**: < 50ms (P95)
- **緩存命中率**: > 95%
- **吞吐量**: > 200K msg/s
- **系統可用性**: > 99.9%

## 測試架構

### 核心組件測試

測試以下關鍵組件的協同工作：

1. **HTTP 客戶端** (`src/infrastructure/network/optimized_http_client.py`)
   - 連接池管理
   - 重試機制
   - 超時控制

2. **多級緩存** (`src/cache/multi_level_cache.py`)
   - L1 內存緩存
   - L2 Redis 緩存
   - L3 數據庫緩存

3. **事件總線** (`src/domain/events/event_bus.py`)
   - 異步事件處理
   - 事件訂閱/發布
   - 工作協程池

4. **協程池** (`src/core/coroutine_pool.py`)
   - 任務調度
   - 併發控制
   - 資源管理

## 快速開始

### 運行所有測試

```bash
# 運行所有整合測試
python tests/run_tests.py

# 運行特定測試
python tests/run_tests.py --test end_to_end
python tests/run_tests.py --test integration
python tests/run_tests.py --test performance
python tests/run_tests.py --test load_test
python tests/run_tests.py --test failover
```

### 使用 pytest 運行

```bash
# 運行端到端測試
pytest tests/integration/test_end_to_end.py -v --asyncio-mode=auto

# 運行集成測試
pytest tests/integration/test_suite.py -v --asyncio-mode=auto

# 運行性能測試
pytest tests/performance/benchmark.py -v --asyncio-mode=auto

# 運行負載測試
pytest tests/performance/load_test.py -v --asyncio-mode=auto

# 運行故障轉移測試
pytest tests/reliability/failover_test.py -v --asyncio-mode=auto
```

### 運行基準測試範例

```bash
# 性能基準測試
python tests/performance/benchmark.py

# 負載測試範例
python tests/performance/load_test.py

# 故障轉移測試範例
python tests/reliability/failover_test.py

# 集成測試套件
python tests/integration/test_suite.py
```

## 測試類型

### 1. 端到端測試 (`test_end_to_end.py`)

測試完整業務流程，包括：

- HTTP 請求 → 緩存 → 事件發布 → 協程池處理
- 錯誤處理和容錯機制
- 併發處理能力
- 端到端延遲驗證

**驗收標準**:
- 完整數據流正常運行
- 所有組件協同工作
- 端到端處理時間 < 1秒

### 2. 性能基準測試 (`benchmark.py`)

提供多種類型的性能測試：

- **負載測試**: 固定併發用戶數和持續時間
- **壓力測試**: 逐步增加負載直到系統極限
- **尖峰測試**: 模擬突然的高負載場景
- **持續測試**: 長期穩定負載測試

**性能指標**:
- 吞吐量 (ops/sec)
- 平均/中位數/P95/P99 延遲
- 成功率/錯誤率
- 資源使用率

### 3. 集成測試 (`test_suite.py`)

測試組件間接口和交互：

- HTTP 客戶端基礎功能
- 緩存系統基礎功能
- 事件總線基礎功能
- 協程池基礎功能
- 數據適配器基礎功能
- API 端點連通性

### 4. 負載測試 (`load_test.py`)

針對 API 和 WebSocket 的高併發測試：

- API 端點負載測試
- WebSocket 連接測試
- 持續負載測試
- 狀態碼分佈分析

### 5. 故障轉移測試 (`failover_test.py`)

驗證系統可靠性：

- 組件故障檢測
- 自動恢復機制
- 級聯故障測試
- 超時處理
- 斷路器模式

## 測試配置

### 配置文件位置

`config/test_config.yaml` - 包含所有測試的默認配置

### 關鍵配置項

```yaml
test:
  # 性能測試
  performance:
    default_duration: 10
    default_concurrent_users: 100

  # 負載測試
  load_test:
    base_url: "http://localhost:8001"
    timeout: 30
    max_concurrent: 1000

  # 基準測試目標
  benchmarks:
    target_metrics:
      http_latency_p95: 50  # ms
      cache_hit_rate: 95    # %
      throughput: 200000    # msg/s
      availability: 99.9    # %

  # 故障轉移測試
  failover:
    max_retry: 3
    retry_delay: 1.0
    recovery_timeout: 30.0
```

## 報告生成

所有測試都會生成詳細的報告，包括：

### 報告格式

- **Markdown** (.md) - 人工可讀的報告
- **JSON** (.json) - 機器可解析的數據

### 報告位置

所有報告保存在 `reports/` 目錄下：

```
reports/
├── performance_benchmark_YYYYMMDD_HHMMSS.md
├── performance_benchmark_YYYYMMDD_HHMMSS.json
├── load_test_YYYYMMDD_HHMMSS.md
├── load_test_YYYYMMDD_HHMMSS.json
├── integration_test_YYYYMMDD_HHMMSS.md
├── failover_test_YYYYMMDD_HHMMSS.md
└── sprint5_integration_test_summary_YYYYMMDD_HHMMSS.md
```

### 報告內容

每個報告包含：

- 測試時長和時間戳
- 測試結果統計
- 性能指標詳情
- 錯誤和警告信息
- 改進建議

## 驗收標準檢查清單

### 功能驗收

- [ ] 端到端測試覆蓋完整業務流程
- [ ] 所有組件集成測試通過
- [ ] API 端點連通性正常
- [ ] 錯誤處理機制有效

### 性能驗收

- [ ] HTTP 延遲 < 50ms (P95)
- [ ] 緩存命中率 > 95%
- [ ] 吞吐量 > 200K msg/s
- [ ] 系統可用性 > 99.9%

### 可靠性驗收

- [ ] 故障檢測機制有效
- [ ] 自動恢復時間 < 30秒
- [ ] 無級聯故障
- [ ] 斷路器模式正常工作

## 常見問題

### Q: 測試運行時報錯 "ModuleNotFoundError"

**A**: 確保已正確設置 PYTHONPATH 或在項目根目錄運行測試。

```bash
# 設置 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
python tests/run_tests.py
```

### Q: 負載測試失敗 "Connection refused"

**A**: 確保測試環境中的服務已啟動。

```bash
# 啟動服務
python complete_project_system.py

# 運行負載測試
python tests/run_tests.py --test load_test
```

### Q: 性能測試結果不達標

**A**: 檢查以下項目：

1. 系統資源使用情況 (CPU, Memory)
2. 數據庫連接池配置
3. 緩存配置
4. 網絡延遲

### Q: 如何自定義測試參數

**A**: 修改 `config/test_config.yaml` 文件，或在代碼中直接指定參數。

例如，修改併發用戶數：

```python
# 在 benchmark.py 中
result = await benchmark.run_load_test(
    test_func,
    test_data,
    concurrent_users=200,  # 修改為 200
    duration=10.0
)
```

## 開發指南

### 添加新測試

1. 創建新的測試文件
2. 遵循現有的命名和結構約定
3. 在 `run_tests.py` 中註冊新測試
4. 更新此 README

### 擴展測試框架

所有測試框架都設計為可擴展的：

- `PerformanceBenchmark`: 可添加新的測試類型
- `LoadTestFramework`: 可添加新的協議測試
- `FailoverTest`: 可添加新的故障場景
- `IntegrationTestSuite`: 可添加新的組件測試

## 最佳實踐

1. **獨立性**: 每個測試應該獨立運行，不依賴其他測試的狀態
2. **可重現性**: 測試結果應該可重現，使用固定種子或Mock數據
3. **資源清理**: 測試結束後確保清理所有資源（連接、文件等）
4. **錯誤處理**: 測試應該優雅地處理錯誤，並提供有用的錯誤信息
5. **性能**: 測試本身也應該高效，長時間測試應該有進度提示

## 聯繫信息

如有問題，請聯繫開發團隊或在 GitHub 上開 Issue。

## 更新日誌

### v1.0.0 (2025-11-04)

- 初始版本
- 實現5個 User Story 的測試
- 完整的測試運行器和報告系統
- 性能基準測試框架
- 故障轉移測試框架
