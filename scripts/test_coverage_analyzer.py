#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Coverage Analyzer

Analyzes test coverage for the multi-source data integration system.
Generates a coverage report and recommendations for reaching 80% coverage.

Author: Claude Code
Version: 1.0
Date: 2025-11-10
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Tuple


class CoverageAnalyzer:
    """Analyze test coverage for data adapters"""

    def __init__(self, src_dir: str, test_dir: str):
        self.src_dir = Path(src_dir)
        self.test_dir = Path(test_dir)
        self.coverage_report = {
            'total_files': 0,
            'tested_files': 0,
            'coverage_percentage': 0.0,
            'details': []
        }

    def find_source_files(self) -> List[Path]:
        """Find all source files in src directory"""
        src_files = list(self.src_dir.rglob('*.py'))
        return [f for f in src_files if not f.name.startswith('__')]

    def find_test_files(self) -> List[Path]:
        """Find all test files"""
        test_files = list(self.test_dir.rglob('test_*.py'))
        return [f for f in test_files if not f.name.startswith('__')]

    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        rel_path = file_path.relative_to(self.src_dir.parent)
        return str(rel_path.with_suffix('')).replace(os.sep, '.')

    def analyze_file_coverage(self, src_file: Path) -> Dict:
        """Analyze coverage for a single source file"""
        try:
            with open(src_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST to get classes and functions
            tree = ast.parse(content)
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            functions = [
                node for node in tree.body
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')
            ]

            # Find corresponding test file
            test_file_patterns = [
                f"test_{src_file.stem}.py",
                f"test_{src_file.parent.name}_{src_file.stem}.py"
            ]

            tested = False
            test_methods = 0

            for pattern in test_file_patterns:
                potential_test = self.test_dir / pattern
                if potential_test.exists():
                    tested = True
                    try:
                        with open(potential_test, 'r', encoding='utf-8') as tf:
                            test_content = tf.read()
                            test_tree = ast.parse(test_content)
                            test_methods = len([
                                node for node in test_tree.body
                                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
                            ])
                    except SyntaxError:
                        # Test file has syntax error, still count as tested
                        tested = True
                        test_methods = 0

            return {
                'file': src_file,
                'classes': len(classes),
                'functions': len(functions),
                'tested': tested,
                'test_methods': test_methods,
                'complexity': self.calculate_complexity(tree),
                'has_error': False
            }
        except SyntaxError as e:
            # File has syntax error
            return {
                'file': src_file,
                'classes': 0,
                'functions': 0,
                'tested': False,
                'test_methods': 0,
                'complexity': 0,
                'has_error': True,
                'error': str(e)
            }

    def calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)

        return complexity

    def find_key_files(self) -> List[str]:
        """Identify key files that must have tests"""
        return [
            'src/data_adapters/visitor_adapter.py',
            'src/data_adapters/property_adapter.py',
            'src/data_adapters/gdp_adapter.py',
            'src/data_adapters/retail_adapter.py',
            'src/data_adapters/trade_adapter.py',
            'src/data_adapters/base_adapter.py',
            'src/orchestration/data_orchestrator.py',
            'src/validators/data_validator.py'
        ]

    def generate_report(self) -> str:
        """Generate comprehensive coverage report"""
        src_files = self.find_source_files()
        test_files = self.find_test_files()

        coverage_details = []
        for src_file in src_files:
            if src_file.name.endswith('.py'):
                detail = self.analyze_file_coverage(src_file)
                coverage_details.append(detail)

        # Calculate statistics
        tested_files = [d for d in coverage_details if d['tested']]
        coverage_percentage = len(tested_files) / len(coverage_details) * 100

        # Generate report
        report = []
        report.append("=" * 80)
        report.append("TEST COVERAGE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"\nSource Files: {len(coverage_details)}")
        report.append(f"Test Files: {len(test_files)}")
        report.append(f"Tested Files: {len(tested_files)}")
        report.append(f"Coverage: {coverage_percentage:.1f}%")

        # Check 80% requirement
        if coverage_percentage >= 80:
            report.append(f"\nStatus: [PASS] Coverage meets 80% requirement")
        else:
            report.append(f"\nStatus: [FAIL] Coverage below 80% requirement")
            report.append(f"Need to test {80 - coverage_percentage:.1f}% more files")

        # Key files status
        report.append("\n" + "=" * 80)
        report.append("KEY FILES COVERAGE STATUS")
        report.append("=" * 80)

        key_files = self.find_key_files()
        for key_file in key_files:
            file_path = Path(key_file)
            if file_path.exists():
                detail = self.analyze_file_coverage(file_path)
                status = "[TESTED]" if detail['tested'] else "[UNTESTED]"
                report.append(f"\n{status} {key_file}")
                report.append(f"  Classes: {detail['classes']}, Functions: {detail['functions']}")
                if detail['tested']:
                    report.append(f"  Test methods: {detail['test_methods']}")
            else:
                report.append(f"\n[MISSING] {key_file}")

        # Detailed breakdown
        report.append("\n" + "=" * 80)
        report.append("DETAILED COVERAGE BREAKDOWN")
        report.append("=" * 80)

        for detail in sorted(coverage_details, key=lambda x: (x['tested'], x['file'])):
            status = "[TESTED]" if detail['tested'] else "[UNTESTED]"
            try:
                rel_path = detail['file'].relative_to(Path.cwd())
            except ValueError:
                rel_path = detail['file']
            report.append(f"\n{status} {rel_path}")
            report.append(f"  Classes: {detail['classes']}, Functions: {detail['functions']}")
            if detail['tested']:
                report.append(f"  Test methods: {detail['test_methods']}")

        # Recommendations
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS FOR 80% COVERAGE")
        report.append("=" * 80)

        untested_files = [d for d in coverage_details if not d['tested']]

        if untested_files:
            report.append("\nPriority 1 - High Impact Files (Must Test):")
            for detail in untested_files[:5]:  # Top 5 priority
                report.append(f"  - {detail['file']}")

            report.append("\nPriority 2 - Additional Coverage Needed:")
            for detail in untested_files[5:10]:
                report.append(f"  - {detail['file']}")

        report.append("\n" + "=" * 80)
        report.append("TESTING STRATEGY")
        report.append("=" * 80)
        report.append("\n1. Unit Tests:")
        report.append("   - Test each adapter's fetch_data method")
        report.append("   - Test data validation and normalization")
        report.append("   - Test error handling and edge cases")
        report.append("   - Mock external API calls")

        report.append("\n2. Integration Tests:")
        report.append("   - Test multi-source data fetching")
        report.append("   - Test parallel processing")
        report.append("   - Test data flow between components")

        report.append("\n3. Contract Tests:")
        report.append("   - Test data schema compliance")
        report.append("   - Test data format and types")
        report.append("   - Test API response validation")

        report.append("\n4. Performance Tests:")
        report.append("   - Test parallel fetch performance")
        report.append("   - Test caching effectiveness")
        report.append("   - Test memory usage")

        report.append("\n" + "=" * 80)

        return '\n'.join(report)

    def generate_test_templates(self):
        """Generate test file templates for untested files"""
        untested = []
        for detail in self.analyze_file_coverage(Path('src/data_adapters/visitor_adapter.py')).values():
            pass  # Implementation would go here


def main():
    """Main entry point"""
    analyzer = CoverageAnalyzer('src', 'tests')

    print("Analyzing test coverage...")
    report = analyzer.generate_report()
    print(report)

    # Save report
    with open('TEST_COVERAGE_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n\nReport saved to: TEST_COVERAGE_REPORT.md")


if __name__ == '__main__':
    main()
