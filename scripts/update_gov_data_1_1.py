#!/usr/bin/env python3
"""
Scheduled Data.gov.hk Real Data Updater

Daily automatic update from data.gov.hk to get latest real data
"""

import os
import sys
import subprocess
from datetime import datetime

def daily_update():
    """Daily data update"""
    print(f"[{datetime.now()}] Starting daily data update...")

    # Run download script
    try:
        result = subprocess.run([
            sys.executable, "activate_real_gov_data_ascii.py"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("[OK] Data update successful")
        else:
            print("[FAIL] Data update failed")
            print(result.stderr)

    except Exception as e:
        print(f"[FAIL] Update process error: {e}")

if __name__ == "__main__":
    daily_update()
