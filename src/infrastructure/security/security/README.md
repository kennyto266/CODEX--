# Phase 6: 安全與沙盒系統

## 概述

Phase 6 實現了完整的安全與沙盒系統，為量化交易系統提供企業級安全保障。

## 組件

### 🛡️ T138: 增強沙盒系統 (`sandbox.py`)
安全的代碼執行環境
- 進程隔離
- 資源限制 (CPU/內存/時間)
- 文件系統訪問控制
- 網絡訪問限制
- 系統調用攔截
- 容器化執行 (Docker)

**核心類**:
```python
ResourceLimits, SecureCodeExecutor, SandboxManager
FileAccessController, NetworkController, SystemCallInterceptor
```

### 📊 T139: 代碼執行監控 (`execution_monitor.py`)
實時監控代碼執行
- 實時執行跟蹤
- 資源使用監控
- 執行超時檢測
- 異常行為檢測
- 執行日誌記錄
- 可配置告警

**核心類**:
```python
ExecutionMonitor, RealTimeMonitor, ExecutionTracker
ResourceUsage, ExecutionLogger
```

### 🔍 T140: 惡意代碼檢測 (`malware_detection.py`)
智能檢測威脅代碼
- 靜態代碼分析 (AST)
- 惡意模式匹配 (25+ 種模式)
- 行為分析
- 啟發式檢測
- 威脅等級評估
- 11 種威脅類型

**核心類**:
```python
MalwareDetector, StaticAnalyzer, PatternMatcher
BehaviorAnalyzer, HeuristicEngine
```

### 🔐 T141: 權限控制系統 (`permission_system.py`)
細粒度權限管理
- 基於角色的訪問控制 (RBAC)
- 動態權限授予
- 實時權限驗證
- 完整訪問日誌
- SQLite 數據庫
- 8 大類權限 (30+ 種)

**核心類**:
```python
PermissionManager, AccessControl, PermissionDatabase
User, Role, PermissionGrant, AccessLog
```

## 快速開始

### 1. 導入模組
```python
from security import (
    SandboxManager, ResourceLimits,
    MalwareDetector, PermissionManager,
    ExecutionMonitor,
    PermissionType, ResourceType
)
```

### 2. 基本使用
```python
# 創建沙盒
limits = ResourceLimits(
    max_cpu_time=5.0,
    max_memory=128*1024*1024,
    allowed_file_paths=["/tmp"]
)
sandbox = SandboxManager(limits)

# 創建檢測器
detector = MalwareDetector()

# 創建權限管理器
perm_manager = PermissionManager("data/permissions.db")
perm_manager.create_default_admin()
admin_id = perm_manager.authenticate("admin", "admin123")

# 掃描代碼
code = "print('Hello, World!')"
result = detector.scan_code(code)
if result.is_malicious:
    print(f"⚠️ 威脅: {result.threat_level.value}")
    exit(1)

# 檢查權限
if not perm_manager.check_permission(
    admin_id, PermissionType.CODE_EXECUTE, ResourceType.PROCESS
):
    print("❌ 權限不足")
    exit(1)

# 沙盒執行
executor = sandbox.create_executor("test_1")
exec_result = executor.execute_code(code)
if exec_result.success:
    print(f"✅ 執行成功: {exec_result.output}")
```

### 3. 啟動監控
```python
monitor = ExecutionMonitor(monitor_interval=0.5)
monitor.start_monitoring()
# ... 監控代碼執行 ...
monitor.stop_monitoring()
```

## 測試

### 運行完整測試
```bash
python tests/test_security_system.py
```

### 快速驗證
```bash
python verify_security_system.py
```

### 綜合演示
```bash
python src/security/security_system_demo.py
```

## 安全特性

### 多層防禦
1. **威脅檢測** - 掃描所有代碼
2. **權限控制** - 檢查執行權限
3. **沙盒隔離** - 隔離執行環境
4. **實時監控** - 監控資源使用
5. **審計日誌** - 記錄所有操作

### 性能
- 沙盒執行: ~50-100ms
- 威脅檢測: ~1-5ms
- 權限檢查: ~1-5ms
- 監控開銷: ~1-5% CPU

## 威脅類型

| 類型 | 描述 | 威脅等級 |
|------|------|----------|
| Command Injection | 命令注入 | HIGH/CRITICAL |
| File Operation | 文件操作 | MEDIUM/HIGH |
| Network Access | 網絡訪問 | MEDIUM |
| System Call | 系統調用 | HIGH |
| Dynamic Code Exec | 動態代碼執行 | CRITICAL |
| Data Exfiltration | 數據滲漏 | HIGH |
| Privilege Escalation | 權限提升 | HIGH |
| Network Scan | 網絡掃描 | HIGH |

## 權限類型

### 文件系統 (5)
- FILE_READ, FILE_WRITE, FILE_DELETE, FILE_EXECUTE, FILE_CREATE

### 網絡 (3)
- NETWORK_CONNECT, NETWORK_LISTEN, NETWORK_BROADCAST

### 系統 (3)
- SYSTEM_EXECUTE, SYSTEM_MODIFY, SYSTEM_ADMIN

### 代碼 (3)
- CODE_EXECUTE, CODE_INJECT, CODE_DEBUG

### 數據 (4)
- DATA_READ, DATA_WRITE, DATA_DELETE, DATA_EXPORT

### 交易 (3)
- TRADE_EXECUTE, TRADE_MODIFY, TRADE_ADMIN

### 策略 (3)
- STRATEGY_EXECUTE, STRATEGY_MODIFY, STRATEGY_CREATE

### 用戶 (3)
- USER_VIEW, USER_MODIFY, USER_ADMIN

## 配置

### 資源限制
```python
limits = ResourceLimits(
    max_cpu_time=5.0,          # CPU時間 (秒)
    max_wall_time=10.0,        # 壁鐘時間 (秒)
    max_memory=128*1024*1024,  # 內存 (字節)
    max_open_files=50,         # 打開文件數
    max_processes=1,           # 進程數
    max_threads=5,             # 線程數
    allowed_file_paths=["/tmp"],  # 允許路徑
    blocked_file_paths=["/etc"],  # 阻止路徑
    container_mode=False       # 容器模式
)
```

### 監控閾值
```python
monitor.set_alert_thresholds({
    'max_cpu_percent': 80.0,
    'max_memory_mb': 512.0,
    'max_network_connections': 10,
    'max_open_files': 50
})
```

## 最佳實踐

### 1. 沙盒執行
- ✅ 設置合理的資源限制
- ✅ 使用唯一執行ID
- ✅ 設置執行超時
- ✅ 啟用容器隔離 (生產環境)

### 2. 代碼檢測
- ✅ 掃描所有用戶代碼
- ✅ 記錄檢測結果
- ✅ 定期更新威脅模式
- ✅ 添加自定義檢測規則

### 3. 權限控制
- ✅ 遵循最小權限原則
- ✅ 使用臨時權限
- ✅ 定期審計訪問日誌
- ✅ 監控異常訪問

### 4. 監控
- ✅ 設置合適的監控間隔
- ✅ 配置告警閾值
- ✅ 使用自定義告警回調
- ✅ 保存監控數據

## 故障排除

### 沙盒執行失敗
- 檢查資源限制
- 確認目錄權限
- 查看錯誤日誌

### 權限檢查失敗
- 驗證用戶狀態
- 檢查角色分配
- 確認權限有效期

### 監控數據丟失
- 檢查進程狀態
- 調整監控間隔
- 查看日誌文件

## 性能優化

1. **重用執行器** - 避免重複創建
2. **緩存權限** - 內存緩存熱權限
3. **批量檢測** - 緩存掃描結果
4. **異步監控** - 多線程監控

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

## 參考文檔

- [完整使用指南](SECURITY_SYSTEM_GUIDE.md)
- [API 參考]()
- [測試報告](../PHASE6_SECURITY_COMPLETION_REPORT.md)

## 維護

### 定期任務
- 每日審計訪問日誌
- 每周更新威脅模式
- 每月備份權限數據庫
- 每季度安全代碼審查

### 更新日誌
- v1.0 (2025-11-09) - 初始版本
  - 實現所有 4 個核心模組
  - 28 個測試用例
  - 完整文檔

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 許可證

MIT License

## 聯繫

Claude Code - 項目維護者

---

**項目狀態**: ✅ 完成
**版本**: 1.0
**最後更新**: 2025-11-09
