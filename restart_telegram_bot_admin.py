#!/usr/bin/env python3
"""
高級 Telegram Bot 管理腳本
完全清理並重啟 Bot
"""

import os
import sys
import subprocess
import time
import signal

def kill_process_tree(pid):
    """殺死進程樹"""
    try:
        # 使用 taskkill 強制終止進程及其子進程
        result = subprocess.run(
            ['taskkill', '/PID', str(pid), '/F', '/T'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False

def find_and_kill_bot_processes():
    """查找並終止所有 Bot 進程"""
    print("=== 正在查找 Telegram Bot 進程 ===")

    # 使用 WMIC 查找所有相關進程
    result = subprocess.run([
        'wmic', 'process',
        'where', 'CommandLine like \'%telegram_bot%\'',
        'get', 'ProcessId,Name'
    ], capture_output=True, text=True)

    lines = result.stdout.strip().split('\n')
    killed = 0
    found = 0

    for line in lines[1:]:  # 跳過標題行
        line = line.strip()
        if not line or 'WMIC.exe' in line:
            continue

        parts = line.split()
        if parts:
            pid = parts[0]
            if pid.isdigit():
                found += 1
                print(f"發現 Bot 進程 PID: {pid}")
                if kill_process_tree(pid):
                    killed += 1
                    print(f"[OK] 已終止進程 {pid}")
                else:
                    print(f"[ERROR] 無法終止進程 {pid}")
                time.sleep(1)

    print(f"\n找到 {found} 個進程，終止 {killed} 個")
    return killed

def wait_for_telegram_release():
    """等待 Telegram 釋放連接"""
    print("\n=== 等待 Telegram 釋放連接 ===")

    import requests
    token = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=1"

    max_attempts = 30
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, timeout=5)
            data = response.json()

            if data.get('ok'):
                print(f"[OK] 第 {attempt} 次嘗試: API 正常")
                if not data.get('result'):
                    print("[OK] 沒有待處理的更新，可以啟動 Bot")
                    return True
                else:
                    print(f"  還有 {len(data['result'])} 個待處理的更新")
            else:
                print(f"[ERROR] 第 {attempt} 次嘗試: API 錯誤 - {data.get('description')}")

        except Exception as e:
            print(f"[ERROR] 第 {attempt} 次嘗試: 連接錯誤 - {e}")

        if attempt < max_attempts:
            print("  等待 10 秒後重試...")
            time.sleep(10)

    print("[WARNING] 等待超時，但仍將嘗試啟動 Bot")
    return False

def start_bot():
    """啟動 Bot"""
    print("\n=== 啟動完整版 Telegram Bot ===")

    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'

    # 啟動 Bot 進程
    process = subprocess.Popen(
        [sys.executable, 'telegram_bot_complete.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )

    print(f"Bot 已啟動，PID: {process.pid}")
    return process

def monitor_bot(process):
    """監控 Bot"""
    print("\n=== 監控 Bot 運行狀態 ===")

    # 等待 15 秒讓 Bot 啟動
    time.sleep(15)

    # 檢查進程是否還在運行
    if process.poll() is None:
        print("[OK] Bot 進程正在運行")

        # 檢查日誌
        if os.path.exists('COMPLETE_bot.log'):
            print("\n--- 最近 20 行日誌 ---")
            with open('COMPLETE_bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())
            print("--- 日誌結束 ---\n")
        else:
            print("[WARNING] 日誌文件不存在")

        return True
    else:
        print("[ERROR] Bot 進程已停止")
        return False

def main():
    """主程序"""
    print("=" * 60)
    print("Telegram Bot 高級管理腳本")
    print("=" * 60)

    # 步驟 1: 終止所有 Bot 進程
    killed = find_and_kill_bot_processes()

    # 步驟 2: 等待 Telegram 釋放連接
    can_start = wait_for_telegram_release()

    # 步驟 3: 啟動 Bot
    if can_start or killed > 0:
        process = start_bot()

        # 步驟 4: 監控
        success = monitor_bot(process)

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] Bot 管理完成！")
            print("=" * 60)
            print("\n📊 Bot 信息:")
            print(f"  進程 PID: {process.pid}")
            print(f"  日誌文件: COMPLETE_bot.log")
            print(f"  命令: python telegram_bot_complete.py")
            print("\n💡 使用說明:")
            print("  tail -f COMPLETE_bot.log  - 實時查看日誌")
            print("  ps -p {pid}               - 檢查進程狀態")
            print("\n🎯 測試 Bot: 在 Telegram 中發送 /start 給 @penguinai_bot")
        else:
            print("\n[FAILED] Bot 啟動失敗，請檢查日誌")
            sys.exit(1)
    else:
        print("\n[FAILED] 無法啟動 Bot，請檢查系統狀態")
        sys.exit(1)

if __name__ == '__main__':
    main()
