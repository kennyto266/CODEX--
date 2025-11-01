#!/usr/bin/env python3
"""
清理所有 Bot 實例並重新啟動穩定版 Bot
"""

import subprocess
import time
import os
import signal

def kill_bot_processes():
    """終止所有可能的 Bot 進程"""
    print("=== 查找並終止所有 Bot 進程 ===")

    # 獲取所有 Python 進程
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')

        killed_pids = []
        for line in lines:
            if 'python' in line.lower() and any(x in line.lower() for x in ['telegram', 'bot', 'stable', 'complete', 'quant']):
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        # 終止進程
                        os.kill(pid, signal.SIGKILL)
                        killed_pids.append(pid)
                        print(f"Killed process {pid}")
                    except Exception as e:
                        print(f"Failed to kill {pid}: {e}")

        print(f"\nTotal processes killed: {len(killed_pids)}")
        return killed_pids
    except Exception as e:
        print(f"Error: {e}")
        return []

def start_stable_bot():
    """啟動穩定版 Bot"""
    print("\n=== 啟動穩定版 Telegram Bot ===")

    try:
        # 啟動 bot
        process = subprocess.Popen(
            ['python', 'telegram_bot_stable.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        print(f"Bot started with PID: {process.pid}")

        # 等待 20 秒
        print("Waiting 20 seconds for bot to start...")
        time.sleep(20)

        # 檢查進程是否還在運行
        if process.poll() is None:
            print("Bot is running successfully!")
            return True
        else:
            print("Bot has stopped")
            return False
    except Exception as e:
        print(f"Failed to start bot: {e}")
        return False

def main():
    print("=" * 60)
    print("Bot Conflict Fix Script")
    print("=" * 60)

    # 步驟 1: 終止所有 bot 進程
    killed = kill_bot_processes()

    # 步驟 2: 等待 Telegram 釋放連接
    print("\nWaiting 60 seconds for Telegram to release connections...")
    time.sleep(60)

    # 步驟 3: 啟動穩定版 Bot
    success = start_stable_bot()

    if success:
        print("\n" + "=" * 60)
        print("SUCCESS! Stable bot is running")
        print("=" * 60)
        print("Now you can test:")
        print("  /score nba")
        print("  /score soccer")
        print("  /mark6")
    else:
        print("\nFAILED to start bot")

if __name__ == '__main__':
    main()
