#!/usr/bin/env python3
"""
Kill old bot processes
"""

import os
import signal

pids_to_kill = [14128, 18128, 612]

for pid in pids_to_kill:
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Killed PID {pid}")
    except ProcessLookupError:
        print(f"PID {pid} not found")
    except Exception as e:
        print(f"Failed to kill PID {pid}: {e}")

print("Done killing processes")
