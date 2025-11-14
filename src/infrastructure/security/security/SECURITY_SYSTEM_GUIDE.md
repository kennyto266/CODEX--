# Phase 6: 安全與沙盒系統 - 完整指南

## 概述

Phase 6 實現了完整的安全與沙盒系統，為量化交易系統提供多層次的安全防護。系統包含四個核心組件：

1. **增強沙盒系統** (T138) - 安全的代碼執行環境
2. **代碼執行監控** (T139) - 實時執行跟蹤和資源監控
3. **惡意代碼檢測** (T140) - 靜態分析和行為檢測
4. **權限控制系統** (T141) - 細粒度權限管理

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    安全系統架構圖                              │
├─────────────────────────────────────────────────────────────┤
│  應用層                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ 沙盒執行   │ │ 執行監控   │ │ 權限控制   │                 │
│  └──────┬─────┘ └──────┬─────┘ └──────┬─────┘                 │
│         │              │              │                        │
│  ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐                 │
│  │ 沙盒管理器 │ │ 監控管理器 │ │ 權限管理器 │                 │
│  └──────┬─────┘ └──────┬─────┘ └──────┬─────┘                 │
│         │              │              │                        │
│  ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐                 │
│  │文件控制器  │ │ 惡意代碼   │ │ 權限數據庫 │                 │
│  │網絡控制器  │ │檢測引擎    │ │ (SQLite)   │                 │
│  │系統調用    │ │(靜態分析)  │ │            │                 │
│  │攔截器      │ │            │ │            │                 │
│  └───────────┘ └───────────┘ └───────────┘                 │
│                                                                │
│  基礎設施層                                                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │  psutil   │ │  SQLite3   │ │  AST分析   │                 │
│  │(資源監控)  │ │ (數據存儲)  │ │ (代碼解析)  │                 │
│  └────────────┘ └────────────┘ └────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## 核心組件詳解

### 1. 增強沙盒系統 (sandbox.py)

#### 主要類和功能

**ResourceLimits** - 資源限制配置
- `max_cpu_time`: 最大CPU時間 (秒)
- `max_wall_time`: 最大壁鐘時間 (秒)
- `max_memory`: 最大內存使用 (字節)
- `max_open_files`: 最大打開文件數
- `max_processes`: 最大進程數
- `max_threads`: 最大線程數
- `allowed_file_paths`: 允許的文件路徑
- `blocked_file_paths`: 阻止的文件路徑
- `container_mode`: 是否使用Docker容器

**SecureCodeExecutor** - 安全代碼執行器
```python
from security import SecureCodeExecutor, ResourceLimits

# 創建資源限制
limits = ResourceLimits(
    max_cpu_time=5.0,
    max_wall_time=10.0,
    max_memory=128 * 1024 * 1024,
    allowed_file_paths=["/tmp"],
    blocked_file_paths=["/etc", "/sys"]
)

# 創建執行器
executor = SecureCodeExecutor(limits)

# 執行代碼
code = """
result = sum(range(100))
print(f"結果: {result}")
"""

result = executor.execute_code(code)
print(f"成功: {result.success}")
print(f"輸出: {result.output}")
print(f"執行時間: {result.execution_time:.2f}秒")
```

**SandboxManager** - 沙盒管理器
```python
from security import SandboxManager

# 創建管理器
manager = SandboxManager(limits)

# 創建執行器
executor = manager.create_executor("test_1")

# 執行代碼
result = executor.execute_code(code)

# 獲取統計
stats = executor.get_execution_stats()
print(f"成功率: {stats['success_rate']:.2%}")
```

#### 安全特性

1. **進程隔離**
   - 每次執行創建獨立的子進程
   - 使用 `preexec_fn` 設置子進程環境

2. **資源限制**
   - CPU時間限制 (使用 `resource` 模組)
   - 內存限制 (使用 `setrlimit`)
   - 執行超時 (使用 `subprocess.communicate(timeout)`)

3. **文件系統控制**
   - 只允許訪問指定路徑
   - 阻止訪問敏感目錄 (/etc, /sys, /root)
   - 使用臨時隔離目錄

4. **系統調用攔截**
   - 阻止危險系統調用 (fork, exec, ptrace等)
   - 只允許安全的系統調用

5. **容器化執行** (可選)
   - 支持Docker容器隔離
   - 完全隔離的執行環境
   - 網絡隔離 (可選)

### 2. 代碼執行監控 (execution_monitor.py)

#### 主要類和功能

**ExecutionMonitor** - 主監控類
```python
from security import ExecutionMonitor

# 創建監控器
monitor = ExecutionMonitor(monitor_interval=0.5)

# 啟動監控
monitor.start_monitoring()

# 開始跟蹤進程
import subprocess
process = subprocess.Popen([sys.executable, "script.py"])
tracker = monitor.start_execution_tracking(process.pid, "session_1")

# 停止跟蹤
summary = monitor.stop_execution_tracking("session_1")
print(f"執行時間: {summary['duration_seconds']:.2f}秒")
```

**RealTimeMonitor** - 實時監控器
- 持續監控進程資源使用
- 檢查資源閾值
- 觸發告警

**ResourceUsage** - 資源使用快照
```python
@dataclass
class ResourceUsage:
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_connections: int
    open_files: int
    thread_count: int
```

#### 監控功能

1. **實時資源監控**
   - CPU使用率
   - 內存使用量
   - 磁盤I/O
   - 網絡連接數
   - 打開文件數
   - 線程數

2. **告警機制**
   - 可配置的資源閾值
   - 自定義告警回調
   - 自動記錄告警事件

3. **執行日誌**
   - 記錄所有執行事件
   - 保存到JSON文件
   - 支持導出和查詢

### 3. 惡意代碼檢測 (malware_detection.py)

#### 檢測引擎

**MalwareDetector** - 主檢測類
```python
from security import MalwareDetector, ThreatLevel

detector = MalwareDetector()

# 掃描代碼
code = """
import os
os.system("ls")
"""

result = detector.scan_code(code)
print(f"威脅等級: {result.threat_level.value}")
print(f"是否惡意: {result.is_malicious}")
print(f"匹配模式: {result.matched_patterns}")
```

#### 檢測方法

1. **靜態代碼分析** (StaticAnalyzer)
   - 使用AST解析代碼
   - 檢測危險函數調用
   - 檢查動態代碼執行
   - 識別不安全的導入

2. **模式匹配** (PatternMatcher)
   - 正則表達式匹配
   - 預定義惡意模式
   - 25+ 種安全模式

3. **行為分析** (BehaviorAnalyzer)
   - 代碼混淆檢測
   - 反分析技術檢測
   - 持久化機制檢測
   - 權限提升檢測

4. **啟發式分析** (HeuristicEngine)
   - 代碼熵值計算
   - 字符串拼接分析
   - 動態執行檢測
   - 文件操作分析

#### 威脅類型

- **命令注入** (Command Injection)
- **文件操作** (File Operation)
- **網絡訪問** (Network Access)
- **系統調用** (System Call)
- **代碼注入** (Code Injection)
- **權限提升** (Privilege Escalation)
- **加密操作** (Encryption)
- **網絡掃描** (Network Scan)
- **動態代碼執行** (Dynamic Code Exec)
- **未授權訪問** (Unauthorized Access)
- **數據滲漏** (Data Exfiltration)

#### 威脅等級

- **SAFE** - 安全
- **LOW** - 低威脅
- **MEDIUM** - 中等威脅
- **HIGH** - 高威脅
- **CRITICAL** - 危險

### 4. 權限控制系統 (permission_system.py)

#### 主要類和功能

**PermissionManager** - 主權限管理器
```python
from security import PermissionManager, PermissionType, ResourceType

# 創建權限管理器
manager = PermissionManager("data/permissions.db")

# 創建用戶
user_id = manager.create_user("alice", "password123", "alice@example.com")

# 認證用戶
auth_id = manager.authenticate("alice", "password123")

# 檢查權限
has_permission = manager.check_permission(
    auth_id,
    PermissionType.CODE_EXECUTE,
    ResourceType.PROCESS
)

# 授予權限
manager.grant_permission(
    granted_by=admin_id,
    user_id=auth_id,
    permission=PermissionType.CODE_EXECUTE,
    resource_type=ResourceType.PROCESS,
    expires_in_hours=24
)
```

#### 權限類型

1. **文件系統權限**
   - `FILE_READ` - 讀取文件
   - `FILE_WRITE` - 寫入文件
   - `FILE_DELETE` - 刪除文件
   - `FILE_EXECUTE` - 執行文件
   - `FILE_CREATE` - 創建文件

2. **網絡權限**
   - `NETWORK_CONNECT` - 建立連接
   - `NETWORK_LISTEN` - 監聽端口
   - `NETWORK_BROADCAST` - 廣播

3. **系統權限**
   - `SYSTEM_EXECUTE` - 執行系統命令
   - `SYSTEM_MODIFY` - 修改系統設置
   - `SYSTEM_ADMIN` - 系統管理

4. **代碼執行權限**
   - `CODE_EXECUTE` - 執行代碼
   - `CODE_INJECT` - 代碼注入
   - `CODE_DEBUG` - 調試代碼

5. **數據權限**
   - `DATA_READ` - 讀取數據
   - `DATA_WRITE` - 寫入數據
   - `DATA_DELETE` - 刪除數據
   - `DATA_EXPORT` - 導出數據

6. **交易權限**
   - `TRADE_EXECUTE` - 執行交易
   - `TRADE_MODIFY` - 修改交易
   - `TRADE_ADMIN` - 交易管理

7. **策略權限**
   - `STRATEGY_EXECUTE` - 執行策略
   - `STRATEGY_MODIFY` - 修改策略
   - `STRATEGY_CREATE` - 創建策略

8. **用戶管理權限**
   - `USER_VIEW` - 查看用戶
   - `USER_MODIFY` - 修改用戶
   - `USER_ADMIN` - 用戶管理

#### 權限管理特性

1. **基於角色的訪問控制 (RBAC)**
   - 預定義角色 (admin, developer, trader, analyst, observer)
   - 角色權限繼承
   - 動態角色分配

2. **細粒度權限控制**
   - 資源級別權限
   - 操作級別權限
   - 時間限制權限

3. **動態權限授予**
   - 臨時權限
   - 條件式權限
   - 自動過期

4. **訪問日誌**
   - 記錄所有訪問嘗試
   - 成功/失敗記錄
   - IP地址追蹤

5. **權限數據庫**
   - SQLite數據庫存儲
   - 自動索引
   - 數據完整性保證

## 使用示例

### 完整安全檢查流程

```python
from security import (
    SandboxManager,
    ResourceLimits,
    ExecutionMonitor,
    MalwareDetector,
    PermissionManager,
    PermissionType,
    ResourceType
)

# 1. 初始化組件
limits = ResourceLimits(max_cpu_time=5.0, max_memory=128*1024*1024)
sandbox_manager = SandboxManager(limits)
monitor = ExecutionMonitor()
detector = MalwareDetector()
perm_manager = PermissionManager("data/permissions.db")

# 2. 創建並認證用戶
perm_manager.create_default_admin()
admin_id = perm_manager.authenticate("admin", "admin123")

# 3. 代碼掃描
code = """
# 量化交易代碼示例
import pandas as pd
import numpy as np

def moving_average(prices, window):
    return prices.rolling(window).mean()

data = pd.Series([100, 101, 102, 103, 104, 105])
ma = moving_average(data, 3)
print(ma.tolist())
"""

scan_result = detector.scan_code(code)

if scan_result.is_malicious:
    print(f"❌ 威脅檢測: {scan_result.threat_level.value}")
    print(f"匹配模式: {scan_result.matched_patterns}")
    exit(1)

# 4. 權限檢查
if not perm_manager.check_permission(
    admin_id,
    PermissionType.CODE_EXECUTE,
    ResourceType.PROCESS
):
    print("❌ 權限不足")
    exit(1)

# 5. 沙盒執行
executor = sandbox_manager.create_executor("exec_1")
result = executor.execute_code(code, timeout=10)

if not result.success:
    print(f"❌ 執行失敗: {result.error}")
    exit(1)

print(f"✅ 執行成功")
print(f"輸出: {result.output}")
print(f"執行時間: {result.execution_time:.2f}秒")

# 6. 啟動監控 (可選)
monitor.start_monitoring()
# ... 監控代碼執行 ...
monitor.stop_monitoring()
```

## 測試

### 運行測試

```bash
# 運行完整測試套件
python tests/test_security_system.py

# 運行單個測試類
python -m unittest tests.test_security_system.TestSandboxSystem

# 運行單個測試方法
python -m unittest tests.test_security_system.TestSandboxSystem.test_safe_code_execution
```

### 測試覆蓋範圍

- ✅ 沙盒系統 (ResourceLimits, SandboxManager, SecureCodeExecutor)
- ✅ 執行監控 (ExecutionMonitor, RealTimeMonitor, ResourceUsage)
- ✅ 惡意代碼檢測 (MalwareDetector, StaticAnalyzer, PatternMatcher)
- ✅ 權限控制 (PermissionManager, AccessControl, PermissionDatabase)
- ✅ 綜合安全流程 (集成測試)

## 最佳實踐

### 1. 沙盒執行

```python
# ✅ 推薦: 設置合理的資源限制
limits = ResourceLimits(
    max_cpu_time=5.0,          # 防止無限循環
    max_wall_time=10.0,        # 防止長時間運行
    max_memory=128*1024*1024,  # 防止內存洩漏
    allowed_file_paths=["/tmp"],  # 限制文件訪問
    blocked_file_paths=["/etc", "/sys", "/root"]  # 阻止敏感路徑
)

# ✅ 推薦: 使用唯一執行ID
executor = manager.create_executor(f"exec_{uuid.uuid4()}")

# ✅ 推薦: 設置超時
result = executor.execute_code(code, timeout=5.0)
```

### 2. 代碼檢測

```python
# ✅ 推薦: 掃描所有用戶代碼
for user_code in user_codes:
    result = detector.scan_code(user_code)
    if result.is_malicious:
        # 阻止執行
        log_security_event(result)

# ✅ 推薦: 記錄檢測結果
stats = detector.get_scan_stats()
print(f"威脅檢測率: {stats['threat_rate']:.2%}")
```

### 3. 權限控制

```python
# ✅ 推薦: 最小權限原則
# 只授予必要的權限
manager.grant_permission(
    granted_by=admin_id,
    user_id=user_id,
    permission=PermissionType.CODE_EXECUTE,  # 最小化權限
    resource_type=ResourceType.PROCESS,
    expires_in_hours=24  # 臨時權限
)

# ✅ 推薦: 定期審計
logs = manager.get_access_logs(limit=1000)
analyze_access_pattern(logs)
```

### 4. 監控

```python
# ✅ 推薦: 設置告警閾值
monitor.set_alert_thresholds({
    'max_cpu_percent': 80.0,
    'max_memory_mb': 512.0,
    'max_network_connections': 10
})

# ✅ 推薦: 自定義告警處理
def custom_alert_handler(tracker, event_type, message, data):
    alert = {
        'session': tracker.process_id,
        'event': event_type,
        'message': message,
        'data': data
    }
    send_alert(alert)

monitor.add_alert_callback(custom_alert_handler)
```

## 性能考量

### 1. 沙盒執行

- 每次執行需要創建子進程 (約 50-100ms)
- Docker容器模式開銷更大 (約 1-2秒)
- 建議重用執行器池

### 2. 代碼檢測

- 靜態分析速度: ~1-5ms (1000行代碼)
- 正則表達式匹配: ~0.1-1ms
- 建議緩存掃描結果

### 3. 權限檢查

- 數據庫查詢: ~1-5ms
- 建議使用內存緩存熱權限
- 定期刷新權限表

### 4. 監控

- 監控開銷: ~1-5% CPU
- 建議監控間隔 >= 0.5秒
- 大量進程時使用多線程

## 安全建議

### 1. 部署建議

```bash
# 使用專用賬戶運行
useradd -r -s /bin/false sandbox

# 限制系統調用 (Linux)
# 使用 seccomp 或 AppArmor

# 啟用容器隔離
limits = ResourceLimits(container_mode=True)
```

### 2. 運維建議

```python
# 定期更新安全模式
detector.load_patterns_from_file("security_patterns.json")

# 審計訪問日誌
logs = manager.get_access_logs(limit=10000)
detect_anomalies(logs)

# 監控系統資源
watch_system_resources()
```

### 3. 開發建議

```python
# 始終驗證用戶輸入
validate_input(user_data)

# 最小化代碼權限
# 不要授予不必要的權限

# 記錄所有安全事件
log_security_event(event_data)
```

## 故障排除

### 常見問題

1. **沙盒執行失敗**
   - 檢查資源限制是否過於嚴格
   - 確認臨時目錄權限
   - 查看錯誤日誌

2. **權限檢查失敗**
   - 驗證用戶存在且激活
   - 檢查角色分配
   - 確認權限未過期

3. **監控數據丟失**
   - 檢查進程是否已結束
   - 確認監控間隔合理
   - 查看日誌文件

4. **誤報/漏報**
   - 調整檢測閾值
   - 添加自定義模式
   - 更新白名單

## 擴展

### 添加自定義安全模式

```python
from security import SecurityPattern, ThreatType, ThreatLevel

pattern = SecurityPattern(
    name="CustomPattern",
    pattern=r"custom_dangerous_function\(",
    threat_type=ThreatType.FILE_OPERATION,
    threat_level=ThreatLevel.HIGH,
    description="Custom dangerous function"
)

detector.add_custom_pattern(pattern)
```

### 自定義角色

```python
role_permissions = {
    'quantitative_analyst': {
        PermissionType.DATA_READ,
        PermissionType.STRATEGY_EXECUTE,
        PermissionType.CODE_EXECUTE
    }
}
```

## 總結

Phase 6 安全與沙盒系統提供了全面的安全防護，涵蓋：

✅ **隔離執行** - 沙盒環境保護主系統
✅ **實時監控** - 持續跟蹤資源使用
✅ **威脅檢測** - 智能識別惡意代碼
✅ **權限管理** - 細粒度訪問控制
✅ **完整審計** - 記錄所有安全事件

系統設計遵循最小權限原則和多層防禦策略，為量化交易系統提供企業級安全保障。

---

**文檔版本**: 1.0
**最後更新**: 2025-11-09
**維護者**: Claude Code
