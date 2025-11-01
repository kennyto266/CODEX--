#!/usr/bin/env python3
"""
只啟動穩定版 Bot，終止其他所有 Bot
"""

import subprocess
import time
import os
import signal

def kill_all_bot_processes():
    """終止所有 bot 相關進程"""
    print("=== 查找並終止所有 Bot 進程 ===")

    # 獲取所有 Python 進程
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')

        killed = []
        for line in lines:
            if 'python' in line.lower() and any(x in line for x in ['telegram', 'bot', 'quant']):
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    # 終止進程
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        killed.append(pid)
                        print(f"✅ 已終止進程 {pid}")
                    except Exception as e:
                        print(f"❌ 無法終止進程 {pid}: {e}")

        print(f"\n共終止 {len(killed)} 個進程")
        return killed
    except Exception as e:
        print(f"錯誤: {e}")
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

        print(f"✅ Bot 已啟動，PID: {process.pid}")

        # 等待 15 秒
        print("等待 15 秒讓 Bot 啟動...")
        time.sleep(15)

        # 檢查進程是否還在運行
        if process.poll() is None:
            print("✅ Bot 正在運行")
            return process
        else:
            print("❌ Bot 已停止")
            return None
    except Exception as e:
        print(f"❌ 啟動 Bot 失敗: {e}")
        return None

def main():
    print("=" * 60)
    print("Telegram Bot 清理和重啟腳本")
    print("=" * 60)

    # 步驟 1: 終止所有 bot 進程
    killed = kill_all_bot_processes()

    # 步驟 2: 等待 Telegram 釋放連接
    print("\n等待 60 秒讓 Telegram 釋放連接...")
    time.sleep(60)

    # 步驟 3: 啟動穩定版 Bot
    bot = start_stable_bot()

    if bot:
        print("\n" + "=" * 60)
        print("✅ 穩定版 Bot 啟動成功！")
        print("=" * 60)
        print(f"PID: {bot.pid}")
        print("日誌文件: STABLE_WORKING.log")
        print("測試指令: tail -f STABLE_WORKING.log")
        print("\n在 Telegram 中發送 /start 給 @penguinai_bot 測試")
    else:
        print("\n❌ Bot 啟動失敗")

if __name__ == '__main__':
    main()
