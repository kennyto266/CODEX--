"""
Unified Parameter Management System

Consolidates all strategy parameter management and optimization logic.
Implements IParameterManager from Phase 2.1.

Features:
- Parameter validation and bounds checking
- Optimization support (grid search, bayesian, genetic algorithms)
- Parameter persistence and loading
- Performance-based parameter selection
- Real-time parameter adjustment

Used by: Strategy executor, backtesting engine, live trading
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger("hk_quant_system.parameter_manager")


@dataclass
class ParameterBounds:
    """Define bounds for a parameter."""
    name: str
    param_type: str  # 'int', 'float', 'bool', 'choice'
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[List[Any]] = None
    default: Any = None
    step: Optional[float] = None  # For grid search
    description: str = ""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate parameter value."""
        if self.param_type == 'int':
            if not isinstance(value, int):
                return False, f"{self.name} must be int"
            if self.min_value is not None and value < self.min_value:
                return False, f"{self.name} must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"{self.name} must be <= {self.max_value}"

        elif self.param_type == 'float':
            if not isinstance(value, (int, float)):
                return False, f"{self.name} must be float"
            if self.min_value is not None and value < self.min_value:
                return False, f"{self.name} must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"{self.name} must be <= {self.max_value}"

        elif self.param_type == 'bool':
            if not isinstance(value, bool):
                return False, f"{self.name} must be bool"

        elif self.param_type == 'choice':
            if self.choices and value not in self.choices:
                return False, f"{self.name} must be one of {self.choices}"

        return True, "Valid"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.param_type,
            'min': self.min_value,
            'max': self.max_value,
            'default': self.default,
            'step': self.step,
            'description': self.description,
        }


class UnifiedParameterManager:
    """
    Unified parameter management for all strategies.

    Provides:
    - Parameter definition and validation
    - Optimization (grid, random, bayesian)
    - Parameter persistence
    - Performance tracking

    Example:
        >>> manager = UnifiedParameterManager()
        >>> manager.register_parameter(
        ...     'rsi_period',
        ...     ParameterBounds('rsi_period', 'int', 10, 30, default=14)
        ... )
        >>> params = manager.get_parameters()
        >>> optimized = manager.optimize_grid(
        ...     strategy=rsi_strategy,
        ...     data=price_data,
        ...     metrics_func=calculate_metrics
        ... )
    """

    def __init__(self, strategy_name: str = "default"):
        """Initialize parameter manager."""
        self.strategy_name = strategy_name
        self.parameters: Dict[str, ParameterBounds] = {}
        self.current_values: Dict[str, Any] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_parameters: Dict[str, Any] = {}
        self.best_score: float = -np.inf

    def register_parameter(self, bounds: ParameterBounds) -> None:
        """
        Register a parameter with bounds.

        Args:
            bounds: ParameterBounds object
        """
        self.parameters[bounds.name] = bounds
        self.current_values[bounds.name] = bounds.default

        logger.info(f"Registered parameter: {bounds.name}")

    def register_parameters(self, bounds_list: List[ParameterBounds]) -> None:
        """Register multiple parameters."""
        for bounds in bounds_list:
            self.register_parameter(bounds)

    def set_parameter(self, name: str, value: Any) -> bool:
        """
        Set parameter value with validation.

        Args:
            name: Parameter name
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        if name not in self.parameters:
            logger.warning(f"Unknown parameter: {name}")
            return False

        bounds = self.parameters[name]
        is_valid, message = bounds.validate(value)

        if not is_valid:
            logger.error(f"Invalid parameter: {message}")
            return False

        self.current_values[name] = value
        return True

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get parameter value."""
        return self.current_values.get(name, default)

    def get_parameters(self) -> Dict[str, Any]:
        """Get all current parameter values."""
        return self.current_values.copy()

    def set_parameters(self, params: Dict[str, Any]) -> bool:
        """Set multiple parameters."""
        for name, value in params.items():
            if not self.set_parameter(name, value):
                return False
        return True

    def get_optimization_bounds(
        self,
        param_name: str,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Get optimization bounds for a parameter."""
        if param_name not in self.parameters:
            return None, None

        bounds = self.parameters[param_name]
        return bounds.min_value, bounds.max_value

    def optimize_grid(
        self,
        strategy,
        data: pd.DataFrame,
        metrics_func: Callable,
        **backtest_kwargs
    ) -> Dict[str, Any]:
        """
        Optimize parameters using grid search.

        Args:
            strategy: Strategy instance
            data: OHLCV data
            metrics_func: Function to calculate metrics
            **backtest_kwargs: Additional backtest parameters

        Returns:
            Dictionary with best parameters and score
        """
        logger.info(f"Starting grid search optimization for {self.strategy_name}")

        # Generate parameter grid
        param_grid = self._generate_grid()

        best_score = -np.inf
        best_params = None

        for combo_idx, param_combo in enumerate(param_grid):
            try:
                # Set parameters
                self.set_parameters(param_combo)

                # Run backtest
                strategy.initialize(data)
                signals = strategy.generate_signals(data)

                # Calculate metrics
                metrics = metrics_func(data, signals)

                # Get score (e.g., Sharpe ratio)
                score = metrics.get('sharpe_ratio', -np.inf)

                # Track this result
                result = {
                    'iteration': combo_idx,
                    'parameters': param_combo.copy(),
                    'score': score,
                    'metrics': metrics,
                }
                self.optimization_history.append(result)

                # Update best
                if score > best_score:
                    best_score = score
                    best_params = param_combo.copy()
                    self.best_score = best_score
                    self.best_parameters = best_params.copy()

                logger.info(
                    f"Iteration {combo_idx}: Score={score:.4f} "
                    f"(Best: {best_score:.4f})"
                )

            except Exception as e:
                logger.error(f"Error in iteration {combo_idx}: {e}")
                continue

        logger.info(f"Grid search complete. Best score: {best_score:.4f}")

        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'history': self.optimization_history,
        }

    def optimize_random(
        self,
        strategy,
        data: pd.DataFrame,
        metrics_func: Callable,
        n_iterations: int = 100,
        **backtest_kwargs
    ) -> Dict[str, Any]:
        """
        Optimize using random search.

        Args:
            strategy: Strategy instance
            data: OHLCV data
            metrics_func: Function to calculate metrics
            n_iterations: Number of random samples
            **backtest_kwargs: Additional parameters

        Returns:
            Best parameters and score
        """
        logger.info(
            f"Starting random search optimization "
            f"({n_iterations} iterations) for {self.strategy_name}"
        )

        best_score = -np.inf
        best_params = None

        for iteration in range(n_iterations):
            try:
                # Generate random parameters
                param_combo = self._generate_random_parameters()

                # Set parameters
                self.set_parameters(param_combo)

                # Run backtest
                strategy.initialize(data)
                signals = strategy.generate_signals(data)

                # Calculate metrics
                metrics = metrics_func(data, signals)

                # Get score
                score = metrics.get('sharpe_ratio', -np.inf)

                # Track result
                result = {
                    'iteration': iteration,
                    'parameters': param_combo.copy(),
                    'score': score,
                    'metrics': metrics,
                }
                self.optimization_history.append(result)

                # Update best
                if score > best_score:
                    best_score = score
                    best_params = param_combo.copy()
                    self.best_score = best_score
                    self.best_parameters = best_params.copy()

                if (iteration + 1) % 10 == 0:
                    logger.info(
                        f"Iteration {iteration + 1}/{n_iterations}: "
                        f"Score={score:.4f} (Best: {best_score:.4f})"
                    )

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                continue

        logger.info(f"Random search complete. Best score: {best_score:.4f}")

        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'history': self.optimization_history,
        }

    def _generate_grid(self) -> List[Dict[str, Any]]:
        """Generate parameter grid for grid search."""
        grid = []

        param_lists = {}
        for name, bounds in self.parameters.items():
            if bounds.param_type == 'choice':
                param_lists[name] = bounds.choices
            elif bounds.step is not None:
                values = np.arange(
                    bounds.min_value,
                    bounds.max_value + bounds.step,
                    bounds.step,
                )
                param_lists[name] = [int(v) if bounds.param_type == 'int' else float(v) for v in values]
            else:
                param_lists[name] = [bounds.default]

        # Generate all combinations
        from itertools import product

        keys = param_lists.keys()
        for combo in product(*[param_lists[k] for k in keys]):
            grid.append(dict(zip(keys, combo)))

        return grid

    def _generate_random_parameters(self) -> Dict[str, Any]:
        """Generate random parameter values."""
        params = {}

        for name, bounds in self.parameters.items():
            if bounds.param_type == 'choice':
                params[name] = np.random.choice(bounds.choices)
            elif bounds.param_type == 'int':
                params[name] = np.random.randint(
                    bounds.min_value,
                    bounds.max_value + 1,
                )
            elif bounds.param_type == 'float':
                params[name] = np.random.uniform(
                    bounds.min_value,
                    bounds.max_value,
                )
            elif bounds.param_type == 'bool':
                params[name] = np.random.choice([True, False])
            else:
                params[name] = bounds.default

        return params

    def save_parameters(self, filepath: str) -> None:
        """Save parameters to JSON file."""
        data = {
            'strategy_name': self.strategy_name,
            'parameters': self.current_values,
            'best_parameters': self.best_parameters,
            'best_score': float(self.best_score),
            'timestamp': datetime.now().isoformat(),
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved parameters to {filepath}")

    def load_parameters(self, filepath: str) -> bool:
        """Load parameters from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.set_parameters(data.get('parameters', {}))
            self.best_parameters = data.get('best_parameters', {})
            self.best_score = data.get('best_score', -np.inf)

            logger.info(f"Loaded parameters from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load parameters: {e}")
            return False

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary."""
        if not self.optimization_history:
            return {
                'total_iterations': 0,
                'best_score': self.best_score,
                'best_parameters': self.best_parameters,
            }

        scores = [h['score'] for h in self.optimization_history]

        return {
            'strategy_name': self.strategy_name,
            'total_iterations': len(self.optimization_history),
            'best_score': self.best_score,
            'best_parameters': self.best_parameters,
            'average_score': np.mean(scores),
            'std_score': np.std(scores),
            'improvement': self.best_score - np.mean(scores[:5]) if len(scores) > 5 else 0,
        }

    def reset_optimization(self) -> None:
        """Reset optimization history."""
        self.optimization_history = []
        self.best_score = -np.inf
        self.best_parameters = {}

        logger.info(f"Reset optimization for {self.strategy_name}")
