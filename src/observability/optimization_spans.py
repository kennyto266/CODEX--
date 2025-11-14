"""
Optimization Tracing Spans (T060m)

This module provides specialized tracing spans for parameter optimization workflows.
It tracks the complete lifecycle of optimization operations including parameter
combination evaluation, parallel execution, and result ranking.

Key Components:
- OptimizationSpans: Factory for creating optimization trace spans
- OptimizationExecutionSpan: Context manager for full optimization execution
- ParallelExecutionContext: Context manager for parallel optimization execution

Author: Claude Code
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from src.observability.trace_context import TraceContext, TraceManager


class OptimizationSpans:
    """
    Factory for creating optimization-related trace spans.

    This class provides methods to create and manage spans for different
    phases of parameter optimization, including parallel execution tracking
    and worker management.
    """

    def __init__(self, trace_manager: TraceManager):
        """
        Initialize OptimizationSpans with a trace manager.

        Args:
            trace_manager: TraceManager instance for span creation
        """
        self.trace_manager = trace_manager

    def trace_optimization_execution(
        self,
        user_id: str,
        strategy_type: str,
        parameter_spaces: List[Dict[str, Any]],
        total_combinations: int
    ) -> 'OptimizationExecutionSpan':
        """
        Create a context manager for full optimization execution trace.

        This is the top-level span that encompasses the entire optimization
        workflow. It serves as the parent for all sub-operations including
        parallel execution and result ranking.

        Args:
            user_id: ID of user who initiated the optimization
            strategy_type: Type of trading strategy being optimized
            parameter_spaces: List of parameter spaces being searched
            total_combinations: Total number of parameter combinations to evaluate

        Returns:
            OptimizationExecutionSpan context manager
        """
        return OptimizationExecutionSpan(
            trace_manager=self.trace_manager,
            user_id=user_id,
            strategy_type=strategy_type,
            parameter_spaces=parameter_spaces,
            total_combinations=total_combinations
        )

    def trace_parameter_combination_evaluation(
        self,
        parameters: Dict[str, Any],
        evaluation_id: str
    ) -> TraceContext:
        """
        Create a span for individual parameter combination evaluation.

        This span tracks the evaluation of a single set of parameters,
        including the backtest execution and performance metrics.

        Args:
            parameters: Dictionary of parameter values
            evaluation_id: Unique identifier for this evaluation

        Returns:
            TraceContext for parameter evaluation
        """
        # Create parameter tags
        param_tags = {
            f"param.{k}": v
            for k, v in parameters.items()
        }

        return self.trace_manager.start_span(
            operation_name="optimization.parameter_evaluation",
            tags={
                "evaluation_id": evaluation_id,
                **param_tags
            }
        )

    def trace_parallel_execution(
        self,
        worker_count: int,
        batch_size: int
    ) -> TraceContext:
        """
        Create a span for parallel optimization execution.

        This span tracks the parallel execution of parameter evaluations
        across multiple workers or threads.

        Args:
            worker_count: Number of parallel workers
            batch_size: Number of evaluations per batch

        Returns:
            TraceContext for parallel execution
        """
        return self.trace_manager.start_span(
            operation_name="optimization.parallel_execution",
            tags={
                "worker_count": worker_count,
                "batch_size": batch_size
            }
        )

    def trace_result_ranking(
        self,
        results_count: int,
        top_n: int
    ) -> TraceContext:
        """
        Create a span for result ranking and selection.

        This span tracks the process of ranking optimization results
        and selecting the top N parameter combinations.

        Args:
            results_count: Total number of results to rank
            top_n: Number of top results to select

        Returns:
            TraceContext for result ranking
        """
        return self.trace_manager.start_span(
            operation_name="optimization.result_ranking",
            tags={
                "results_count": results_count,
                "top_n": top_n
            }
        )


class OptimizationExecutionSpan:
    """
    Context manager for optimization execution trace lifecycle.

    This class manages the complete optimization execution trace, including
    setup, parallel execution, and result ranking. It provides methods to
    create child spans for each phase of the optimization.

    Example:
        with optimization_spans.trace_optimization_execution(
            user_id="user123",
            strategy_type="kdj",
            parameter_spaces=[
                {"k_period": [5, 10, 15]},
                {"d_period": [3, 5]}
            ],
            total_combinations=400
        ) as execution:
            with execution.trace_parallel_execution(
                worker_count=8,
                batch_size=50,
                total_batches=8
            ) as parallel_ctx:
                for i in range(8):
                    worker_span = parallel_ctx.start_worker_span(
                        worker_id=i+1,
                        batch_id=1,
                        combinations_count=50
                    )
    """

    def __init__(
        self,
        trace_manager: TraceManager,
        user_id: str,
        strategy_type: str,
        parameter_spaces: List[Dict[str, Any]],
        total_combinations: int
    ):
        """
        Initialize optimization execution span.

        Args:
            trace_manager: TraceManager instance
            user_id: User who initiated the optimization
            strategy_type: Trading strategy type
            parameter_spaces: Parameter spaces being searched
            total_combinations: Total number of combinations
        """
        self.trace_manager = trace_manager
        self.user_id = user_id
        self.strategy_type = strategy_type
        self.parameter_spaces = parameter_spaces
        self.total_combinations = total_combinations

        # Child spans
        self.main_span: Optional[TraceContext] = None
        self.parallel_span: Optional[TraceContext] = None
        self.ranking_span: Optional[TraceContext] = None

    def __enter__(self) -> 'OptimizationExecutionSpan':
        """
        Enter optimization execution context.

        Creates the main optimization execution span and sets it as current.

        Returns:
            Self for context manager
        """
        self.main_span = self.trace_manager.start_span(
            operation_name="optimization.execution",
            user_id=self.user_id,
            tags={
                "strategy_type": self.strategy_type,
                "total_combinations": self.total_combinations,
                "parameter_space_count": len(self.parameter_spaces),
                "parameter_spaces": self.parameter_spaces
            }
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit optimization execution context.

        Finishes the main optimization span and logs the result.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if exc_type is not None:
            # An error occurred
            self.main_span.add_log("optimization_error", {
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_val),
                "strategy_type": self.strategy_type,
                "total_combinations": self.total_combinations
            })
            self.main_span.finish(status="ERROR", error=exc_val)
        else:
            # Success
            self.main_span.add_log("optimization_completed", {
                "strategy_type": self.strategy_type,
                "total_combinations": self.total_combinations,
                "parameter_space_count": len(self.parameter_spaces)
            })
            self.main_span.finish(status="OK")

    def trace_parallel_execution(
        self,
        worker_count: int,
        batch_size: int,
        total_batches: int
    ) -> 'ParallelExecutionContext':
        """
        Start a parallel execution span as a child of the main optimization span.

        Args:
            worker_count: Number of parallel workers
            batch_size: Number of evaluations per batch
            total_batches: Total number of batches

        Returns:
            ParallelExecutionContext for parallel operations
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before creating child spans")

        self.parallel_span = self.trace_manager.start_span(
            operation_name="optimization.parallel_execution",
            tags={
                "worker_count": worker_count,
                "batch_size": batch_size,
                "total_batches": total_batches,
                "parent_strategy": self.strategy_type
            }
        )

        return ParallelExecutionContext(
            self.trace_manager,
            self.parallel_span,
            worker_count
        )

    def trace_result_ranking(
        self,
        results_count: int,
        top_n: int
    ) -> TraceContext:
        """
        Start a result ranking span as a child of the main optimization span.

        Args:
            results_count: Total number of results to rank
            top_n: Number of top results to select

        Returns:
            TraceContext for result ranking
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before creating child spans")

        self.ranking_span = self.trace_manager.start_span(
            operation_name="optimization.result_ranking",
            tags={
                "results_count": results_count,
                "top_n": top_n,
                "parent_strategy": self.strategy_type
            }
        )

        return self.ranking_span

    def add_optimization_summary(
        self,
        best_sharpe: float,
        best_parameters: Dict[str, Any],
        total_evaluations: int,
        successful_evaluations: int
    ):
        """
        Add summary information to the main span.

        Args:
            best_sharpe: Best Sharpe ratio achieved
            best_parameters: Parameters that achieved best performance
            total_evaluations: Total number of evaluations attempted
            successful_evaluations: Number of successful evaluations
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before adding summary")

        self.main_span.add_tag("best_sharpe", best_sharpe)
        self.main_span.add_tag("total_evaluations", total_evaluations)
        self.main_span.add_tag("successful_evaluations", successful_evaluations)
        self.main_span.add_tag("success_rate", successful_evaluations / total_evaluations if total_evaluations > 0 else 0)

        # Add best parameters as tags
        for key, value in best_parameters.items():
            self.main_span.add_tag(f"best_param.{key}", value)

        self.main_span.add_log("optimization_summary", {
            "best_sharpe": best_sharpe,
            "best_parameters": best_parameters,
            "total_evaluations": total_evaluations,
            "successful_evaluations": successful_evaluations,
            "success_rate": successful_evaluations / total_evaluations if total_evaluations > 0 else 0
        })


class ParallelExecutionContext:
    """
    Context manager for parallel execution span lifecycle.

    This class manages a span that tracks parallel execution of parameter
    evaluations across multiple workers. It provides methods to create
    individual worker spans and track their performance.
    """

    def __init__(
        self,
        trace_manager: TraceManager,
        span: TraceContext,
        worker_count: int
    ):
        """
        Initialize parallel execution context.

        Args:
            trace_manager: TraceManager instance
            span: The span to manage
            worker_count: Expected number of workers
        """
        self.trace_manager = trace_manager
        self.span = span
        self.worker_count = worker_count
        self.worker_spans: List[TraceContext] = []

    def __enter__(self) -> 'ParallelExecutionContext':
        """Enter parallel execution context"""
        self.span.add_log("parallel_execution_started", {
            "operation": "parallel_execution",
            "worker_count": self.worker_count,
            "timestamp": self.span.start_time
        })
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit parallel execution context.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if exc_type is not None:
            self.span.add_log("error", {
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_val),
                "operation": "parallel_execution"
            })
            self.span.finish(status="ERROR", error=exc_val)
        else:
            # Log summary of worker performance
            worker_durations = [
                worker.duration for worker in self.worker_spans
                if worker.duration is not None
            ]

            avg_duration = sum(worker_durations) / len(worker_durations) if worker_durations else 0

            self.span.add_log("parallel_execution_completed", {
                "status": "success",
                "operation": "parallel_execution",
                "worker_count": len(self.worker_spans),
                "expected_worker_count": self.worker_count,
                "avg_worker_duration_ms": avg_duration * 1000
            })
            self.span.finish(status="OK")

    def start_worker_span(
        self,
        worker_id: int,
        batch_id: int,
        combinations_count: int
    ) -> TraceContext:
        """
        Start a span for an individual worker.

        Args:
            worker_id: Worker identifier
            batch_id: Batch identifier this worker is processing
            combinations_count: Number of parameter combinations to evaluate

        Returns:
            TraceContext for the worker
        """
        worker_span = self.trace_manager.start_span(
            operation_name=f"optimization.worker_{worker_id}",
            tags={
                "worker_id": worker_id,
                "batch_id": batch_id,
                "combinations_count": combinations_count,
                "parent_worker_count": self.worker_count
            }
        )

        self.worker_spans.append(worker_span)
        return worker_span

    def log_worker_completion(
        self,
        worker_id: int,
        combinations_evaluated: int,
        duration_ms: float,
        success: bool
    ):
        """
        Log worker completion information.

        Args:
            worker_id: Worker identifier
            combinations_evaluated: Number of combinations evaluated
            duration_ms: Time taken in milliseconds
            success: Whether the worker completed successfully
        """
        # Find the worker span
        worker_span = next(
            (w for w in self.worker_spans if w.tags.get("worker_id") == worker_id),
            None
        )

        if worker_span:
            worker_span.add_tag("combinations_evaluated", combinations_evaluated)
            worker_span.add_tag("duration_ms", duration_ms)
            worker_span.add_tag("success", success)

            worker_span.add_log("worker_completed", {
                "worker_id": worker_id,
                "combinations_evaluated": combinations_evaluated,
                "duration_ms": duration_ms,
                "avg_time_per_combination_ms": duration_ms / combinations_evaluated if combinations_evaluated > 0 else 0,
                "success": success
            })

    def get_worker_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of all worker performance.

        Returns:
            Dictionary with performance metrics for all workers
        """
        if not self.worker_spans:
            return {}

        # Collect metrics from all worker spans
        worker_metrics = []
        for worker in self.worker_spans:
            if worker.duration is not None:
                worker_metrics.append({
                    "worker_id": worker.tags.get("worker_id"),
                    "duration_ms": worker.duration * 1000,  # Convert to ms
                    "combinations": worker.tags.get("combinations_count", 0),
                    "status": worker.status
                })

        # Calculate aggregate metrics
        total_combinations = sum(m["combinations"] for m in worker_metrics)
        total_duration_ms = max((m["duration_ms"] for m in worker_metrics), default=0)
        successful_workers = sum(1 for m in worker_metrics if m["status"] == "OK")

        return {
            "total_workers": len(self.worker_spans),
            "successful_workers": successful_workers,
            "total_combinations": total_combinations,
            "max_duration_ms": total_duration_ms,
            "avg_combinations_per_worker": total_combinations / len(self.worker_spans) if self.worker_spans else 0,
            "worker_metrics": worker_metrics
        }


# Export public API
__all__ = [
    'OptimizationSpans',
    'OptimizationExecutionSpan',
    'ParallelExecutionContext'
]
