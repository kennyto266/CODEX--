"""
Mock implementations of Phase 2 interfaces for testing.

This module provides mock implementations of:
- IDataSource (data sources)
- IDataCleaner (data cleaners)
- IProcessor (data processors)
- IStrategy (trading strategies)
- IVariableManager (variable management)
- IChartBuilder (chart builders)
- IAnalyzer (analyzers)

Used by: integration tests and test mocks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import interfaces
from src.data_pipeline.sources.base_source import (
    IDataSource,
    IDataCleaner,
    IProcessor,
    ValidationResult,
    DataMetadata,
)
from src.core.base_strategy import (
    IStrategy,
    IVariableManager,
    IParameterManager,
    Signal,
    SignalType,
    Variable,
)
from src.visualization.base_chart import (
    IChartBuilder,
    IAnalyzer,
    ChartConfig,
)

from tests.fixtures.mock_data import mock_ohlcv_data


class MockDataSource(IDataSource):
    """Mock data source for testing data layer."""

    def __init__(self, data: Optional[pd.DataFrame] = None):
        """Initialize with optional data."""
        self.data = data if data is not None else mock_ohlcv_data()
        self.last_metadata = None

    def fetch_raw(self, symbol: str, start_date, end_date, **kwargs) -> Dict[str, Any]:
        """Fetch mock raw data."""
        return {
            'data': self.data.copy(),
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
        }

    def validate(self, raw_data: Dict[str, Any]) -> ValidationResult:
        """Validate mock data - always returns valid for simplicity."""
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            quality_score=0.95,
        )

    def get_metadata(self) -> DataMetadata:
        """Get mock metadata."""
        if self.last_metadata is None:
            self.last_metadata = DataMetadata(
                symbol='0700.HK',
                start_date=self.data.index[0],
                end_date=self.data.index[-1],
                record_count=len(self.data),
                source_name='mock_source',
                last_updated=datetime.now(),
                data_frequency='daily',
                has_missing_data=False,
            )
        return self.last_metadata

    @property
    def source_name(self) -> str:
        """Return source name."""
        return 'mock_source'


class MockDataCleaner(IDataCleaner):
    """Mock data cleaner for testing data layer."""

    def __init__(self):
        """Initialize cleaner."""
        self.last_quality_score = 1.0
        self.operations_applied = []

    def clean(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Clean mock data."""
        cleaned = raw_data.copy()

        # Simulate cleaning operations
        self.operations_applied = [
            'removed_nan',
            'removed_outliers',
            'normalized_volume',
        ]

        # Just return data as-is for mock
        self.last_quality_score = 0.95
        return cleaned

    def get_quality_score(self) -> float:
        """Return mock quality score."""
        return self.last_quality_score

    @property
    def cleaning_operations_applied(self) -> list:
        """Return operations applied."""
        return self.operations_applied


class MockProcessor(IProcessor):
    """Mock data processor for testing data layer."""

    def __init__(self):
        """Initialize processor."""
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process mock data."""
        processed = data.copy()

        # Record processing info
        self.processing_info = {
            'temporal_aligned': True,
            'normalized': True,
            'num_records': len(processed),
        }

        return processed

    def get_processing_info(self) -> Dict[str, Any]:
        """Return processing information."""
        return self.processing_info


class MockStrategy(IStrategy):
    """Mock trading strategy for testing calculation layer."""

    def __init__(self, name: str = "MockStrategy"):
        """Initialize strategy."""
        self.name = name
        self.parameters = {'threshold': 0.5}
        self.initialized = False
        self.supported_symbols = ['0700.HK', '0388.HK', '1398.HK']

    def initialize(self, historical_data: pd.DataFrame, **kwargs) -> None:
        """Initialize strategy with historical data."""
        self.initialized = True

    def generate_signals(self, current_data: pd.DataFrame) -> List[Signal]:
        """Generate mock trading signals."""
        if not self.initialized:
            return []

        # Generate a random signal
        signal_type = np.random.choice([SignalType.BUY, SignalType.SELL, SignalType.HOLD])

        return [
            Signal(
                symbol='0700.HK',
                timestamp=pd.Timestamp.now(),
                signal_type=signal_type,
                confidence=0.75,
                reason='Mock signal for testing',
                price=100.0,
                metadata={'mock': True},
            )
        ]

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.parameters.copy()

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set strategy parameters."""
        self.parameters.update(parameters)

    @property
    def strategy_name(self) -> str:
        """Return strategy name."""
        return self.name

    @property
    def supported_symbols(self) -> List[str]:
        """Return supported symbols."""
        return self._supported_symbols

    @supported_symbols.setter
    def supported_symbols(self, symbols: List[str]):
        """Set supported symbols."""
        self._supported_symbols = symbols


class MockVariableManager(IVariableManager):
    """Mock variable manager for testing calculation layer."""

    def __init__(self):
        """Initialize manager."""
        self.variables = {}
        self.cache = {}

    def register_variable(self, name: str, calculation_func, refresh_frequency: str = "daily") -> None:
        """Register a variable."""
        self.variables[name] = {
            'func': calculation_func,
            'frequency': refresh_frequency,
        }

    def get_variable(self, symbol: str, variable_name: str) -> Variable:
        """Get a variable value."""
        cache_key = f"{symbol}:{variable_name}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Generate mock variable
        var = Variable(
            name=variable_name,
            value=np.random.uniform(0, 100),
            timestamp=pd.Timestamp.now(),
            symbol=symbol,
            indicator_type='technical',
            unit='%',
        )

        self.cache[cache_key] = var
        return var

    def cache_variable(self, variable: Variable) -> None:
        """Cache a variable."""
        cache_key = f"{variable.symbol}:{variable.name}"
        self.cache[cache_key] = variable

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Clear cache."""
        if symbol:
            # Clear only for specific symbol
            self.cache = {
                k: v for k, v in self.cache.items()
                if not k.startswith(f"{symbol}:")
            }
        else:
            # Clear all
            self.cache = {}


class MockChartBuilder(IChartBuilder):
    """Mock chart builder for testing visualization layer."""

    def __init__(self):
        """Initialize builder."""
        self.supported_formats = ['ohlcv', 'indicators', 'performance']

    def build(self, data: pd.DataFrame, config: ChartConfig) -> str:
        """Build mock chart HTML."""
        html = f"""
        <div>
            <h3>{config.title}</h3>
            <p>Chart Type: {config.chart_type}</p>
            <p>Records: {len(data)}</p>
            <p>X Label: {config.x_label}</p>
            <p>Y Label: {config.y_label}</p>
        </div>
        """
        return html

    def get_supported_data_formats(self) -> List[str]:
        """Get supported data formats."""
        return self.supported_formats

    @property
    def chart_type(self) -> str:
        """Return chart type."""
        return 'line'


class MockAnalyzer(IAnalyzer):
    """Mock analyzer for testing visualization layer."""

    def __init__(self):
        """Initialize analyzer."""
        self.required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    def analyze(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Perform mock analysis."""
        return {
            'mean': float(data['Close'].mean()),
            'std': float(data['Close'].std()),
            'min': float(data['Close'].min()),
            'max': float(data['Close'].max()),
            'records_analyzed': len(data),
        }

    def get_analysis_name(self) -> str:
        """Return analysis name."""
        return 'MockAnalysis'

    def get_required_columns(self) -> List[str]:
        """Return required columns."""
        return self.required_columns


# Convenience functions for tests
def create_mock_data_source() -> MockDataSource:
    """Create a mock data source."""
    return MockDataSource()


def create_mock_data_cleaner() -> MockDataCleaner:
    """Create a mock data cleaner."""
    return MockDataCleaner()


def create_mock_processor() -> MockProcessor:
    """Create a mock processor."""
    return MockProcessor()


def create_mock_strategy() -> MockStrategy:
    """Create a mock strategy."""
    return MockStrategy()


def create_mock_variable_manager() -> MockVariableManager:
    """Create a mock variable manager."""
    return MockVariableManager()


def create_mock_chart_builder() -> MockChartBuilder:
    """Create a mock chart builder."""
    return MockChartBuilder()


def create_mock_analyzer() -> MockAnalyzer:
    """Create a mock analyzer."""
    return MockAnalyzer()
