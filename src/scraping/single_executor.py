"""
Single execution orchestrator for scraping operations

Coordinates the end-to-end execution of single scraping requests,
from natural language processing to data extraction and transformation.
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .nlp_interface import NLPInterface, NLPProcessor
from .pipet_config_generator import PipetConfigGenerator
from .config_validator import ConfigValidator
from .pipet_executor import PipetExecutor
from .data_transformers import DataTransformer
from .models import (
    NaturalLanguageRequest, NLPProcessingResult, PipetConfiguration,
    ScrapingExecution, ProcessingStatus, ScrapedDataRecord
)
from .exceptions import (
    NLPProcessingError, ConfigurationGenerationError,
    ValidationError, ExecutionError
)
from .config import get_global_config
from .logging_config import StructuredLogger


class SingleExecutionOrchestrator:
    """Orchestrates single scraping execution from request to result"""

    def __init__(self, config=None):
        self.logger = StructuredLogger("scraping.single_executor")
        self.config = config or get_global_config()

        # Initialize components
        self.nlp_processor = NLPProcessor()
        self.config_generator = PipetConfigGenerator(self.config)
        self.config_validator = ConfigValidator()
        self.pipet_executor = PipetExecutor()
        self.data_transformer = DataTransformer()

    async def execute_request(
        self,
        request: NaturalLanguageRequest,
        execution_options: Optional[Dict[str, Any]] = None
    ) -> ScrapingExecution:
        """
        Execute a single scraping request end-to-end

        Args:
            request: Natural language request from user
            execution_options: Options for execution (validation, transformation, etc.)

        Returns:
            Complete scraping execution result

        Raises:
            Various exceptions based on failure point
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Set default execution options
        options = {
            "validate_config": True,
            "perform_url_check": False,
            "perform_selector_test": False,
            "transform_data": True,
            "export_results": True,
            "output_format": "json"
        }
        if execution_options:
            options.update(execution_options)

        # Create execution tracking object
        execution = ScrapingExecution(
            execution_id=execution_id,
            config_id="",  # Will be set after config generation
            start_time=start_time,
            status=ProcessingStatus.PENDING
        )

        try:
            self.logger.info(
                f"Starting single execution",
                execution_id=execution_id,
                request_id=request.request_id,
                description_length=len(request.user_description),
                operation="execute_request"
            )

            # Step 1: Natural Language Processing
            self.logger.info("Step 1: Processing natural language request", execution_id=execution_id)
            execution.status = ProcessingStatus.PROCESSING

            nlp_result = await self.nlp_processor.process_single_request(request)
            execution.monitoring_data["nlp_confidence"] = nlp_result.confidence_score
            execution.monitoring_data["nlp_processing_time"] = nlp_result.processing_time

            self.logger.info(
                f"NLP processing completed",
                execution_id=execution_id,
                confidence_score=nlp_result.confidence_score,
                urls_extracted=len(nlp_result.extracted_urls),
                operation="execute_request"
            )

            # Step 2: Configuration Generation
            self.logger.info("Step 2: Generating pipet configuration", execution_id=execution_id)

            pipet_config = await self.config_generator.generate_configuration(nlp_result)
            execution.config_id = pipet_config.config_id
            execution.monitoring_data["config_generated"] = True

            self.logger.info(
                f"Configuration generated",
                execution_id=execution_id,
                config_id=pipet_config.config_id,
                selector_count=len(pipet_config.selectors),
                operation="execute_request"
            )

            # Step 3: Configuration Validation
            if options["validate_config"]:
                self.logger.info("Step 3: Validating configuration", execution_id=execution_id)

                validation_result = await self.config_validator.validate_configuration(
                    pipet_config,
                    perform_url_check=options["perform_url_check"],
                    perform_selector_test=options["perform_selector_test"]
                )
                execution.monitoring_data["config_validation"] = validation_result

                if not validation_result["is_valid"]:
                    raise ValidationError(
                        f"Configuration validation failed with score {validation_result['validation_score']:.2f}",
                        validation_issues=validation_result["issues"]
                    )

                self.logger.info(
                    f"Configuration validation passed",
                    execution_id=execution_id,
                    validation_score=validation_result["validation_score"],
                    operation="execute_request"
                )

            # Step 4: Pipet Execution
            self.logger.info("Step 4: Executing pipet configuration", execution_id=execution_id)
            execution.status = ProcessingStatus.PROCESSING

            pipet_execution = await self.pipet_executor.execute_configuration(pipet_config)

            # Update execution with pipet results
            execution.end_time = pipet_execution.end_time
            execution.duration = pipet_execution.duration
            execution.status = pipet_execution.status
            execution.exit_code = pipet_execution.exit_code
            execution.error_message = pipet_execution.error_message
            execution.data_records_count = pipet_execution.data_records_count
            execution.output_file = pipet_execution.output_file
            execution.file_size = pipet_execution.file_size
            execution.resource_usage = pipet_execution.resource_usage

            self.logger.info(
                f"Pipet execution completed",
                execution_id=execution_id,
                status=execution.status.value,
                records_count=execution.data_records_count,
                duration=execution.duration,
                operation="execute_request"
            )

            # Step 5: Data Transformation (if execution succeeded)
            if execution.status == ProcessingStatus.COMPLETED and options["transform_data"]:
                self.logger.info("Step 5: Transforming extracted data", execution_id=execution_id)

                # Load and transform extracted data
                transformed_records = await self._transform_extracted_data(
                    pipet_execution.output_file,
                    execution_id,
                    options
                )
                execution.monitoring_data["transformed_records"] = len(transformed_records)

                # Export transformed data if requested
                if options["export_results"]:
                    transformed_output_file = await self._export_transformed_data(
                        transformed_records,
                        execution_id,
                        options["output_format"]
                    )
                    execution.monitoring_data["transformed_output_file"] = transformed_output_file

                self.logger.info(
                    f"Data transformation completed",
                    execution_id=execution_id,
                    records_transformed=len(transformed_records),
                    operation="execute_request"
                )

            # Update final execution status
            if execution.status == ProcessingStatus.COMPLETED:
                self.logger.info(
                    f"Execution completed successfully",
                    execution_id=execution_id,
                    total_duration=(datetime.now() - start_time).total_seconds(),
                    records_extracted=execution.data_records_count,
                    operation="execute_request"
                )
            else:
                self.logger.error(
                    f"Execution failed",
                    execution_id=execution_id,
                    status=execution.status.value,
                    error_message=execution.error_message,
                    operation="execute_request"
                )

            return execution

        except (NLPProcessingError, ConfigurationGenerationError, ValidationError, ExecutionError) as e:
            # Handle known errors
            execution.status = ProcessingStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.duration = (execution.end_time - execution.start_time).total_seconds()

            self.logger.error(
                f"Execution failed with known error: {str(e)}",
                execution_id=execution_id,
                error_type=type(e).__name__,
                operation="execute_request"
            )

            raise

        except Exception as e:
            # Handle unexpected errors
            execution.status = ProcessingStatus.FAILED
            execution.error_message = f"Unexpected error: {str(e)}"
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.duration = (execution.end_time - execution.start_time).total_seconds()

            self.logger.error(
                f"Execution failed with unexpected error: {str(e)}",
                execution_id=execution_id,
                operation="execute_request"
            )

            raise ExecutionError(
                f"Single execution failed: {str(e)}",
                execution_id=execution_id
            )

    async def _transform_extracted_data(
        self,
        output_file: Optional[str],
        execution_id: str,
        options: Dict[str, Any]
    ) -> List[ScrapedDataRecord]:
        """Transform extracted data using data transformer"""
        if not output_file or not Path(output_file).exists():
            self.logger.warning(
                "No output file available for transformation",
                execution_id=execution_id,
                output_file=output_file,
                operation="transform_extracted_data"
            )
            return []

        try:
            # Read raw data (implementation depends on output format)
            raw_data = self._read_raw_data(output_file)

            # Convert to ScrapedDataRecord objects
            records = []
            for i, data_item in enumerate(raw_data):
                record = ScrapedDataRecord(
                    record_id=f"{execution_id}_{i}",
                    execution_id=execution_id,
                    source_url="",  # Would be populated from execution context
                    data_fields=data_item,
                    extraction_timestamp=datetime.now()
                )
                records.append(record)

            # Transform records
            transformation_config = {
                "remove_duplicates": options.get("remove_duplicates", True),
                "missing_values": options.get("missing_values", "drop")
            }

            transformed_records = self.data_transformer.transform_batch(
                records,
                transformation_config
            )

            return transformed_records

        except Exception as e:
            self.logger.error(
                f"Data transformation failed: {str(e)}",
                execution_id=execution_id,
                output_file=output_file,
                operation="transform_extracted_data"
            )
            raise ExecutionError(f"Data transformation failed: {str(e)}", execution_id=execution_id)

    async def _export_transformed_data(
        self,
        records: List[ScrapedDataRecord],
        execution_id: str,
        output_format: str
    ) -> str:
        """Export transformed data to specified format"""
        try:
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"transformed_data_{execution_id[:8]}_{timestamp}.{output_format}"
            output_path = f"data/output/{output_filename}"

            # Create output directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Export data
            success = self.data_transformer.export_to_format(
                records,
                output_format,
                output_path
            )

            if success:
                self.logger.info(
                    f"Transformed data exported successfully",
                    execution_id=execution_id,
                    output_path=output_path,
                    records_count=len(records),
                    operation="export_transformed_data"
                )
                return output_path
            else:
                raise ExecutionError("Data export failed", execution_id=execution_id)

        except Exception as e:
            self.logger.error(
                f"Data export failed: {str(e)}",
                execution_id=execution_id,
                operation="export_transformed_data"
            )
            raise

    def _read_raw_data(self, output_file: str) -> List[Dict[str, Any]]:
        """Read raw data from output file"""
        import json

        file_path = Path(output_file)
        if not file_path.exists():
            return []

        file_extension = file_path.suffix.lower()

        try:
            if file_extension == ".json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return [data]
                    else:
                        return []

            elif file_extension == ".csv":
                import pandas as pd
                df = pd.read_csv(file_path)
                return df.to_dict('records')

            else:
                self.logger.warning(
                    f"Unsupported file format for reading: {file_extension}",
                    output_file=output_file,
                    operation="read_raw_data"
                )
                return []

        except Exception as e:
            self.logger.error(
                f"Failed to read raw data: {str(e)}",
                output_file=output_file,
                operation="read_raw_data"
            )
            return []

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of an execution

        Args:
            execution_id: ID of the execution to check

        Returns:
            Current execution status or None if not found
        """
        # This would typically query a database or execution store
        # For now, return basic status information

        return {
            "execution_id": execution_id,
            "status": "unknown",  # Would be retrieved from storage
            "message": "Status tracking not implemented in this version"
        }

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an active execution

        Args:
            execution_id: ID of the execution to cancel

        Returns:
            True if cancellation was successful
        """
        self.logger.info(
            f"Cancellation requested for execution: {execution_id}",
            execution_id=execution_id,
            operation="cancel_execution"
        )

        # This would implement actual cancellation logic
        # For now, just log the request

        return True

    def create_execution_report(self, execution: ScrapingExecution) -> str:
        """Create detailed execution report"""
        report = []
        report.append("Scraping Execution Report")
        report.append("=" * 40)
        report.append(f"Execution ID: {execution.execution_id}")
        report.append(f"Config ID: {execution.config_id}")
        report.append(f"Start Time: {execution.start_time}")
        report.append(f"End Time: {execution.end_time}")
        report.append(f"Duration: {execution.duration:.2f} seconds")
        report.append(f"Status: {execution.status.value}")
        report.append(f"Exit Code: {execution.exit_code}")
        report.append(f"Records Extracted: {execution.data_records_count}")
        report.append(f"Output File: {execution.output_file}")
        report.append(f"File Size: {execution.file_size} bytes")

        if execution.error_message:
            report.append(f"Error Message: {execution.error_message}")

        # Resource usage
        if execution.resource_usage:
            report.append("\nResource Usage:")
            report.append(f"  CPU Time: {execution.resource_usage.cpu_time:.2f}s")
            report.append(f"  Wall Time: {execution.resource_usage.wall_time:.2f}s")
            report.append(f"  Peak Memory: {execution.resource_usage.memory_peak / 1024 / 1024:.2f} MB")
            report.append(f"  Network Bytes Sent: {execution.resource_usage.network_bytes_sent}")
            report.append(f"  Network Bytes Received: {execution.resource_usage.network_bytes_received}")

        # Monitoring data
        if execution.monitoring_data:
            report.append("\nMonitoring Data:")
            for key, value in execution.monitoring_data.items():
                report.append(f"  {key}: {value}")

        return "\n".join(report)


class BatchExecutionOrchestrator:
    """Orchestrates batch execution of multiple scraping requests"""

    def __init__(self, config=None):
        self.logger = StructuredLogger("scraping.batch_executor")
        self.config = config or get_global_config()
        self.single_executor = SingleExecutionOrchestrator(config)

    async def execute_batch(
        self,
        requests: List[NaturalLanguageRequest],
        batch_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute batch of scraping requests

        Args:
            requests: List of natural language requests
            batch_options: Options for batch execution

        Returns:
            Batch execution results
        """
        batch_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Set default batch options
        options = {
            "max_concurrent": 3,
            "continue_on_error": True,
            "execution_options": {
                "validate_config": True,
                "perform_url_check": False,
                "transform_data": True,
                "export_results": True
            }
        }
        if batch_options:
            options.update(batch_options)

        self.logger.info(
            f"Starting batch execution",
            batch_id=batch_id,
            requests_count=len(requests),
            max_concurrent=options["max_concurrent"],
            operation="execute_batch"
        )

        # Execute requests with concurrency control
        semaphore = asyncio.Semaphore(options["max_concurrent"])

        async def execute_single_with_semaphore(request):
            async with semaphore:
                try:
                    return await self.single_executor.execute_request(
                        request, options["execution_options"]
                    )
                except Exception as e:
                    self.logger.error(
                        f"Request execution failed: {str(e)}",
                        request_id=request.request_id,
                        batch_id=batch_id,
                        operation="execute_batch"
                    )
                    if not options["continue_on_error"]:
                        raise
                    # Return failed execution object
                    failed_execution = ScrapingExecution(
                        execution_id=str(uuid.uuid4()),
                        config_id="",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        status=ProcessingStatus.FAILED,
                        error_message=str(e)
                    )
                    return failed_execution

        # Execute all requests
        executions = await asyncio.gather(
            *[execute_single_with_semaphore(req) for req in requests],
            return_exceptions=True
        )

        # Process results
        successful_executions = []
        failed_executions = []

        for i, execution in enumerate(executions):
            if isinstance(execution, Exception):
                failed_executions.append({
                    "request_id": requests[i].request_id,
                    "error": str(execution)
                })
            elif execution.status == ProcessingStatus.COMPLETED:
                successful_executions.append(execution)
            else:
                failed_executions.append({
                    "request_id": requests[i].request_id,
                    "execution": execution,
                    "error": execution.error_message or "Execution failed"
                })

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Calculate batch statistics
        batch_results = {
            "batch_id": batch_id,
            "total_requests": len(requests),
            "successful_requests": len(successful_executions),
            "failed_requests": len(failed_executions),
            "success_rate": len(successful_executions) / len(requests),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration": total_duration,
            "average_duration": total_duration / len(requests),
            "executions": executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions
        }

        self.logger.info(
            f"Batch execution completed",
            batch_id=batch_id,
            success_rate=batch_results["success_rate"],
            successful=batch_results["successful_requests"],
            failed=batch_results["failed_requests"],
            duration=total_duration,
            operation="execute_batch"
        )

        return batch_results


# Convenience functions
def create_single_executor(config=None) -> SingleExecutionOrchestrator:
    """Create single execution orchestrator"""
    return SingleExecutionOrchestrator(config)


def create_batch_executor(config=None) -> BatchExecutionOrchestrator:
    """Create batch execution orchestrator"""
    return BatchExecutionOrchestrator(config)


async def execute_scraping_request(
    request: NaturalLanguageRequest,
    execution_options: Optional[Dict[str, Any]] = None
) -> ScrapingExecution:
    """Execute a single scraping request"""
    executor = SingleExecutionOrchestrator()
    return await executor.execute_request(request, execution_options)