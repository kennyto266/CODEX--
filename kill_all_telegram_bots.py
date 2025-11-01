#!/usr/bin/env python3
"""
Kill all Telegram bot processes
"""

import os
import sys
import subprocess

def kill_process(pid):
    """Kill a process by PID"""
    try:
        result = subprocess.run(
            ['taskkill', '/PID', str(pid), '/F'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error killing {pid}: {e}")
        return False

def main():
    """Main function"""
    # List of PIDs to kill
    pids = [
        27684, 59624, 29080, 18716, 23928, 17592, 55864, 54856, 47176,
        41780, 43928, 48948, 24500, 59168, 54540, 56452, 46776
    ]

    print(f"Killing {len(pids)} processes...")
    killed = 0
    for pid in pids:
        if kill_process(pid):
            killed += 1
            print(f"Killed PID {pid}")
        else:
            print(f"Failed to kill PID {pid}")

    print(f"\nKilled {killed} processes")

    # Wait a bit
    print("Waiting 30 seconds...")
    import time
    time.sleep(30)

    # Test Telegram API
    print("\nTesting Telegram API...")
    import requests
    token = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=1"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('ok'):
            print("SUCCESS: No conflicts detected!")
        else:
            print(f"API Error: {data.get('description')}")
    except Exception as e:
        print(f"API Test Failed: {e}")

if __name__ == '__main__':
    main()
