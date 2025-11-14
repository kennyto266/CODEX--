"""
Pipet executor wrapper for configuration execution and monitoring

Provides interface for executing pipet configurations with comprehensive
monitoring, error handling, and resource tracking.
"""

import asyncio
import subprocess
import json
import yaml
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .exceptions import ExecutionError, ValidationError, TimeoutError, NetworkError
from .models import PipetConfiguration, ScrapingExecution, ProcessingStatus, ResourceUsage
from .logging_config import StructuredLogger
from .config import get_global_config


class PipetExecutor:
    """Executor for running pipet configurations with monitoring"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.executor")
        self.config = get_global_config()

    async def execute_configuration(
        self,
        config: PipetConfiguration,
        timeout_override: Optional[int] = None
    ) -> ScrapingExecution:
        """
        Execute a single pipet configuration

        Args:
            config: Pipet configuration to execute
            timeout_override: Optional timeout override

        Returns:
            ScrapingExecution with execution results

        Raises:
            ValidationError: If configuration is invalid
            ExecutionError: If execution fails
            TimeoutError: If execution times out
        """
        execution = ScrapingExecution(
            config_id=config.config_id,
            start_time=datetime.now()
        )

        try:
            # Validate configuration
            await self._validate_configuration(config)

            # Create temporary configuration file
            config_file = await self._create_config_file(config)
            execution.execution_id = str(uuid.uuid4())

            self.logger.info(
                "Starting pipet execution",
                execution_id=execution.execution_id,
                config_id=config.config_id,
                url=config.url,
                operation="execute_configuration"
            )

            # Execute pipet
            result = await self._run_pipet(
                config_file=config_file,
                timeout=timeout_override or config.timeout,
                execution_id=execution.execution_id
            )

            # Process results
            await self._process_execution_result(execution, result, config)

        except Exception as e:
            execution.status = ProcessingStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.duration = (execution.end_time - execution.start_time).total_seconds()

            self.logger.error(
                f"Execution failed: {str(e)}",
                execution_id=execution.execution_id,
                config_id=config.config_id,
                operation="execute_configuration"
            )
            raise

        return execution

    async def _validate_configuration(self, config: PipetConfiguration) -> None:
        """Validate pipet configuration"""
        errors = []

        # URL validation
        if not config.url or not config.url.strip():
            errors.append("URL is required")

        # Selector validation
        if not config.selectors:
            errors.append("At least one selector is required")

        # Output format validation
        if not config.output_format:
            errors.append("Output format is required")

        # Timeout validation
        if config.timeout <= 0:
            errors.append("Timeout must be greater than 0")

        if errors:
            raise ValidationError(
                f"Configuration validation failed: {', '.join(errors)}",
                validation_issues=errors
            )

    async def _create_config_file(self, config: PipetConfiguration) -> Path:
        """Create temporary pipet configuration file"""
        config_data = {
            "url": config.url,
            "method": config.method.value.lower(),
            "headers": config.headers,
            "extract": {
                **config.selectors,
                **config.extract_rules
            },
            "output": {
                "format": config.output_format.value,
                "file": config.output_file
            }
        }

        # Add payload if present
        if config.payload:
            config_data["payload"] = config.payload

        # Add retry configuration
        config_data["retry"] = {
            "max_retries": config.retry_config.max_retries,
            "delay": config.retry_config.retry_delay,
            "backoff": config.retry_config.backoff_factor,
            "max_time": config.retry_config.max_retry_time
        }

        # Create temporary file
        temp_dir = Path(self.config.config_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        config_file = temp_dir / f"pipet_config_{config.config_id}.yaml"

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

            self.logger.debug(
                f"Created pipet configuration file: {config_file}",
                config_id=config.config_id,
                operation="create_config_file"
            )

            return config_file

        except Exception as e:
            raise ExecutionError(
                f"Failed to create configuration file: {str(e)}",
                config_id=config.config_id
            )

    async def _run_pipet(
        self,
        config_file: Path,
        timeout: int,
        execution_id: str
    ) -> subprocess.CompletedProcess:
        """Run pipet command with the given configuration file"""
        try:
            # Prepare pipet command
            cmd = ["pipet", "run", "--config", str(config_file)]

            self.logger.debug(
                f"Executing pipet command: {' '.join(cmd)}",
                execution_id=execution_id,
                operation="run_pipet",
                timeout=timeout
            )

            # Execute pipet
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                result = subprocess.CompletedProcess(
                    args=cmd,
                    returncode=process.returncode,
                    stdout=stdout,
                    stderr=stderr
                )

                self.logger.debug(
                    f"Pipet execution completed",
                    execution_id=execution_id,
                    returncode=result.returncode,
                    operation="run_pipet"
                )

                return result

            except asyncio.TimeoutError:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()

                raise TimeoutError(
                    f"Pipet execution timed out after {timeout} seconds",
                    timeout_duration=timeout,
                    operation_type="pipet_execution"
                )

        except FileNotFoundError:
            raise ExecutionError(
                "pipet command not found. Please ensure pipet is installed and in PATH",
                operation_type="pipet_not_found"
            )
        except Exception as e:
            raise ExecutionError(
                f"Failed to execute pipet: {str(e)}",
                operation_type="pipet_execution"
            )

    async def _process_execution_result(
        self,
        execution: ScrapingExecution,
        result: subprocess.CompletedProcess,
        config: PipetConfiguration
    ) -> None:
        """Process pipet execution result"""
        execution.end_time = datetime.now()
        execution.duration = (execution.end_time - execution.start_time).total_seconds()
        execution.exit_code = result.returncode

        if result.returncode == 0:
            execution.status = ProcessingStatus.COMPLETED
            self.logger.info(
                "Pipet execution completed successfully",
                execution_id=execution.execution_id,
                config_id=config.config_id,
                returncode=result.returncode,
                duration=execution.duration,
                operation="process_result"
            )

            # Check for output file
            if config.output_file and Path(config.output_file).exists():
                execution.output_file = config.output_file
                execution.file_size = Path(config.output_file).stat().st_size

                # Count records (simple estimation for JSON files)
                if config.output_format.value == "json":
                    try:
                        with open(config.output_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                execution.data_records_count = len(data)
                            elif isinstance(data, dict):
                                execution.data_records_count = 1
                    except Exception:
                        self.logger.warning(
                            "Could not parse output file to count records",
                            execution_id=execution.execution_id,
                            output_file=config.output_file,
                            operation="process_result"
                        )
        else:
            execution.status = ProcessingStatus.FAILED
            execution.error_message = f"Pipet execution failed with exit code {result.returncode}"

            if result.stderr:
                execution.error_message += f": {result.stderr.decode('utf-8', errors='replace')}"

            self.logger.error(
                f"Pipet execution failed: {execution.error_message}",
                execution_id=execution.execution_id,
                config_id=config.config_id,
                returncode=result.returncode,
                operation="process_result"
            )

    async def monitor_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Monitor the status of an executing scraping job

        Args:
            execution_id: Identifier of the execution to monitor

        Returns:
            Dictionary with current execution state
        """
        # This would integrate with a monitoring system
        # For now, return basic status
        return {
            "execution_id": execution_id,
            "status": "monitoring",
            "message": "Execution monitoring not fully implemented"
        }

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an executing scraping job

        Args:
            execution_id: Identifier of the execution to cancel

        Returns:
            True if cancellation was successful, False otherwise
        """
        # This would integrate with a process management system
        self.logger.info(
            f"Cancellation requested for execution: {execution_id}",
            execution_id=execution_id,
            operation="cancel_execution"
        )
        return True

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats

        Returns:
            List of supported format names
        """
        return ["json", "csv", "xml", "yaml"]