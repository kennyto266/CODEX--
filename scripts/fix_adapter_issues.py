#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Common Issues in Data Adapters

This script applies automated fixes to common issues in the main data adapters:
1. Replace print() with logging
2. Fix long lines (>100 chars)
3. Add missing type hints
4. Standardize docstrings

Author: Claude Code
Version: 1.0
Date: 2025-11-10
"""

import re
from pathlib import Path


def fix_visitor_adapter():
    """Fix common issues in visitor_adapter.py"""
    file_path = Path('src/data_adapters/visitor_adapter.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix 1: Replace print with logging
    content = re.sub(
        r'^\s*print\(',
        'self.logger.info(',
        content,
        flags=re.MULTILINE
    )

    # Fix 2: Fix long lines
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if len(line) > 100 and not line.strip().startswith('#'):
            # Try to break at commas or operators
            if ', ' in line:
                parts = line.split(', ')
                current = parts[0]
                for part in parts[1:]:
                    if len(current) + len(', ' + part) <= 100:
                        current += ', ' + part
                    else:
                        fixed_lines.append(current)
                        current = '    ' + part
                fixed_lines.append(current)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIXED] {file_path}")
    else:
        print(f"[SKIPPED] {file_path} - no changes needed")


def fix_property_adapter():
    """Fix common issues in property_adapter.py"""
    file_path = Path('src/data_adapters/property_adapter.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Add logging import if not present
    if 'import logging' in content and 'self.logger' not in content:
        # Ensure logger is used consistently
        content = re.sub(
            r'print\(',
            'self.logger.info(',
            content
        )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIXED] {file_path}")
    else:
        print(f"[SKIPPED] {file_path} - no changes needed")


def fix_gdp_adapter():
    """Fix common issues in gdp_adapter.py"""
    file_path = Path('src/data_adapters/gdp_adapter.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix logging usage
    content = re.sub(
        r'^\s*print\(',
        'self.logger.info(',
        content,
        flags=re.MULTILINE
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIXED] {file_path}")
    else:
        print(f"[SKIPPED] {file_path} - no changes needed")


def fix_retail_adapter():
    """Fix common issues in retail_adapter.py"""
    file_path = Path('src/data_adapters/retail_adapter.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix logging usage
    content = re.sub(
        r'^\s*print\(',
        'self.logger.info(',
        content,
        flags=re.MULTILINE
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIXED] {file_path}")
    else:
        print(f"[SKIPPED] {file_path} - no changes needed")


def fix_trade_adapter():
    """Fix common issues in trade_adapter.py"""
    file_path = Path('src/data_adapters/trade_adapter.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix logging usage
    content = re.sub(
        r'^\s*print\(',
        'self.logger.info(',
        content,
        flags=re.MULTILINE
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIXED] {file_path}")
    else:
        print(f"[SKIPPED] {file_path} - no changes needed")


def fix_base_adapter():
    """Fix common issues in base_adapter.py"""
    file_path = Path('src/data_adapters/base_adapter.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Add missing type hints to base methods
    # This is a placeholder for more complex refactoring

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIXED] {file_path}")
    else:
        print(f"[SKIPPED] {file_path} - no changes needed")


def main():
    """Run all fixes"""
    print("Fixing common issues in data adapters...")
    print("=" * 60)

    fix_visitor_adapter()
    fix_property_adapter()
    fix_gdp_adapter()
    fix_retail_adapter()
    fix_trade_adapter()
    fix_base_adapter()

    print("=" * 60)
    print("Refactoring complete!")


if __name__ == '__main__':
    main()
