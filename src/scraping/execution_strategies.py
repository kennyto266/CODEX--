"""
Execution strategies for batch processing

Implements different strategies for executing multiple scraping requests:
- Sequential: Process one request at a time
- Parallel: Process multiple requests concurrently
- Adaptive: Dynamically adjust based on system resources and workload
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .models import (
    NaturalLanguageRequest, PipetConfiguration, ScrapingExecution,
    ProcessingStatus, BatchRequest, BatchResult, ResourceUsage
)
from .exceptions import BatchExecutionError, ValidationError
from .monitoring import ResourceTracker, PerformanceTimerContext
from .logging_config import StructuredLogger
from .nlp_interface import NLPProcessor
from .pipet_config_generator import PipetConfigGenerator
from .single_executor import SingleExecutionOrchestrator
from .data_transformers import DataTransformer


class StrategyType(str, Enum):
    """Execution strategy types"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class ExecutionContext:
    """Context for execution strategy"""
    batch_id: str
    requests: List[NaturalLanguageRequest]
    configurations: List[PipetConfiguration]
    max_concurrent: int
    timeout_per_request: int
    continue_on_error: bool
    progress_callback: Optional[Callable]
    use_priority_ordering: bool
    enable_caching: bool
    resource_tracker: ResourceTracker
    logger: StructuredLogger


class ExecutionStrategy(ABC):
    """Abstract base class for execution strategies"""

    def __init__(self, name: str):
        self.name = name
        self.logger = StructuredLogger.get_logger(__name__)

    @abstractmethod
    async def execute(
        self,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> List[ScrapingExecution]:
        """Execute batch requests using this strategy"""
        pass

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Get strategy-specific metrics"""
        return {
            "strategy_name": self.name,
            "execution_time": 0.0,
            "resource_usage": ResourceUsage()
        }


class SequentialStrategy(ExecutionStrategy):
    """Sequential execution strategy - processes one request at a time"""

    def __init__(self):
        super().__init__("sequential")

    async def execute(
        self,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> List[ScrapingExecution]:
        """Execute requests sequentially"""
        start_time = time.time()
        results = []

        self.logger.info(
            "Starting sequential execution",
            batch_id=context.batch_id,
            total_requests=len(context.requests)
        )

        # Apply priority ordering if enabled
        requests_to_process = context.requests.copy()
        if context.use_priority_ordering:
            requests_to_process.sort(key=lambda x: x.priority, reverse=True)

        for i, request in enumerate(requests_to_process):
            try:
                # Call progress callback if provided
                if context.progress_callback:
                    await context.progress_callback(i, len(requests_to_process), request)

                # Process single request
                execution_result = await self._process_single_request(
                    request=request,
                    context=context,
                    nlp_processor=nlp_processor,
                    config_generator=config_generator,
                    orchestrator=orchestrator,
                    data_transformer=data_transformer
                )

                results.append(execution_result)

                # Stop processing if single failure and not continuing on error
                if (execution_result.status == ProcessingStatus.FAILED
                    and not context.continue_on_error):
                    self.logger.error(
                        "Stopping sequential execution due to failure",
                        batch_id=context.batch_id,
                        request_id=request.request_id,
                        error=execution_result.error_message
                    )
                    break

            except Exception as e:
                self.logger.error(
                    "Error processing request in sequential execution",
                    batch_id=context.batch_id,
                    request_id=request.request_id,
                    error=str(e)
                )

                # Create failed execution result
                failed_execution = ScrapingExecution(
                    config_id="",  # No config generated due to error
                    status=ProcessingStatus.FAILED,
                    error_message=str(e),
                    execution_environment={"strategy": "sequential"}
                )
                results.append(failed_execution)

                if not context.continue_on_error:
                    break

        execution_time = time.time() - start_time
        self.logger.info(
            "Completed sequential execution",
            batch_id=context.batch_id,
            total_requests=len(context.requests),
            successful_requests=len([r for r in results if r.status == ProcessingStatus.COMPLETED]),
            execution_time=execution_time
        )

        return results

    async def _process_single_request(
        self,
        request: NaturalLanguageRequest,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> ScrapingExecution:
        """Process a single request with timeout"""
        try:
            # Use asyncio.wait_for to apply timeout
            execution = await asyncio.wait_for(
                orchestrator.execute_single_request(
                    natural_language_request=request,
                    user_context=request.user_context
                ),
                timeout=context.timeout_per_request
            )
            return execution

        except asyncio.TimeoutError:
            self.logger.warning(
                "Request timed out",
                batch_id=context.batch_id,
                request_id=request.request_id,
                timeout=context.timeout_per_request
            )

            return ScrapingExecution(
                config_id="",
                status=ProcessingStatus.TIMEOUT,
                error_message=f"Request timed out after {context.timeout_per_request} seconds",
                execution_environment={"strategy": "sequential"}
            )


class ParallelStrategy(ExecutionStrategy):
    """Parallel execution strategy - processes multiple requests concurrently"""

    def __init__(self):
        super().__init__("parallel")

    async def execute(
        self,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> List[ScrapingExecution]:
        """Execute requests in parallel"""
        start_time = time.time()

        self.logger.info(
            "Starting parallel execution",
            batch_id=context.batch_id,
            total_requests=len(context.requests),
            max_concurrent=context.max_concurrent
        )

        # Apply priority ordering if enabled
        requests_to_process = context.requests.copy()
        if context.use_priority_ordering:
            requests_to_process.sort(key=lambda x: x.priority, reverse=True)

        # Create semaphore to limit concurrent executions
        semaphore = asyncio.Semaphore(context.max_concurrent)

        # Create tasks for parallel execution
        tasks = []
        for i, request in enumerate(requests_to_process):
            task = self._execute_with_semaphore(
                semaphore=semaphore,
                request=request,
                index=i,
                total=len(requests_to_process),
                context=context,
                nlp_processor=nlp_processor,
                config_generator=config_generator,
                orchestrator=orchestrator,
                data_transformer=data_transformer
            )
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "Exception in parallel execution",
                    batch_id=context.batch_id,
                    request_id=requests_to_process[i].request_id,
                    error=str(result)
                )

                failed_execution = ScrapingExecution(
                    config_id="",
                    status=ProcessingStatus.FAILED,
                    error_message=str(result),
                    execution_environment={"strategy": "parallel"}
                )
                processed_results.append(failed_execution)
            else:
                processed_results.append(result)

        execution_time = time.time() - start_time
        self.logger.info(
            "Completed parallel execution",
            batch_id=context.batch_id,
            total_requests=len(context.requests),
            successful_requests=len([r for r in processed_results if r.status == ProcessingStatus.COMPLETED]),
            execution_time=execution_time
        )

        return processed_results

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        request: NaturalLanguageRequest,
        index: int,
        total: int,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> ScrapingExecution:
        """Execute a single request with semaphore control"""
        async with semaphore:
            try:
                # Call progress callback if provided
                if context.progress_callback:
                    await context.progress_callback(index, total, request)

                # Process with timeout
                execution = await asyncio.wait_for(
                    orchestrator.execute_single_request(
                        natural_language_request=request,
                        user_context=request.user_context
                    ),
                    timeout=context.timeout_per_request
                )
                return execution

            except asyncio.TimeoutError:
                self.logger.warning(
                    "Request timed out in parallel execution",
                    batch_id=context.batch_id,
                    request_id=request.request_id,
                    timeout=context.timeout_per_request
                )

                return ScrapingExecution(
                    config_id="",
                    status=ProcessingStatus.TIMEOUT,
                    error_message=f"Request timed out after {context.timeout_per_request} seconds",
                    execution_environment={"strategy": "parallel"}
                )


class AdaptiveStrategy(ExecutionStrategy):
    """Adaptive execution strategy - dynamically adjusts based on system conditions"""

    def __init__(self):
        super().__init__("adaptive")
        self.performance_history: List[Dict[str, Any]] = []

    async def execute(
        self,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> List[ScrapingExecution]:
        """Execute with adaptive strategy"""
        start_time = time.time()

        self.logger.info(
            "Starting adaptive execution",
            batch_id=context.batch_id,
            total_requests=len(context.requests),
            max_concurrent=context.max_concurrent
        )

        # Analyze workload and determine optimal strategy
        optimal_concurrent = await self._determine_optimal_concurrency(
            context.requests,
            context.resource_tracker
        )

        # Create dynamic semaphore with optimal concurrency
        semaphore = asyncio.Semaphore(optimal_concurrent)

        # Apply priority ordering
        requests_to_process = context.requests.copy()
        if context.use_priority_ordering:
            requests_to_process.sort(key=lambda x: x.priority, reverse=True)

        # Execute with adaptive batching
        results = await self._execute_adaptive_batches(
            semaphore=semaphore,
            requests=requests_to_process,
            context=context,
            nlp_processor=nlp_processor,
            config_generator=config_generator,
            orchestrator=orchestrator,
            data_transformer=data_transformer
        )

        execution_time = time.time() - start_time

        # Record performance for future optimization
        self._record_performance_metrics(
            total_requests=len(context.requests),
            execution_time=execution_time,
            concurrency_used=optimal_concurrent,
            success_rate=len([r for r in results if r.status == ProcessingStatus.COMPLETED]) / len(results)
        )

        self.logger.info(
            "Completed adaptive execution",
            batch_id=context.batch_id,
            total_requests=len(context.requests),
            successful_requests=len([r for r in results if r.status == ProcessingStatus.COMPLETED]),
            optimal_concurrency=optimal_concurrent,
            execution_time=execution_time
        )

        return results

    async def _determine_optimal_concurrency(
        self,
        requests: List[NaturalLanguageRequest],
        resource_tracker: ResourceTracker
    ) -> int:
        """Determine optimal concurrency based on system resources and workload"""
        # Get current system metrics
        system_metrics = await resource_tracker.get_current_metrics()

        # Base concurrency on system load
        cpu_usage = system_metrics.get("cpu_percent", 0)
        memory_usage = system_metrics.get("memory_percent", 0)

        # Adjust concurrency based on system load
        if cpu_usage > 80 or memory_usage > 80:
            # High system load - reduce concurrency
            return max(1, min(3, len(requests)))
        elif cpu_usage > 60 or memory_usage > 60:
            # Medium system load - moderate concurrency
            return max(2, min(5, len(requests)))
        else:
            # Low system load - can use higher concurrency
            return max(3, min(10, len(requests)))

    async def _execute_adaptive_batches(
        self,
        semaphore: asyncio.Semaphore,
        requests: List[NaturalLanguageRequest],
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> List[ScrapingExecution]:
        """Execute requests in adaptive batches"""
        results = []
        batch_size = max(1, len(requests) // 3)  # Divide into 3 batches

        for batch_start in range(0, len(requests), batch_size):
            batch_end = min(batch_start + batch_size, len(requests))
            batch_requests = requests[batch_start:batch_end]

            self.logger.info(
                "Processing adaptive batch",
                batch_id=context.batch_id,
                batch_start=batch_start,
                batch_end=batch_end,
                batch_size=len(batch_requests)
            )

            # Execute batch in parallel
            batch_tasks = []
            for i, request in enumerate(batch_requests):
                task = self._execute_with_semaphore(
                    semaphore=semaphore,
                    request=request,
                    index=batch_start + i,
                    total=len(requests),
                    context=context,
                    nlp_processor=nlp_processor,
                    config_generator=config_generator,
                    orchestrator=orchestrator,
                    data_transformer=data_transformer
                )
                batch_tasks.append(task)

            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process batch results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    failed_execution = ScrapingExecution(
                        config_id="",
                        status=ProcessingStatus.FAILED,
                        error_message=str(result),
                        execution_environment={"strategy": "adaptive"}
                    )
                    results.append(failed_execution)
                else:
                    results.append(result)

            # Short pause between batches for system stability
            if batch_end < len(requests):
                await asyncio.sleep(0.1)

        return results

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        request: NaturalLanguageRequest,
        index: int,
        total: int,
        context: ExecutionContext,
        nlp_processor: NLPProcessor,
        config_generator: PipetConfigGenerator,
        orchestrator: SingleExecutionOrchestrator,
        data_transformer: DataTransformer
    ) -> ScrapingExecution:
        """Execute a single request with semaphore control"""
        async with semaphore:
            try:
                # Call progress callback if provided
                if context.progress_callback:
                    await context.progress_callback(index, total, request)

                # Process with timeout
                execution = await asyncio.wait_for(
                    orchestrator.execute_single_request(
                        natural_language_request=request,
                        user_context=request.user_context
                    ),
                    timeout=context.timeout_per_request
                )
                return execution

            except asyncio.TimeoutError:
                return ScrapingExecution(
                    config_id="",
                    status=ProcessingStatus.TIMEOUT,
                    error_message=f"Request timed out after {context.timeout_per_request} seconds",
                    execution_environment={"strategy": "adaptive"}
                )

    def _record_performance_metrics(
        self,
        total_requests: int,
        execution_time: float,
        concurrency_used: int,
        success_rate: float
    ) -> None:
        """Record performance metrics for future optimization"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": total_requests,
            "execution_time": execution_time,
            "throughput": total_requests / execution_time if execution_time > 0 else 0,
            "concurrency_used": concurrency_used,
            "success_rate": success_rate
        }

        self.performance_history.append(metrics)

        # Keep only last 100 performance records
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)


def create_strategy(strategy_type: StrategyType) -> ExecutionStrategy:
    """Factory function to create execution strategy"""

    if strategy_type == StrategyType.SEQUENTIAL:
        return SequentialStrategy()
    elif strategy_type == StrategyType.PARALLEL:
        return ParallelStrategy()
    elif strategy_type == StrategyType.ADAPTIVE:
        return AdaptiveStrategy()
    else:
        raise ValidationError(f"Unknown execution strategy: {strategy_type}")


def get_strategy_recommendations(
    requests: List[NaturalLanguageRequest],
    system_metrics: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Get strategy recommendations based on workload and system conditions"""

    request_count = len(requests)
    avg_priority = sum(r.priority for r in requests) / request_count if requests else 1

    recommendations = {
        "recommended_strategy": StrategyType.ADAPTIVE,
        "max_concurrent": 5,
        "timeout_per_request": 300,
        "reasoning": []
    }

    # Simple rules for strategy recommendation
    if request_count == 1:
        recommendations["recommended_strategy"] = StrategyType.SEQUENTIAL
        recommendations["max_concurrent"] = 1
        recommendations["reasoning"].append("Single request - use sequential processing")

    elif request_count <= 5:
        recommendations["recommended_strategy"] = StrategyType.PARALLEL
        recommendations["max_concurrent"] = min(request_count, 3)
        recommendations["reasoning"].append("Small batch - parallel processing is efficient")

    elif request_count > 20:
        recommendations["max_concurrent"] = 8
        recommendations["reasoning"].append("Large batch - higher concurrency for better throughput")

    # Consider system metrics if provided
    if system_metrics:
        cpu_usage = system_metrics.get("cpu_percent", 0)
        memory_usage = system_metrics.get("memory_percent", 0)

        if cpu_usage > 70 or memory_usage > 70:
            recommendations["recommended_strategy"] = StrategyType.SEQUENTIAL
            recommendations["max_concurrent"] = 2
            recommendations["reasoning"].append("High system load - use conservative processing")

    # Consider priority
    if avg_priority >= 4:
        recommendations["use_priority_ordering"] = True
        recommendations["reasoning"].append("High priority requests - use priority ordering")

    return recommendations