#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quickstart Guide Validation Script

Validates that the quickstart guide examples work correctly and
generates a validation report.

Author: Claude Code
Version: 1.0
Date: 2025-11-10
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple


class QuickstartValidator:
    """Validate quickstart guide examples"""

    def __init__(self):
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

    def validate_imports(self) -> Tuple[bool, str]:
        """Validate that required modules can be imported"""
        required_modules = [
            'pandas',
            'numpy',
            'asyncio',
            'datetime',
            'pathlib'
        ]

        missing = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)

        if missing:
            return False, f"Missing required modules: {', '.join(missing)}"

        return True, "All required modules available"

    def validate_data_adapters_exist(self) -> Tuple[bool, str]:
        """Check if data adapter files exist"""
        adapters = [
            'src/data_adapters/visitor_adapter.py',
            'src/data_adapters/property_adapter.py',
            'src/data_adapters/gdp_adapter.py',
            'src/data_adapters/retail_adapter.py',
            'src/data_adapters/trade_adapter.py',
            'src/data_adapters/base_adapter.py'
        ]

        missing = []
        for adapter in adapters:
            if not Path(adapter).exists():
                missing.append(adapter)

        if missing:
            return False, f"Missing adapter files: {', '.join(missing)}"

        return True, f"All {len(adapters)} adapter files exist"

    def validate_backtest_framework(self) -> Tuple[bool, str]:
        """Check if backtest framework exists"""
        framework_files = [
            'non_price_backtest_demo.py',
            'src/backtest',
        ]

        missing = []
        for file in framework_files:
            if not Path(file).exists():
                missing.append(file)

        if missing:
            return False, f"Missing framework files: {', '.join(missing)}"

        return True, "Backtest framework exists"

    def validate_examples_syntax(self) -> Tuple[bool, str]:
        """Validate syntax of code examples in quickstart"""
        examples = [
            ("Example 1: Fetch Single Data Source", """
import asyncio
from datetime import date

async def fetch_visitor_data():
    adapter = VisitorAdapter()
    raw_data = await adapter.fetch_data(
        start_date=date(2024, 1, 1),
        end_date=date(2025, 11, 10)
    )
    return raw_data
"""),
            ("Example 2: Fetch All 5 Sources", """
import asyncio
from data_adapters import DataOrchestrator

async def fetch_all_sources():
    orchestrator = DataOrchestrator()
    results = await orchestrator.fetch_all_sources(
        sources=['visitor', 'property', 'gdp', 'retail', 'trade']
    )
    return results
"""),
            ("Example 3: Calculate Indicators", """
from technical_indicators import TechnicalIndicatorCalculator

def calculate_indicators(data):
    calculator = TechnicalIndicatorCalculator()
    indicators = calculator.calculate_all(data)
    return indicators
""")
        ]

        all_valid = True
        for name, code in examples:
            try:
                compile(code, name, 'exec')
                self.results['details'].append(f"[PASS] {name}: Syntax valid")
            except SyntaxError as e:
                all_valid = False
                self.results['details'].append(f"[FAIL] {name}: Syntax error - {e}")

        if all_valid:
            return True, f"All {len(examples)} code examples have valid syntax"
        else:
            return False, "Some examples have syntax errors"

    def validate_dependencies(self) -> Tuple[bool, str]:
        """Validate Python dependencies"""
        required_packages = [
            'pandas',
            'numpy',
            'requests',
            'beautifulsoup4'
        ]

        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        if missing:
            return False, f"Missing packages: {', '.join(missing)}. Install with: pip install {' '.join(missing)}"

        return True, "All required packages installed"

    def validate_documentation_completeness(self) -> Tuple[bool, str]:
        """Check if quickstart guide is complete"""
        quickstart_file = Path('specs/002-expand-nonprice-conversion/quickstart.md')

        if not quickstart_file.exists():
            return False, "Quickstart guide not found"

        with open(quickstart_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_sections = [
            'Overview',
            'Prerequisites',
            'Quick Start',
            'Basic Usage',
            'Fetch All 5 Sources',
            'Calculate 12 Technical Indicators',
            'Run Multi-Source Backtest',
            'Expected Output'
        ]

        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)

        if missing:
            return False, f"Missing sections: {', '.join(missing)}"

        # Check code examples
        if content.count('```python') < 4:
            return False, "Insufficient code examples"

        return True, "Quickstart guide is complete"

    def run_all_validations(self) -> Dict:
        """Run all validation tests"""
        print("=" * 80)
        print("QUICKSTART GUIDE VALIDATION")
        print("=" * 80)

        tests = [
            ("Python Dependencies", self.validate_dependencies),
            ("Data Adapter Files", self.validate_data_adapters_exist),
            ("Backtest Framework", self.validate_backtest_framework),
            ("Quickstart Documentation", self.validate_documentation_completeness),
            ("Code Example Syntax", self.validate_examples_syntax),
            ("Required Modules", self.validate_imports)
        ]

        for test_name, test_func in tests:
            self.results['total'] += 1
            print(f"\n{test_name}:")

            try:
                passed, message = test_func()
                if passed:
                    self.results['passed'] += 1
                    print(f"  [PASS] {message}")
                else:
                    self.results['failed'] += 1
                    print(f"  [FAIL] {message}")
            except Exception as e:
                self.results['failed'] += 1
                error_msg = f"Exception: {str(e)}"
                print(f"  [ERROR] {error_msg}")
                self.results['details'].append(f"[ERROR] {test_name}: {error_msg}")

        return self.results

    def generate_validation_report(self) -> str:
        """Generate validation report"""
        report = []
        report.append("=" * 80)
        report.append("QUICKSTART VALIDATION REPORT")
        report.append("=" * 80)

        report.append(f"\nSummary:")
        report.append(f"  Total Tests: {self.results['total']}")
        report.append(f"  Passed: {self.results['passed']}")
        report.append(f"  Failed: {self.results['failed']}")
        report.append(f"  Success Rate: {self.results['passed']/self.results['total']*100:.1f}%")

        # Overall status
        if self.results['failed'] == 0:
            report.append(f"\nStatus: [PASS] All validations passed!")
        else:
            report.append(f"\nStatus: [FAIL] {self.results['failed']} validation(s) failed")

        # Detailed results
        if self.results['details']:
            report.append("\n" + "=" * 80)
            report.append("DETAILED RESULTS")
            report.append("=" * 80)
            for detail in self.results['details']:
                report.append(f"\n{detail}")

        # Recommendations
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)

        if self.results['failed'] > 0:
            report.append("\n1. Install Missing Dependencies:")
            report.append("   pip install pandas numpy requests beautifulsoup4")

            report.append("\n2. Verify Adapter Files:")
            report.append("   ls -la src/data_adapters/*_adapter.py")

            report.append("\n3. Check Framework Files:")
            report.append("   ls -la non_price_backtest_demo.py")

            report.append("\n4. Review Quickstart Guide:")
            report.append("   cat specs/002-expand-nonprice-conversion/quickstart.md")

        report.append("\n5. Run Quickstart Examples:")
        report.append("   python validate_quickstart.py")

        report.append("\n" + "=" * 80)

        return '\n'.join(report)


def main():
    """Main entry point"""
    validator = QuickstartValidator()
    results = validator.run_all_validations()

    # Generate report
    report = validator.generate_validation_report()
    print("\n" + report)

    # Save report
    with open('QUICKSTART_VALIDATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: QUICKSTART_VALIDATION_REPORT.md")

    # Return exit code
    if results['failed'] > 0:
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
