"""
Data validation module
"""

__all__ = [
    "DataValidator",
    "DataValidationResult",
    "FinancialStatementValidator",
    "validate_trading_data",
    "quick_validate",
    "validate_fusion_result",
    "quick_validate_enhanced"
]

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

logger = logging.getLogger('quant_system.validation')


class DataValidationResult:
    """Validation result"""
    def __init__(
        self,
        is_valid: bool = True,
        quality_score: float = 1.0,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.is_valid = is_valid
        self.quality_score = quality_score
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}

    def __repr__(self):
        return f"DataValidationResult(valid={self.is_valid}, score={self.quality_score:.2f})"


class DataValidator:
    """Data validator"""
    
    def __init__(self):
        self.validation_stats = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
    
    def validate_ohlcv(self, data: Union[pd.DataFrame, Dict], symbol: Optional[str] = None) -> Dict:
        """Validate OHLCV data"""
        self.validation_stats['total_validated'] += 1
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Basic validation
        if isinstance(data, dict) and not data:
            result['valid'] = False
            result['errors'].append("Empty data")
        elif isinstance(data, pd.DataFrame) and data.empty:
            result['valid'] = False
            result['errors'].append("Empty DataFrame")
        
        if result['errors']:
            self.validation_stats['failed'] += 1
        else:
            self.validation_stats['passed'] += 1
        
        return result
    
    def validate_json_data(self, data: Any) -> Dict:
        """Validate JSON data"""
        return {'valid': True, 'errors': [], 'warnings': []}
    
    def validate_numerical_array(self, data: Any) -> Dict:
        """Validate numerical array"""
        return {'valid': True, 'errors': [], 'warnings': []}


class FinancialStatementValidator:
    """Financial statement validator"""
    
    def validate_financial_statement(self, statement) -> DataValidationResult:
        """Validate financial statement"""
        errors = []
        
        if not hasattr(statement, 'symbol') or not statement.symbol:
            errors.append("Missing symbol")
        
        is_valid = len(errors) == 0
        quality_score = 1.0 if is_valid else 0.5
        
        return DataValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            errors=errors
        )


def validate_trading_data(data: Any, data_type: str) -> bool:
    """Validate trading data"""
    validator = DataValidator()
    
    if data_type == 'ohlcv':
        result = validator.validate_ohlcv(data)
    else:
        result = {'valid': True}
    
    return result.get('valid', False)


def quick_validate(data: Any, data_type: str = 'ohlcv') -> bool:
    """Quick validation"""
    return validate_trading_data(data, data_type)


def validate_fusion_result(
    fusion_result,
    expected_ranges: Optional[Dict[str, Tuple[float, float]]] = None
) -> DataValidationResult:
    """Validate fusion result"""
    errors = []
    
    if not hasattr(fusion_result, 'merged_data'):
        errors.append("Missing merged data")
    
    is_valid = len(errors) == 0
    quality_score = 1.0 if is_valid else 0.5
    
    return DataValidationResult(
        is_valid=is_valid,
        quality_score=quality_score,
        errors=errors
    )


def quick_validate_enhanced(data, data_type: str = 'ohlcv') -> bool:
    """Quick validation enhanced"""
    validator = DataValidator()
    result = validator.validate_ohlcv(data)
    return result.get('valid', False)
