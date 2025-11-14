"""
Batch processor for handling multiple scraping requests

Provides comprehensive batch processing capabilities including queue management,
execution strategies, progress tracking, and result aggregation.
"""

import asyncio
import time
import gc
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque, defaultdict
import weakref

from .models import (
    BatchRequest, BatchResult, NaturalLanguageRequest, NLPProcessingResult,
    PipetConfiguration, ScrapingExecution, ProcessingStatus, ResourceUsage
)
from .nlp_interface import NLPProcessor
from .pipet_config_generator import PipetConfigGenerator
from .single_executor import SingleExecutionOrchestrator
from .data_transformers import DataTransformer
from .execution_strategies import ExecutionStrategy, create_strategy
from .exceptions import BatchExecutionError, ValidationError, NLPProcessingError
from .logging_config import StructuredLogger
from .monitoring import ResourceTracker, PerformanceTimerContext, track_resources
from .config import get_global_config


@dataclass
class BatchQueue:
    """Thread-safe queue for batch requests"""

    queue: deque = field(default_factory=deque)
    max_size: int = 100
    priority_queue: bool = field(default=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self):
        if self.priority_queue:
            # For priority queue, we'll store tuples of (priority, timestamp, request)
            self.queue = deque()

    async def enqueue(self, request: NaturalLanguageRequest) -> None:
        """Add request to queue"""
        async with self._lock:
            if len(self.queue) >= self.max_size:
                raise OverflowError("Batch queue is full")

            if self.priority_queue:
                # Store with priority and timestamp for ordering
                priority = getattr(request, 'priority', 3)
                timestamp = time.time()
                # Use negative priority for max-heap behavior
                self.queue.append((-priority, timestamp, request))
                # Maintain heap property
                self.queue = deque(sorted(self.queue))
            else:
                self.queue.append(request)

    async def dequeue(self) -> NaturalLanguageRequest:
        """Remove and return next request from queue"""
        async with self._lock:
            if not self.queue:
                raise IndexError("Batch queue is empty")

            if self.priority_queue:
                priority, timestamp, request = self.queue.popleft()
                return request
            else:
                return self.queue.popleft()

    async def peek(self) -> Optional[NaturalLanguageRequest]:
        """Peek at next request without removing it"""
        async with self._lock:
            if not self.queue:
                return None

            if self.priority_queue:
                priority, timestamp, request = self.queue[0]
                return request
            else:
                return self.queue[0]

    def empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.queue) == 0

    def size(self) -> int:
        """Get current queue size"""
        return len(self.queue)

    def full(self) -> bool:
        """Check if queue is full"""
        return len(self.queue) >= self.max_size


@dataclass
class BatchExecutionManager:
    """Manages batch execution lifecycle and state"""

    active_batches: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    batch_history: List[Dict[str, Any]] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self):
        # Store weak references for cleanup
        self._batch_refs = weakref.WeakValueDictionary()

    async def create_batch_request(
        self,
        requests: List[NaturalLanguageRequest],
        batch_options: Optional[Dict[str, Any]] = None
    ) -> BatchRequest:
        """Create a new batch request"""
        batch_request = BatchRequest(
            requests=requests,
            **(batch_options or {})
        )

        # Store in active batches
        async with self._lock:
            self.active_batches[batch_request.batch_id] = {
                "request": batch_request.dict(),
                "status": "created",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

        return batch_request

    async def schedule_batch_execution(
        self,
        batch_request: BatchRequest
    ) -> str:
        """Schedule batch execution"""
        execution_id = f"exec_{batch_request.batch_id}_{int(time.time())}"

        async with self._lock:
            if batch_request.batch_id not in self.active_batches:
                raise ValidationError(f"Batch {batch_request.batch_id} not found")

            # Update status
            self.active_batches[batch_request.batch_id]["status"] = "scheduled"
            self.active_batches[batch_request.batch_id]["scheduled_at"] = datetime.now()
            self.active_batches[batch_request.batch_id]["execution_id"] = execution_id
            self.active_batches[batch_request.batch_id]["updated_at"] = datetime.now()

        return execution_id

    async def get_batch_status(
        self,
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current status of batch"""
        async with self._lock:
            if batch_id in self.active_batches:
                return self.active_batches[batch_id].copy()
            else:
                # Check history
                for historical_batch in self.batch_history:
                    if historical_batch["batch_id"] == batch_id:
                        return historical_batch.copy()

        return None

    async def cancel_batch_execution(
        self,
        batch_id: str
    ) -> bool:
        """Cancel batch execution"""
        async with self._lock:
            if batch_id in self.active_batches:
                self.active_batches[batch_id]["status"] = "cancelled"
                self.active_batches[batch_id]["cancelled_at"] = datetime.now()
                self.active_batches[batch_id]["updated_at"] = datetime.now()
                return True

        return False

    async def archive_batch(self, batch_id: str) -> bool:
        """Archive completed batch to history"""
        async with self._lock:
            if batch_id in self.active_batches:
                batch_data = self.active_batches[batch_id]
                batch_data["archived_at"] = datetime.now()

                # Move to history
                self.batch_history.append(batch_data)
                del self.active_batches[batch_id]

                # Keep history size manageable
                if len(self.batch_history) > 1000:
                    self.batch_history = self.batch_history[-500:]

                return True

        return False

    def aggregate_batch_results(
        self,
        batch_id: str,
        execution_results: List[ScrapingExecution]
    ) -> BatchResult:
        """Aggregate individual execution results into batch result"""
        # Calculate basic statistics
        total_requests = len(execution_results)
        successful_requests = len([
            e for e in execution_results
            if e.status == ProcessingStatus.COMPLETED
        ])
        failed_requests = len([
            e for e in execution_results
            if e.status == ProcessingStatus.FAILED
        ])
        cancelled_requests = len([
            e for e in execution_results
            if e.status == ProcessingStatus.CANCELLED
        ])

        # Calculate timing
        start_time = min(e.start_time for e in execution_results)
        end_time = max(
            e.end_time for e in execution_results
            if e.end_time
        )

        total_duration = (end_time - start_time).total_seconds() if end_time else 0

        # Calculate resource usage
        total_resource_usage = ResourceUsage(
            cpu_time=sum(e.resource_usage.cpu_time for e in execution_results if e.resource_usage),
            wall_time=sum(e.resource_usage.wall_time for e in execution_results if e.resource_usage),
            memory_peak=max(
                e.resource_usage.memory_peak for e in execution_results
                if e.resource_usage
            ),
            memory_average=sum(
                e.resource_usage.memory_average for e in execution_results
                if e.resource_usage
            ) / len(execution_results) if execution_results else 0,
            network_bytes_sent=sum(
                e.resource_usage.network_bytes_sent for e in execution_results
                if e.resource_usage
            ),
            network_bytes_received=sum(
                e.resource_usage.network_bytes_received for e in execution_results
                if e.resource_usage
            ),
            network_requests=sum(
                e.resource_usage.network_requests for e in execution_results
                if e.resource_usage
            ),
            subprocess_count=sum(
                e.resource_usage.subprocess_count for e in execution_results
                if e.resource_usage
            ),
            file_handles=sum(
                e.resource_usage.file_handles for e in execution_results
                if e.resource_usage
            )
        )

        return BatchResult(
            batch_id=batch_id,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            cancelled_requests=cancelled_requests,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            execution_results=execution_results,
            average_processing_time=(
                sum(e.duration for e in execution_results if e.duration) / len(execution_results)
            ),
            success_rate=successful_requests / total_requests if total_requests > 0 else 0.0,
            throughput=successful_requests / (total_duration / 60) if total_duration > 0 else 0.0,
            total_resource_usage=total_resource_usage,
            peak_memory_usage=max(
                e.resource_usage.memory_peak for e in execution_results
                if e.resource_usage
            ),
            peak_cpu_usage=max(
                e.monitoring_data.get("cpu_usage", 0) for e in execution_results
            ),
            total_data_records=sum(e.data_records_count for e in execution_results)
        )


class BatchProcessor:
    """High-performance batch processor for scraping operations"""

    def __init__(
        self,
        max_concurrent: int = 5,
        default_strategy: str = "adaptive",
        continue_on_error: bool = True,
        failure_threshold: float = 0.5,
        enable_monitoring: bool = True,
        enable_optimization: bool = True,
        resource_monitoring: bool = False
    ):
        self.logger = StructuredLogger("scraping.batch_processor")

        self.max_concurrent = max_concurrent
        self.default_strategy = default_strategy
        self.continue_on_error = continue_on_error
        self.failure_threshold = failure_threshold
        self.enable_monitoring = enable_monitoring
        self.enable_optimization = enable_optimization
        self.resource_monitoring = resource_monitoring

        # Initialize components
        self.config = get_global_config()
        self.nlp_processor = NLPProcessor()
        self.config_generator = PipetConfigGenerator(self.config)
        self.execution_manager = BatchExecutionManager()
        self.data_transformer = DataTransformer()

        # Create request queue
        self.request_queue = BatchQueue(max_size=1000, priority_queue=True)

        # Performance tracking
        self.performance_stats = {
            "total_batches_processed": 0,
            "total_requests_processed": 0,
            "average_batch_time": 0.0,
            "total_processing_time": 0.0,
            "cache_hits": 0,
            "retry_attempts": 0
        }

        # Execution strategies
        self.strategies = {
            "sequential": create_strategy("sequential"),
            "parallel": create_strategy("parallel"),
            "adaptive": create_strategy("adaptive")
        }

        # Resource tracking
        self.resource_tracker = ResourceTracker() if self.resource_monitoring else None
        self.performance_monitor = None

        # Cache for frequently used configurations
        self._config_cache = {}
        self._cache_max_size = 100

        self.logger.info(
            f"Batch processor initialized",
            max_concurrent=self.max_concurrent,
            default_strategy=self.default_strategy,
            enable_monitoring=self.enable_monitoring,
            enable_optimization=self.enable_optimization,
            operation="batch_processor_init"
        )

    async def process_batch_requests(
        self,
        requests: List[NaturalLanguageRequest],
        processing_strategy: Optional[str] = None,
        execution_options: Optional[Dict[str, Any]] = None,
        use_priority_ordering: bool = True,
        enable_caching: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> BatchResult:
        """
        Process a batch of natural language requests

        Args:
            requests: List of natural language requests
            processing_strategy: Execution strategy to use
            execution_options: Additional execution options
            use_priority_ordering: Whether to sort requests by priority
            enable_caching: Whether to enable result caching
            progress_callback: Optional progress callback function

        Returns:
            BatchResult with execution outcomes
        """
        if not requests:
            raise ValidationError("Empty request list provided")

        # Create batch request
        batch_options = execution_options or {}
        batch_options.update({
            "processing_strategy": processing_strategy or self.default_strategy,
            "priority_ordering": use_priority_ordering
        })

        batch_request = await self.execution_manager.create_batch_request(
            requests,
            batch_options
        )

        self.logger.info(
            f"Processing batch request",
            batch_id=batch_request.batch_id,
            requests_count=len(requests),
            strategy=batch_request.processing_strategy,
            operation="process_batch_requests"
        )

        # Start execution tracking
        execution_id = await self.execution_manager.schedule_batch_execution(
            batch_request
        )

        try:
            # Process the batch
            with track_resources(execution_id, self.resource_tracker) if self.resource_tracker else nullcontext():
                batch_result = await self._execute_batch_processing(
                    batch_request,
                    progress_callback
                )

            # Archive the batch
            await self.execution_manager.archive_batch(batch_request.batch_id)

            # Update performance statistics
            self._update_performance_stats(batch_result)

            self.logger.info(
                f"Batch processing completed",
                batch_id=batch_request.batch_id,
                success_rate=batch_result.success_rate,
                duration=batch_result.total_duration,
                operation="process_batch_requests"
            )

            return batch_result

        except Exception as e:
            # Update batch with error
            await self._handle_batch_error(batch_request.batch_id, e)
            raise BatchExecutionError(
                f"Batch processing failed: {str(e)}",
                batch_id=batch_request.batch_id,
                execution_id=execution_id
            )

    async def _execute_batch_processing(
        self,
        batch_request: BatchRequest,
        progress_callback: Optional[Callable] = None
    ) -> BatchResult:
        """Execute the actual batch processing"""
        start_time = datetime.now()

        # Strategy-based execution
        strategy_name = batch_request.processing_strategy
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            raise ValidationError(f"Unknown execution strategy: {strategy_name}")

        # Configure strategy
        await strategy.configure(
            max_concurrent=batch_request.max_concurrent,
            continue_on_error=batch_request.continue_on_error,
            failure_threshold=batch_request.failure_threshold
        )

        # Sort requests by priority if requested
        requests = batch_request.requests[:]
        if batch_request.priority_ordering:
            requests.sort(key=lambda r: getattr(r, 'priority', 3), reverse=True)

        # Track progress
        total_requests = len(requests)
        completed_requests = 0

        # Store execution results
        execution_results = []
        nlp_results = []
        configurations = []

        # Phase 1: NLP Processing and Configuration Generation
        self.logger.debug(
            f"Starting NLP and configuration generation",
            batch_id=batch_request.batch_id,
            requests_count=total_requests,
            operation="_execute_batch_processing"
        )

        nlp_start_time = time.time()

        for i, request in enumerate(requests):
            try:
                # Progress callback
                if progress_callback:
                    progress = (i + 1) / (total_requests * 2)  # 50% for NLP/config phase
                    await progress_callback(
                        batch_request.batch_id,
                        progress,
                        f"Processing request {i+1}/{total_requests}"
                    )

                # NLP processing
                nlp_result = await self.nlp_processor.process_single_request(request)
                nlp_results.append(nlp_result)

                # Configuration generation
                config = await self.config_generator.generate_configuration(nlp_result)
                configurations.append(config)

                self.logger.debug(
                    f"Completed NLP/config for request {i+1}",
                    batch_id=batch_request.batch_id,
                    request_id=request.request_id,
                    confidence=nlp_result.confidence_score,
                    operation="_execute_batch_processing"
                )

            except Exception as e:
                self.logger.warning(
                    f"NLP/config failed for request {i+1}",
                    batch_id=batch_request.batch_id,
                    request_id=request.request_id,
                    error=str(e),
                    operation="_execute_batch_processing"
                )

                # Create failed execution result
                failed_execution = ScrapingExecution(
                    execution_id=f"failed_{request.request_id}",
                    config_id=f"failed_{request.request_id}",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    status=ProcessingStatus.FAILED,
                    error_message=str(e)
                )
                execution_results.append(failed_execution)

                if not batch_request.continue_on_error:
                    raise

        nlp_duration = time.time() - nlp_start_time

        # Phase 2: Scraping Execution
        self.logger.debug(
            f"Starting scraping execution",
            batch_id=batch_request.batch_id,
            configurations_count=len(configurations),
            operation="_execute_batch_processing"
        )

        # Execute configurations using strategy
        scraping_results = await strategy.execute_batch(configurations)
        execution_results.extend(scraping_results)

        # Phase 3: Data Transformation and Consolidation
        if self.enable_optimization:
            self.logger.debug(
                f"Starting data transformation and consolidation",
                batch_id=batch_request.batch_id,
                operation="_execute_batch_processing"
            )

            # Transform data
            transformed_data = []
            for result in execution_results:
                if result.status == ProcessingStatus.COMPLETED and result.output_file:
                    try:
                        # Create scraped data record for transformation
                        records = self._create_scraped_data_records(result)
                        if records:
                            transformed_records.extend(
                                self.data_transformer.transform_batch(
                                    records,
                                    batch_request.consolidation_options
                                )
                            )
                    except Exception as e:
                        self.logger.warning(
                            f"Data transformation failed for {result.execution_id}",
                            batch_id=batch_request.batch_id,
                            error=str(e),
                            operation="_execute_batch_processing"
                        )

            # Consolidate results
            consolidated_data = await self._consolidate_results(
                batch_request,
                execution_results,
                transformed_data
            )

        # Create final batch result
        batch_result = self.execution_manager.aggregate_batch_results(
            batch_request.batch_id,
            execution_results
        )

        # Add enhanced metrics
        batch_result.total_data_records = sum(e.data_records_count for e in execution_results)
        batch_result.consolidated_data = consolidated_data
        batch_result.optimization_applied = self._get_optimizations_applied()
        batch_result.performance_metrics = self._calculate_performance_metrics(
            batch_result, nlp_duration, start_time
        )

        batch_result.resource_constraints = {
            "max_concurrent": batch_request.max_concurrent,
            "failure_threshold": batch_request.failure_threshold
        }

        return batch_result

    def _create_scraped_data_records(self, execution: ScrapingExecution) -> List[Any]:
        """Create scraped data records from execution result"""
        # This would typically read the output file and create records
        # For now, return empty list - implementation would depend on actual data format
        return []

    async def _consolidate_results(
        self,
        batch_request: BatchRequest,
        execution_results: List[ScrapingExecution],
        transformed_data: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """Consolidate results from multiple executions"""
        if not execution_results:
            return None

        consolidation_options = batch_request.consolidation_options
        if not consolidation_options:
            return None

        # Basic consolidation by data type
        consolidated = {
            "execution_summary": {
                "total_executions": len(execution_results),
                "successful_executions": len([
                    e for e in execution_results
                    if e.status == ProcessingStatus.COMPLETED
                ]),
                "failed_executions": len([
                    e for e in execution_results
                    if e.status == ProcessingStatus.FAILED
                ]),
                "total_data_records": sum(
                    e.data_records_count for e in execution_results
                )
            },
            "by_status": defaultdict(list)
        }

        # Group results by status
        for result in execution_results:
            consolidated["by_status"][result.status.value].append({
                "execution_id": result.execution_id,
                "config_id": result.config_id,
                "data_records_count": result.data_records_count,
                "duration": result.duration,
                "error_message": result.error_message
            })

        # Add transformed data if available
        if transformed_data:
            consolidated["transformed_data"] = {
                "total_records": len(transformed_data),
                "sample_data": transformed_data[:5]  # Show sample of transformed data
            }

        return consolidated

    def _get_optimizations_applied(self) -> List[str]:
        """Get list of optimizations applied during processing"""
        optimizations = []

        if self.enable_optimization:
            optimizations.extend([
                "memory_optimization",
                "resource_monitoring",
                "performance_tracking"
            ])

        if self.resource_monitoring:
            optimizations.append("resource_tracking")

        return optimizations

    def _calculate_performance_metrics(
        self,
        batch_result: BatchResult,
        nlp_duration: float,
        start_time: datetime
    ) -> Dict[str, float]:
        """Calculate detailed performance metrics"""
        total_duration = (datetime.now() - start_time).total_seconds()

        if total_duration > 0:
            return {
                "nlp_time_ratio": nlp_duration / total_duration,
                "execution_time_ratio": batch_result.total_duration / total_duration,
                "overhead_ratio": (total_duration - batch_result.total_duration) / total_duration,
                "requests_per_second": batch_result.total_requests / total_duration,
                "data_records_per_second": batch_result.total_data_records / total_duration,
                "memory_efficiency": batch_result.peak_memory_usage / (
                    batch_result.total_data_records if batch_result.total_data_records > 0 else 1
                )
            }

        return {}

    def _update_performance_stats(self, batch_result: BatchResult):
        """Update performance statistics"""
        self.performance_stats["total_batches_processed"] += 1
        self.performance_stats["total_requests_processed"] += batch_result.total_requests

        # Update timing statistics
        if batch_result.total_duration:
            total_time = self.performance_stats["total_processing_time"] + batch_result.total_duration
            batch_count = self.performance_stats["total_batches_processed"]
            self.performance_stats["average_batch_time"] = total_time / batch_count

    async def _handle_batch_error(self, batch_id: str, error: Exception):
        """Handle batch processing error"""
        self.logger.error(
            f"Batch processing error",
            batch_id=batch_id,
            error=str(error),
            operation="_handle_batch_error"
        )

        # Update batch status in execution manager
        await self.execution_manager.active_batches[batch_id].update({
            "status": "failed",
            "error": str(error),
            "failed_at": datetime.now()
        })

    def _get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            process = psutil.Process()
            return {
                "cpu_usage": process.cpu_percent(),
                "memory_usage": process.memory_percent(),
                "active_connections": len(self._get_active_connections()),
                "queue_size": self.request_queue.size()
            }
        except Exception:
            return {"cpu_usage": 0.0, "memory_usage": 0.0, "active_connections": 0, "queue_size": 0}

    def _get_active_connections(self) -> int:
        """Get count of active network connections"""
        # This would be implemented based on actual connection tracking
        return 0

    async def generate_batch_configurations(
        self,
        requests: List[NaturalLanguageRequest],
        enable_caching: bool = True
    ) -> List[PipetConfiguration]:
        """Generate configurations for batch requests with caching"""
        configurations = []
        cache_hits = 0

        for request in requests:
            # Check cache first if enabled
            cache_key = self._generate_cache_key(request)

            if enable_caching and cache_key in self._config_cache:
                configurations.append(self._config_cache[cache_key])
                cache_hits += 1
                continue

            # Generate configuration
            nlp_result = await self.nlp_processor.process_single_request(request)
            config = await self.config_generator.generate_configuration(nlp_result)
            configurations.append(config)

            # Cache if enabled
            if enable_caching:
                self._cache_configuration(cache_key, config)

        if cache_hits > 0:
            self.performance_stats["cache_hits"] += cache_hits
            self.logger.debug(
                f"Cache hits: {cache_hits}/{len(configurations)}",
                operation="generate_batch_configurations"
            )

        return configurations

    def _generate_cache_key(self, request: NaturalLanguageRequest) -> str:
        """Generate cache key for request"""
        # Create deterministic key from request
        key_data = f"{request.user_description}|{request.request_id}"
        return hash(key_data) % (self._cache_max_size * 10)

    def _cache_configuration(self, cache_key: str, config: PipetConfiguration):
        """Cache a configuration"""
        if len(self._config_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._config_cache.keys()))
            del self._config_cache[oldest_key]

        self._config_cache[cache_key] = config

    def validate_batch_request(self, requests: List[NaturalLanguageRequest]) -> None:
        """Validate batch request"""
        if not requests:
            raise ValidationError("Empty request list provided")

        # Check for duplicate request IDs
        request_ids = [req.request_id for req in requests]
        if len(request_ids) != len(set(request_ids)):
            raise ValidationError("Duplicate request IDs found in batch")

        # Validate individual requests
        for request in requests:
            if not request.user_description or not request.user_description.strip():
                raise ValidationError(f"Empty description in request {request.request_id}")

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "statistics": self.performance_stats.copy(),
            "queue_size": self.request_queue.size(),
            "cache_size": len(self._config_cache),
            "active_batches": len(self.execution_manager.active_batches),
            "batch_history_size": len(self.execution_manager.batch_history)
        }

    async def get_batch_result(
        self,
        batch_id: str,
        include_details: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get detailed batch result"""
        batch_status = await self.execution_manager.get_batch_status(batch_id)

        if not batch_status:
            return None

        result = {
            "batch_id": batch_id,
            "status": batch_status["status"],
            "created_at": batch_status.get("created_at"),
            "updated_at": batch_status.get("updated_at")
        }

        if include_details:
            result["request_details"] = batch_status.get("request", {})
            result["execution_details"] = batch_status.get("result", {})

        return result


# Convenience functions
def create_batch_processor(
    max_concurrent: int = 5,
    default_strategy: str = "adaptive",
    **kwargs
) -> BatchProcessor:
    """Create batch processor with custom configuration"""
    return BatchProcessor(
        max_concurrent=max_concurrent,
        default_strategy=default_strategy,
        **kwargs
    )


async def process_batch_requests(
    requests: List[NaturalLanguageRequest],
    **kwargs
) -> BatchResult:
    """Process batch requests (convenience function)"""
    processor = create_batch_processor()
    return await processor.process_batch_requests(requests, **kwargs)