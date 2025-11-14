#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QF-Lib 4.0.4 Compatibility Patch for Python 3.13 + matplotlib 3.9+

This module provides a compatibility patch for QF-Lib to work with
Python 3.13 and matplotlib 3.9+ by monkey-patching the matplotlib.cm interface.

Issue: matplotlib.cm.get_cmap was deprecated in matplotlib 3.5+ and removed in 3.9+
Solution: Provide get_cmap from matplotlib.colormaps
"""

import sys
import warnings
from typing import Any, Optional

# Log the patch initialization
print("=" * 80)
print("QF-Lib 4.0.4 Compatibility Patch")
print("=" * 80)

# Try to import matplotlib and apply the patch
try:
    import matplotlib
    print(f"[OK] matplotlib version: {matplotlib.__version__}")

    # Check if get_cmap exists in matplotlib.cm
    if not hasattr(matplotlib.cm, 'get_cmap'):
        print("[WARN] matplotlib.cm.get_cmap not found - applying patch")

        # Apply patch: Use matplotlib.colormaps.get_cmap
        try:
            from matplotlib import colormaps
            matplotlib.cm.get_cmap = colormaps.get_cmap
            print("[OK] Patch applied: matplotlib.cm.get_cmap = matplotlib.colormaps.get_cmap")
        except Exception as e:
            print(f"[WARN] Could not import colormaps: {e}")

            # Fallback: Create our own get_cmap function
            def get_cmap(name=None, lut=None):
                """
                Fallback get_cmap function
                """
                from matplotlib import colormaps as cm

                if name is None:
                    return cm.get_cmap('viridis')

                # Try to get the colormap
                try:
                    return cm.get_cmap(name)
                except (KeyError, ValueError):
                    # If not found, return a default colormap
                    warnings.warn(f"Colormap '{name}' not found. Using 'viridis' instead.")
                    return cm.get_cmap('viridis')

            matplotlib.cm.get_cmap = get_cmap
            print("[OK] Patch applied: Created fallback get_cmap function")

    else:
        print("[OK] matplotlib.cm.get_cmap already available")

    # Additional patch: Ensure colormap module exists
    if not hasattr(matplotlib.cm, 'colormaps'):
        try:
            from matplotlib import colormaps
            matplotlib.cm.colormaps = colormaps
            print("[OK] Patch applied: Added matplotlib.cm.colormaps")
        except ImportError as e:
            print(f"[WARN] Could not import matplotlib.colormaps: {e}")

    print("=" * 80)
    print("QF-Lib compatibility patch applied successfully")
    print("=" * 80)

except ImportError as e:
    print(f"[WARN] Warning: Could not import matplotlib: {e}")
    print("QF-Lib may not work without matplotlib")
except Exception as e:
    print(f"[WARN] Warning: Error applying patch: {e}")

# Test the patch
print("\nTesting patch...")
try:
    import matplotlib.cm as cm
    test_cmap = cm.get_cmap('viridis')
    print(f"[OK] Test successful: cm.get_cmap('viridis') = {test_cmap}")
except Exception as e:
    print(f"[ERROR] Test failed: {e}")

print("\nPatch complete!\n")
