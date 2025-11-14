"""
Pipet Non-Price Data Crawler Module

This module provides natural language interface for configuring and executing
web scraping tasks using pipet for non-price economic data collection.

Components:
- nlp_interface: Natural language processing for user descriptions
- pipet_config_generator: Automatic pipet configuration generation
- batch_processor: Batch processing for multiple data sources
- quality_monitor: Data quality monitoring and validation
"""

__version__ = "1.0.0"
__author__ = "CODEX Quant Trading System"

from .nlp_interface import NLPInterface
from .pipet_config_generator import PipetConfigGenerator
from .batch_processor import BatchProcessor

__all__ = [
    "NLPInterface",
    "PipetConfigGenerator",
    "BatchProcessor"
]