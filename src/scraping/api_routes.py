"""
FastAPI routes for scraping operations

Provides REST API endpoints for single and batch scraping requests,
configuration management, and system monitoring.
"""

import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from .models import (
    NaturalLanguageRequest, NLPProcessingResult, PipetConfiguration,
    ScrapingExecution, ProcessingStatus, BatchRequest, BatchResult,
    AggregationStrategy
)
from .single_executor import SingleExecutionOrchestrator
from .batch_processor import BatchProcessor
from .batch_config_manager import BatchConfigManager, ConfigTemplateType, ConfigValidationLevel
from .batch_result_aggregator import BatchResultAggregator
from .config_validator import ConfigValidator
from .logging_config import StructuredLogger
from .exceptions import (
    NLPProcessingError, ConfigurationGenerationError,
    ValidationError, ExecutionError, BatchExecutionError
)


# Create router
router = APIRouter(prefix="/api/v1", tags=["scraping"])
logger = StructuredLogger("scraping.api_routes")

# Global executors (in production, these would be properly managed)
single_executor = SingleExecutionOrchestrator()
batch_processor = BatchProcessor()
config_manager = BatchConfigManager()
result_aggregator = BatchResultAggregator()
config_validator = ConfigValidator()

# Active executions storage (in production, use proper database)
active_executions = {}
active_batches = {}


# Pydantic models for API requests/responses
class ScrapingRequest(BaseModel):
    user_description: str = Field(..., description="Natural language description of scraping task")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")
    execution_options: Optional[Dict[str, Any]] = Field(None, description="Execution options")


class ScrapingResponse(BaseModel):
    execution_id: str
    status: str
    message: str
    execution_details: Optional[Dict[str, Any]] = None


class BatchScrapingRequest(BaseModel):
    requests: List[ScrapingRequest]
    batch_options: Optional[Dict[str, Any]] = Field(None, description="Batch execution options")


class ValidationRequest(BaseModel):
    config: Dict[str, Any]
    validation_options: Optional[Dict[str, Any]] = Field(None, description="Validation options")


class StatusResponse(BaseModel):
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


# Enhanced Batch Processing Models
class EnhancedBatchRequest(BaseModel):
    requests: List[ScrapingRequest]
    processing_strategy: str = Field(default="adaptive", description="Execution strategy")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="Maximum concurrent executions")
    timeout_per_request: int = Field(default=300, ge=1, le=3600, description="Timeout per request")
    continue_on_error: bool = Field(default=True, description="Continue on individual failures")
    priority_ordering: bool = Field(default=True, description="Enable priority ordering")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    aggregation_strategy: str = Field(default="union", description="Data aggregation strategy")
    consolidation_options: Optional[Dict[str, Any]] = Field(None, description="Data consolidation options")
    template_id: Optional[str] = Field(None, description="Configuration template to use")
    execution_options: Optional[Dict[str, Any]] = Field(None, description="Additional execution options")


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    cancelled_requests: int
    success_rate: float
    total_duration: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    error_summary: Optional[List[Dict[str, Any]]] = None


class ConfigurationTemplateRequest(BaseModel):
    template_type: str = Field(..., description="Template type")
    url: str = Field(..., description="Target URL")
    selectors: Dict[str, str] = Field(..., description="CSS selectors")
    user_overrides: Optional[Dict[str, Any]] = Field(None, description="User configuration overrides")


class ConfigurationValidationRequest(BaseModel):
    config: Dict[str, Any]
    validation_level: str = Field(default="basic", description="Validation level")
    optimize_config: bool = Field(default=False, description="Optimize configuration")


class BatchReportRequest(BaseModel):
    batch_id: str
    report_format: str = Field(default="summary", description="Report format")
    include_detailed_data: bool = Field(default=False, description="Include detailed execution data")


# API Routes

@router.post("/scrape", response_model=ScrapingResponse)
async def create_scraping_task(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Create and execute a new scraping task.

    This endpoint accepts a natural language description and creates a scraping
    configuration that is executed asynchronously.
    """
    try:
        # Generate execution ID
        execution_id = str(uuid.uuid4())

        # Create natural language request
        nl_request = NaturalLanguageRequest(
            request_id=str(uuid.uuid4()),
            user_description=request.user_description,
            user_context=request.user_context or {}
        )

        # Store initial execution status
        active_executions[execution_id] = {
            "status": "pending",
            "created_at": datetime.now(),
            "request": nl_request.dict()
        }

        # Start execution in background
        background_tasks.add_task(
            execute_scraping_task,
            execution_id,
            nl_request,
            request.execution_options or {}
        )

        logger.info(
            f"Scraping task created",
            execution_id=execution_id,
            description_length=len(request.user_description),
            operation="create_scraping_task"
        )

        return ScrapingResponse(
            execution_id=execution_id,
            status="pending",
            message="Scraping task created and queued for execution",
            execution_details={
                "created_at": datetime.now().isoformat(),
                "estimated_duration": "30-120 seconds"
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to create scraping task: {str(e)}",
            operation="create_scraping_task"
        )
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


async def execute_scraping_task(
    execution_id: str,
    request: NaturalLanguageRequest,
    execution_options: Dict[str, Any]
):
    """Execute scraping task in background"""
    try:
        # Update execution status
        active_executions[execution_id]["status"] = "processing"
        active_executions[execution_id]["started_at"] = datetime.now()

        # Execute scraping
        execution = await single_executor.execute_request(request, execution_options)

        # Store execution result
        active_executions[execution_id]["status"] = execution.status.value
        active_executions[execution_id]["completed_at"] = datetime.now()
        active_executions[execution_id]["result"] = execution.dict()

        logger.info(
            f"Scraping task completed",
            execution_id=execution_id,
            status=execution.status.value,
            records_count=execution.data_records_count,
            operation="execute_scraping_task"
        )

    except Exception as e:
        # Update execution status with error
        active_executions[execution_id]["status"] = "failed"
        active_executions[execution_id]["completed_at"] = datetime.now()
        active_executions[execution_id]["error"] = str(e)

        logger.error(
            f"Scraping task failed",
            execution_id=execution_id,
            error=str(e),
            operation="execute_scraping_task"
        )


@router.get("/scrape/{execution_id}", response_model=StatusResponse)
async def get_scraping_status(execution_id: str):
    """Get status of a scraping task."""
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution_data = active_executions[execution_id]

    return StatusResponse(
        status=execution_data["status"],
        timestamp=execution_data.get("completed_at", execution_data.get("started_at", execution_data["created_at"])),
        details={
            "created_at": execution_data["created_at"],
            "started_at": execution_data.get("started_at"),
            "completed_at": execution_data.get("completed_at"),
            "result": execution_data.get("result"),
            "error": execution_data.get("error")
        }
    )


@router.delete("/scrape/{execution_id}")
async def cancel_scraping_task(execution_id: str):
    """Cancel a scraping task."""
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution_data = active_executions[execution_id]

    if execution_data["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed execution")

    try:
        # Attempt cancellation
        cancelled = await single_executor.cancel_execution(execution_id)

        if cancelled:
            execution_data["status"] = "cancelled"
            execution_data["completed_at"] = datetime.now()

            logger.info(
                f"Scraping task cancelled",
                execution_id=execution_id,
                operation="cancel_scraping_task"
            )

            return {"message": "Task cancelled successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel task")

    except Exception as e:
        logger.error(
            f"Failed to cancel task: {str(e)}",
            execution_id=execution_id,
            operation="cancel_scraping_task"
        )
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/scrape/batch", response_model=Dict[str, Any])
async def create_batch_scraping_task(
    request: BatchScrapingRequest,
    background_tasks: BackgroundTasks
):
    """Create and execute a batch of scraping tasks."""
    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Convert API requests to natural language requests
        nl_requests = []
        for req in request.requests:
            nl_request = NaturalLanguageRequest(
                request_id=str(uuid.uuid4()),
                user_description=req.user_description,
                user_context=req.user_context or {}
            )
            nl_requests.append(nl_request)

        # Store initial batch status
        active_executions[batch_id] = {
            "status": "pending",
            "created_at": datetime.now(),
            "type": "batch",
            "requests_count": len(nl_requests)
        }

        # Start batch execution in background
        background_tasks.add_task(
            execute_batch_scraping_task,
            batch_id,
            nl_requests,
            request.batch_options or {}
        )

        logger.info(
            f"Batch scraping task created",
            batch_id=batch_id,
            requests_count=len(nl_requests),
            operation="create_batch_scraping_task"
        )

        return {
            "batch_id": batch_id,
            "status": "pending",
            "message": "Batch scraping task created and queued for execution",
            "requests_count": len(nl_requests),
            "created_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to create batch task: {str(e)}",
            operation="create_batch_scraping_task"
        )
        raise HTTPException(status_code=500, detail=f"Failed to create batch task: {str(e)}")


async def execute_batch_scraping_task(
    batch_id: str,
    requests: List[NaturalLanguageRequest],
    batch_options: Dict[str, Any]
):
    """Execute batch scraping task in background"""
    try:
        # Update batch status
        active_executions[batch_id]["status"] = "processing"
        active_executions[batch_id]["started_at"] = datetime.now()

        # Execute batch
        batch_results = await batch_executor.execute_batch(requests, batch_options)

        # Store batch result
        active_executions[batch_id]["status"] = "completed"
        active_executions[batch_id]["completed_at"] = datetime.now()
        active_executions[batch_id]["result"] = batch_results

        logger.info(
            f"Batch scraping task completed",
            batch_id=batch_id,
            success_rate=batch_results["success_rate"],
            operation="execute_batch_scraping_task"
        )

    except Exception as e:
        # Update batch status with error
        active_executions[batch_id]["status"] = "failed"
        active_executions[batch_id]["completed_at"] = datetime.now()
        active_executions[batch_id]["error"] = str(e)

        logger.error(
            f"Batch scraping task failed",
            batch_id=batch_id,
            error=str(e),
            operation="execute_batch_scraping_task"
        )


@router.get("/scrape/batch/{batch_id}", response_model=StatusResponse)
async def get_batch_scraping_status(batch_id: str):
    """Get status of a batch scraping task."""
    if batch_id not in active_executions:
        raise HTTPException(status_code=404, detail="Batch execution not found")

    batch_data = active_executions[batch_id]

    if batch_data.get("type") != "batch":
        raise HTTPException(status_code=400, detail="Not a batch execution")

    return StatusResponse(
        status=batch_data["status"],
        timestamp=batch_data.get("completed_at", batch_data.get("started_at", batch_data["created_at"])),
        details={
            "created_at": batch_data["created_at"],
            "started_at": batch_data.get("started_at"),
            "completed_at": batch_data.get("completed_at"),
            "requests_count": batch_data.get("requests_count"),
            "result": batch_data.get("result"),
            "error": batch_data.get("error")
        }
    )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_configuration(request: ValidationRequest):
    """Validate a pipet configuration."""
    try:
        # Convert dict to PipetConfiguration (simplified)
        config_data = request.config
        validation_options = request.validation_options or {}

        # Create configuration object
        from .models import PipetConfiguration, HttpMethod, OutputFormat, RetryConfig, RateLimitConfig

        pipet_config = PipetConfiguration(
            config_id=config_data.get("config_id", "api_validation"),
            request_id="api_validation",
            url=config_data.get("url", ""),
            method=HttpMethod(config_data.get("method", "GET")),
            headers=config_data.get("headers", {}),
            selectors=config_data.get("selectors", {}),
            output_format=OutputFormat(config_data.get("output_format", "json")),
            output_file=config_data.get("output_file"),
            timeout=config_data.get("timeout", 30)
        )

        # Validate configuration
        validation_result = await config_validator.validate_configuration(
            pipet_config,
            perform_url_check=validation_options.get("perform_url_check", False),
            perform_selector_test=validation_options.get("perform_selector_test", False)
        )

        logger.info(
            f"Configuration validation completed",
            config_id=pipet_config.config_id,
            is_valid=validation_result["is_valid"],
            validation_score=validation_result["validation_score"],
            operation="validate_configuration"
        )

        return {
            "config_id": pipet_config.config_id,
            "is_valid": validation_result["is_valid"],
            "validation_score": validation_result["validation_score"],
            "issues": validation_result["issues"],
            "warnings": validation_result["warnings"],
            "suggestions": validation_result["suggestions"],
            "url_accessible": validation_result.get("url_accessible", False),
            "validation_timestamp": validation_result["validation_timestamp"]
        }

    except Exception as e:
        logger.error(
            f"Configuration validation failed: {str(e)}",
            operation="validate_configuration"
        )
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_system_status():
    """Get system status and statistics."""
    try:
        # Calculate statistics from active executions
        total_executions = len(active_executions)
        pending_executions = len([e for e in active_executions.values() if e["status"] == "pending"])
        processing_executions = len([e for e in active_executions.values() if e["status"] == "processing"])
        completed_executions = len([e for e in active_executions.values() if e["status"] == "completed"])
        failed_executions = len([e for e in active_executions.values() if e["status"] == "failed"])

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "statistics": {
                "total_executions": total_executions,
                "pending_executions": pending_executions,
                "processing_executions": processing_executions,
                "completed_executions": completed_executions,
                "failed_executions": failed_executions
            },
            "system_info": {
                "python_version": "3.13+",
                "asyncio_running": True,
                "data_directory": str(Path("data/").absolute()),
                "log_directory": str(Path("logs/").absolute())
            }
        }

    except Exception as e:
        logger.error(
            f"Failed to get system status: {str(e)}",
            operation="get_system_status"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/executions", response_model=List[Dict[str, Any]])
async def list_executions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of executions to return")
):
    """List scraping executions."""
    try:
        executions = []

        for execution_id, execution_data in active_executions.items():
            # Filter by status if specified
            if status and execution_data["status"] != status:
                continue

            executions.append({
                "execution_id": execution_id,
                "status": execution_data["status"],
                "created_at": execution_data["created_at"],
                "type": execution_data.get("type", "single"),
                "requests_count": execution_data.get("requests_count", 1)
            })

        # Sort by creation time (newest first) and limit
        executions.sort(key=lambda x: x["created_at"], reverse=True)
        executions = executions[:limit]

        return executions

    except Exception as e:
        logger.error(
            f"Failed to list executions: {str(e)}",
            operation="list_executions"
        )
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.get("/executions/{execution_id}/download")
async def download_execution_result(execution_id: str):
    """Download result file for an execution."""
    try:
        if execution_id not in active_executions:
            raise HTTPException(status_code=404, detail="Execution not found")

        execution_data = active_executions[execution_id]

        if execution_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="Execution not completed")

        result = execution_data.get("result")
        if not result or not result.get("output_file"):
            raise HTTPException(status_code=404, detail="No output file available")

        output_file = Path(result["output_file"])
        if not output_file.exists():
            raise HTTPException(status_code=404, detail="Output file not found")

        logger.info(
            f"Downloading execution result",
            execution_id=execution_id,
            output_file=str(output_file),
            operation="download_execution_result"
        )

        return FileResponse(
            path=output_file,
            filename=output_file.name,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to download result: {str(e)}",
            execution_id=execution_id,
            operation="download_execution_result"
        )
        raise HTTPException(status_code=500, detail=f"Failed to download result: {str(e)}")


@router.post("/upload/batch")
async def upload_batch_file(file: UploadFile = File(...)):
    """Upload and process batch requests from file."""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")

        # Read and parse file content
        content = await file.read()
        import json
        requests_data = json.loads(content.decode('utf-8'))

        if not isinstance(requests_data, list):
            raise HTTPException(status_code=400, detail="File must contain a JSON array of requests")

        # Convert to batch request
        batch_requests = []
        for req_data in requests_data:
            batch_requests.append(ScrapingRequest(
                user_description=req_data["user_description"],
                user_context=req_data.get("user_context"),
                execution_options=req_data.get("execution_options")
            ))

        # Create batch task
        batch_request = BatchScrapingRequest(requests=batch_requests)

        # Process the batch
        return await create_batch_scraping_task(batch_request, None)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(
            f"Failed to process batch file: {str(e)}",
            filename=file.filename,
            operation="upload_batch_file"
        )
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.delete("/executions/cleanup")
async def cleanup_old_executions(
    older_than_hours: int = Query(24, ge=1, description="Remove executions older than this many hours")
):
    """Clean up old execution records."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        removed_executions = []
        for execution_id, execution_data in list(active_executions.items()):
            created_at = execution_data["created_at"]
            if created_at < cutoff_time:
                # Remove old executions
                del active_executions[execution_id]
                removed_executions.append(execution_id)

        logger.info(
            f"Cleaned up old executions",
            removed_count=len(removed_executions),
            cutoff_hours=older_than_hours,
            operation="cleanup_old_executions"
        )

        return {
            "message": f"Cleaned up {len(removed_executions)} old executions",
            "removed_executions": removed_executions,
            "cutoff_time": cutoff_time.isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to cleanup executions: {str(e)}",
            operation="cleanup_old_executions"
        )
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Error handlers
@router.exception_handler(NLPProcessingError)
async def nlp_processing_error_handler(request, exc: NLPProcessingError):
    """Handle NLP processing errors."""
    logger.error(
        f"NLP processing error: {str(exc)}",
        error_code=exc.error_code,
        operation="nlp_error_handler"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "NLP Processing Error",
            "message": str(exc),
            "error_code": exc.error_code,
            "type": "nlp_processing_error"
        }
    )


@router.exception_handler(ConfigurationGenerationError)
async def config_generation_error_handler(request, exc: ConfigurationGenerationError):
    """Handle configuration generation errors."""
    logger.error(
        f"Configuration generation error: {str(exc)}",
        error_code=exc.error_code,
        operation="config_error_handler"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Configuration Generation Error",
            "message": str(exc),
            "error_code": exc.error_code,
            "type": "config_generation_error"
        }
    )


@router.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    """Handle validation errors."""
    logger.error(
        f"Validation error: {str(exc)}",
        error_code=exc.error_code,
        operation="validation_error_handler"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "error_code": exc.error_code,
            "type": "validation_error"
        }
    )


@router.exception_handler(ExecutionError)
async def execution_error_handler(request, exc: ExecutionError):
    """Handle execution errors."""
    logger.error(
        f"Execution error: {str(exc)}",
        error_code=exc.error_code,
        operation="execution_error_handler"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Execution Error",
            "message": str(exc),
            "error_code": exc.error_code,
            "type": "execution_error"
        }
    )


# Enhanced Batch Processing Endpoints

@router.post("/batch/process", response_model=Dict[str, Any])
async def process_enhanced_batch(
    request: EnhancedBatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Process batch scraping requests with advanced options.

    Supports multiple execution strategies, priority ordering, caching,
    and data consolidation with comprehensive monitoring.
    """
    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Convert API requests to natural language requests
        nl_requests = []
        for i, req in enumerate(request.requests):
            nl_request = NaturalLanguageRequest(
                request_id=str(uuid.uuid4()),
                user_description=req.user_description,
                user_context=req.user_context or {},
                priority=i + 1  # Simple priority assignment
            )
            nl_requests.append(nl_request)

        # Create batch request
        batch_request = BatchRequest(
            batch_id=batch_id,
            requests=nl_requests,
            processing_strategy=request.processing_strategy,
            max_concurrent=request.max_concurrent,
            timeout_per_request=request.timeout_per_request,
            continue_on_error=request.continue_on_error,
            priority_ordering=request.priority_ordering,
            analysis_type="multi_source",
            consolidation_options=request.consolidation_options or {}
        )

        # Store initial batch status
        active_batches[batch_id] = {
            "status": "pending",
            "created_at": datetime.now(),
            "batch_request": batch_request,
            "result": None,
            "error": None
        }

        # Start enhanced batch execution in background
        background_tasks.add_task(
            execute_enhanced_batch_processing,
            batch_id,
            batch_request,
            request.dict()
        )

        logger.info(
            f"Enhanced batch processing task created",
            batch_id=batch_id,
            strategy=request.processing_strategy,
            max_concurrent=request.max_concurrent,
            requests_count=len(nl_requests),
            operation="process_enhanced_batch"
        )

        return {
            "batch_id": batch_id,
            "status": "pending",
            "message": "Enhanced batch processing task created and queued for execution",
            "processing_strategy": request.processing_strategy,
            "max_concurrent": request.max_concurrent,
            "requests_count": len(nl_requests),
            "aggregation_strategy": request.aggregation_strategy,
            "created_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to create enhanced batch task: {str(e)}",
            operation="process_enhanced_batch"
        )
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced batch task: {str(e)}")


async def execute_enhanced_batch_processing(
    batch_id: str,
    batch_request: BatchRequest,
    request_options: Dict[str, Any]
):
    """Execute enhanced batch processing in background"""
    try:
        # Update batch status
        active_batches[batch_id]["status"] = "processing"
        active_batches[batch_id]["started_at"] = datetime.now()

        # Process batch using enhanced processor
        batch_result = await batch_processor.process_batch_requests(
            requests=batch_request.requests,
            processing_strategy=request_options["processing_strategy"],
            execution_options=request_options.get("execution_options", {}),
            use_priority_ordering=request_options["priority_ordering"],
            enable_caching=request_options["enable_caching"]
        )

        # Aggregate results if requested
        if request_options.get("aggregation_strategy"):
            aggregator = BatchResultAggregator()
            aggregated_result = await aggregator.aggregate_batch_results(
                batch_request=batch_request,
                execution_results=batch_result.execution_results,
                aggregation_strategy=AggregationStrategy(request_options["aggregation_strategy"]),
                consolidation_options=request_options.get("consolidation_options")
            )
            batch_result.consolidated_data = aggregated_result.consolidated_data
            batch_result.quality_metrics = aggregated_result.quality_metrics

        # Store batch result
        active_batches[batch_id]["status"] = "completed"
        active_batches[batch_id]["completed_at"] = datetime.now()
        active_batches[batch_id]["result"] = batch_result

        logger.info(
            f"Enhanced batch processing completed",
            batch_id=batch_id,
            success_rate=batch_result.success_rate,
            total_duration=batch_result.total_duration,
            operation="execute_enhanced_batch_processing"
        )

    except Exception as e:
        # Update batch status with error
        active_batches[batch_id]["status"] = "failed"
        active_batches[batch_id]["completed_at"] = datetime.now()
        active_batches[batch_id]["error"] = str(e)

        logger.error(
            f"Enhanced batch processing failed",
            batch_id=batch_id,
            error=str(e),
            operation="execute_enhanced_batch_processing"
        )


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_enhanced_batch_status(batch_id: str):
    """Get detailed status of enhanced batch processing."""
    try:
        if batch_id not in active_batches:
            raise HTTPException(status_code=404, detail="Batch execution not found")

        batch_data = active_batches[batch_id]
        result = batch_data.get("result")

        return BatchStatusResponse(
            batch_id=batch_id,
            status=batch_data["status"],
            total_requests=result.total_requests if result else 0,
            successful_requests=result.successful_requests if result else 0,
            failed_requests=result.failed_requests if result else 0,
            cancelled_requests=result.cancelled_requests if result else 0,
            success_rate=result.success_rate if result else 0.0,
            total_duration=result.total_duration if result else None,
            start_time=result.start_time if result else None,
            end_time=result.end_time if result else None,
            performance_metrics=result.performance_metrics if result else None,
            quality_metrics=result.quality_metrics if result else None,
            error_summary=result.error_summary if result else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get batch status: {str(e)}",
            batch_id=batch_id,
            operation="get_enhanced_batch_status"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@router.post("/batch/config/template", response_model=Dict[str, Any])
async def create_configuration_from_template(request: ConfigurationTemplateRequest):
    """Create configuration using predefined template."""
    try:
        # Create configuration from template
        config = config_manager.create_configuration_from_template(
            template_id=f"{request.template_type}_default",
            url=request.url,
            selectors=request.selectors,
            user_overrides=request.user_overrides
        )

        logger.info(
            f"Configuration created from template",
            template_type=request.template_type,
            config_id=config.config_id,
            url=request.url,
            operation="create_configuration_from_template"
        )

        return {
            "config_id": config.config_id,
            "template_type": request.template_type,
            "url": config.url,
            "confidence_score": config.confidence_score,
            "validation_status": config.validation_status,
            "configuration": config.dict(),
            "created_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to create configuration from template: {str(e)}",
            template_type=request.template_type,
            operation="create_configuration_from_template"
        )
        raise HTTPException(status_code=500, detail=f"Failed to create configuration: {str(e)}")


@router.get("/batch/templates", response_model=Dict[str, Any])
async def list_configuration_templates():
    """List available configuration templates."""
    try:
        templates_stats = config_manager.get_usage_statistics()

        logger.info(
            "Retrieved configuration templates list",
            total_templates=templates_stats["total_templates"],
            operation="list_configuration_templates"
        )

        return {
            "total_templates": templates_stats["total_templates"],
            "template_usage": templates_stats["template_usage"],
            "most_used_template": templates_stats.get("most_used_template"),
            "average_success_rate": templates_stats["average_success_rate"],
            "retrieved_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to list templates: {str(e)}",
            operation="list_configuration_templates"
        )
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.post("/batch/config/validate", response_model=Dict[str, Any])
async def validate_batch_configuration(request: ConfigurationValidationRequest):
    """Validate and optionally optimize batch configuration."""
    try:
        # Import configuration
        config = config_manager.import_configuration(request.config)

        # Validate configuration
        validation_level = ConfigValidationLevel(request.validation_level)
        validation_result = config_manager.validate_configuration(config, validation_level)

        response_data = {
            "config_id": config.config_id,
            "validation_level": request.validation_level,
            "is_valid": validation_result["is_valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "recommendations": validation_result["recommendations"]
        }

        # Optimize if requested
        if request.optimize_config:
            optimization_result = config_manager.optimize_configuration(config)
            response_data.update({
                "optimization_applied": optimization_result.optimization_applied,
                "performance_improvement": optimization_result.performance_improvement,
                "optimized_config": optimization_result.optimized_config.dict()
            })

        logger.info(
            f"Configuration validation completed",
            config_id=config.config_id,
            validation_level=request.validation_level,
            is_valid=validation_result["is_valid"],
            optimized=request.optimize_config,
            operation="validate_batch_configuration"
        )

        return response_data

    except Exception as e:
        logger.error(
            f"Failed to validate configuration: {str(e)}",
            operation="validate_batch_configuration"
        )
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")


@router.get("/batch/system/status", response_model=Dict[str, Any])
async def get_batch_system_status():
    """Get batch processing system status and statistics."""
    try:
        # Get batch statistics
        total_batches = len(active_batches)
        pending_batches = len([b for b in active_batches.values() if b["status"] == "pending"])
        processing_batches = len([b for b in active_batches.values() if b["status"] == "processing"])
        completed_batches = len([b for b in active_batches.values() if b["status"] == "completed"])
        failed_batches = len([b for b in active_batches.values() if b["status"] == "failed"])

        # Get template statistics
        templates_stats = config_manager.get_usage_statistics()

        return {
            "system_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "batch_statistics": {
                "total_batches": total_batches,
                "pending_batches": pending_batches,
                "processing_batches": processing_batches,
                "completed_batches": completed_batches,
                "failed_batches": failed_batches
            },
            "template_statistics": templates_stats,
            "processor_status": {
                "queue_active": True,
                "cache_enabled": True,
                "monitoring_active": True
            },
            "system_resources": {
                "active_executions": len(active_executions),
                "active_batches": len(active_batches),
                "memory_usage": "normal",  # Would be monitored in production
                "cpu_usage": "normal"  # Would be monitored in production
            }
        }

    except Exception as e:
        logger.error(
            f"Failed to get batch system status: {str(e)}",
            operation="get_batch_system_status"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.delete("/batch/{batch_id}")
async def cancel_batch_processing(batch_id: str):
    """Cancel batch processing task."""
    try:
        if batch_id not in active_batches:
            raise HTTPException(status_code=404, detail="Batch execution not found")

        batch_data = active_batches[batch_id]

        if batch_data["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed batch")

        # Update status to cancelled
        batch_data["status"] = "cancelled"
        batch_data["completed_at"] = datetime.now()

        logger.info(
            f"Batch processing cancelled",
            batch_id=batch_id,
            operation="cancel_batch_processing"
        )

        return {
            "message": "Batch processing cancelled successfully",
            "batch_id": batch_id,
            "cancelled_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to cancel batch: {str(e)}",
            batch_id=batch_id,
            operation="cancel_batch_processing"
        )
        raise HTTPException(status_code=500, detail=f"Failed to cancel batch: {str(e)}")


# Additional error handler for batch processing
@router.exception_handler(BatchExecutionError)
async def batch_execution_error_handler(request, exc: BatchExecutionError):
    """Handle batch execution errors."""
    logger.error(
        f"Batch execution error: {str(exc)}",
        error_code=exc.error_code,
        operation="batch_error_handler"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Batch Execution Error",
            "message": str(exc),
            "error_code": exc.error_code,
            "type": "batch_execution_error"
        }
    )