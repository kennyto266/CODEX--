# 測試框架配置指南
## Sprint 0 - US-002 Task 2.4

### 目錄
1. [測試框架概述](#測試框架概述)
2. [測試類型](#測試類型)
3. [測試標記](#測試標記)
4. [測試執行](#測試執行)
5. [代碼覆蓋率](#代碼覆蓋率)
6. [測試模板](#測試模板)
7. [最佳實踐](#最佳實踐)
8. [常見問題](#常見問題)

---

## 測試框架概述

### 技術棧
- **pytest**: 主要測試框架
- **coverage.py**: 代碼覆蓋率分析
- **pytest-cov**: pytest 覆蓋率插件
- **pytest-mock**: Mock 測試支持
- **pytest-asyncio**: 異步測試支持
- **pytest-xdist**: 並行測試支持

### 測試目錄結構
```
tests/
├── __init__.py
├── conftest.py              # 全局fixtures
├── fixtures/                # 測試數據
│   ├── __init__.py
│   ├── mock_data.py
│   └── mock_adapters.py
├── unit/                    # 單元測試
│   ├── __init__.py
│   └── test_*.py
├── integration/             # 集成測試
│   ├── __init__.py
│   ├── conftest.py          # 集成測試配置
│   └── test_*.py
├── performance/             # 性能測試
│   ├── __init__.py
│   └── test_*.py
├── security/                # 安全測試
│   ├── __init__.py
│   └── test_*.py
└── helpers/                 # 測試輔助工具
    ├── __init__.py
    └── test_utils.py
```

### 配置要求
- **覆蓋率閾值**: 80%
- **分支覆蓋**: 啟用
- **測試報告**: HTML, XML, JSON, Terminal
- **測試時間**: 統計最慢的10個測試

---

## 測試類型

### 1. 單元測試 (Unit Tests)

**目標**: 測試獨立的函數或類方法

**特點**:
- 執行速度快 (< 1秒)
- 無外部依賴
- 使用 Mock 模擬依賴
- 覆蓋邊界情況

**標記**: `@pytest.mark.unit`

**示例**:
```python
@pytest.mark.unit
def test_repository_get():
    # 單元測試示例
    pass
```

### 2. 集成測試 (Integration Tests)

**目標**: 測試組件間的交互

**特點**:
- 需要實際依賴（數據庫、API等）
- 執行時間較長 (1-5秒)
- 測試數據流和組件協作

**標記**: `@pytest.mark.integration`

**示例**:
```python
@pytest.mark.integration
@pytest.mark.database
async def test_repository_integration():
    # 集成測試示例
    pass
```

### 3. API 測試 (API Tests)

**目標**: 測試 REST API 端點

**特點**:
- 使用 HTTP 客戶端
- 測試請求和響應
- 驗證狀態碼和數據

**標記**: `@pytest.mark.api`

**示例**:
```python
@pytest.mark.api
async def test_get_macro_indicators():
    # API 測試示例
    pass
```

### 4. 性能測試 (Performance Tests)

**目標**: 驗證系統性能指標

**特點**:
- 測試響應時間
- 測試吞吐量
- 測試資源使用

**標記**: `@pytest.mark.performance`

**示例**:
```python
@pytest.mark.performance
def test_strategy_performance():
    # 性能測試示例
    pass
```

---

## 測試標記

### 依賴標記
```python
# 需要真實數據
@pytest.mark.real-data

# 需要 Docker
@pytest.mark.docker

# 需要外部 API
@pytest.mark.external

# 需要數據庫
@pytest.mark.database
```

### 速度標記
```python
# 快速測試 (< 1秒)
@pytest.mark.fast

# 慢速測試 (> 5秒)
@pytest.mark.slow
```

### 功能標記
```python
# 冒煙測試
@pytest.mark.smoke

# 回歸測試
@pytest.mark.regression

# 新功能測試
@pytest.mark.new
```

### 模塊標記
```python
# 數據適配器
@pytest.mark.data-adapter

# 宏觀指標
@pytest.mark.macro-indicator

# 策略測試
@pytest.mark.strategy

# 風險管理
@pytest.mark.risk

# Repository 模式
@pytest.mark.repository

# Agent 系統
@pytest.mark.agent
```

---

## 測試執行

### 基本命令

```bash
# 運行所有測試
pytest

# 運行特定標記的測試
pytest -m unit              # 只運行單元測試
pytest -m "not slow"        # 跳過慢速測試
pytest -m "unit and fast"   # 單元測試中的快速測試
pytest -m "integration or api"  # 集成或API測試

# 運行特定文件
pytest tests/unit/test_repository.py

# 運行特定測試
pytest tests/unit/test_repository.py::TestIRepository::test_get

# 並行執行
pytest -n auto              # 自動檢測CPU核心數
pytest -n 4                 # 使用4個進程

# 生成覆蓋率報告
pytest --cov=src --cov-report=html

# 顯示最慢的10個測試
pytest --durations=10

# 詳細輸出
pytest -v                   # 詳細模式
pytest -vv                  # 更詳細
pytest -s                   # 顯示 print 輸出

# 失敗時停止
pytest -x                   # 第一個失敗後停止
pytest -x --tb=short        # 第一個失敗後停止，簡短輸出
```

### CI/CD 命令

```bash
# CI 環境推薦命令
pytest \
  -m "not slow and not external" \
  --cov=src \
  --cov-report=xml \
  --cov-fail-under=80 \
  --strict-markers \
  --tb=short \
  -v
```

### 調試測試

```bash
# 進入 pdb 調試器
pytest --pdb

# 在第一個失敗時進入調試器
pytest --pdbcls=IPython.terminal.debugger:Pdb

# 顯示局部變量
pytest --lfnf=short

# 捕獲日誌
pytest --log-cli-level=INFO
```

---

## 代碼覆蓋率

### 配置
```ini
[tool:pytest]
addopts =
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-report=term-missing
    --cov-report=json:coverage.json
    --cov-fail-under=80
    --cov-branch
```

### 報告格式

1. **HTML 報告** (最詳細)
   ```bash
   pytest --cov=src --cov-report=html
   open htmlcov/index.html  # 查看詳細報告
   ```

2. **XML 報告** (CI/CD)
   ```bash
   pytest --cov=src --cov-report=xml
   ```

3. **JSON 報告** (程序化處理)
   ```bash
   pytest --cov=src --cov-report=json
   ```

4. **終端報告** (快速查看)
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

### 覆蓋率閱讀

```
Name                            Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src/core/interfaces/__init__.py     12      0   100%
src/core/interfaces/repository.py  145     45    69%   47-48, 52-53...
---------------------------------------------------------------
TOTAL                             1234    123    90%
```

**指標說明**:
- **Stmts**: 語句總數
- **Miss**: 未覆蓋的語句
- **Cover**: 覆蓋百分比
- **Missing**: 未覆蓋的具體行號

### 提高覆蓋率

```python
# 測試邊界條件
@pytest.mark.unit
def test_get_with_empty_id():
    with pytest.raises(ValueError):
        repository.get("")

# 測試異常情況
@pytest.mark.unit
def test_create_duplicate():
    with pytest.raises(ValueError, match="already exists"):
        repository.create(existing_entity)

# 測試所有分支
@pytest.mark.unit
async def test_get_all_with_limit():
    # 測試 limit 參數
    result = await repository.get_all(limit=10)
    assert len(result) == 10

    # 測試無 limit
    result = await repository.get_all()
    assert len(result) > 0
```

---

## 測試模板

### 1. 單元測試模板

```python
"""
單元測試模板
"""
import pytest
from unittest.mock import Mock, AsyncMock


@pytest.mark.unit
class TestClassName:
    """測試類名稱"""

    def setup_method(self):
        """每個測試前調用"""
        self.mock_obj = Mock()

    def teardown_method(self):
        """每個測試後調用"""
        pass

    def test_function_name(self):
        """測試功能描述"""
        # Arrange - 準備數據
        input_data = "test"
        expected = "expected_result"

        # Act - 執行功能
        result = function_under_test(input_data)

        # Assert - 驗證結果
        assert result == expected

    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
        ("case3", "result3"),
    ])
    def test_function_with_params(self, input, expected):
        """使用參數化測試多個場景"""
        result = function_under_test(input)
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_function(self):
        """測試異步函數"""
        # Arrange
        mock_service = AsyncMock(return_value="result")

        # Act
        result = await async_function_under_test(mock_service)

        # Assert
        assert result == "result"
        mock_service.assert_called_once()
```

### 2. 集成測試模板

```python
"""
集成測試模板
"""
import pytest
import asyncio
from unittest.mock import AsyncMock


@pytest.mark.integration
@pytest.mark.database
class TestIntegration:
    """集成測試類"""

    @pytest.fixture(autouse=True)
    async def setup_database(self, test_db):
        """自動設置數據庫"""
        await test_db.setup()
        yield
        await test_db.cleanup()

    @pytest.mark.asyncio
    async def test_data_flow(self):
        """測試完整數據流"""
        # 步驟1: 創建數據
        entity = await create_entity(data={"key": "value"})
        assert entity.id is not None

        # 步驟2: 查詢數據
        retrieved = await get_entity(entity.id)
        assert retrieved.key == "value"

        # 步驟3: 更新數據
        updated = await update_entity(entity.id, {"key": "new_value"})
        assert updated.key == "new_value"

        # 步驟4: 刪除數據
        deleted = await delete_entity(entity.id)
        assert deleted is True

        # 步驟5: 驗證刪除
        with pytest.raises(EntityNotFoundError):
            await get_entity(entity.id)
```

### 3. API 測試模板

```python
"""
API 測試模板
"""
import pytest
import httpx
from fastapi.testclient import TestClient


@pytest.mark.api
class TestAPIEndpoints:
    """API 端點測試"""

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        from main import app
        return TestClient(app)

    def test_get_health(self, client):
        """測試健康檢查端點"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_macro_indicators(self, client):
        """測試獲取宏觀指標"""
        response = client.get("/api/macro-indicators")
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert len(data["indicators"]) > 0

    @pytest.mark.parametrize("symbol,expected_status", [
        ("0700.HK", 200),
        ("INVALID", 400),
    ])
    def test_get_stock_data(self, client, symbol, expected_status):
        """使用參數化測試股票數據端點"""
        response = client.get(f"/api/stock/{symbol}")
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """測試 WebSocket 連接"""
        with client.websocket_connect("/ws") as websocket:
            # 發送消息
            websocket.send_json({"type": "ping"})
            # 接收響應
            data = websocket.receive_json()
            assert data["type"] == "pong"
```

### 4. Repository 測試模板

```python
"""
Repository 測試模板
"""
import pytest
from unittest.mock import Mock, AsyncMock


@pytest.mark.repository
@pytest.mark.unit
class TestIRepository:
    """Repository 接口測試"""

    def setup_method(self):
        """設置測試數據"""
        self.repository = Mock()
        self.entity = Mock()
        self.entity.id = "test_id"

    @pytest.mark.asyncio
    async def test_get_success(self):
        """測試成功獲取實體"""
        # Arrange
        self.repository.get = AsyncMock(return_value=self.entity)

        # Act
        result = await self.repository.get("test_id")

        # Assert
        assert result == self.entity
        self.repository.get.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """測試實體不存在"""
        # Arrange
        self.repository.get = AsyncMock(return_value=None)

        # Act
        result = await self.repository.get("nonexistent_id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_create_success(self):
        """測試成功創建實體"""
        # Arrange
        self.repository.create = AsyncMock(return_value=self.entity)

        # Act
        result = await self.repository.create(self.entity)

        # Assert
        assert result == self.entity
        self.repository.create.assert_called_once_with(self.entity)

    @pytest.mark.asyncio
    async def test_create_duplicate(self):
        """測試創建重複實體"""
        # Arrange
        self.repository.create = AsyncMock(side_effect=ValueError("Entity exists"))

        # Act & Assert
        with pytest.raises(ValueError, match="Entity exists"):
            await self.repository.create(self.entity)

    @pytest.mark.asyncio
    async def test_update_success(self):
        """測試成功更新實體"""
        # Arrange
        updated_entity = Mock()
        updated_entity.id = "test_id"
        self.repository.update = AsyncMock(return_value=updated_entity)

        # Act
        result = await self.repository.update("test_id", updated_entity)

        # Assert
        assert result == updated_entity
        self.repository.update.assert_called_once_with("test_id", updated_entity)

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """測試成功刪除實體"""
        # Arrange
        self.repository.delete = AsyncMock(return_value=True)

        # Act
        result = await self.repository.delete("test_id")

        # Assert
        assert result is True
        self.repository.delete.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_exists(self):
        """測試實體存在檢查"""
        # Arrange
        self.repository.exists = AsyncMock(return_value=True)

        # Act
        result = await self.repository.exists("test_id")

        # Assert
        assert result is True
        self.repository.exists.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_count(self):
        """測試獲取實體計數"""
        # Arrange
        self.repository.count = AsyncMock(return_value=42)

        # Act
        result = await self.repository.count()

        # Assert
        assert result == 42
```

### 5. Mock 和 Fixture 模板

```python
"""
Mock 和 Fixture 模板
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime


@pytest.fixture
def mock_macro_indicator_service():
    """Mock 宏觀指標服務"""
    service = Mock()
    service.get_latest_indicators = AsyncMock(return_value={
        "hibor_overnight": 3.5,
        "gdp_growth": 2.1,
    })
    service.calculate_oscillator = AsyncMock(return_value=0.65)
    return service


@pytest.fixture
def sample_entity():
    """示例實體"""
    entity = Mock()
    entity.id = "entity_001"
    entity.name = "Test Entity"
    entity.created_at = datetime(2025, 1, 1)
    return entity


@pytest.fixture
def mock_repository():
    """Mock Repository"""
    repository = Mock()
    repository.get = AsyncMock()
    repository.create = AsyncMock()
    repository.update = AsyncMock()
    repository.delete = AsyncMock()
    repository.exists = AsyncMock()
    repository.count = AsyncMock(return_value=0)
    repository.get_all = AsyncMock(return_value=[])
    return repository


@pytest.fixture
def mock_time_series_repository(mock_repository):
    """Mock 時間序列 Repository"""
    time_series_repo = Mock()
    time_series_repo.insert_timeseries = AsyncMock()
    time_series_repo.query_timeseries = AsyncMock(return_value=[])
    time_series_repo.delete_timeseries = AsyncMock()
    # 繼承 mock_repository 的方法
    time_series_repo.get = mock_repository.get
    time_series_repo.create = mock_repository.create
    time_series_repo.update = mock_repository.update
    time_series_repo.delete = mock_repository.delete
    return time_series_repo


@pytest.fixture
def mock_cache_repository(mock_repository):
    """Mock 緩存 Repository"""
    cache_repo = Mock()
    cache_repo.set_with_ttl = AsyncMock()
    cache_repo.get_with_ttl = AsyncMock(return_value=None)
    cache_repo.flush_db = AsyncMock()
    # 繼承 mock_repository 的方法
    cache_repo.get = mock_repository.get
    cache_repo.create = mock_repository.create
    cache_repo.update = mock_repository.update
    cache_repo.delete = mock_repository.delete
    return cache_repo
```

---

## 最佳實踐

### 1. 測試命名
```python
# ✅ 好的測試名稱
def test_repository_get_returns_entity_when_exists():
    pass

def test_macro_indicator_calculate_oscillator_returns_value_between_0_and_1():
    pass

# ❌ 不好的測試名稱
def test_repo():
    pass

def test_macro():
    pass
```

### 2. AAA 模式 (Arrange-Act-Assert)
```python
def test_example():
    # Arrange - 準備
    input_data = create_test_data()
    expected = calculate_expected_result(input_data)

    # Act - 執行
    result = function_under_test(input_data)

    # Assert - 驗證
    assert result == expected
```

### 3. 使用 Mock 正確
```python
# ✅ 正確使用 Mock
@pytest.mark.unit
def test_with_mock():
    mock_service = Mock()
    mock_service.method.return_value = "expected"
    result = use_service(mock_service)
    assert result == "expected"
    mock_service.method.assert_called_once()

# ❌ 錯誤使用 Mock
@pytest.mark.unit
def test_without_mock():
    # 這不是單元測試，而是集成測試
    result = actual_service.method()
    assert result == "expected"
```

### 4. 測試數據管理
```python
# ✅ 使用工廠模式
class EntityFactory:
    @staticmethod
    def create_entity(id="test_id", name="Test"):
        entity = Mock()
        entity.id = id
        entity.name = name
        return entity

@pytest.mark.unit
def test_with_factory():
    entity = EntityFactory.create_entity()
    assert entity.id == "test_id"

# ❌ 硬編碼測試數據
@pytest.mark.unit
def test_with_hardcoded():
    entity = Mock()
    entity.id = "test_id"
    entity.name = "Test"
    # ...
```

### 5. 異步測試
```python
# ✅ 正確的異步測試
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# ❌ 同步方式測試異步函數
def test_async_function_wrong():
    result = async_function()  # 這會返回 coroutine
    assert result is not None  # 這是錯誤的
```

### 6. 異常測試
```python
# ✅ 測試異常情況
@pytest.mark.unit
def test_raises_exception():
    with pytest.raises(ValueError, match="Invalid input"):
        function_under_test("invalid")

# ✅ 測試異常消息
@pytest.mark.unit
def test_exception_message():
    with pytest.raises(ValueError) as exc_info:
        function_under_test("invalid")
    assert "Invalid input" in str(exc_info.value)
```

---

## 常見問題

### Q1: 如何運行特定模塊的測試？
```bash
# 運行特定標記
pytest -m "unit and repository"

# 運行特定文件
pytest tests/unit/test_repository.py

# 運行特定類
pytest tests/unit/test_repository.py::TestIRepository

# 運行特定方法
pytest tests/unit/test_repository.py::TestIRepository::test_get
```

### Q2: 如何跳過慢速測試？
```bash
# 方法1: 使用標記
pytest -m "not slow"

# 方法2: 使用環境變量
SKIP_SLOW=1 pytest -m slow

# 測試文件中
@pytest.mark.skipif(
    os.getenv("SKIP_SLOW") == "1",
    reason="Slow test skipped"
)
def test_slow_operation():
    pass
```

### Q3: 如何提高測試速度？
```bash
# 並行執行
pytest -n auto

# 使用 SSD
# 將測試目錄放在 SSD 上

# 優化 fixture
@pytest.fixture(scope="module")  # 模塊級別，而不是函數級別
def expensive_resource():
    # 創建一次，模塊內所有測試共享
    return create_resource()
```

### Q4: 如何處理外部依賴？
```python
# 使用標記跳過
@pytest.mark.skipif(
    not os.getenv("INTEGRATION_TEST"),
    reason="Set INTEGRATION_TEST=1 to run"
)
@pytest.mark.integration
def test_external_api():
    pass

# 使用 mock
@pytest.mark.unit
def test_with_external_mock():
    with patch("module.external_api") as mock_api:
        mock_api.return_value = {"status": "ok"}
        result = function_that_uses_api()
        assert result is not None
```

### Q5: 如何調試測試失敗？
```bash
# 進入調試器
pytest --pdb

# 查看詳細輸出
pytest -vv --tb=long

# 只運行失敗的測試
pytest --lf  # 運行上次失敗的測試
pytest --ff  # 失敗優先

# 捕獲日誌
pytest --log-cli-level=DEBUG
```

### Q6: 如何驗證覆蓋率？
```bash
# 生成完整報告
pytest --cov=src --cov-report=html
open htmlcov/index.html

# 檢查特定文件
pytest --cov=src/core/interfaces --cov-report=term-missing

# 分支覆蓋
pytest --cov=src --cov-branch

# 缺少覆蓋的行
pytest --cov=src --cov-missing
```

---

## 總結

遵循本指南，確保：

✅ 測試覆蓋率 >= 80%
✅ 所有測試通過
✅ 測試命名清晰
✅ 使用適當的 Mock
✅ 遵循 AAA 模式
✅ 測試執行快速
✅ 覆蓋邊界情況

---

**文檔版本**: 1.0.0
**更新日期**: 2025-11-05
**維護者**: Sprint 0 團隊
