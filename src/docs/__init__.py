"""
文档测试和验证系统 (T599)

一个全面的文档质量保证工具集，包含质量检查、自动化测试、
实时监控和CI/CD集成等功能。

主要模块:
- quality_checker: 文档质量检查器
- monitor: 监控系统
- test_framework: 文档测试框架

使用示例:
    from src.docs import DocumentationQualityChecker

    checker = DocumentationQualityChecker('.', './docs', './src')
    results = checker.check_all()
"""

__version__ = '1.0.0'
__author__ = 'Claude Code Team'
__email__ = 'claude@anthropic.com'

# 导出主要类
from .quality_checker import DocumentationQualityChecker
from .monitor import DocumentationMonitor
from .test_framework import DocumentationTestFramework, TestStatus, CodeTestResult

__all__ = [
    'DocumentationQualityChecker',
    'DocumentationMonitor',
    'DocumentationTestFramework',
    'TestStatus',
    'CodeTestResult'
]
