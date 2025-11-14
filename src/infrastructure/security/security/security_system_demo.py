"""
安全系統綜合示例 - 展示Phase 6安全與沙盒系統
包含沙盒執行、執行監控、惡意代碼檢測和權限控制
"""

import sys
import os
import logging
import time
from pathlib import Path

# 添加src目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from security.sandbox import (
    ResourceLimits,
    SecureCodeExecutor,
    SandboxManager,
    SecurityViolationError
)
from security.execution_monitor import ExecutionMonitor
from security.malware_detection import (
    MalwareDetector,
    ThreatLevel,
    ThreatType
)
from security.permission_system import (
    PermissionManager,
    PermissionType,
    ResourceType
)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/security_system_demo.log')
    ]
)
logger = logging.getLogger(__name__)


def demo_sandbox_execution():
    """演示沙盒執行"""
    print("\n" + "="*60)
    print("1. 沙盒執行系統演示")
    print("="*60)

    # 創建資源限制
    limits = ResourceLimits(
        max_cpu_time=5.0,
        max_wall_time=10.0,
        max_memory=128 * 1024 * 1024,  # 128MB
        max_open_files=50,
        max_processes=1,
        max_threads=5,
        allowed_file_paths=["/tmp", "/var/tmp"],
        blocked_file_paths=["/etc", "/sys", "/root"]
    )

    # 創建沙盒管理器
    manager = SandboxManager(limits)

    # 演示1: 安全代碼執行
    print("\n[測試1] 安全代碼執行")
    executor = manager.create_executor("test_1")

    safe_code = """
import time
import math

# 計算圓周率
result = 0.0
for i in range(1000000):
    result += (-1)**i / (2*i + 1)

print(f"PI 近似值: {4 * result}")
print(f"PI 實際值: {math.pi}")
print(f"誤差: {abs(4 * result - math.pi)}")
"""

    result = executor.execute_code(safe_code)
    print(f"執行結果: {'成功' if result.success else '失敗'}")
    print(f"執行時間: {result.execution_time:.2f}秒")
    if result.output:
        print(f"輸出: {result.output[:200]}...")

    # 演示2: 檢測危險代碼
    print("\n[測試2] 危險代碼檢測")
    executor2 = manager.create_executor("test_2")

    dangerous_code = """
import os
# 嘗試執行系統命令
os.system("ls -la /etc/passwd")
"""

    result2 = executor2.execute_code(dangerous_code, timeout=2)
    print(f"執行結果: {'成功' if result2.success else '失敗'}")
    print(f"錯誤信息: {result2.error if result2.error else '無'}")

    # 演示3: 獲取執行統計
    print("\n[測試3] 執行統計")
    stats = executor.get_execution_stats()
    print(f"總執行次數: {stats.get('total_executions', 0)}")
    print(f"成功率: {stats.get('success_rate', 0):.2%}")
    print(f"平均執行時間: {stats.get('average_execution_time', 0):.2f}秒")


def demo_malware_detection():
    """演示惡意代碼檢測"""
    print("\n" + "="*60)
    print("2. 惡意代碼檢測系統演示")
    print("="*60)

    detector = MalwareDetector()

    # 測試案例
    test_cases = [
        {
            "name": "安全代碼",
            "code": """
import math

def calculate_sma(prices, window):
    return [sum(prices[i:i+window])/window for i in range(len(prices)-window+1)]

prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
sma = calculate_sma(prices, 3)
print(sma)
"""
        },
        {
            "name": "命令注入",
            "code": """
import os

# 危險: 命令注入
user_input = input("輸入文件名: ")
os.system(f"cat {user_input}")
"""
        },
        {
            "name": "動態代碼執行",
            "code": """
import os

# 危險: eval調用
code = input("輸入代碼: ")
result = eval(code)
print(result)
"""
        },
        {
            "name": "文件操作",
            "code": """
import os

# 創建文件
with open("/tmp/test.txt", "w") as f:
    f.write("測試數據")

# 讀取文件
with open("/tmp/test.txt", "r") as f:
    print(f.read())
"""
        }
    ]

    for test_case in test_cases:
        print(f"\n[測試] {test_case['name']}")
        result = detector.scan_code(test_case['code'])

        print(f"威脅等級: {result.threat_level.value}")
        print(f"是否惡意: {result.is_malicious}")
        print(f"匹配模式: {result.matched_patterns}")
        print(f"掃描時間: {result.scan_time*1000:.2f}ms")

        if result.details.get('ast_issues'):
            print(f"AST問題: {len(result.details['ast_issues'])}個")
        if result.details.get('heuristic_triggers'):
            print(f"啟發式觸發: {result.details['heuristic_triggers']}")

    # 顯示檢測統計
    stats = detector.get_scan_stats()
    print(f"\n檢測統計:")
    print(f"總掃描次數: {stats['total_scans']}")
    print(f"威脅檢測數: {stats['threats_detected']}")
    print(f"威脅率: {stats['threat_rate']:.2%}")


def demo_execution_monitoring():
    """演示執行監控"""
    print("\n" + "="*60)
    print("3. 執行監控系統演示")
    print("="*60)

    monitor = ExecutionMonitor(monitor_interval=0.5)

    # 添加自定義告警回調
    def alert_handler(tracker, event_type, message, data):
        print(f"🚨 告警: {message}")

    monitor.add_alert_callback(alert_handler)

    # 設置告警閾值
    monitor.set_alert_thresholds({
        'max_cpu_percent': 10.0,
        'max_memory_mb': 50.0
    })

    # 啟動監控
    monitor.start_monitoring()
    print("監控已啟動")

    # 模擬執行跟蹤
    import subprocess
    import signal

    # 創建一個測試進程
    test_code = """
import time
import sys

print("開始執行...")
sys.stdout.flush()

for i in range(10):
    print(f"進度: {i+1}/10", flush=True)
    time.sleep(0.5)

print("執行完成!")
"""

    # 創建臨時文件
    with open('/tmp/test_process.py', 'w') as f:
        f.write(test_code)

    try:
        # 啟動進程
        process = subprocess.Popen(
            [sys.executable, '/tmp/test_process.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 開始跟蹤
        session_id = f"session_{int(time.time())}"
        tracker = monitor.start_execution_tracking(process.pid, session_id)

        print(f"開始跟蹤進程: PID={process.pid}, Session={session_id}")

        # 等待進程完成
        process.wait(timeout=10)

        # 停止跟蹤
        summary = monitor.stop_execution_tracking(session_id)

        print(f"\n執行摘要:")
        print(f"持續時間: {summary.get('duration_seconds', 0):.2f}秒")
        print(f"事件總數: {summary.get('total_events', 0)}")
        print(f"資源快照: {summary.get('total_resource_snapshots', 0)}次")

        if summary.get('resource_stats'):
            stats = summary['resource_stats']
            print(f"最大CPU使用: {stats.get('max_cpu', 0):.2f}%")
            print(f"最大內存使用: {stats.get('max_memory_mb', 0):.2f}MB")

    finally:
        if os.path.exists('/tmp/test_process.py'):
            os.unlink('/tmp/test_process.py')

    # 停止監控
    monitor.stop_monitoring()
    print("監控已停止")


def demo_permission_system():
    """演示權限控制系統"""
    print("\n" + "="*60)
    print("4. 權限控制系統演示")
    print("="*60)

    # 創建權限管理器
    manager = PermissionManager("data/security/demo_permissions.db")

    # 創建默認管理員
    manager.create_default_admin()

    # 創建測試用戶
    print("\n[步驟1] 創建用戶")
    user1_id = manager.create_user("alice", "password123", "alice@example.com")
    user2_id = manager.create_user("bob", "password123", "bob@example.com")

    if user1_id and user2_id:
        print(f"用戶 alice 創建成功: {user1_id}")
        print(f"用戶 bob 創建成功: {user2_id}")
    else:
        print("用戶已存在或創建失敗")
        # 獲取現有用戶
        users = manager.list_users()
        user1_id = next((u['user_id'] for u in users if u['username'] == 'alice'), None)
        user2_id = next((u['user_id'] for u in users if u['username'] == 'bob'), None)

    # 認證用戶
    print("\n[步驟2] 認證用戶")
    alice_id = manager.authenticate("alice", "password123")
    bob_id = manager.authenticate("bob", "password123")
    admin_id = manager.authenticate("admin", "admin123")

    if alice_id and admin_id:
        print(f"Alice 認證成功: {alice_id}")
        print(f"Admin 認證成功: {admin_id}")

    # 檢查權限
    print("\n[步驟3] 檢查權限")
    print(f"Alice 是否有代碼執行權限: {manager.check_permission(alice_id, PermissionType.CODE_EXECUTE, ResourceType.PROCESS)}")
    print(f"Bob 是否有交易執行權限: {manager.check_permission(bob_id, PermissionType.TRADE_EXECUTE, ResourceType.TRADE)}")
    print(f"Admin 是否有用戶管理權限: {manager.check_permission(admin_id, PermissionType.USER_ADMIN, ResourceType.USER)}")

    # 授予權限
    print("\n[步驟4] 授予權限")
    granted = manager.grant_permission(
        granted_by=admin_id,
        user_id=alice_id,
        permission=PermissionType.CODE_EXECUTE,
        resource_type=ResourceType.PROCESS,
        expires_in_hours=24
    )

    if granted:
        print("權限授予成功")
        print(f"Alice 是否有代碼執行權限(授予後): {manager.check_permission(alice_id, PermissionType.CODE_EXECUTE, ResourceType.PROCESS)}")

    # 獲取用戶有效權限
    print("\n[步驟5] 用戶有效權限")
    alice_perms = manager.get_user_permissions(alice_id)
    print(f"Alice 的權限: {[p.value for p in list(alice_perms)[:5]]}")

    # 查看訪問日誌
    print("\n[步驟6] 訪問日誌")
    logs = manager.get_access_logs(limit=10)
    print(f"最近 {len(logs)} 次訪問記錄")


def demo_integration():
    """演示綜合安全系統"""
    print("\n" + "="*60)
    print("5. 綜合安全系統演示")
    print("="*60)

    # 初始化各個組件
    detector = MalwareDetector()
    manager = SandboxManager(ResourceLimits())
    monitor = ExecutionMonitor()
    perm_manager = PermissionManager("data/security/integration_permissions.db")

    # 創建用戶並認證
    perm_manager.create_default_admin()
    admin_id = perm_manager.authenticate("admin", "admin123")

    # 測試代碼
    test_code = """
import time
import math

# 計算移動平均線
def moving_average(data, window):
    return [sum(data[i:i+window])/window for i in range(len(data)-window+1)]

# 模擬股票數據
prices = [100 + i + (i%5-2) for i in range(50)]

# 計算5日移動平均
ma5 = moving_average(prices, 5)
ma10 = moving_average(prices, 10)

print("移動平均線計算完成")
print(f"當前價格: {prices[-1]}")
print(f"5日均線: {ma5[-1]:.2f}")
print(f"10日均線: {ma10[-1]:.2f}")

# 生成交易信號
if ma5[-1] > ma10[-1]:
    print("信號: 買入")
else:
    print("信號: 賣出")
"""

    print("\n[第1步] 惡意代碼檢測")
    scan_result = detector.scan_code(test_code)
    print(f"威脅等級: {scan_result.threat_level.value}")
    print(f"掃描結果: {'安全' if not scan_result.is_malicious else '發現威脅'}")

    if scan_result.is_malicious:
        print("❌ 代碼存在威脅，終止執行")
        return

    print("\n[第2步] 權限檢查")
    if not perm_manager.check_permission(admin_id, PermissionType.CODE_EXECUTE, ResourceType.PROCESS):
        print("❌ 權限不足，拒絕執行")
        return

    print("✓ 權限驗證通過")

    print("\n[第3步] 沙盒執行")
    executor = manager.create_executor("integration_test")
    execution_result = executor.execute_code(test_code)

    if not execution_result.success:
        print(f"❌ 執行失敗: {execution_result.error}")
        return

    print("✓ 執行成功")
    print(f"執行時間: {execution_result.execution_time:.2f}秒")

    print("\n[第4步] 執行監控")
    monitor.start_monitoring()
    print("✓ 監控已啟動")

    # 清理
    time.sleep(1)
    monitor.stop_monitoring()
    print("✓ 監控已停止")

    print("\n✅ 綜合安全檢查完成 - 所有階段通過")


def main():
    """主函數"""
    print("\n" + "="*60)
    print(" Phase 6: 安全與沙盒系統 - 綜合演示")
    print("="*60)
    print("\n此演示展示以下安全功能:")
    print("1. 安全沙盒執行環境")
    print("2. 惡意代碼檢測")
    print("3. 實時執行監控")
    print("4. 權限控制系統")
    print("5. 綜合安全檢查")

    # 創建日誌目錄
    Path("logs").mkdir(exist_ok=True)
    Path("data/security").mkdir(parents=True, exist_ok=True)

    try:
        # 執行各個演示
        demo_sandbox_execution()
        demo_malware_detection()
        demo_execution_monitoring()
        demo_permission_system()
        demo_integration()

        print("\n" + "="*60)
        print("✅ 所有演示完成!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
