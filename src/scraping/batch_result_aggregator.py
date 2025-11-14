"""
Batch result aggregator for consolidating and analyzing batch scraping results

Provides comprehensive result aggregation, data consolidation, quality assessment,
and report generation for batch processing operations.
"""

import json
import statistics
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import pandas as pd
import numpy as np

from .models import (
    BatchResult, BatchRequest, ScrapingExecution, ScrapedDataRecord,
    DataQualityReport, QualityIssue, ProcessingStatus, FieldMetadata
)
from .exceptions import ValidationError, AggregationError
from .logging_config import StructuredLogger
from .data_transformers import DataTransformer


class AggregationStrategy(str, Enum):
    """Data aggregation strategies"""
    UNION = "union"  # Combine all records
    INTERSECTION = "intersection"  # Keep only common fields
    PRIORITY = "priority"  # Use priority-based merging
    TEMPORAL = "temporal"  # Time-based aggregation
    CUSTOM = "custom"  # Custom aggregation logic


class ConsolidationMethod(str, Enum):
    """Data consolidation methods"""
    CONCATENATE = "concatenate"  # Simple concatenation
    MERGE = "merge"  # Intelligent merging
    DEDUPLICATE = "deduplicate"  # Remove duplicates
    ENRICH = "enrich"  # Enrich missing data
    TRANSFORM = "transform"  # Apply transformations


@dataclass
class AggregationMetrics:
    """Metrics for aggregation process"""

    total_records_processed: int = 0
    unique_records: int = 0
    duplicate_records: int = 0
    missing_fields: Dict[str, int] = field(default_factory=dict)
    data_types: Dict[str, str] = field(default_factory=dict)
    field_coverage: Dict[str, float] = field(default_factory=dict)
    consistency_scores: Dict[str, float] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    aggregation_time: float = 0.0


@dataclass
class ConsolidationRule:
    """Rule for data consolidation"""

    rule_id: str
    field_name: str
    rule_type: str  # "fill_missing", "standardize", "validate", "transform"
    condition: Optional[str] = None
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1


class BatchResultAggregator:
    """Aggregator for batch scraping results"""

    def __init__(self):
        self.logger = StructuredLogger.get_logger(__name__)
        self.data_transformer = DataTransformer()

    def aggregate_batch_results(
        self,
        batch_request: BatchRequest,
        execution_results: List[ScrapingExecution],
        aggregation_strategy: AggregationStrategy = AggregationStrategy.UNION,
        consolidation_options: Optional[Dict[str, Any]] = None
    ) -> BatchResult:
        """Aggregate batch execution results into comprehensive batch result"""

        start_time = datetime.now()

        self.logger.info(
            "Starting batch result aggregation",
            batch_id=batch_request.batch_id,
            total_executions=len(execution_results),
            aggregation_strategy=aggregation_strategy
        )

        # Initialize metrics
        metrics = AggregationMetrics()

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
        start_time_batch = min(e.start_time for e in execution_results)
        end_time_batch = max(
            e.end_time for e in execution_results
            if e.end_time
        )
        total_duration = (end_time_batch - start_time_batch).total_seconds() if end_time_batch else 0

        # Aggregate resource usage
        total_resource_usage = self._aggregate_resource_usage(execution_results)

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(execution_results)

        # Create basic batch result
        batch_result = BatchResult(
            batch_id=batch_request.batch_id,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            cancelled_requests=cancelled_requests,
            start_time=start_time_batch,
            end_time=end_time_batch,
            total_duration=total_duration,
            execution_results=execution_results,
            average_processing_time=statistics.mean([
                e.duration for e in execution_results if e.duration
            ]) if execution_results else 0,
            success_rate=successful_requests / total_requests if total_requests > 0 else 0,
            throughput=successful_requests / (total_duration / 60) if total_duration > 0 else 0,
            total_resource_usage=total_resource_usage,
            performance_metrics=performance_metrics
        )

        # Consolidate data if requested
        if consolidation_options or batch_request.consolidation_options:
            consolidation_settings = consolidation_options or batch_request.consolidation_options

            try:
                consolidated_data, aggregation_metrics = self._consolidate_data(
                    execution_results=execution_results,
                    strategy=aggregation_strategy,
                    consolidation_settings=consolidation_settings
                )

                batch_result.consolidated_data = consolidated_data
                batch_result.total_data_records = aggregation_metrics.total_records_processed

                # Add aggregation metrics to performance metrics
                batch_result.performance_metrics.update({
                    "aggregation_metrics": asdict(aggregation_metrics),
                    "consolidation_method": consolidation_settings.get("method", "default")
                })

            except Exception as e:
                self.logger.error(
                    "Failed to consolidate data",
                    batch_id=batch_request.batch_id,
                    error=str(e)
                )
                batch_result.consolidated_data = None

        # Generate quality report
        try:
            quality_report = self._generate_quality_report(execution_results)
            batch_result.quality_metrics = {
                "overall_quality_score": quality_report.overall_quality_score,
                "completeness_score": quality_report.completeness_score,
                "accuracy_score": quality_report.accuracy_score,
                "timeliness_score": quality_report.timeliness_score,
                "consistency_score": quality_report.consistency_score,
                "quality_issues_count": len(quality_report.quality_issues)
            }
        except Exception as e:
            self.logger.error(
                "Failed to generate quality report",
                batch_id=batch_request.batch_id,
                error=str(e)
            )
            batch_result.quality_metrics = {}

        # Generate error summary
        error_summary = self._generate_error_summary(execution_results)
        batch_result.error_summary = error_summary

        # Calculate peak resource usage
        batch_result.peak_memory_usage = max([
            e.resource_usage.memory_peak for e in execution_results
            if e.resource_usage
        ], default=0)

        batch_result.peak_cpu_usage = self._calculate_peak_cpu_usage(execution_results)

        # Calculate additional metrics
        batch_result.concurrent_executions = batch_request.max_concurrent
        batch_result.retry_attempts = sum([
            len(e.monitoring_data.get("retry_attempts", [])) for e in execution_results
            if e.monitoring_data
        ])
        batch_result.cache_hits = sum([
            e.monitoring_data.get("cache_hits", 0) for e in execution_results
            if e.monitoring_data
        ])

        self.logger.info(
            "Completed batch result aggregation",
            batch_id=batch_request.batch_id,
            total_requests=total_requests,
            successful_requests=successful_requests,
            total_duration=total_duration,
            success_rate=batch_result.success_rate
        )

        return batch_result

    def _aggregate_resource_usage(
        self,
        executions: List[ScrapingExecution]
    ) -> Dict[str, Any]:
        """Aggregate resource usage from multiple executions"""

        total_cpu_time = sum(e.resource_usage.cpu_time for e in executions if e.resource_usage)
        total_wall_time = sum(e.resource_usage.wall_time for e in executions if e.resource_usage)
        total_memory_peak = max([
            e.resource_usage.memory_peak for e in executions
            if e.resource_usage
        ], default=0)
        avg_memory_average = statistics.mean([
            e.resource_usage.memory_average for e in executions
            if e.resource_usage
        ]) if executions else 0

        total_network_bytes_sent = sum(
            e.resource_usage.network_bytes_sent for e in executions
            if e.resource_usage
        )
        total_network_bytes_received = sum(
            e.resource_usage.network_bytes_received for e in executions
            if e.resource_usage
        )
        total_network_requests = sum(
            e.resource_usage.network_requests for e in executions
            if e.resource_usage
        )

        return {
            "total_cpu_time": total_cpu_time,
            "total_wall_time": total_wall_time,
            "peak_memory_usage": total_memory_peak,
            "average_memory_usage": avg_memory_average,
            "total_network_bytes_sent": total_network_bytes_sent,
            "total_network_bytes_received": total_network_bytes_received,
            "total_network_requests": total_network_requests
        }

    def _calculate_performance_metrics(
        self,
        executions: List[ScrapingExecution]
    ) -> Dict[str, float]:
        """Calculate detailed performance metrics"""

        durations = [e.duration for e in executions if e.duration]
        data_records = [e.data_records_count for e in executions if e.data_records_count > 0]
        file_sizes = [e.file_size for e in executions if e.file_size]

        metrics = {}

        if durations:
            metrics.update({
                "min_processing_time": min(durations),
                "max_processing_time": max(durations),
                "median_processing_time": statistics.median(durations),
                "std_dev_processing_time": statistics.stdev(durations) if len(durations) > 1 else 0
            })

        if data_records:
            metrics.update({
                "total_data_records": sum(data_records),
                "avg_records_per_execution": statistics.mean(data_records),
                "min_records_per_execution": min(data_records),
                "max_records_per_execution": max(data_records)
            })

        if file_sizes:
            metrics.update({
                "total_output_size": sum(file_sizes),
                "avg_file_size": statistics.mean(file_sizes),
                "largest_file_size": max(file_sizes),
                "smallest_file_size": min(file_sizes)
            })

        # Success rate by status
        status_counts = Counter(e.status for e in executions)
        total_executions = len(executions)

        metrics.update({
            "success_rate": status_counts[ProcessingStatus.COMPLETED] / total_executions,
            "failure_rate": status_counts[ProcessingStatus.FAILED] / total_executions,
            "timeout_rate": status_counts[ProcessingStatus.TIMEOUT] / total_executions,
            "cancellation_rate": status_counts[ProcessingStatus.CANCELLED] / total_executions
        })

        return metrics

    def _consolidate_data(
        self,
        execution_results: List[ScrapingExecution],
        strategy: AggregationStrategy,
        consolidation_settings: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], AggregationMetrics]:
        """Consolidate data from multiple execution results"""

        start_time = datetime.now()
        metrics = AggregationMetrics()

        # Collect all data records
        all_records = []
        for execution in execution_results:
            if execution.status == ProcessingStatus.COMPLETED and execution.output_file:
                try:
                    # Load data from output file (simplified)
                    # In practice, you'd load the actual scraped data
                    records = self._load_data_from_file(execution.output_file)
                    all_records.extend(records)
                except Exception as e:
                    self.logger.warning(
                        "Failed to load data from execution output",
                        execution_id=execution.execution_id,
                        output_file=execution.output_file,
                        error=str(e)
                    )
                    continue

        metrics.total_records_processed = len(all_records)

        # Apply consolidation strategy
        if strategy == AggregationStrategy.UNION:
            consolidated_data = self._union_consolidate(all_records, metrics)
        elif strategy == AggregationStrategy.INTERSECTION:
            consolidated_data = self._intersection_consolidate(all_records, metrics)
        elif strategy == AggregationStrategy.PRIORITY:
            consolidated_data = self._priority_consolidate(all_records, metrics)
        elif strategy == AggregationStrategy.TEMPORAL:
            consolidated_data = self._temporal_consolidate(all_records, metrics)
        else:
            consolidated_data = {"records": all_records, "consolidation_method": "none"}

        # Apply data quality improvements
        if consolidation_settings.get("apply_quality_improvements", False):
            consolidated_data = self._apply_quality_improvements(consolidated_data, metrics)

        # Calculate aggregation metrics
        aggregation_time = (datetime.now() - start_time).total_seconds()
        metrics.aggregation_time = aggregation_time

        return consolidated_data, metrics

    def _union_consolidate(
        self,
        records: List[Dict[str, Any]],
        metrics: AggregationMetrics
    ) -> Dict[str, Any]:
        """Union consolidation - combine all records"""

        # Remove duplicates based on a key field
        key_field = "id"  # Default key field
        unique_records = {}
        duplicates = 0

        for record in records:
            record_key = record.get(key_field, str(hash(str(record))))
            if record_key in unique_records:
                duplicates += 1
            else:
                unique_records[record_key] = record

        metrics.unique_records = len(unique_records)
        metrics.duplicate_records = duplicates

        # Calculate field coverage
        if unique_records:
            all_fields = set()
            for record in unique_records.values():
                all_fields.update(record.keys())

            for field in all_fields:
                field_count = sum(1 for record in unique_records.values() if field in record)
                metrics.field_coverage[field] = field_count / len(unique_records)

        return {
            "consolidation_method": "union",
            "total_unique_records": len(unique_records),
            "duplicates_removed": duplicates,
            "field_coverage": metrics.field_coverage,
            "records": list(unique_records.values())
        }

    def _intersection_consolidate(
        self,
        records: List[Dict[str, Any]],
        metrics: AggregationMetrics
    ) -> Dict[str, Any]:
        """Intersection consolidation - keep only common fields"""

        if not records:
            return {"consolidation_method": "intersection", "records": []}

        # Find common fields across all records
        common_fields = set(records[0].keys())
        for record in records[1:]:
            common_fields.intersection_update(record.keys())

        # Keep only common fields
        filtered_records = []
        for record in records:
            filtered_record = {field: record[field] for field in common_fields if field in record}
            filtered_records.append(filtered_record)

        metrics.field_coverage = {field: 1.0 for field in common_fields}

        return {
            "consolidation_method": "intersection",
            "common_fields": list(common_fields),
            "total_records": len(filtered_records),
            "field_coverage": metrics.field_coverage,
            "records": filtered_records
        }

    def _priority_consolidate(
        self,
        records: List[Dict[str, Any]],
        metrics: AggregationMetrics
    ) -> Dict[str, Any]:
        """Priority-based consolidation - merge records with priority rules"""

        # Sort records by some priority criteria (e.g., timestamp, completeness)
        prioritized_records = sorted(
            records,
            key=lambda x: (len(x), x.get("timestamp", "")),
            reverse=True
        )

        # Merge records, with higher priority records overwriting lower priority ones
        merged_records = {}
        for i, record in enumerate(prioritized_records):
            record_key = record.get("id", f"record_{i}")

            if record_key not in merged_records:
                merged_records[record_key] = record.copy()
            else:
                # Merge with higher priority taking precedence
                merged_records[record_key].update(record)

        metrics.unique_records = len(merged_records)

        return {
            "consolidation_method": "priority",
            "total_merged_records": len(merged_records),
            "priority_criteria": "field_count_then_timestamp",
            "records": list(merged_records.values())
        }

    def _temporal_consolidate(
        self,
        records: List[Dict[str, Any]],
        metrics: AggregationMetrics
    ) -> Dict[str, Any]:
        """Temporal consolidation - organize records by time"""

        # Group records by time periods
        time_groups = defaultdict(list)
        for record in records:
            timestamp = record.get("timestamp", record.get("date"))
            if timestamp:
                # Extract date part (simplified)
                date_key = timestamp.split("T")[0] if isinstance(timestamp, str) else str(timestamp)
                time_groups[date_key].append(record)
            else:
                time_groups["unknown"].append(record)

        # Calculate temporal statistics
        temporal_stats = {
            "total_time_periods": len(time_groups),
            "records_per_period": {period: len(group_records) for period, group_records in time_groups.items()},
            "time_range": {
                "start": min(time_groups.keys()) if time_groups else None,
                "end": max(time_groups.keys()) if time_groups else None
            }
        }

        return {
            "consolidation_method": "temporal",
            "temporal_statistics": temporal_stats,
            "time_groups": dict(time_groups),
            "records": records
        }

    def _apply_quality_improvements(
        self,
        data: Dict[str, Any],
        metrics: AggregationMetrics
    ) -> Dict[str, Any]:
        """Apply data quality improvements"""

        records = data.get("records", [])
        improved_records = []

        for record in records:
            improved_record = record.copy()

            # Remove empty/null fields
            improved_record = {k: v for k, v in improved_record.items() if v is not None and v != ""}

            # Standardize data types (simplified)
            for key, value in improved_record.items():
                if isinstance(value, str) and value.replace(".", "").replace("-", "").isdigit():
                    try:
                        improved_record[key] = float(value) if "." in value else int(value)
                    except ValueError:
                        pass

            improved_records.append(improved_record)

        # Update data type statistics
        field_types = defaultdict(set)
        for record in improved_records:
            for field, value in record.items():
                field_types[field].add(type(value).__name__)

        metrics.data_types = {field: list(types) for field, types in field_types.items()}

        return {
            **data,
            "quality_improvements_applied": True,
            "records": improved_records,
            "data_types": metrics.data_types
        }

    def _generate_quality_report(
        self,
        executions: List[ScrapingExecution]
    ) -> DataQualityReport:
        """Generate comprehensive data quality report"""

        # Calculate quality scores
        completeness_scores = []
        accuracy_scores = []
        timeliness_scores = []
        consistency_scores = []

        quality_issues = []

        for execution in executions:
            if execution.status == ProcessingStatus.COMPLETED:
                # Extract quality metrics from monitoring data
                monitoring = execution.monitoring_data or {}

                completeness = monitoring.get("completeness_score", 0.8)
                accuracy = monitoring.get("accuracy_score", 0.9)
                timeliness = monitoring.get("timeliness_score", 0.95)
                consistency = monitoring.get("consistency_score", 0.85)

                completeness_scores.append(completeness)
                accuracy_scores.append(accuracy)
                timeliness_scores.append(timeliness)
                consistency_scores.append(consistency)

                # Collect quality issues
                issues = monitoring.get("quality_issues", [])
                for issue in issues:
                    quality_issues.append(QualityIssue(
                        severity=issue.get("severity", "medium"),
                        issue_type=issue.get("type", "inconsistent"),
                        field_name=issue.get("field", "unknown"),
                        description=issue.get("description", ""),
                        affected_records=issue.get("affected_records", 1),
                        suggested_fix=issue.get("suggested_fix", "Review data")
                    ))

        # Calculate average scores
        overall_quality = statistics.mean([
            statistics.mean(completeness_scores) if completeness_scores else 0,
            statistics.mean(accuracy_scores) if accuracy_scores else 0,
            statistics.mean(timeliness_scores) if timeliness_scores else 0,
            statistics.mean(consistency_scores) if consistency_scores else 0
        ])

        return DataQualityReport(
            overall_quality_score=overall_quality,
            completeness_score=statistics.mean(completeness_scores) if completeness_scores else 0,
            accuracy_score=statistics.mean(accuracy_scores) if accuracy_scores else 0,
            timeliness_score=statistics.mean(timeliness_scores) if timeliness_scores else 0,
            consistency_score=statistics.mean(consistency_scores) if consistency_scores else 0,
            quality_issues=quality_issues,
            recommendations=self._generate_quality_recommendations(quality_issues)
        )

    def _generate_quality_recommendations(
        self,
        quality_issues: List[QualityIssue]
    ) -> List[str]:
        """Generate recommendations based on quality issues"""

        recommendations = []

        # Count issues by type
        issue_counts = Counter(issue.issue_type for issue in quality_issues)
        severity_counts = Counter(issue.severity for issue in quality_issues)

        # Generate recommendations based on issue patterns
        if issue_counts["missing"] > 0:
            recommendations.append("Review data selectors to ensure complete data extraction")

        if issue_counts["inaccurate"] > 0:
            recommendations.append("Validate CSS selectors and data transformation rules")

        if issue_counts["inconsistent"] > 0:
            recommendations.append("Standardize data formats and validation rules")

        if severity_counts["critical"] > 0:
            recommendations.append("Address critical quality issues before production deployment")

        if severity_counts["high"] > len(quality_issues) * 0.3:
            recommendations.append("Consider implementing additional data validation steps")

        # General recommendations
        if not recommendations:
            recommendations.append("Data quality is acceptable, continue monitoring")

        return recommendations

    def _generate_error_summary(
        self,
        executions: List[ScrapingExecution]
    ) -> List[Dict[str, Any]]:
        """Generate summary of errors encountered"""

        error_summary = []

        for execution in executions:
            if execution.status in [ProcessingStatus.FAILED, ProcessingStatus.TIMEOUT]:
                error_summary.append({
                    "execution_id": execution.execution_id,
                    "config_id": execution.config_id,
                    "status": execution.status.value,
                    "error_message": execution.error_message,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "duration": execution.duration,
                    "exit_code": execution.exit_code
                })

        return error_summary

    def _calculate_peak_cpu_usage(
        self,
        executions: List[ScrapingExecution]
    ) -> float:
        """Calculate peak CPU usage across executions"""

        cpu_usages = []

        for execution in executions:
            # Get CPU usage from monitoring data
            monitoring = execution.monitoring_data or {}
            cpu_usage = monitoring.get("peak_cpu_percent", 0)
            if cpu_usage > 0:
                cpu_usages.append(cpu_usage)

        return max(cpu_usages) if cpu_usages else 0.0

    def _load_data_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from file (simplified implementation)"""

        # This is a placeholder - in practice, you'd implement proper file loading
        # based on the file format (JSON, CSV, XML, etc.)

        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'records' in data:
                    return data['records']
                else:
                    return [data]

            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                return df.to_dict('records')

            else:
                # Default placeholder data
                return [
                    {
                        "id": f"record_{i}",
                        "data": f"sample_data_{i}",
                        "timestamp": datetime.now().isoformat()
                    }
                    for i in range(10)  # Placeholder 10 records
                ]

        except Exception as e:
            self.logger.error(
                "Failed to load data from file",
                file_path=file_path,
                error=str(e)
            )
            return []

    def export_batch_result(
        self,
        batch_result: BatchResult,
        export_format: str = "json",
        include_detailed_data: bool = False
    ) -> Dict[str, Any]:
        """Export batch result in specified format"""

        # Create export data
        export_data = {
            "batch_summary": {
                "batch_id": batch_result.batch_id,
                "total_requests": batch_result.total_requests,
                "successful_requests": batch_result.successful_requests,
                "failed_requests": batch_result.failed_requests,
                "success_rate": batch_result.success_rate,
                "total_duration": batch_result.total_duration,
                "throughput": batch_result.throughput
            },
            "performance_metrics": batch_result.performance_metrics,
            "quality_metrics": batch_result.quality_metrics,
            "error_summary": batch_result.error_summary,
            "resource_usage": asdict(batch_result.total_resource_usage) if batch_result.total_resource_usage else {}
        }

        # Include consolidated data if requested
        if include_detailed_data and batch_result.consolidated_data:
            export_data["consolidated_data"] = batch_result.consolidated_data

        # Include detailed execution results if requested
        if include_detailed_data:
            export_data["execution_details"] = [
                {
                    "execution_id": exec_result.execution_id,
                    "config_id": exec_result.config_id,
                    "status": exec_result.status.value,
                    "duration": exec_result.duration,
                    "data_records_count": exec_result.data_records_count,
                    "error_message": exec_result.error_message
                }
                for exec_result in batch_result.execution_results
            ]

        # Format based on export format
        if export_format.lower() == "json":
            return export_data
        elif export_format.lower() == "csv":
            # Convert to CSV-friendly format
            return self._convert_to_csv_format(export_data)
        else:
            raise ValidationError(f"Unsupported export format: {export_format}")

    def _convert_to_csv_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data to CSV-friendly format"""

        # Flatten nested structures for CSV export
        csv_data = {}

        # Batch summary
        for key, value in data["batch_summary"].items():
            csv_data[f"batch_{key}"] = value

        # Performance metrics (flatten)
        for key, value in data["performance_metrics"].items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    csv_data[f"perf_{key}_{sub_key}"] = sub_value
            else:
                csv_data[f"perf_{key}"] = value

        # Quality metrics
        for key, value in data["quality_metrics"].items():
            csv_data[f"quality_{key}"] = value

        return csv_data

    def generate_batch_report(
        self,
        batch_result: BatchResult,
        report_format: str = "summary"
    ) -> Dict[str, Any]:
        """Generate comprehensive batch report"""

        report = {
            "report_metadata": {
                "batch_id": batch_result.batch_id,
                "report_generated_at": datetime.now().isoformat(),
                "report_format": report_format
            }
        }

        if report_format == "summary":
            report.update({
                "executive_summary": {
                    "total_requests": batch_result.total_requests,
                    "success_rate": f"{batch_result.success_rate:.1%}",
                    "total_processing_time": f"{batch_result.total_duration:.2f} seconds",
                    "average_throughput": f"{batch_result.throughput:.2f} requests/minute"
                },
                "quality_overview": {
                    "overall_quality_score": f"{batch_result.quality_metrics.get('overall_quality_score', 0):.1%}",
                    "total_quality_issues": batch_result.quality_metrics.get('quality_issues_count', 0)
                },
                "performance_highlights": {
                    "fastest_execution": f"{batch_result.performance_metrics.get('min_processing_time', 0):.2f}s",
                    "slowest_execution": f"{batch_result.performance_metrics.get('max_processing_time', 0):.2f}s",
                    "total_data_extracted": batch_result.performance_metrics.get('total_data_records', 0)
                }
            })

        elif report_format == "detailed":
            report.update({
                "detailed_results": {
                    "execution_breakdown": self._generate_execution_breakdown(batch_result),
                    "error_analysis": self._generate_error_analysis(batch_result),
                    "resource_utilization": self._generate_resource_analysis(batch_result),
                    "quality_assessment": self._generate_quality_assessment(batch_result)
                }
            })

        return report

    def _generate_execution_breakdown(self, batch_result: BatchResult) -> Dict[str, Any]:
        """Generate detailed execution breakdown"""

        status_counts = {}
        duration_stats = {}

        for execution in batch_result.execution_results:
            # Count by status
            status = execution.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Collect duration statistics
            if execution.duration:
                duration_stats.setdefault(execution.status.value, []).append(execution.duration)

        # Calculate duration statistics by status
        duration_analysis = {}
        for status, durations in duration_stats.items():
            if durations:
                duration_analysis[status] = {
                    "count": len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "avg": statistics.mean(durations),
                    "median": statistics.median(durations)
                }

        return {
            "status_distribution": status_counts,
            "duration_analysis": duration_analysis
        }

    def _generate_error_analysis(self, batch_result: BatchResult) -> Dict[str, Any]:
        """Generate detailed error analysis"""

        error_types = Counter()
        error_messages = []

        for execution in batch_result.execution_results:
            if execution.status == ProcessingStatus.FAILED and execution.error_message:
                # Categorize error type (simplified)
                if "timeout" in execution.error_message.lower():
                    error_types["timeout"] += 1
                elif "connection" in execution.error_message.lower():
                    error_types["connection"] += 1
                elif "permission" in execution.error_message.lower():
                    error_types["permission"] += 1
                else:
                    error_types["other"] += 1

                error_messages.append(execution.error_message)

        return {
            "error_types": dict(error_types),
            "total_errors": len(error_messages),
            "error_rate": len(error_messages) / len(batch_result.execution_results) if batch_result.execution_results else 0,
            "sample_errors": error_messages[:5]  # First 5 error messages
        }

    def _generate_resource_analysis(self, batch_result: BatchResult) -> Dict[str, Any]:
        """Generate resource utilization analysis"""

        if not batch_result.total_resource_usage:
            return {"message": "No resource usage data available"}

        resource_usage = batch_result.total_resource_usage

        return {
            "memory_utilization": {
                "peak_usage_mb": resource_usage.get("peak_memory_usage", 0) / (1024 * 1024),
                "average_usage_mb": resource_usage.get("average_memory_usage", 0) / (1024 * 1024)
            },
            "network_utilization": {
                "total_requests": resource_usage.get("total_network_requests", 0),
                "bytes_sent": resource_usage.get("total_network_bytes_sent", 0),
                "bytes_received": resource_usage.get("total_network_bytes_received", 0)
            },
            "processing_efficiency": {
                "total_cpu_time": resource_usage.get("total_cpu_time", 0),
                "total_wall_time": resource_usage.get("total_wall_time", 0),
                "parallel_efficiency": (
                    resource_usage.get("total_cpu_time", 0) / resource_usage.get("total_wall_time", 1)
                )
            }
        }

    def _generate_quality_assessment(self, batch_result: BatchResult) -> Dict[str, Any]:
        """Generate quality assessment"""

        quality_metrics = batch_result.quality_metrics or {}

        return {
            "overall_quality": {
                "score": quality_metrics.get("overall_quality_score", 0),
                "grade": self._calculate_quality_grade(quality_metrics.get("overall_quality_score", 0))
            },
            "quality_dimensions": {
                "completeness": quality_metrics.get("completeness_score", 0),
                "accuracy": quality_metrics.get("accuracy_score", 0),
                "timeliness": quality_metrics.get("timeliness_score", 0),
                "consistency": quality_metrics.get("consistency_score", 0)
            },
            "quality_issues": {
                "total_issues": quality_metrics.get("quality_issues_count", 0),
                "requires_attention": quality_metrics.get("quality_issues_count", 0) > 0
            }
        }

    def _calculate_quality_grade(self, score: float) -> str:
        """Calculate quality grade based on score"""

        if score >= 0.95:
            return "A+ (Excellent)"
        elif score >= 0.90:
            return "A (Very Good)"
        elif score >= 0.80:
            return "B (Good)"
        elif score >= 0.70:
            return "C (Fair)"
        elif score >= 0.60:
            return "D (Poor)"
        else:
            return "F (Very Poor)"